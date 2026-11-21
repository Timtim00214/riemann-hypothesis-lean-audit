#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sorry_check.py — Inspect the MIT challenge export (challenge.ndjson) and verify
that each of the 5 target theorems uses `sorryAx` as a placeholder proof value,
confirming that challenge.ndjson is a pure statement specification.

Usage:
    python sorry_check.py [--ndjson external/challenge.ndjson]
"""

from __future__ import annotations

import argparse
import json
import sys
from array import array
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_NDJSON = ROOT / "external" / "challenge.ndjson"

TARGETS = {
    "riemannHypothesis",
    "riemannZeta_eq_zero_re",
    "LFunction_ne_zero_of_half_lt_re",
    "LFunction_eq_zero_re",
    "LFunction_eq_zero_re_of_isPrimitive",
}


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(
        description="Verify that the 5 target theorems in challenge.ndjson contain sorryAx placeholders."
    )
    ap.add_argument(
        "--ndjson",
        type=Path,
        default=DEFAULT_NDJSON,
        help="Path to decompressed challenge.ndjson (default: external/challenge.ndjson)",
    )
    args = ap.parse_args()

    ndjson_path: Path = args.ndjson
    if not ndjson_path.exists():
        print(
            f"ERROR: {ndjson_path} not found. Run `python challenge_check.py` first.",
            file=sys.stderr,
        )
        return 1

    names: dict[int, tuple[int, str]] = {}
    with ndjson_path.open("rb") as fh:
        for line in fh:
            if b'"in":' not in line[:20]:
                continue
            o = json.loads(line)
            if "str" in o:
                names[o["in"]] = (o["str"].get("pre", 0), o["str"].get("str", ""))
            elif "num" in o:
                names[o["in"]] = (o["num"].get("pre", 0), str(o["num"].get("i", "?")))

    def full(i: int | None) -> str:
        if i is None:
            return "?"
        parts: list[str] = []
        while i:
            pre, s = names.get(i, (0, "?"))
            parts.append(str(s))
            i = pre
        return ".".join(reversed(parts))

    K = array("b")
    A1 = array("i")
    A2 = array("i")
    A3 = array("i")
    decls: list[tuple[str, int | None, int | None, int | None]] = []

    with ndjson_path.open("rb") as fh:
        for line in fh:
            h = line[:16]
            if (
                h.startswith(b'{"thm"')
                or h.startswith(b'{"def"')
                or h.startswith(b'{"axiom"')
                or h.startswith(b'{"opaque"')
                or h.startswith(b'{"inductive"')
                or h.startswith(b'{"quot"')
            ):
                o = json.loads(line)
                k = next(iter(o))
                d = o[k]
                decls.append((k, d.get("name"), d.get("type"), d.get("value")))
                continue
            if h.startswith(b'{"il"') or h.startswith(b'{"in"'):
                continue
            if not (
                h.startswith(b'{"ie"')
                or h.startswith(b'{"app"')
                or h.startswith(b'{"forallE"')
                or h.startswith(b'{"bvar"')
                or h.startswith(b'{"const"')
                or h.startswith(b'{"lam"')
            ):
                continue
            o = json.loads(line)
            if "app" in o:
                K.append(1)
                A1.append(o["app"]["fn"])
                A2.append(o["app"]["arg"])
                A3.append(0)
            elif "forallE" in o:
                e = o["forallE"]
                K.append(2)
                A1.append(e["name"])
                A2.append(e["type"])
                A3.append(e["body"])
            elif "const" in o:
                K.append(3)
                A1.append(o["const"]["name"])
                A2.append(0)
                A3.append(0)
            elif "bvar" in o:
                K.append(4)
                A1.append(o["bvar"])
                A2.append(0)
                A3.append(0)
            elif "sort" in o:
                K.append(5)
                A1.append(o["sort"])
                A2.append(0)
                A3.append(0)
            elif "lam" in o:
                e = o["lam"]
                K.append(6)
                A1.append(e["name"])
                A2.append(e["type"])
                A3.append(e["body"])
            else:
                K.append(0)
                A1.append(0)
                A2.append(0)
                A3.append(0)

    axioms = [full(d[1]) for d in decls if d[0] == "axiom"]
    sorry_idx = {d[1] for d in decls if d[0] == "axiom" and full(d[1]) == "sorryAx" and d[1] is not None}
    print("axioms in challenge:", sorted(axioms))
    print("sorryAx name idx:", sorted(sorry_idx))

    def scan(root: int | None) -> tuple[set[str], int]:
        if root is None:
            return set(), 0
        seen: set[int] = set()
        st = [root]
        found: set[str] = set()
        while st:
            e = st.pop()
            if e in seen:
                continue
            seen.add(e)
            if e >= len(K):
                continue
            k = K[e]
            if k == 1:
                st.append(A1[e])
                st.append(A2[e])
            elif k in (2, 6):
                st.append(A2[e])
                st.append(A3[e])
            elif k == 3:
                if A1[e] in sorry_idx:
                    found.add(full(A1[e]))
        return found, len(seen)

    for k, ni, _ty, va in decls:
        nm = full(ni)
        if k == "thm" and nm in TARGETS:
            found, sz = scan(va)
            print(f"{nm:40s} value_expr_size={sz:5d} contains_sorryAx={sorted(found)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
