"""List every Python docstring in the tracked tree and split the list into judge chunks.

Usage: docstring_inventory.py OUT_DIR [--chunks N] [--skip PREFIX ...]
Writes OUT_DIR/docstrings.json and OUT_DIR/chunk_K.json (lists of ids, whole files per chunk).
Run from the repo root.
"""

import argparse
import ast
import json
import os
import subprocess
import sys

DEFAULT_SKIP = ("references/", "backups/", "backend/puppet/", "vendor/", "node_modules/")


def tracked_python(skip):
    out = subprocess.run(
        ["git", "ls-files", "-c", "*.py"], capture_output=True, text=True, check=True
    ).stdout.split()
    return [f for f in out if not f.startswith(skip) and os.path.exists(f)]


def docstring_of(node):
    if not isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return None
    if not node.body:
        return None
    first = node.body[0]
    ok = isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
    return first if ok and isinstance(first.value.value, str) else None


def inventory(files):
    rows = []
    for path in files:
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            first = docstring_of(node)
            if first is None:
                continue
            kind = (
                "module"
                if isinstance(node, ast.Module)
                else "class"
                if isinstance(node, ast.ClassDef)
                else "function"
            )
            rows.append(
                {
                    "id": len(rows),
                    "file": path,
                    "line": first.lineno,
                    "end": first.end_lineno,
                    "owner": getattr(node, "name", "<module>"),
                    "kind": kind,
                    "only": len(node.body) == 1,
                    "lines": first.end_lineno - first.lineno + 1,
                    "text": first.value.value,
                }
            )
    return rows


def split(rows, count):
    by_file = {}
    for row in rows:
        by_file.setdefault(row["file"], []).append(row)
    target = sum(r["lines"] for r in rows) / count
    chunks, acc = [[]], 0
    for file_rows in by_file.values():
        if acc >= target and len(chunks) < count:
            chunks.append([])
            acc = 0
        chunks[-1].extend(file_rows)
        acc += sum(r["lines"] for r in file_rows)
    return chunks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("out_dir")
    parser.add_argument("--chunks", type=int, default=6)
    parser.add_argument("--skip", nargs="*", default=[])
    args = parser.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    rows = inventory(tracked_python(DEFAULT_SKIP + tuple(args.skip)))
    with open(os.path.join(args.out_dir, "docstrings.json"), "w") as handle:
        json.dump(rows, handle)
    for number, chunk in enumerate(split(rows, args.chunks), 1):
        with open(os.path.join(args.out_dir, f"chunk_{number}.json"), "w") as handle:
            json.dump([r["id"] for r in chunk], handle)
        print(f"chunk {number}: {len(chunk)} docstrings, {sum(r['lines'] for r in chunk)} lines")
    sizes = [r["lines"] for r in rows]
    print(
        f"total {len(rows)} docstrings, {sum(sizes)} lines; "
        f"1-line {sum(s == 1 for s in sizes)}, 5+ lines {sum(s >= 5 for s in sizes)} "
        f"({sum(s for s in sizes if s >= 5)} lines)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
