"""Apply KEEP/TRIM/DELETE docstring decisions with an AST-equality proof.

Usage: docstring_apply.py dry|apply INVENTORY.json DECISIONS.json [DECISIONS.json ...]
         [--protect PATH ...]
Decision item: {"id": N, "action": "KEEP|TRIM|DELETE", "new": "one line (TRIM only)"}.
Refuses (and applies nothing for that item or file) when:
  - the file is protected, or its source mentions __doc__ (CLI help text);
  - DELETE targets a module, a class, or a docstring that is the only statement in its body;
  - TRIM text is empty, multi-line, over 100 chars, ends with a period, or has quotes/backslashes;
  - the docstring text at the recorded line no longer matches the inventory;
  - the code with all docstrings stripped differs before vs after.
Run dry first; exit 1 lists every problem. Run from the repo root, then run the formatter.
"""

import argparse
import ast
import copy
import json
import sys


def doc_expr(node):
    if not isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return None
    if not node.body:
        return None
    first = node.body[0]
    ok = isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
    return first if ok and isinstance(first.value.value, str) else None


def stripped_dump(tree):
    clone = copy.deepcopy(tree)
    for node in ast.walk(clone):
        if doc_expr(node) is not None:
            node.body = node.body[1:] or [ast.Pass()]
    return ast.dump(clone)


def recorded_docstrings(tree):
    found = {}
    for node in ast.walk(tree):
        first = doc_expr(node)
        if first is not None:
            found[first.lineno] = first.value.value
    return found


def bad_trim(text):
    return (
        not text
        or "\n" in text
        or '"' in text
        or "\\" in text
        or len(text) > 100
        or text.endswith(".")
    )


def plan(rows, decisions, protect):
    by_file, problems = {}, []
    for ident, decision in decisions.items():
        row = rows[ident]
        action = decision["action"]
        if action == "KEEP":
            continue
        if row["file"] in protect:
            problems.append((ident, "protected file " + row["file"]))
        elif action == "DELETE" and (row["only"] or row["kind"] != "function"):
            problems.append((ident, f"DELETE not allowed for {row['kind']} / sole statement"))
        elif action == "TRIM" and bad_trim(decision.get("new", "").strip()):
            problems.append((ident, "bad TRIM text"))
        elif action not in ("DELETE", "TRIM"):
            problems.append((ident, "unknown action " + action))
        else:
            by_file.setdefault(row["file"], []).append((row, decision))
    return by_file, problems


def rewrite(path, items, apply, problems):
    with open(path, encoding="utf-8") as handle:
        original = handle.read()
    tree = ast.parse(original)
    here = recorded_docstrings(tree)
    if any(here.get(row["line"]) != row["text"] for row, _ in items):
        problems.append((path, "tree changed since inventory"))
        return 0
    lines = original.splitlines(keepends=True)
    for row, decision in sorted(items, key=lambda item: -item[0]["line"]):
        start, end = row["line"] - 1, row["end"]
        if decision["action"] == "DELETE":
            del lines[start:end]
            blank_after_def = start < len(lines) and not lines[start].strip()
            if blank_after_def and start and lines[start - 1].rstrip().endswith(":"):
                del lines[start]
        else:
            first = lines[start]
            indent = first[: len(first) - len(first.lstrip())]
            lines[start:end] = [f'{indent}"""{decision["new"].strip()}"""\n']
    updated = "".join(lines)
    try:
        same = stripped_dump(tree) == stripped_dump(ast.parse(updated))
    except SyntaxError as error:
        problems.append((path, f"syntax error after edit: {error}"))
        return 0
    if not same:
        problems.append((path, "code differs beyond docstrings"))
        return 0
    if apply:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(updated)
    return len(original.splitlines()) - len(updated.splitlines())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["dry", "apply"])
    parser.add_argument("inventory")
    parser.add_argument("decisions", nargs="+")
    parser.add_argument("--protect", nargs="*", default=[])
    args = parser.parse_args()
    with open(args.inventory) as handle:
        rows = {r["id"]: r for r in json.load(handle)}
    decisions = {}
    for path in args.decisions:
        with open(path) as handle:
            for item in json.load(handle):
                decisions[int(item["id"])] = item
    protect = set(args.protect)
    for row in rows.values():
        with open(row["file"], encoding="utf-8") as handle:
            if "__doc__" in handle.read():
                protect.add(row["file"])
    by_file, problems = plan(rows, decisions, protect)
    removed = 0
    for path, items in sorted(by_file.items()):
        removed += rewrite(path, items, args.mode == "apply", problems)
    counts = {}
    for item in decisions.values():
        counts[item["action"]] = counts.get(item["action"], 0) + 1
    print(f"{len(decisions)} decisions {counts}; files {len(by_file)}; net lines removed {removed}; problems {len(problems)}")
    for problem in problems[:30]:
        print("  PROBLEM", problem)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
