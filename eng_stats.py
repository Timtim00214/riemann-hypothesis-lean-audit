#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eng_stats.py — 黎曼猜想 Lean 工程的轻量结构统计（支持 .tar.gz / .zip / 解压源码目录）。

设计要点
  * 支持直接顺序流式读取官方 `external/lean.tar.gz`（或 `riemann-hypothesis-lean-main.zip`、
    或已解压的源码目录），无需解压 17.5 万个小文件到磁盘。
  * 只用 Python 标准库；默认输出到 `analysis/eng_stats.json` 与 `analysis/eng_stats.txt`。
  * 声明/import/tactic 统计是正则粗统计（注释、字符串里的关键字也会被计入），
    报告里一律标注为"粗统计"。

用法:
    python eng_stats.py [--archive external/lean.tar.gz] [--limit N] [--sample 3000]
"""

from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import math
import os
import re
import sys
import tarfile
import time
import zipfile
from collections import Counter, defaultdict, deque
from pathlib import Path

sys.dont_write_bytecode = True

_HERE = Path(__file__).resolve().parent
ROOT = _HERE.parent if _HERE.name == "analysis" else _HERE

DEFAULT_CANDIDATES = [
    ROOT / "external" / "lean.tar.gz",
    ROOT / "lean.tar.gz",
    ROOT / "riemann-hypothesis-lean-main.zip",
    ROOT / "external" / "riemann-hypothesis-lean-main.zip",
    ROOT / "repo" / "riemann-hypothesis-lean-main",
]
OUT_JSON = ROOT / "analysis" / "eng_stats.json"
OUT_TXT = ROOT / "analysis" / "eng_stats.txt"

SAMPLE_N = 3000

LIBS = {
    "BuildAid", "CompanionTheory", "Development", "Formalism", "GroundTheory",
    "GroundTheoryFields", "Lemmata", "PositivityTheory", "ReciprocityTheory",
    "Supplements", "Statements", "Main",
}

WATCH_WORDS = [
    "Statement", "Statements", "Proofs", "Proof", "PublishedTheorems",
    "MainOf", "Use", "Unfolding", "Assembly", "Reduction", "Explicit", "Of",
    "StatementGram", "Definitions", "Implementations", "Kernels",
]

SUFFIXES = [
    "Statement", "Statements", "Proof", "Proofs", "Def", "Definitions",
    "Assembly", "Reduction", "Explicit", "Use", "Unfolding", "Lemma", "Theorem",
]

PREFIXES = [
    "MainOf", "Of", "Explicit", "Use", "Unfolding", "Assembly", "Reduction",
    "Statement",
]

# ---------------------------------------------------------------- regexes

DECL_RE = re.compile(
    r"(?m)^[ \t]*(?:@\[[^\n]*\]\s*)?"
    r"(?:(?:private|protected|noncomputable|partial|unsafe|scoped|local)\s+)*"
    r"(theorem|lemma|def|abbrev|structure|class|instance|inductive)\b"
)

IMPORT_RE = re.compile(r"(?m)^[ \t]*import[ \t]+(\S+)")

ONELINE_THEOREM_RE = re.compile(r"(?m)^[^\n]*\btheorem\b[^\n]*:=")

COLON_BY_RE = re.compile(r":=\s*by\b")

WRAPPER_RE = re.compile(r"first\s*\|\s*exact\s*@")

AXIOM_RE = re.compile(
    r"(?m)^[ \t]*(?:@\[[^\n]*\]\s*)?(?:private|protected|noncomputable|unsafe\s+)*axiom\b"
)

TAC_RE = re.compile(r"\b(simp|simpa|simp_all|omega|norm_num|linarith|by)\b")

COMMENT_BLOCK_RE = re.compile(r"/-.*?-/", re.S)
COMMENT_LINE_RE = re.compile(r"--[^\n]*")
STRING_RE = re.compile(r'"(?:\\.|[^"\\])*"')
IDENT_RE = re.compile(r"[^\W\d_][\w'!?]*", re.UNICODE)
NUM_RE = re.compile(r"\d+")
WS_RE = re.compile(r"\s+")
CAMEL_RE = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z][a-z0-9]*|[a-z0-9]+|[^\x00-\x7f]+")

KEYWORDS = frozenset("""
theorem lemma def abbrev structure class instance inductive axiom constant
opaque example by exact intro intros apply simp simpa simp_all rw have let
show from fun Prop Type Sort sorry first assumption constructor refine obtain
cases induction unfold change congr ext rfl trivial norm_num omega linarith
nlinarith ring aesop positivity field_simp push_neg contrapose classical
noncomputable section namespace end open variable set_option in at with using
if then else match do return where deriving attribute local scoped macro
syntax elab run_cmd private protected partial unsafe universe import mutual
termination_by decreasing_by calc conv subsume
""".split())


def pct(sorted_vals, q):
    """Linear-interpolation percentile on an already sorted list."""
    if not sorted_vals:
        return 0
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (len(sorted_vals) - 1) * q
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_vals[int(k)]
    return sorted_vals[f] * (c - k) + sorted_vals[c] * (k - f)


def r2(x):
    return round(float(x), 2)


def line_summary(vals):
    if not vals:
        return {"files": 0}
    s = sorted(vals)
    return {
        "files": len(vals),
        "median": r2(pct(s, 0.50)),
        "mean": r2(sum(vals) / len(vals)),
        "p90": r2(pct(s, 0.90)),
        "max": max(vals),
        "le_10_lines": sum(1 for x in vals if x <= 10),
        "le_20_lines": sum(1 for x in vals if x <= 20),
        "le_5_lines": sum(1 for x in vals if x <= 5),
    }


def bucket(value, edges, labels):
    for e, lab in zip(edges, labels):
        if value <= e:
            return lab
    return labels[-1]


def camel_tokens(s):
    s = re.sub(r"[_\-\.]+", " ", s)
    return CAMEL_RE.findall(s)


def skeleton(text):
    """Replace identifiers (except Lean keywords) and numbers with I / N."""
    t = COMMENT_BLOCK_RE.sub(" ", text)
    t = COMMENT_LINE_RE.sub("", t)
    t = STRING_RE.sub('"S"', t)
    t = "\n".join(
        ln for ln in t.splitlines() if not ln.lstrip().startswith("import ")
    )
    t = IDENT_RE.sub(lambda m: m.group(0) if m.group(0) in KEYWORDS else "I", t)
    t = NUM_RE.sub("N", t)
    t = WS_RE.sub(" ", t).strip()
    return t


def proof_styles(text):
    """Count theorem declarations whose proof starts with `by` vs a term.

    Heuristic: from each `theorem` keyword, find the first top-level `:=`
    (bracket depth 0) and inspect the next token.  Encodings (structure
    literals, `let` bindings inside the statement) are rare in this corpus;
    the residual is reported as `unknown` by the caller.
    """
    by_n = 0
    term_n = 0
    for m in DECL_RE.finditer(text):
        if m.group(1) != "theorem":
            continue
        i = m.end()
        depth = 0
        while i < len(text):
            c = text[i]
            if c in "([{":
                depth += 1
            elif c in ")]}":
                if depth:
                    depth -= 1
            elif c == ":" and depth == 0 and i + 1 < len(text) \
                    and text[i + 1] == "=":
                j = i + 2
                while j < len(text) and text[j] in " \t\r\n":
                    j += 1
                if text.startswith("by", j) and (
                        j + 2 >= len(text)
                        or not (text[j + 2].isalnum() or text[j + 2] == "_")):
                    by_n += 1
                else:
                    term_n += 1
                break
            i += 1
    return by_n, term_n


def _iter_lean_sources(archive_path: Path):
    """Return (total_size_bytes, list_of_paths, list_of_sizes, reader_fn(idx)->bytes)."""
    name = archive_path.name.lower()
    if archive_path.is_dir():
        files = sorted(archive_path.rglob("*.lean"))
        paths = []
        sizes = []
        for f in files:
            rel = f.relative_to(archive_path).as_posix()
            if rel.startswith("src/"):
                rel = rel[4:]
            elif "/src/" in rel:
                rel = rel.split("/src/", 1)[1]
            paths.append(rel)
            sizes.append(f.stat().st_size)

        def read_dir(idx: int) -> bytes:
            return files[idx].read_bytes()

        def close_dir() -> None:
            pass

        return sum(sizes), paths, sizes, read_dir, close_dir

    if name.endswith(".zip"):
        zf = zipfile.ZipFile(archive_path)
        infos = [i for i in zf.infolist() if i.filename.endswith(".lean")]
        infos.sort(key=lambda i: i.filename)
        paths = []
        sizes = []
        for info in infos:
            fn = info.filename
            if "/src/" in fn:
                rel = fn.split("/src/", 1)[1]
            elif fn.startswith("src/"):
                rel = fn[4:]
            else:
                parts = fn.split("/", 2)
                rel = parts[2] if len(parts) > 2 else fn
            paths.append(rel)
            sizes.append(info.file_size)

        def read_zip(idx: int) -> bytes:
            with zf.open(infos[idx]) as fh:
                return fh.read()

        return archive_path.stat().st_size, paths, sizes, read_zip, zf.close

    if name.endswith(".tar.gz") or name.endswith(".tgz") or name.endswith(".tar"):
        tf = tarfile.open(archive_path, "r:*")
        entries: list[tuple[str, int, bytes]] = []
        for member in tf:
            if not member.isfile() or not member.name.endswith(".lean"):
                continue
            fn = member.name.lstrip("./")
            if "/src/" in fn:
                rel = fn.split("/src/", 1)[1]
            elif fn.startswith("src/"):
                rel = fn[4:]
            else:
                rel = fn
            fh = tf.extractfile(member)
            raw = fh.read() if fh is not None else b""
            entries.append((rel, member.size, raw))
        tf.close()
        entries.sort(key=lambda x: x[0])
        paths = [e[0] for e in entries]
        sizes = [e[1] for e in entries]

        def read_tar(idx: int) -> bytes:
            return entries[idx][2]

        def close_tar() -> None:
            entries.clear()

        return archive_path.stat().st_size, paths, sizes, read_tar, close_tar

    raise ValueError(f"Unsupported archive or directory format: {archive_path}")


def scan(archive_path: Path, limit=0, sample_n=SAMPLE_N):
    t0 = time.time()
    archive_bytes, all_paths, all_sizes, read_raw, close_fn = _iter_lean_sources(archive_path)
    if limit:
        paths = all_paths[:limit]
        sizes = all_sizes[:limit]
    else:
        paths = all_paths
        sizes = all_sizes
    n = len(paths)

    mod_to_idx = {p[:-5].replace("/", "."): i for i, p in enumerate(paths)}

    if n <= sample_n:
        sample_idx = set(range(n))
    else:
        sample_idx = {round(k * (n - 1) / (sample_n - 1)) for k in range(sample_n)}

    line_counts = []
    byte_counts = []
    decl_per_file = []
    theorem_per_file = []
    import_per_file = []
    lines_by_idx = []

    hist_lines = Counter()
    hist_bytes = Counter()
    hist_decls = Counter()
    hist_theorems = Counter()
    hist_imports = Counter()
    path_depth_hist = Counter()
    decl_totals = Counter()

    lib_agg = defaultdict(
        lambda: {"files": 0, "lines": 0, "bytes": 0, "decls": 0,
                 "theorems": 0, "imports": 0, "zero_import_files": 0,
                 "statement_files": 0, "proofdir_files": 0,
                 "published_files": 0, "wrapper_files": 0,
                 "one_theorem_files": 0}
    )
    dir2_agg = defaultdict(lambda: [0, 0, 0, 0, 0])
    dir3_agg = defaultdict(lambda: [0, 0, 0, 0, 0])

    edges = []
    unresolved = Counter()
    unresolved_samples = []
    matrix = Counter()

    tac_occ = Counter()
    tac_files = Counter()

    flags = Counter()

    top20 = []
    sample_rows = []
    special = []

    total_bytes = 0
    total_lines = 0
    total_decls = 0
    total_theorems = 0
    total_import_lines = 0
    proj_import_lines = 0
    mathlib_files = 0
    zero_proj_files = 0
    duplicate_import_files = 0
    read_errors = 0
    oneline_total = 0
    colon_by_total = 0
    by_proof_total = 0
    term_proof_total = 0
    wrapper_files = 0
    stmt_wrapper_files = 0
    import_only_files = 0
    mathlib_only_files = 0
    stmt_line_counts = []
    stmt_theorem_counts = []
    pub_line_counts = []
    proof_line_counts = []
    max_import = (0, "")
    max_decl = (0, "")

    t_read = time.time()

    for idx in range(n):
        p = paths[idx]
        try:
            raw = read_raw(idx)
        except Exception:
            read_errors += 1
            raw = b""
        text = raw.decode("utf-8", "replace")

        lines = text.count("\n")
        if text and not text.endswith("\n"):
            lines += 1

        parts = p.split("/")
        lib = parts[0] if len(parts) > 1 else "(root)"
        depth = max(0, len(parts) - 1)

        # ---- declarations ----
        decls = DECL_RE.findall(text)
        dc = Counter(decls)
        th = dc.get("theorem", 0)
        nd = len(decls)

        if p.endswith("Statement.lean"):
            stmt_line_counts.append(lines)
            stmt_theorem_counts.append(th)
        if "/PublishedTheorems/" in p:
            pub_line_counts.append(lines)
        if "/Proofs/" in p:
            proof_line_counts.append(lines)
        if nd > max_decl[0]:
            max_decl = (nd, p)

        # ---- imports ----
        imps = IMPORT_RE.findall(text)
        proj = [m for m in imps if m.split(".")[0] in LIBS]
        nproj = len(proj)
        total_import_lines += len(imps)
        proj_import_lines += nproj
        if imps and len(set(imps)) != len(imps):
            duplicate_import_files += 1
        has_mathlib = any(m == "Mathlib" or m.startswith("Mathlib.") for m in imps)
        if has_mathlib:
            mathlib_files += 1
        if nproj == 0:
            zero_proj_files += 1
        if nproj > max_import[0]:
            max_import = (nproj, p)

        for m in proj:
            j = mod_to_idx.get(m)
            if j is None:
                unresolved[m] += 1
                if len(unresolved_samples) < 20:
                    unresolved_samples.append({"source": p, "import": m})
            else:
                edges.append((idx, j))
                tgt_parts = paths[j].split("/")
                tgt_lib = tgt_parts[0] if len(tgt_parts) > 1 else "(root)"
                matrix[(lib, tgt_lib)] += 1

        # ---- tactics / flags ----
        seen = set()
        for m in TAC_RE.finditer(text):
            tac_occ[m.group(1)] += 1
            seen.add(m.group(1))
        for k in seen:
            tac_files[k] += 1

        if "autoImplicit false" in text:
            flags["autoImplicit_false"] += 1
        if "maxHeartbeats" in text:
            flags["maxHeartbeats"] += 1
        if re.search(r"\bsorry\b", text):
            flags["sorry"] += 1
        if "/-" in text or "--" in text:
            flags["comments"] += 1
        if "run_cmd" in text:
            flags["run_cmd"] += 1
        if "#eval" in text:
            flags["eval"] += 1
        if "#check" in text:
            flags["check"] += 1
        if "native_decide" in text:
            flags["native_decide"] += 1
        if AXIOM_RE.search(text):
            flags["axiom"] += 1
        if re.search(r"\badmit\b", text):
            flags["admit"] += 1
        if "addDecl" in text:
            flags["addDecl"] += 1

        has_wrapper = WRAPPER_RE.search(text) is not None
        if has_wrapper:
            wrapper_files += 1
            if p.endswith("Statement.lean"):
                stmt_wrapper_files += 1
        stripped = [ln.strip() for ln in text.splitlines() if ln.strip()]
        if nd == 0 and stripped and all(ln.startswith("import ") for ln in stripped):
            import_only_files += 1
        if "".join(text.split()) == "importMathlib":
            mathlib_only_files += 1

        oneline = len(ONELINE_THEOREM_RE.findall(text))
        oneline_total += oneline
        if th:
            pby, pterm = proof_styles(text)
            by_proof_total += pby
            term_proof_total += pterm
        decl_totals.update(dc)

        # ---- aggregates ----
        total_bytes += sizes[idx]
        total_lines += lines
        total_decls += nd
        total_theorems += th

        line_counts.append(lines)
        byte_counts.append(sizes[idx])
        decl_per_file.append(nd)
        theorem_per_file.append(th)
        import_per_file.append(nproj)
        lines_by_idx.append(lines)

        hist_lines[bucket(lines, [1, 5, 10, 20, 50, 100, 200, 500, 1000],
                          ["1", "2-5", "6-10", "11-20", "21-50", "51-100",
                           "101-200", "201-500", "501-1000", ">1000"])] += 1
        hist_bytes[bucket(sizes[idx], [1024, 2048, 5120, 10240, 20480,
                                       51200, 102400, 204800],
                          ["<1KB", "1-2KB", "2-5KB", "5-10KB", "10-20KB",
                           "20-50KB", "50-100KB", "100-200KB", ">200KB"])] += 1
        hist_decls[bucket(nd, [0, 1, 3, 5, 10, 20],
                          ["0", "1", "2-3", "4-5", "6-10", "11-20", "21+"])] += 1
        hist_theorems[bucket(th, [0, 1, 2, 5, 10],
                             ["0", "1", "2", "3-5", "6-10", "11+"])] += 1
        hist_imports[bucket(nproj, [0, 1, 2, 5, 10, 20],
                            ["0", "1", "2", "3-5", "6-10", "11-20", "21+"])] += 1
        path_depth_hist[depth] += 1

        la = lib_agg[lib]
        la["files"] += 1
        la["lines"] += lines
        la["bytes"] += sizes[idx]
        la["decls"] += nd
        la["theorems"] += th
        la["imports"] += nproj
        if nproj == 0:
            la["zero_import_files"] += 1
        if p.endswith("Statement.lean"):
            la["statement_files"] += 1
        if "/Proofs/" in p:
            la["proofdir_files"] += 1
        if "/PublishedTheorems/" in p:
            la["published_files"] += 1
        if has_wrapper:
            la["wrapper_files"] += 1
        if th == 1:
            la["one_theorem_files"] += 1

        second = "/".join(parts[:2]) if len(parts) > 2 else lib
        third = "/".join(parts[:3]) if len(parts) > 3 else second
        for agg, key in ((dir2_agg, second), (dir3_agg, third)):
            row = agg[key]
            row[0] += 1
            row[1] += lines
            row[2] += sizes[idx]
            row[3] += nd
            row[4] += th

        if len(top20) < 20:
            heapq.heappush(top20, (sizes[idx], p, lines))
        elif sizes[idx] > top20[0][0]:
            heapq.heappushpop(top20, (sizes[idx], p, lines))

        if p.startswith("BuildAid/") or p.startswith("Supplements/") \
                or p in ("Main.lean", "Statements.lean") or "run_cmd" in text:
            if len(special) < 30:
                special.append({
                    "path": p,
                    "lines": lines,
                    "head": text[:260].strip(),
                })

        if idx in sample_idx:
            sk = skeleton(text)
            sample_rows.append((sk, p, lines, p.endswith("Statement.lean"), lib))

        if (idx + 1) % 20000 == 0:
            el = time.time() - t_read
            print(f"  [{idx + 1}/{n}] {el:.1f}s  {((idx + 1) / max(el, 1e-9)):.0f} files/s",
                  flush=True)

    scan_seconds = time.time() - t0

    # ---------------------------------------------------------------- graph
    uniq_edges = sorted(set(edges))
    adj = [[] for _ in range(n)]
    indeg = [0] * n
    for s, t in uniq_edges:
        adj[s].append(t)
        indeg[t] += 1

    roots = sum(1 for d in indeg if d == 0)
    leaves = sum(1 for a in adj if not a)

    indeg2 = indeg[:]
    q = deque(i for i in range(n) if indeg2[i] == 0)
    depth = [0] * n
    order = 0
    while q:
        u = q.popleft()
        order += 1
        du = depth[u]
        for v in adj[u]:
            if depth[v] < du + 1:
                depth[v] = du + 1
            indeg2[v] -= 1
            if indeg2[v] == 0:
                q.append(v)
    cycles = n - order
    depth_sorted = sorted(depth)
    graph_depth_hist = Counter(depth)

    main_idx = mod_to_idx.get("Main", -1)
    reach = 0
    if main_idx >= 0:
        seen = bytearray(n)
        seen[main_idx] = 1
        dq = deque([main_idx])
        reach = 1
        while dq:
            u = dq.popleft()
            for v in adj[u]:
                if not seen[v]:
                    seen[v] = 1
                    reach += 1
                    dq.append(v)

    top_indeg = heapq.nlargest(20, range(n), key=lambda i: indeg[i])

    # ---------------------------------------------------------------- naming
    name_tokens = Counter()
    dir_tokens = Counter()
    sub_name = Counter()
    sub_path = Counter()
    suffix_ct = Counter()
    prefix_ct = Counter()
    ending_digit = 0
    for p in paths:
        base = p.rsplit("/", 1)[-1][:-5]
        name_tokens.update(camel_tokens(base))
        for d in p.split("/")[:-1]:
            dir_tokens.update(camel_tokens(d))
        for w in WATCH_WORDS:
            if w in base:
                sub_name[w] += 1
            if w in p:
                sub_path[w] += 1
        for s in SUFFIXES:
            if base.endswith(s):
                suffix_ct[s] += 1
        for pre in PREFIXES:
            if base.startswith(pre):
                prefix_ct[pre] += 1
        if re.search(r"[0-9\u2082\u2083]$", base):
            ending_digit += 1

    # ---------------------------------------------------------------- pairs
    pathset = set(paths)
    stmt_files = [p for p in paths if p.endswith("Statement.lean")]
    stmt_matched = 0
    stmt_unmatched = []
    stmt_pairs = []
    for p in stmt_files:
        basep = p[: -len("Statement.lean")] + ".lean"
        if basep in pathset:
            stmt_matched += 1
            if len(stmt_pairs) < 5:
                stmt_pairs.append({"statement": p, "proof": basep})
        elif len(stmt_unmatched) < 10:
            stmt_unmatched.append(p)

    basename_map = defaultdict(list)
    for p in paths:
        basename_map[p.rsplit("/", 1)[-1]].append(p)

    pub_files = [p for p in paths if "/PublishedTheorems/" in p]
    pub_matched = 0
    pub_samples = []
    for p in pub_files:
        bn = p.rsplit("/", 1)[-1]
        other = [q for q in basename_map.get(bn, []) if q != p and "/Proofs/" in q]
        if other:
            pub_matched += 1
            if len(pub_samples) < 5:
                pub_samples.append({"published": p, "proof": other[0]})

    # ---------------------------------------------------------------- templates
    def pack_templates(rows, k):
        c = Counter(hashlib.sha1(r[0].encode("utf-8")).hexdigest() for r in rows)
        ex = {}
        for sk, p, ln, is_stmt, lib in rows:
            h = hashlib.sha1(sk.encode("utf-8")).hexdigest()
            if h not in ex:
                ex[h] = (p, ln, sk[:320])
        out = []
        for h, cnt in c.most_common(k):
            p, ln, preview = ex[h]
            out.append({
                "hash": h[:12],
                "count": cnt,
                "share": round(cnt / max(len(rows), 1), 4),
                "example": p,
                "lines": ln,
                "preview": preview,
            })
        return out, c

    top_overall, skel_counter = pack_templates(sample_rows, 10)
    stmt_rows = [r for r in sample_rows if r[3]]
    non_rows = [r for r in sample_rows if not r[3]]
    top_stmt, _ = pack_templates(stmt_rows, 6)
    top_non, _ = pack_templates(non_rows, 6)
    top10_share = round(sum(x["count"] for x in top_overall) / max(len(sample_rows), 1), 4)

    # ---------------------------------------------------------------- assemble
    lib_rows = []
    for lib, a in sorted(lib_agg.items(), key=lambda kv: -kv[1]["files"]):
        out_edges = sum(v for (s, _), v in matrix.items() if s == lib)
        in_edges = sum(v for (_, t), v in matrix.items() if t == lib)
        internal = matrix.get((lib, lib), 0)
        lib_rows.append({
            "name": lib,
            "files": a["files"],
            "lines": a["lines"],
            "bytes": a["bytes"],
            "decls": a["decls"],
            "theorems": a["theorems"],
            "statement_files": a["statement_files"],
            "proofdir_files": a["proofdir_files"],
            "published_files": a["published_files"],
            "one_theorem_files": a["one_theorem_files"],
            "wrapper_files": a["wrapper_files"],
            "import_edges_out": out_edges,
            "import_edges_in": in_edges,
            "internal_edges": internal,
            "zero_import_files": a["zero_import_files"],
        })

    top_lib = lib_rows

    dir2_rows = [
        {"dir": k, "files": v[0], "lines": v[1], "bytes": v[2],
         "decls": v[3], "theorems": v[4]}
        for k, v in sorted(dir2_agg.items(), key=lambda kv: -kv[1][0])
    ]
    dir3_rows = [
        {"dir": k, "files": v[0], "lines": v[1], "bytes": v[2]}
        for k, v in sorted(dir3_agg.items(), key=lambda kv: -kv[1][0])[:25]
    ]

    data = {
        "meta": {
            "zip": str(archive_path),
            "zip_bytes": archive_bytes,
            "lean_files": n,
            "scan_seconds": round(scan_seconds, 2),
            "sample_size": len(sample_rows),
            "read_errors": read_errors,
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        },
        "totals": {
            "files": n,
            "bytes": total_bytes,
            "lines": total_lines,
            "decls": total_decls,
            "theorems": total_theorems,
            "project_import_lines": proj_import_lines,
            "import_lines": total_import_lines,
        },
        "lines": {
            "min": min(line_counts),
            "p25": r2(pct(sorted(line_counts), 0.25)),
            "median": r2(pct(sorted(line_counts), 0.50)),
            "mean": r2(sum(line_counts) / len(line_counts)),
            "p90": r2(pct(sorted(line_counts), 0.90)),
            "p99": r2(pct(sorted(line_counts), 0.99)),
            "max": max(line_counts),
            "histogram": dict(hist_lines),
        },
        "bytes_stats": {
            "min": min(byte_counts),
            "median": r2(pct(sorted(byte_counts), 0.50)),
            "mean": r2(sum(byte_counts) / len(byte_counts)),
            "p90": r2(pct(sorted(byte_counts), 0.90)),
            "p99": r2(pct(sorted(byte_counts), 0.99)),
            "max": max(byte_counts),
            "histogram": dict(hist_bytes),
        },
        "top20_largest": [
            {"path": p, "bytes": b, "lines": ln}
            for b, p, ln in sorted(top20, reverse=True)
        ],
        "dirs": {
            "depth_hist": dict(sorted(path_depth_hist.items())),
            "top_level": top_lib,
            "second_level": dir2_rows,
            "third_level_top": dir3_rows,
        },
        "naming": {
            "basename_tokens": [{"token": k, "count": v}
                                for k, v in name_tokens.most_common(40)],
            "dir_tokens": [{"token": k, "count": v}
                           for k, v in dir_tokens.most_common(40)],
            "substring_in_basename": dict(sub_name),
            "substring_in_path": dict(sub_path),
            "suffix": dict(suffix_ct),
            "prefix": dict(prefix_ct),
            "ending_digit_or_subscript": ending_digit,
        },
        "pairs": {
            "statement_files": len(stmt_files),
            "statement_paired_same_dir": stmt_matched,
            "statement_paired_share": round(stmt_matched / max(len(stmt_files), 1), 4),
            "statement_wrapper_files": stmt_wrapper_files,
            "statement_and_proof_both": sum(
                1 for p in stmt_files
                if p[: -len("Statement.lean")] + ".lean" in pathset),
            "statement_exactly_one_theorem": sum(
                1 for t in stmt_theorem_counts if t == 1),
            "statement_line_stats": line_summary(stmt_line_counts),
            "proofdir_line_stats": line_summary(proof_line_counts),
            "published_line_stats": line_summary(pub_line_counts),
            "unpaired_samples": stmt_unmatched,
            "pairs_samples": stmt_pairs,
            "published_files": len(pub_files),
            "published_with_proof_same_basename": pub_matched,
            "published_samples": pub_samples,
        },
        "decls": {
            "totals": dict(decl_totals),
            "per_file": {
                "median": r2(pct(sorted(decl_per_file), 0.50)),
                "mean": r2(sum(decl_per_file) / len(decl_per_file)),
                "p90": r2(pct(sorted(decl_per_file), 0.90)),
                "max": max(decl_per_file),
                "histogram": dict(hist_decls),
            },
            "theorem_histogram": dict(hist_theorems),
            "files_with_theorem": sum(1 for t in theorem_per_file if t > 0),
            "exactly_one_theorem_files": sum(1 for t in theorem_per_file if t == 1),
            "zero_theorem_files": sum(1 for t in theorem_per_file if t == 0),
            "oneline_theorem_decls": oneline_total,
            "oneline_share_of_theorems": round(
                oneline_total / max(total_theorems, 1), 4),
            "by_proof_theorems": by_proof_total,
            "term_proof_theorems": term_proof_total,
            "unknown_proof_theorems": max(
                total_theorems - by_proof_total - term_proof_total, 0),
            "by_proof_share": round(
                by_proof_total / max(total_theorems, 1), 4),
            "max_decl_file": {"path": max_decl[1], "decls": max_decl[0]},
        },
        "imports": {
            "per_file": {
                "median": r2(pct(sorted(import_per_file), 0.50)),
                "mean": r2(sum(import_per_file) / len(import_per_file)),
                "p90": r2(pct(sorted(import_per_file), 0.90)),
                "max": max(import_per_file),
                "histogram": dict(hist_imports),
            },
            "mathlib_files": mathlib_files,
            "zero_project_import_files": zero_proj_files,
            "duplicate_import_files": duplicate_import_files,
            "import_only_files": import_only_files,
            "mathlib_only_files": mathlib_only_files,
            "max_import_file": {"path": max_import[1], "imports": max_import[0]},
            "resolved_edges": len(uniq_edges),
            "unresolved_total": sum(unresolved.values()),
            "unresolved_modules": len(unresolved),
            "unresolved_top": [{"module": k, "count": v}
                               for k, v in unresolved.most_common(20)],
            "unresolved_samples": unresolved_samples,
        },
        "graph": {
            "nodes": n,
            "edges": len(uniq_edges),
            "cycles": cycles,
            "roots": roots,
            "leaves": leaves,
            "max_depth": max(depth),
            "depth_p90": r2(pct(depth_sorted, 0.90)),
            "depth_hist": dict(sorted(graph_depth_hist.items())),
            "reachable_from_Main": reach,
            "reachable_share": round(reach / max(n, 1), 4),
            "top_indegree": [
                {"module": paths[i][:-5].replace("/", "."), "indegree": indeg[i],
                 "lines": lines_by_idx[i]}
                for i in top_indeg
            ],
        },
        "templates": {
            "sample_size": len(sample_rows),
            "distinct": len(skel_counter),
            "top_overall": top_overall,
            "top10_share": top10_share,
            "top_statement": top_stmt,
            "top_nonstatement": top_non,
            "wrapper": {
                "files_with_first_exact": wrapper_files,
                "statement_files_with_first_exact": stmt_wrapper_files,
                "share_of_statement_files": round(
                    stmt_wrapper_files / max(len(stmt_files), 1), 4),
            },
            "tactics": {
                k: {"occurrences": tac_occ.get(k, 0), "files": tac_files.get(k, 0)}
                for k in ("simp", "simpa", "simp_all", "omega", "norm_num",
                          "linarith", "by")
            },
        },
        "build": {
            "special_files": special,
        },
        "flags": dict(flags),
    }

    # declaration totals need the Counter from the loop; recompute cheaply here
    # (kept out of the loop's hot path by accumulating below)
    close_fn()
    return data


def _resolve_default_archive() -> Path:
    for c in DEFAULT_CANDIDATES:
        if c.exists():
            return c
    return ROOT / "external" / "lean.tar.gz"


def main():
    global DECL_TOTALS
    ap = argparse.ArgumentParser(
        description="Compute full engineering statistics and DAG metrics for the Lean corpus."
    )
    ap.add_argument(
        "--archive",
        type=Path,
        default=None,
        help="Path to lean.tar.gz, riemann-hypothesis-lean-main.zip, or extracted src directory "
             "(default: auto-detect under ./external/ or repo root)",
    )
    ap.add_argument(
        "--out-json",
        type=Path,
        default=OUT_JSON,
        help="Output path for JSON statistics (default: ./analysis/eng_stats.json)",
    )
    ap.add_argument(
        "--out-txt",
        type=Path,
        default=OUT_TXT,
        help="Output path for text summary (default: ./analysis/eng_stats.txt)",
    )
    ap.add_argument("--limit", type=int, default=0, help="Limit number of files scanned (0 = all)")
    ap.add_argument("--sample", type=int, default=SAMPLE_N, help="Number of files to sample for template analysis")
    args = ap.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    archive_path = args.archive if args.archive is not None else _resolve_default_archive()
    if not archive_path.exists():
        print(
            f"[ERROR] Source archive not found: {archive_path}\n"
            f"Please download lean.tar.gz into ./external/lean.tar.gz or pass --archive <path>.",
            file=sys.stderr,
        )
        sys.exit(1)

    out_json = args.out_json
    out_txt = args.out_txt
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_txt.parent.mkdir(parents=True, exist_ok=True)

    print(f"scanning {archive_path.name} ...", flush=True)
    data = scan(archive_path=archive_path, limit=args.limit, sample_n=args.sample)

    out_json.write_text(json.dumps(data, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    txt = render_txt(data)
    out_txt.write_text(txt, encoding="utf-8")
    print(f"wrote {out_json}")
    print(f"wrote {out_txt} ({len(txt.splitlines())} lines)")


def render_txt(d):
    L = []
    a = L.append
    a("=" * 78)
    a("Lean 工程结构统计（analysis/eng_stats.py）")
    a("=" * 78)
    m = d["meta"]
    t = d["totals"]
    a(f"zip: {m['zip']}  ({m['zip_bytes']:,} bytes)")
    a(f"lean 文件: {m['lean_files']:,}   源码字节: {t['bytes']:,}   行数: {t['lines']:,}")
    a(f"声明(粗): {t['decls']:,}   theorem: {t['theorems']:,}   "
      f"project import 边: {t['project_import_lines']:,} / import 行: {t['import_lines']:,}")
    a(f"扫描耗时: {m['scan_seconds']} s   样本: {m['sample_size']} 文件")
    a("")
    a("[1] 行数分布")
    for k in ("min", "p25", "median", "mean", "p90", "p99", "max"):
        a(f"  {k:>7}: {d['lines'][k]}")
    a("  直方图: " + "  ".join(f"{k}:{v:,}" for k, v in d["lines"]["histogram"].items()))
    a("")
    a("[2] 字节分布")
    for k in ("min", "median", "mean", "p90", "p99", "max"):
        a(f"  {k:>7}: {d['bytes_stats'][k]}")
    a("  直方图: " + "  ".join(f"{k}:{v:,}" for k, v in d["bytes_stats"]["histogram"].items()))
    a("  最大 20 文件:")
    for x in d["top20_largest"]:
        a(f"    {x['bytes']:>9,} B  {x['lines']:>6} 行  {x['path']}")
    a("")
    a("[3] 顶层库")
    a("  " + f"{'库':<22}{'文件':>9}{'行数':>13}{'theorem':>10}")
    for x in d["dirs"]["top_level"]:
        a(f"  {x['name']:<22}{x['files']:>9,}{x['lines']:>13,}{x['theorems']:>10,}")
    a("")
    a("[4] 二级目录 Top 25")
    for x in d["dirs"]["second_level"][:25]:
        a(f"  {x['files']:>7,}  {x['lines']:>11,}  {x['dir']}")
    a("")
    a("[5] 命名")
    a("  basename 高频词段: " + ", ".join(
        f"{x['token']}({x['count']:,})" for x in d["naming"]["basename_tokens"][:25]))
    a("  目录高频词段: " + ", ".join(
        f"{x['token']}({x['count']:,})" for x in d["naming"]["dir_tokens"][:20]))
    a("  basename 命中: " + ", ".join(
        f"{k}={v:,}" for k, v in d["naming"]["substring_in_basename"].items()))
    a("  后缀: " + ", ".join(f"{k}={v:,}" for k, v in d["naming"]["suffix"].items()))
    a("  前缀: " + ", ".join(f"{k}={v:,}" for k, v in d["naming"]["prefix"].items()))
    a("")
    p = d["pairs"]
    a("[6] Statement / Proof 配对")
    a(f"  *Statement.lean: {p['statement_files']:,}，同目录同名证明: "
      f"{p['statement_paired_same_dir']:,} ({p['statement_paired_share']:.1%})")
    a(f"  PublishedTheorems 文件: {p['published_files']:,}，同名出现在 Proofs: "
      f"{p['published_with_proof_same_basename']:,}")
    a(f"  Statement 行数: median={p['statement_line_stats'].get('median')} "
      f"p90={p['statement_line_stats'].get('p90')} "
      f"≤10行={p['statement_line_stats'].get('le_10_lines', 0) / max(p['statement_line_stats']['files'], 1):.1%}"
      f"；其中恰好 1 theorem: {p['statement_exactly_one_theorem']:,}")
    a(f"  Proofs 目录文件行数: median={p['proofdir_line_stats'].get('median')} "
      f"p90={p['proofdir_line_stats'].get('p90')}")
    a(f"  PublishedTheorems 行数: median={p['published_line_stats'].get('median')} "
      f"p90={p['published_line_stats'].get('p90')} max={p['published_line_stats'].get('max')}")
    a("  配对样本:")
    for x in p["pairs_samples"]:
        a(f"    {x['statement']}  <->  {x['proof']}")
    a("")
    a("[7] 声明密度")
    a(f"  per-file: median={d['decls']['per_file']['median']} "
      f"mean={d['decls']['per_file']['mean']} p90={d['decls']['per_file']['p90']} "
      f"max={d['decls']['per_file']['max']}")
    a(f"  theorem 分布: {d['decls']['theorem_histogram']}")
    a(f"  恰好 1 theorem: {d['decls']['exactly_one_theorem_files']:,} 文件 "
      f"({d['decls']['exactly_one_theorem_files'] / max(t['files'], 1):.1%} of all)")
    a(f"  证明形态: by={d['decls']['by_proof_theorems']:,} "
      f"({d['decls']['by_proof_share']:.1%})  term={d['decls']['term_proof_theorems']:,} "
      f" unknown={d['decls']['unknown_proof_theorems']:,}")
    a(f"  单行 theorem:=...: {d['decls']['oneline_theorem_decls']:,} "
      f"({d['decls']['oneline_share_of_theorems']:.1%})")
    a(f"  声明最多文件: {d['decls']['max_decl_file']['decls']:,} 条  "
      f"{d['decls']['max_decl_file']['path']}")
    a("")
    a("[8] import")
    i = d["imports"]
    a(f"  per-file: median={i['per_file']['median']} mean={i['per_file']['mean']} "
      f"p90={i['per_file']['p90']} max={i['per_file']['max']}")
    a(f"  import Mathlib 文件: {i['mathlib_files']:,}；0 project import: "
      f"{i['zero_project_import_files']:,}；重复 import 文件: {i['duplicate_import_files']:,}")
    a(f"  import-only 文件: {i['import_only_files']:,}；仅 import Mathlib: "
      f"{i['mathlib_only_files']:,}；单文件最多 import: {i['max_import_file']['imports']} "
      f"({i['max_import_file']['path']})")
    a(f"  可解析 project 边(去重): {i['resolved_edges']:,}；未解析: "
      f"{i['unresolved_total']:,} ({i['unresolved_modules']} 个模块)")
    a("")
    g = d["graph"]
    a("[9] import 图")
    a(f"  nodes={g['nodes']:,} edges={g['edges']:,} cycles={g['cycles']} "
      f"roots={g['roots']:,} leaves={g['leaves']:,}")
    a(f"  max_depth={g['max_depth']} p90_depth={g['depth_p90']}  "
      f"reachable_from_Main={g['reachable_from_Main']:,} ({g['reachable_share']:.1%})")
    a("  入度最高模块:")
    for x in g["top_indegree"][:12]:
        a(f"    indeg={x['indegree']:>4}  lines={x['lines']:>6}  {x['module']}")
    a("")
    a("[10] 模板骨架（样本 %d）" % d["templates"]["sample_size"])
    a(f"  distinct={d['templates']['distinct']}  top10_share={d['templates']['top10_share']:.1%}")
    a(f"  `first | exact @` 装配壳: {d['templates']['wrapper']['files_with_first_exact']:,} 文件"
      f"（Statement 中 {d['templates']['wrapper']['statement_files_with_first_exact']:,}，"
      f"{d['templates']['wrapper']['share_of_statement_files']:.1%}）")
    for x in d["templates"]["top_overall"][:5]:
        a(f"    {x['count']:>4} ({x['share']:.1%})  {x['lines']:>4} 行  {x['example']}")
        a(f"        {x['preview'][:180]}")
    a("  仅 Statement 文件 top:")
    for x in d["templates"]["top_statement"][:3]:
        a(f"    {x['count']:>4} ({x['share']:.1%})  {x['example']}")
    a("  非 Statement 文件 top:")
    for x in d["templates"]["top_nonstatement"][:3]:
        a(f"    {x['count']:>4} ({x['share']:.1%})  {x['example']}")
    a("  tactics: " + ", ".join(
        f"{k}={v['occurrences']:,}/{v['files']:,}文件"
        for k, v in d["templates"]["tactics"].items()))
    a("")
    a("[11] 特殊文件")
    for x in d["build"]["special_files"]:
        a(f"    {x['lines']:>4} 行  {x['path']}")
    a("")
    a("[12] flags")
    a("  " + ", ".join(f"{k}={v:,}" for k, v in d["flags"].items()))
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
