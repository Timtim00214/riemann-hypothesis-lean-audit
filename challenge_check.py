#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
challenge_check.py — Download (if missing), decompress, and verify the SHA-256
checksums and declaration count of the MIT challenge export (challenge.ndjson.zst).

Usage:
    python challenge_check.py [--zst external/challenge.ndjson.zst]
                              [--ndjson external/challenge.ndjson]
                              [--proxy http://host:port]
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import ssl
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_ZST = ROOT / "external" / "challenge.ndjson.zst"
DEFAULT_NDJSON = ROOT / "external" / "challenge.ndjson"
DEFAULT_URL = "https://math.mit.edu/~drew/grh/challenge.ndjson.zst"

EXP_ZST = "c24ef99dab3556a52c7fb886e03cf22a242f3b96f82ae4cc40539e5d2f678ac6"
EXP_ND = "bd484ac9886a96f26b1d9a7a59ebd45b7a70d102c015d4f31f9302bbdd6ab2b9"
EXP_LINES = 51692


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(1 << 22)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def build_opener(proxy: str | None) -> urllib.request.OpenerDirector:
    handlers: list[urllib.request.BaseHandler] = [
        urllib.request.HTTPSHandler(context=ssl.create_default_context())
    ]
    if proxy:
        handlers.insert(0, urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
    else:
        # Respect standard HTTP_PROXY / HTTPS_PROXY environment variables automatically
        handlers.insert(0, urllib.request.ProxyHandler())
    return urllib.request.build_opener(*handlers)


def download_file(url: str, dest: Path, proxy: str | None, timeout: int = 90) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    opener = build_opener(proxy)
    print(f"Downloading {url} -> {dest} ...", flush=True)
    with opener.open(url, timeout=timeout) as resp, part.open("wb") as out:
        done = 0
        next_report = 8 << 20
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            out.write(chunk)
            done += len(chunk)
            if done >= next_report:
                print(f"  {done / 1e6:.1f} MB", flush=True)
                next_report += 8 << 20
    part.replace(dest)


def decompress_zst(zst_path: Path, ndjson_path: Path) -> None:
    ndjson_path.parent.mkdir(parents=True, exist_ok=True)
    part = ndjson_path.with_suffix(ndjson_path.suffix + ".part")
    print(f"Decompressing {zst_path} -> {ndjson_path} ...", flush=True)

    # 1. Python 3.14+ standard library `compression.zstd`
    try:
        from compression import zstd as std_zstd  # type: ignore[import-not-found]

        with std_zstd.ZstdFile(zst_path, "rb") as fi, part.open("wb") as fo:
            shutil.copyfileobj(fi, fo, 1 << 22)
        part.replace(ndjson_path)
        return
    except ImportError:
        pass

    # 2. Third-party `zstandard` package
    try:
        import zstandard as zstd_pkg  # type: ignore[import-not-found]

        dctx = zstd_pkg.ZstdDecompressor()
        with zst_path.open("rb") as fi, part.open("wb") as fo:
            dctx.copy_stream(fi, fo)
        part.replace(ndjson_path)
        return
    except ImportError:
        pass

    # 3. System `zstd` CLI
    zstd_bin = shutil.which("zstd")
    if zstd_bin:
        subprocess.run(
            [zstd_bin, "-d", "-f", "-o", str(part), str(zst_path)],
            check=True,
        )
        part.replace(ndjson_path)
        return

    raise RuntimeError(
        "Cannot decompress .zst file: require Python 3.14+ (`compression.zstd`), "
        "`pip install zstandard`, or the `zstd` command-line utility."
    )


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(
        description="Verify MIT challenge.ndjson.zst and challenge.ndjson hashes and line count."
    )
    ap.add_argument(
        "--zst",
        type=Path,
        default=DEFAULT_ZST,
        help="Path to challenge.ndjson.zst (default: external/challenge.ndjson.zst)",
    )
    ap.add_argument(
        "--ndjson",
        type=Path,
        default=DEFAULT_NDJSON,
        help="Path to decompressed challenge.ndjson (default: external/challenge.ndjson)",
    )
    ap.add_argument(
        "--url",
        default=DEFAULT_URL,
        help="Download URL if --zst is missing",
    )
    ap.add_argument(
        "--proxy",
        default=None,
        help="Optional HTTP/HTTPS proxy URL (defaults to system/environment proxy)",
    )
    ap.add_argument(
        "--no-download",
        action="store_true",
        help="Fail instead of downloading when challenge.ndjson.zst is absent",
    )
    args = ap.parse_args()

    zst_path: Path = args.zst
    ndjson_path: Path = args.ndjson

    zst_match = True
    if zst_path.exists():
        zst_size = zst_path.stat().st_size
        zst_hash = sha256_file(zst_path)
        zst_match = zst_hash == EXP_ZST
        print(
            f"zst size={zst_size} sha256={zst_hash} expected={EXP_ZST} MATCH={zst_match}",
            flush=True,
        )
    elif not ndjson_path.exists():
        if args.no_download:
            print(f"ERROR: {zst_path} not found and --no-download set.", file=sys.stderr)
            return 1
        download_file(args.url, zst_path, args.proxy)
        zst_size = zst_path.stat().st_size
        zst_hash = sha256_file(zst_path)
        zst_match = zst_hash == EXP_ZST
        print(
            f"zst size={zst_size} sha256={zst_hash} expected={EXP_ZST} MATCH={zst_match}",
            flush=True,
        )

    if not ndjson_path.exists():
        decompress_zst(zst_path, ndjson_path)

    nd_size = ndjson_path.stat().st_size
    nd_hash = sha256_file(ndjson_path)
    nd_match = nd_hash == EXP_ND
    print(
        f"ndjson size={nd_size} sha256={nd_hash} expected={EXP_ND} MATCH={nd_match}",
        flush=True,
    )

    n_lines = 0
    first_lines: list[bytes] = []
    with ndjson_path.open("rb") as fh:
        for line in fh:
            n_lines += 1
            if len(first_lines) < 2:
                first_lines.append(line)

    lines_match = n_lines == EXP_LINES
    print(f"lines={n_lines} expected={EXP_LINES} MATCH={lines_match}", flush=True)
    for idx, raw_line in enumerate(first_lines, start=1):
        print(f"--- first line {idx} ({len(raw_line)} bytes) ---")
        print(raw_line[:700].decode("utf-8", "replace").rstrip("\r\n"))

    return 0 if (zst_match and nd_match and lines_match) else 1


if __name__ == "__main__":
    raise SystemExit(main())
