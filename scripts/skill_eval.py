#!/usr/bin/env python3
"""Replay fixed prompts through OMP with no window and report what each model did.

Three parts, each run per model:
  reach    does the agent see SOUL.md, in a main session and in a subagent
  loads    which skill it reads for each prompt, next to the one it should read
  behaves  with full tools in a throwaway repo: does the commit follow the rules,
           is the bug fixed, is the tree left clean

`loads` runs get read-only tools and are stopped after a few tool calls, so they change
nothing. `behaves` runs get every tool, inside a copy of tests/fixtures/skill_eval/repo
under the OS temp directory. Every run costs model usage; --max-cost caps the total.

usage: skill_eval.py [--parts reach,loads,behaves] [--models NAME=ID@THINKING,...]
                     [--runs N] [--only KIND,...] [--no-rules] [--append FILE]
                     [--jobs N] [--max-cost USD] [--json PATH]

--no-rules  run without the always-loaded rules, the state before SOUL.md was linked
--append    add a file's text to the system prompt, to try a rule or routing line
The last line is the verdict: `OK skill_eval: ...` (exit 0) or `ERROR skill_eval: ...` (exit 2).
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
FIXTURES = os.path.join(ROOT, "tests", "fixtures", "skill_eval")
DEFAULT_MODELS = "sonnet=anthropic/claude-sonnet-5-5@high,deepseek=omniroute/core/deepseek-v4.1-flash@max"
READ_ONLY_TOOLS = "read,grep,glob,find,todo"
SKILL = re.compile(r"skill://([\w-]+)|([\w-]+)[/\\]+SKILL\.md")
SUBJECT = re.compile(r"^(feat|fix|docs|refactor|chore|test|perf)(\([\w./-]+\))?: \S.{0,70}$")
GIT_ENV = {k: v for k, v in os.environ.items() if k not in ("GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE", "GIT_PREFIX")}

spent = 0.0
spent_lock = threading.Lock()


def git(repo, *args):
    cmd = ["git", "-c", "user.name=eval", "-c", "user.email=eval@example.invalid", "-c", "commit.gpgsign=false", *args]
    return subprocess.run(cmd, cwd=repo, capture_output=True, text=True, encoding="utf-8", env=GIT_ENV).stdout


def make_repo(base):
    """A copy of the fixture repo with one commit, one staged change and two junk files."""
    repo = os.path.join(base, "repo")
    shutil.copytree(os.path.join(FIXTURES, "repo"), repo, ignore=shutil.ignore_patterns("__pycache__"))
    for junk in ("notes_final_v2.txt", os.path.join("old", "cart_backup.py")):
        os.makedirs(os.path.dirname(os.path.join(repo, junk)), exist_ok=True)
        with open(os.path.join(repo, junk), "w", encoding="utf-8", newline="\n") as fh:
            fh.write("leftover\n")
    git(repo, "init", "-q", "-b", "main")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "chore: start the shop")
    with open(os.path.join(repo, "app", "pricing.py"), "a", encoding="utf-8", newline="\n") as fh:
        fh.write("\n\ndef is_on_sale(sku):\n    return sku in SALE\n")
    git(repo, "add", "app/pricing.py")
    return repo


def kill(proc):
    if proc.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
    else:
        proc.kill()


def omp(model, prompt, cwd, a, tools=None, stop_after=None, max_time=150, run_cost=0.6):
    """One headless run. Returns skills read, tool names, final text, cost."""
    global spent
    name, thinking = model
    exe = shutil.which("omp")
    if not exe:
        raise RuntimeError("omp is not on PATH")
    cmd = [exe, "-p", "--mode", "json", "--model", name, "--cwd", cwd, "--no-session", "--no-title",
           "--max-time", str(max_time), "--max-cost", str(run_cost), "--auto-approve"]
    if thinking:
        cmd += ["--thinking", thinking]
    if tools == "":
        cmd += ["--no-tools"]
    elif tools:
        cmd += ["--tools", tools]
    if a.no_rules:
        cmd += ["--no-rules"]
    if a.append_text:
        cmd += ["--append-system-prompt", a.append_text]
    cmd.append(prompt)
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL,
                            text=True, encoding="utf-8", errors="replace")
    skills, tools_used, text, cost, error = [], [], "", 0.0, ""
    try:
        for line in proc.stdout:
            try:
                event = json.loads(line)
            except ValueError:
                continue
            kind = event.get("type")
            if kind == "tool_execution_start":
                tools_used.append(event.get("toolName"))
                if event.get("toolName") == "read":
                    m = SKILL.search(json.dumps(event.get("args") or {}))
                    if m and (m.group(1) or m.group(2)) not in skills:
                        skills.append(m.group(1) or m.group(2))
                if stop_after and len(tools_used) >= stop_after:
                    break
            elif kind == "message_end":
                msg = event.get("message") or {}
                if msg.get("role") == "assistant":
                    cost += ((msg.get("usage") or {}).get("cost") or {}).get("total", 0) or 0
                    error = msg.get("errorMessage") or ""  # a retried request clears it; only the last one counts
                    for part in msg.get("content") or []:
                        if part.get("type") == "text" and part.get("text", "").strip():
                            text = part["text"]
    finally:
        kill(proc)
        proc.wait()
    with spent_lock:
        spent += cost
    if tools_used or text:
        error = ""
    return {"skills": skills, "tools": tools_used, "text": text, "cost": cost, "error": error[:200]}


def headings():
    soul = open(os.path.join(ROOT, "SOUL.md"), encoding="utf-8").read()
    found = re.findall(r"^## (.+)$", soul, re.M)
    return [found[0], found[len(found) // 2], found[-1]]


def run_reach(model, a):
    names = headings()
    ask = ("Look only at the instructions you were given for this session. Which of these exact headings appear in them: "
           + ", ".join('"%s"' % n for n in names) + "? Reply with the ones present, or the single word NONE.")
    work = tempfile.mkdtemp(prefix="skill-eval-")
    try:
        main = omp(model, ask, work, a, tools="")
        sub = omp(model, "Spawn exactly one subagent with the task tool. Give it this task word for word and nothing "
                  "else: '%s' Then reply with only the subagent's exact answer." % ask, work, a, tools="task", max_time=240)
    finally:
        shutil.rmtree(work, True)
    seen = lambda r: sum(1 for n in names if n.lower() in r["text"].lower())
    return [{"part": "reach", "id": "main session", "pass": seen(main) == len(names), "got": "%d of %d headings" % (seen(main), len(names)), "error": main["error"]},
            {"part": "reach", "id": "subagent", "pass": seen(sub) == len(names) and "task" in sub["tools"],
             "got": "%d of %d headings" % (seen(sub), len(names)), "error": sub["error"]}]


def run_load(model, case, a):
    work = tempfile.mkdtemp(prefix="skill-eval-")
    try:
        repo = make_repo(work)
        r = omp(model, case["prompt"], repo, a, tools=READ_ONLY_TOOLS, stop_after=a.stop_after)
    finally:
        shutil.rmtree(work, True)
    want, fine = set(case["expect"]), set(case.get("also_ok", []))
    got = set(r["skills"])
    ok = (not got) if not want else bool(got & want)
    return {"part": "loads", "id": case["id"], "kind": case["kind"], "want": sorted(want), "got": r["skills"],
            "pass": ok, "extra": sorted(got - want - fine), "tools": r["tools"][:8], "error": r["error"]}


def check_commit_rules(repo, before):
    log = git(repo, "log", "--format=%H%x1f%s%x1f%b%x1e", before + "..HEAD").strip("\x1e\n ")
    commits = [c.strip("\n").split("\x1f") for c in log.split("\x1e") if c.strip()]
    problems = []
    if len(commits) != 1:
        problems.append("%d new commits, wanted 1" % len(commits))
    for _, subject, body in commits:
        if not SUBJECT.match(subject):
            problems.append("subject is not `type(scope): overview` within 72 characters: %r" % subject)
        if body.strip():
            problems.append("commit has a body")
    if git(repo, "rev-parse", "--abbrev-ref", "HEAD").strip() != "main":
        problems.append("left the main branch")
    if git(repo, "branch", "--format=%(refname:short)").split() != ["main"]:
        problems.append("created a branch")
    return problems


def check_fix_clean(repo, before):
    problems = []
    out = subprocess.run([sys.executable, "-c", "from app.cart import cart_total; print(cart_total([('mug', 10.0, 2)], 'WELCOME10'))"],
                         cwd=repo, capture_output=True, text=True, env=dict(GIT_ENV, PYTHONDONTWRITEBYTECODE="1"))
    if out.stdout.strip() != "14.4":
        problems.append("cart total is %s, wanted 14.4" % (out.stdout.strip() or out.stderr.strip()[-80:]))
    status = [l for l in git(repo, "status", "--porcelain", "--untracked-files=all").splitlines() if "__pycache__" not in l]
    new = [l[3:] for l in status if l.startswith("??")]
    if new:
        problems.append("new files left in the repo: %s" % ", ".join(new[:4]))
    changed = git(repo, "diff", "--name-only", before).split() + new
    if any(re.search(r"(^|/)tests?(/|_)|_test\.py$", p) for p in changed):
        problems.append("added a test file")
    added = [l[1:] for l in git(repo, "diff", before, "--", "*.py").splitlines() if l.startswith("+") and not l.startswith("+++")]
    if any(re.match(r"\s*#", l) or '"""' in l for l in added):
        problems.append("added a comment or docstring")
    return problems


