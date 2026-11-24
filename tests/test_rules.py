import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CHECK = Path(__file__).resolve().parents[1] / "scripts" / "check_rules.py"
STUB = """import json, sys
args = sys.argv[1:]
name = args[args.index("--rule") + 1].replace("\\\\", "/").rsplit("/", 1)[-1][:-3]
text = sys.stdin.read()
if "GARBLE" in text:
    print("not json")
elif "REJECT" in text:
    print(json.dumps({"error": "no usable TTSR condition"}))
else:
    print(json.dumps({"triggered": [{"name": name}] if "HIT" in text else []}))
"""
RULE = """---
description: Sample
condition: 'HIT'
scope: "tool:bash"
interruptMode: tool-only
repeatMode: always
---

Do the other thing.
"""
CASES = [{"source": "tool", "tool": "bash", "snippet": "HIT here", "trigger": True},
         {"source": "tool", "tool": "bash", "snippet": "nothing", "trigger": False}]


class CheckRulesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="skills-rules-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        (self.tmp / "rules").mkdir()
        (self.tmp / "empty-path").mkdir()
        self.stub = self.tmp / "omp_stub.py"
        self.stub.write_text(STUB, encoding="utf-8")
        self.put()

    def put(self, rule=RULE, cases=CASES, name="sample"):
        (self.tmp / "rules" / (name + ".md")).write_text(rule, encoding="utf-8", newline="\n")
        (self.tmp / "cases.json").write_text(json.dumps({name: cases}), encoding="utf-8")

    def run_check(self, omp=True):
        cmd = [sys.executable, str(CHECK), "--rules-dir", str(self.tmp / "rules"), "--cases", str(self.tmp / "cases.json")]
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        if omp:
            cmd += ["--omp", sys.executable, str(self.stub)]
        else:
            env["PATH"] = str(self.tmp / "empty-path")
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
        lines = proc.stdout.strip().splitlines()
        return proc.returncode, lines[-1] if lines else "", proc.stdout + proc.stderr

    def assertFails(self, fragment, omp=True):
        code, last, out = self.run_check(omp)
        self.assertEqual(code, 1, out)
        self.assertTrue(last.startswith("FAIL rules: "), out)
        self.assertIn(fragment, out)

    def test_valid_rule_with_both_cases_passes(self):
        code, last, out = self.run_check()
        self.assertEqual(code, 0, out)
        self.assertEqual(last, "PASS rules: 1 rules, 2 trigger cases through omp ttsr test", out)

    def test_without_omp_static_checks_run_and_the_verdict_is_skip(self):
        code, last, out = self.run_check(omp=False)
        self.assertEqual(code, 0, out)
        self.assertTrue(last.startswith("SKIP rules: 1 rules pass the frontmatter checks; omp is not on PATH"), out)

    def test_static_failure_is_not_hidden_by_a_missing_omp(self):
        self.put(RULE.replace("repeatMode: always", "repeatMode: forever"))
        self.assertFails("repeatMode is 'forever'", omp=False)

    def test_invalid_or_missing_modes_fail(self):
        self.put(RULE.replace("interruptMode: tool-only", "interruptMode: sometimes"))
        self.assertFails("interruptMode is 'sometimes'")
        self.put(RULE.replace("repeatMode: always\n", ""))
        self.assertFails("repeatMode is None")

    def test_regex_rule_without_scope_fails(self):
        self.put(RULE.replace('scope: "tool:bash"\n', ""))
        self.assertFails("regex rule has no scope")

    def test_empty_body_fails(self):
        self.put(RULE.replace("Do the other thing.\n", ""))
        self.assertFails("body is empty")

    def test_rule_without_a_trigger_fails(self):
        self.put(RULE.replace("condition: 'HIT'\n", ""))
        self.assertFails("no condition or astCondition")

    def test_version_number_and_unknown_key_fail(self):
        self.put(RULE.replace("Do the other thing.", "Needs omp 19.1.1 or later."))
        self.assertFails("holds a version number (19.1.1)")
        self.put(RULE.replace("description: Sample", "description: Sample\nalwaysApply: true"))
        self.assertFails("unknown frontmatter keys: alwaysApply")

    def test_double_quoted_regex_backslash_fails(self):
        self.put(RULE.replace("condition: 'HIT'", 'condition: "\\bHIT"'))
        self.assertFails("use single quotes")

    def test_each_rule_needs_a_positive_and_a_negative_case(self):
        self.put(cases=CASES[:1])
        self.assertFails("no must-not-trigger case")
        self.put(cases=CASES[1:])
        self.assertFails("no must-trigger case")

    def test_missed_positive_and_false_positive_fail(self):
        self.put(cases=[dict(CASES[0], snippet="quiet"), CASES[1]])
        self.assertFails("missed a case it must trigger on")
        self.put(cases=[CASES[0], dict(CASES[1], snippet="HIT again")])
        self.assertFails("triggered on a case it must leave alone")

    def test_omp_error_or_garbled_output_fails(self):
        self.put(cases=[dict(CASES[0], snippet="HIT REJECT"), CASES[1]])
        self.assertFails("omp rejected the rule")
        self.put(cases=[dict(CASES[0], snippet="HIT GARBLE"), CASES[1]])
        self.assertFails("printed no JSON")

    def test_cases_for_a_missing_rule_fail(self):
        (self.tmp / "cases.json").write_text(json.dumps({"sample": CASES, "ghost": CASES}), encoding="utf-8")
        self.assertFails("ghost: cases exist for a rule file that does not")

    def test_block_list_conditions_parse(self):
        self.put(RULE.replace("condition: 'HIT'", "condition:\n  - 'HIT'\n  - 'it''s'"))
        code, last, out = self.run_check()
        self.assertEqual(code, 0, out)


if __name__ == "__main__":
    unittest.main()
