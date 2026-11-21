#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
decode_challenge.py — Parse the MIT lean4export challenge file (challenge.ndjson)
to reconstruct and pretty-print the 5 target theorems, 4 statement definitions,
and all axioms declared in the challenge export.

Usage:
    python decode_challenge.py [--ndjson external/challenge.ndjson]
"""

from __future__ import annotations

import argparse
import json
import sys
from array import array
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_NDJSON = ROOT / "external" / "challenge.ndjson"

TARGETS = [
    "riemannHypothesis",
    "riemannZeta_eq_zero_re",
    "LFunction_ne_zero_of_half_lt_re",
    "LFunction_eq_zero_re",
    "LFunction_eq_zero_re_of_isPrimitive",
]

PROPS = [
    "RiemannZetaZerosOnLine",
    "DirichletLNonvanishingRightOfHalf",
    "DirichletLZerosOnLine",
    "PrimitiveDirichletLZerosOnLine",
]


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(
        description="Decode and pretty-print the 5 theorem types, 4 Prop definitions, and axioms from challenge.ndjson."
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

    # ---------- pass 1: interned names ----------
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

    def full(i: int) -> str:
        parts: list[str] = []
        while i:
            pre, s = names.get(i, (0, "?"))
            parts.append(str(s))
            i = pre
        return ".".join(reversed(parts))

    def short(i: int) -> str:
        s = names.get(i, (0, "?"))[1]
        return str(s) if s not in ("", "_") else "_"

    # ---------- pass 2: nodes and declarations ----------
    K = array("b")
    A1 = array("i")
    A2 = array("i")
    A3 = array("i")
    BI = array("b")
    US: dict[int, list[int]] = {}

    LK = array("b")
    L1 = array("i")
    L2 = array("i")

    decls: list[tuple[str, int | None, int | None, int | None]] = []
    axiom_names: list[int] = []
    mism = 0

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
                if k == "axiom" and d.get("name") is not None:
                    axiom_names.append(d["name"])
                continue
            if h.startswith(b'{"il"'):
                o = json.loads(line)
                il = o["il"]
                if il != len(LK):
                    mism += 1
                if "param" in o:
                    LK.append(1)
                    L1.append(o["param"])
                    L2.append(0)
                elif "succ" in o:
                    LK.append(2)
                    L1.append(o["succ"])
                    L2.append(0)
                elif "max" in o:
                    LK.append(3)
                    L1.append(o["max"][0])
                    L2.append(o["max"][1])
                elif "imax" in o:
                    LK.append(4)
                    L1.append(o["imax"][0])
                    L2.append(o["imax"][1])
                else:
                    LK.append(0)
                    L1.append(0)
                    L2.append(0)
                continue
            if h.startswith(b'{"in"'):
                continue
            if (
                h.startswith(b'{"ie"')
                or h.startswith(b'{"app"')
                or h.startswith(b'{"forallE"')
                or h.startswith(b'{"bvar"')
                or h.startswith(b'{"const"')
                or h.startswith(b'{"lam"')
            ):
                o = json.loads(line)
                ie = o["ie"]
                if ie != len(K):
                    mism += 1
                if "app" in o:
                    K.append(1)
                    A1.append(o["app"]["fn"])
                    A2.append(o["app"]["arg"])
                    A3.append(0)
                    BI.append(0)
                elif "forallE" in o:
                    e = o["forallE"]
                    K.append(2)
                    A1.append(e["name"])
                    A2.append(e["type"])
                    A3.append(e["body"])
                    BI.append(
                        {
                            "default": 0,
                            "implicit": 1,
                            "instImplicit": 2,
                            "strictImplicit": 3,
                        }.get(e["binderInfo"], 0)
                    )
                elif "const" in o:
                    c = o["const"]
                    K.append(3)
                    A1.append(c["name"])
                    A2.append(0)
                    A3.append(0)
                    BI.append(0)
                    US[ie] = c.get("us", [])
                elif "bvar" in o:
                    K.append(4)
                    A1.append(o["bvar"])
                    A2.append(0)
                    A3.append(0)
                    BI.append(0)
                elif "sort" in o:
                    K.append(5)
                    A1.append(o["sort"])
                    A2.append(0)
                    A3.append(0)
                    BI.append(0)
                elif "lam" in o:
                    e = o["lam"]
                    K.append(6)
                    A1.append(e["name"])
                    A2.append(e["type"])
                    A3.append(e["body"])
                    BI.append(
                        {
                            "default": 0,
                            "implicit": 1,
                            "instImplicit": 2,
                            "strictImplicit": 3,
                        }.get(e["binderInfo"], 0)
                    )
                else:
                    K.append(0)
                    A1.append(0)
                    A2.append(0)
                    A3.append(0)
                    BI.append(0)
                continue

    print(
        f"expr nodes={len(K)} level nodes={len(LK)} decls={len(decls)} index_mismatch={mism}",
        flush=True,
    )

    def plevel(l: int) -> str:
        if l >= len(LK):
            return f"?L{l}"
        k = LK[l]
        if k == 1:
            return full(L1[l])
        if k == 2:
            return f"({plevel(L1[l])}+1)"
        if k == 3:
            return f"max({plevel(L1[l])},{plevel(L2[l])})"
        if k == 4:
            return f"imax({plevel(L1[l])},{plevel(L2[l])})"
        return f"?L{l}"

    def pexpr(e: int | None, binders: tuple[str, ...] = (), top: bool = True) -> str:
        if e is None:
            return "<none>"
        if e >= len(K):
            return f"?E{e}"
        k = K[e]
        if k == 1:
            f_ = pexpr(A1[e], binders, False)
            a = pexpr(A2[e], binders, False)
            arg = a if K[A2[e]] in (3, 4, 5) or K[A2[e]] == 0 else f"({a})"
            return f"{f_} {arg}"
        if k == 2:
            n = short(A1[e])
            t = pexpr(A2[e], binders)
            b = pexpr(A3[e], binders + (n,))
            bi = BI[e]
            if bi == 1:
                head = f"{{{n} : {t}}}"
            elif bi == 2:
                head = f"[{n} : {t}]"
            elif bi == 3:
                head = f"⦃{n} : {t}⦄"
            else:
                head = f"({n} : {t})"
            return f"{head} → {b}"
        if k == 3:
            nm = full(A1[e])
            us = US.get(e, [])
            return nm + (("." + "{" + ",".join(plevel(l) for l in us) + "}") if us else "")
        if k == 4:
            v = A1[e]
            return binders[len(binders) - 1 - v] if v < len(binders) else f"?b{v}"
        if k == 5:
            l = A1[e]
            return "Prop" if l == 0 else f"Sort {plevel(l)}"
        if k == 6:
            n = short(A1[e])
            t = pexpr(A2[e], binders)
            b = pexpr(A3[e], binders + (n,))
            return f"fun ({n} : {t}) => {b}"
        return f"<kind{k}>"

    by_name: dict[str, list[tuple[str, int | None, int | None]]] = {}
    for k, ni, ty, va in decls:
        by_name.setdefault(full(ni) if ni is not None else "?", []).append((k, ty, va))

    print("\n=== 5 Theorem Declarations (from MIT challenge export) ===")
    for t in TARGETS:
        for kind, ty, va in by_name.get(t, []):
            print(f"[{kind}] {t}\n  type : {pexpr(ty, (), True)}")

    print("\n=== 4 Axioms in challenge.ndjson ===")
    for i in axiom_names:
        print(" ", full(i))

    print("\n=== 4 Statement Definitions in challenge.ndjson ===")
    for p in PROPS:
        for kind, ty, va in by_name.get(p, []):
            print(f"[{kind}] {p}\n  type : {pexpr(ty)}\n  value: {pexpr(va)}")

    axset = {full(i) for i in axiom_names}
    print("\naxiom set:", sorted(axset))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