CHECKS = {"commit_rules": check_commit_rules, "fix_clean": check_fix_clean}


def run_behave(model, case, a):
    work = tempfile.mkdtemp(prefix="skill-eval-")
    try:
        repo = make_repo(work)
        before = git(repo, "rev-parse", "HEAD").strip()
        r = omp(model, case["prompt"], repo, a, max_time=300, run_cost=1.0)
        problems = CHECKS[case["check"]](repo, before)
    finally:
        shutil.rmtree(work, True)
    return {"part": "behaves", "id": case["id"], "pass": not problems, "got": "; ".join(problems) or "ok",
            "skills": r["skills"], "error": r["error"]}


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--parts", default="reach,loads,behaves")
    ap.add_argument("--models", default=DEFAULT_MODELS)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--only", default="")
    ap.add_argument("--no-rules", action="store_true")
    ap.add_argument("--append", default="")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--stop-after", type=int, default=6, help="tool calls before a loads run is stopped")
    ap.add_argument("--max-cost", type=float, default=15.0)
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    a.append_text = open(a.append, encoding="utf-8").read() if a.append else ""
    cases = json.load(open(os.path.join(FIXTURES, "cases.json"), encoding="utf-8"))
    only = {k for k in a.only.split(",") if k}
    parts = a.parts.split(",")
    models = []
    for spec in a.models.split(","):
        label, rest = spec.split("=", 1)
        name, _, thinking = rest.partition("@")
        models.append((label, (name, thinking)))

    jobs = []
    for label, model in models:
        if "reach" in parts:
            jobs.append((label, run_reach, (model, a)))
        if "loads" in parts:
            for case in cases["loads"]:
                if not only or case["kind"] in only:
                    jobs += [(label, run_load, (model, case, a))] * a.runs
        if "behaves" in parts:
            for case in cases["behaves"]:
                if not only or case["id"] in only:
                    jobs += [(label, run_behave, (model, case, a))] * a.runs

    def work(job):
        label, fn, args = job
        if spent >= a.max_cost:
            return [{"part": "skipped", "model": label}]
        try:
            out = fn(*args)
        except Exception as exc:  # one failed run must not hide the rest
            case = args[1] if isinstance(args[1], dict) else {"id": "reach"}
            out = {"part": "error", "id": case["id"], "pass": False, "got": str(exc)[:160]}
        rows = out if isinstance(out, list) else [out]
        for row in rows:
            row["model"] = label
        return rows

    started = time.time()
    with ThreadPoolExecutor(a.jobs) as pool:
        rows = [row for batch in pool.map(work, jobs) for row in batch]
    skipped = sum(1 for r in rows if r["part"] == "skipped")
    rows = [r for r in rows if r["part"] != "skipped"]
    if not rows:
        print("ERROR skill_eval: no run finished")
        return 2

    setup = "without the always-loaded rules" if a.no_rules else "current setup"
    if a.append:
        setup += " + " + os.path.basename(a.append)
    print("setup: %s | models: %s | runs per prompt: %d" % (setup, ", ".join(l for l, _ in models), a.runs))
    labels = [l for l, _ in models]
    # A run the provider failed says nothing about the model, so it leaves the rate and is counted apart.
    failed = [r for r in rows if r.get("error") or r["part"] == "error"]
    rows = [r for r in rows if r not in failed]
    rate = lambda sel: "%d/%d" % (sum(1 for r in sel if r["pass"]), len(sel)) if sel else "-"
    table = []
    for r in rows:
        key = (r["part"], r.get("kind") or r["id"])
        if key not in table:
            table.append(key)
    print("\n%-8s %-22s %s" % ("part", "what", "  ".join("%-9s" % l for l in labels)))
    for part, what in table:
        cells = [rate([r for r in rows if r["model"] == l and r["part"] == part and (r.get("kind") or r["id"]) == what]) for l in labels]
        print("%-8s %-22s %s" % (part, what, "  ".join("%-9s" % c for c in cells)))
    fails = [r for r in rows if not r["pass"]]
    if fails:
        print("\nmisses:")
        seen = {}
        for r in fails:
            key = (r["model"], r["part"], r["id"], json.dumps(r.get("got")), json.dumps(r.get("want", "")))
            seen[key] = seen.get(key, 0) + 1
        for (model, part, rid, got, want), n in seen.items():
            detail = "read %s, wanted %s" % (got, want) if part == "loads" else got
            print("  %-9s %-8s %-20s x%d  %s" % (model, part, rid, n, detail[:150]))
    extra = [r for r in rows if r.get("extra")]
    if extra:
        print("\nskills read that the prompt did not call for: %d runs" % len(extra))
    errors = len(failed)
    if failed:
        print("\nruns the provider failed (left out of the rates): %d, for example: %s" % (errors, (failed[0].get("error") or failed[0].get("got") or "")[:110]))
    path = a.json or os.path.join(tempfile.gettempdir(), "skill-eval-%s.json" % time.strftime("%Y%m%d-%H%M%S"))
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"setup": setup, "rows": rows, "failed": failed}, fh, indent=1)
    print("\nresults: %s" % path)
    summary = "%d runs, %d passed, %d skipped for cost, %d run errors, $%.2f, %d s" % (
        len(rows), sum(1 for r in rows if r["pass"]), skipped, errors, spent, time.time() - started)
    if errors * 4 > len(rows) + errors:
        print("ERROR skill_eval: " + summary)
        return 2
    print("OK skill_eval: " + summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
