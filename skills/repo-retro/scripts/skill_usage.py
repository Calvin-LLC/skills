#!/usr/bin/env python3
"""Count skill use across every working directory.

usage: skill_usage.py SKILLS_DIR [--days N] [--harness NAME] [--skip-cwd PATH]

SKILLS_DIR holds one folder per skill, each with a SKILL.md. Typed use is a
prompt that starts with the skill's invocation token. A self-load is a read
call whose only target is that skill's SKILL.md or its skill:// address.
Both dumps come from the recall skill's sessions.py; rows that replay a
forked session's history are counted once.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict

READER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "recall", "scripts", "sessions.py")
TYPED = re.compile(r"\s*[/$](?:skill:)?([\w-]+)")
LOADED = re.compile(r"(?:skill://([\w-]+)|([\w-]+)[/\\]+SKILL\.md)[\"'\s]*[,}]")


def rows(kind, days, harness):
    cmd = [sys.executable, READER, kind, "--days", str(days), "--limit", "0", "--clip", "400"]
    for h in harness:
        cmd += ["--harness", h]
    with subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True, encoding="utf-8") as p:
        for line in p.stdout:
            yield json.loads(line)
    if p.returncode:
        sys.exit("sessions.py %s exited %d" % (kind, p.returncode))


def norm(path):
    return path.replace("\\", "/").rstrip("/").lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("skills_dir")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--harness", action="append", default=[])
    ap.add_argument("--skip-cwd", action="append", default=[], help="reads in this tree are authoring, not use")
    a = ap.parse_args()
    names = {d for d in os.listdir(a.skills_dir) if os.path.isfile(os.path.join(a.skills_dir, d, "SKILL.md"))}
    skip = [norm(p) for p in a.skip_cwd]
    skipped = lambda r: any(norm(r["cwd"]).startswith(p) for p in skip)
    typed = defaultdict(int)
    typed_in = defaultdict(set)
    loaded_in = defaultdict(set)
    roots, harnesses, seen = set(), set(), set()
    for r in rows("prompts", a.days, a.harness):
        if r["kind"] != "user":
            continue
        roots.add(r["parent"] or r["session"])
        harnesses.add(r["harness"])
        m = TYPED.match(r["text"])
        key = (r["ts"], r["text"][:80])
        if m and m.group(1) in names and key not in seen:
            seen.add(key)
            typed[m.group(1)] += 1
            typed_in[m.group(1)].add(r["parent"] or r["session"])
    seen.clear()
    for r in rows("calls", a.days, a.harness):
        if r["kind"] != "call" or "read" not in r["tool"].lower():
            continue
        roots.add(r["parent"] or r["session"])
        key = r["id"] or (r["session"], r["ts"])
        if skipped(r) or key in seen:
            continue
        seen.add(key)
        m = LOADED.search(r["text"])
        name = m and (m.group(1) or m.group(2))
        if name in names:
            loaded_in[name].add(r["parent"] or r["session"])
    print("window: %d days; root sessions: %d; harnesses: %s" % (a.days, len(roots), ", ".join(sorted(harnesses))))
    print("skill | typed | self-load sessions | sessions")
    use = lambda n: len(typed_in[n] | loaded_in[n])
    for n in sorted(names, key=lambda n: (-use(n), n)):
        print(n, typed[n], len(loaded_in[n]), use(n), sep=" | ")


main()
