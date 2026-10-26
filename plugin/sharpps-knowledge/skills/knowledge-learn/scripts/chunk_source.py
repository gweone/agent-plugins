#!/usr/bin/env python3
"""Split text/markdown sources into provenance-tagged chunks for knowledge drafting.

Stdlib only, offline and read-only: it reads the given file or directory and prints JSON.
It never submits anything. Chunks that look like they contain credentials are withheld.
"""
import argparse
import hashlib
import json
import os
import re
import sys

MAX_FILE_BYTES = 1_000_000
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
SECRET_PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"(?i)\b(?:password|passwd|secret|token|api[_-]?key)\b\s*[:=]\s*\S{6,}"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{20,}"),
]
HEADING = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
FENCE = re.compile(r"^\s*(```|~~~)")


def iter_files(path, exts):
    if os.path.isfile(path):
        yield path, os.path.basename(path)
        return
    for root, dirs, files in os.walk(path):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith("."))
        for name in sorted(files):
            if name.rsplit(".", 1)[-1].lower() in exts:
                full = os.path.join(root, name)
                yield full, os.path.relpath(full, path).replace(os.sep, "/")


def read_text(full):
    if os.path.getsize(full) > MAX_FILE_BYTES:
        return None
    with open(full, "rb") as handle:
        raw = handle.read()
    if b"\x00" in raw:
        return None
    return raw.decode("utf-8", errors="replace")


def sections(lines):
    """Yield (heading_path, start_line, end_line, lines) per heading-delimited section."""
    stack, start, current, in_fence = [], 1, [], False
    path_at_start = []
    for number, line in enumerate(lines, 1):
        if FENCE.match(line):
            in_fence = not in_fence
        match = None if in_fence else HEADING.match(line)
        if match and current:
            yield list(path_at_start), start, number - 1, current
            current, start = [], number
        if match:
            level = len(match.group(1))
            stack = [h for h in stack if h[0] < level] + [(level, match.group(2))]
            path_at_start = [h[1] for h in stack]
        current.append(line)
    if current:
        yield list(path_at_start), start, len(lines), current


def pack(heading_path, start, lines, max_chars):
    """Greedy split of one section into pieces of at most max_chars, preferring blank lines."""
    piece, piece_start, size = [], start, 0
    for offset, line in enumerate(lines):
        number = start + offset
        pieces = [line[i:i + max_chars] for i in range(0, len(line), max_chars)] or [""]
        for part in pieces:
            if piece and size + len(part) + 1 > max_chars:
                cut = max((i for i, text in enumerate(piece) if not text.strip()), default=None)
                if cut is not None and cut > 0:
                    head, piece = piece[:cut], piece[cut:]
                else:
                    head, piece = piece, []
                yield heading_path, piece_start, piece_start + len(head) - 1, head
                piece_start += len(head)
                size = sum(len(text) + 1 for text in piece)
            if not piece:
                piece_start = number
            piece.append(part)
            size += len(part) + 1
    if piece:
        yield heading_path, piece_start, piece_start + len(piece) - 1, piece


def build_chunks(path, exts, max_chars, min_chars):
    seen, chunks, skipped_small, skipped_files = set(), [], 0, 0
    for full, rel in iter_files(path, exts):
        text = read_text(full)
        if text is None:
            skipped_files += 1
            continue
        lines = text.splitlines()
        for heading_path, start, end, body in sections(lines):
            for hp, s, e, piece in pack(heading_path, start, body, max_chars):
                content = "\n".join(piece).strip()
                if len(content) < min_chars:
                    skipped_small += 1
                    continue
                digest = hashlib.sha256(" ".join(content.split()).encode("utf-8")).hexdigest()
                if digest in seen:
                    continue
                seen.add(digest)
                reason = None
                if any(p.search(content) for p in SECRET_PATTERNS):
                    reason = "possible credential"
                chunks.append({
                    "id": digest[:12], "source": rel, "heading_path": hp,
                    "line_start": s, "line_end": e, "chars": len(content), "sha256": digest,
                    "withheld": reason, "text": None if reason else content,
                })
    return chunks, skipped_small, skipped_files


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("path")
    parser.add_argument("--max-chars", type=int, default=1800)
    parser.add_argument("--min-chars", type=int, default=80)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--ext", default="md,markdown,txt,rst")
    args = parser.parse_args(argv)
    if not os.path.exists(args.path):
        print("path not found: %s" % args.path, file=sys.stderr)
        return 2
    if args.max_chars < 200 or args.limit < 1 or args.offset < 0:
        print("invalid --max-chars/--limit/--offset", file=sys.stderr)
        return 2
    exts = {e.strip().lower().lstrip(".") for e in args.ext.split(",") if e.strip()}
    chunks, skipped_small, skipped_files = build_chunks(args.path, exts, args.max_chars, args.min_chars)
    page = chunks[args.offset:args.offset + args.limit]
    end = args.offset + len(page)
    json.dump({
        "schema_version": 1, "total_chunks": len(chunks), "offset": args.offset,
        "limit": args.limit, "next_offset": end if end < len(chunks) else None,
        "withheld_in_page": sum(1 for c in page if c["withheld"]),
        "skipped_small": skipped_small, "skipped_files": skipped_files, "chunks": page,
    }, sys.stdout, ensure_ascii=True, indent=1)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
