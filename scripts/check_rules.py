#!/usr/bin/env python3
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
KEYS = {"description", "condition", "astCondition", "scope", "agents", "interruptMode", "repeatMode", "globs"}
INTERRUPT = {"never", "prose-only", "tool-only", "always"}
REPEAT = {"once", "after-gap", "always"}
VERSION = re.compile(r"\b\d+\.\d+\.\d+\b")
KEY_LINE = re.compile(r"^([A-Za-z][\w-]*):\s*(.*)$")
ITEM_LINE = re.compile(r"^\s+-\s+(.*)$")
OMP_TIMEOUT = 120


def scalar(raw):
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] == "'":
        return raw[1:-1].replace("''", "'")
    if len(raw) >= 2 and raw[0] == raw[-1] == '"':
        if "\\" in raw:
            raise ValueError("double-quoted value %s holds a backslash, which YAML reads as an escape; use single quotes" % raw)
        return raw[1:-1]
    return raw


def split_rule(text):
    text = text.replace("\r\n", "\n")
    if not text.startswith("---\n"):
        raise ValueError("no frontmatter block at the top")
    end = text.find("\n---\n", 3)
    if end < 0:
        raise ValueError("frontmatter block is not closed with ---")
    fields, key = {}, None
    for line in text[4:end].split("\n"):
        if not line.strip():
            continue
        found = KEY_LINE.match(line)
        if found:
            key, raw = found.group(1), found.group(2).strip()
            if key in fields:
                raise ValueError("frontmatter key %s appears twice" % key)
            if not raw:
                fields[key] = []
            elif raw.startswith("[") and raw.endswith("]"):
                fields[key] = [scalar(part) for part in raw[1:-1].split(",") if part.strip()]
            else:
                fields[key] = scalar(raw)
            continue
        found = ITEM_LINE.match(line)
        if found and key is not None and isinstance(fields[key], list):
            fields[key].append(scalar(found.group(1)))
            continue
        raise ValueError("frontmatter line not understood: %s" % line.strip())
    return fields, text[end + 5:].strip()


def as_list(value):
    if value is None:
        return []
    return [v for v in (value if isinstance(value, list) else [value]) if str(v).strip()]


def static_problems(text):
    try:
        fields, body = split_rule(text)
    except ValueError as err:
        return [str(err)]
    problems = []
    unknown = sorted(set(fields) - KEYS)
    if unknown:
        problems.append("unknown frontmatter keys: %s" % ", ".join(unknown))
    if not body:
        problems.append("body is empty; the body is the reminder the agent reads")
    conditions = as_list(fields.get("condition"))
    if not conditions and not as_list(fields.get("astCondition")):
        problems.append("no condition or astCondition, so the rule never triggers")
    if conditions and not as_list(fields.get("scope")):
        problems.append("regex rule has no scope; name the stream it watches, such as tool:bash or text")
    for key, allowed in (("interruptMode", INTERRUPT), ("repeatMode", REPEAT)):
        value = fields.get(key)
        if value not in allowed:
            problems.append("%s is %r; set one of %s" % (key, value, ", ".join(sorted(allowed))))
    if VERSION.search(text):
        problems.append("holds a version number (%s); a rule names behaviour, not a release" % VERSION.search(text).group(0))
    return problems


def case_label(case):
    where = ":".join(str(case[k]) for k in ("source", "tool", "path") if case.get(k))
    return "%s %r" % (where, case.get("snippet", "")[:50])


def case_problem(omp, rule, case):
    cmd = omp + ["ttsr", "test", "--rule", str(rule), "--json", "--file", "-", "--source", case["source"]]
    for key in ("tool", "path", "agent"):
        if case.get(key):
            cmd += ["--" + key, case[key]]
    try:
        proc = subprocess.run(cmd, input=case["snippet"].encode("utf-8"), capture_output=True, timeout=OMP_TIMEOUT)
    except subprocess.TimeoutExpired:
        return "omp ttsr test gave no answer in %d seconds on %s" % (OMP_TIMEOUT, case_label(case))
    out = proc.stdout.decode("utf-8", "replace")
    try:
        result = json.loads(out)
    except ValueError:
        tail = (out + proc.stderr.decode("utf-8", "replace")).strip().splitlines()
        return "omp ttsr test printed no JSON on %s: %s" % (case_label(case), tail[-1] if tail else "no output")
    if "error" in result:
        return "omp rejected the rule on %s: %s" % (case_label(case), result["error"])
    fired = rule.stem in [hit.get("name") for hit in result.get("triggered", [])]
    if case["trigger"] and not fired:
        return "missed a case it must trigger on: %s" % case_label(case)
    if not case["trigger"] and fired:
        return "triggered on a case it must leave alone: %s" % case_label(case)
    return None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules-dir", default=str(REPO / "rules"))
    ap.add_argument("--cases", default=str(REPO / "tests" / "fixtures" / "rules" / "cases.json"))
    ap.add_argument("--omp", nargs="+", default=None)
    args = ap.parse_args(argv)

    rules = sorted(Path(args.rules_dir).glob("*.md"))
    if not rules:
        print("FAIL rules: no rule files in %s" % args.rules_dir)
        return 1
    try:
        cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    except (OSError, ValueError) as err:
        print("FAIL rules: cannot read cases from %s: %s" % (args.cases, err))
        return 1

    failures = []
    for rule in rules:
        for problem in static_problems(rule.read_text(encoding="utf-8")):
            failures.append("%s: %s" % (rule.name, problem))
        own = cases.get(rule.stem) or []
        for wanted, label in ((True, "must-trigger"), (False, "must-not-trigger")):
            if not any(case.get("trigger") is wanted for case in own):
                failures.append("%s: no %s case in %s" % (rule.name, label, args.cases))
    for name in sorted(set(cases) - {rule.stem for rule in rules}):
        failures.append("%s: cases exist for a rule file that does not" % name)

    total = sum(len(cases.get(rule.stem) or []) for rule in rules)
    omp = args.omp or ([shutil.which("omp")] if shutil.which("omp") else None)
    if omp and not failures:
        for rule in rules:
            for case in cases[rule.stem]:
                problem = case_problem(omp, rule, case)
                if problem:
                    failures.append("%s: %s" % (rule.name, problem))

    if failures:
        for failure in failures:
            print("FAIL  %s" % failure)
        print("FAIL rules: %d problems in %d rules" % (len(failures), len(rules)))
        return 1
    if not omp:
        print("SKIP rules: %d rules pass the frontmatter checks; omp is not on PATH, so %d trigger cases did not run"
              % (len(rules), total))
        return 0
    print("PASS rules: %d rules, %d trigger cases through omp ttsr test" % (len(rules), total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
