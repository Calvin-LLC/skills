import os
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))
PY = sys.executable


def run(args, cwd=None):
    p = subprocess.run([PY] + args, cwd=cwd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, env=dict(os.environ, PYTHONIOENCODING='utf-8'))
    return p.returncode, p.stdout.decode('utf-8', 'replace'), p.stderr.decode('utf-8', 'replace')


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


STUBS = {
    'check_ok.py': 'print("scanned things")\nprint("PASS ok: 3 things")\n',
    'check_bad.py': 'print("FAIL  a.md:1: rejected thing, do this instead")\nprint("FAIL bad: 1 failure")\nraise SystemExit(1)\n',
    'check_throws.py': 'raise RuntimeError("fixture missing")\n',
    'check_silent.py': 'pass\n',
    'check_skipme.py': 'print("SKIP skipme: needs a build tree")\n',
}


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.dir = os.path.join(self.tmp, 'scripts')

    def stub(self, *names, **extra):
        for n in names:
            write(os.path.join(self.dir, n), STUBS[n])
        for n, body in extra.items():
            write(os.path.join(self.dir, 'check_' + n + '.py'), body)

    def runner(self, *args):
        return run([os.path.join(SCRIPTS, 'check.py'), '--scripts-dir', self.dir, '--cwd', self.tmp] + list(args))

    def test_each_outcome_is_separated_and_run_exits_1(self):
        self.stub(*STUBS)
        code, out, _ = self.runner()
        self.assertEqual(code, 1)
        lines = out.splitlines()
        by_name = {l.split()[1]: l.split()[0] for l in lines if l[:5].strip() in ('PASS', 'FAIL', 'ERROR', 'SKIP')}
        self.assertEqual(by_name, {'ok': 'PASS', 'bad': 'FAIL', 'throws': 'ERROR', 'silent': 'ERROR', 'skipme': 'SKIP'})
        self.assertIn('needs a build tree', out)
        self.assertIn('5 checks: 1 pass, 1 fail, 2 error, 1 skip', out)

    def test_failing_check_output_is_printed(self):
        self.stub('check_bad.py')
        code, out, _ = self.runner()
        self.assertEqual(code, 1)
        self.assertIn('a.md:1: rejected thing, do this instead', out)

    def test_crash_names_the_exception(self):
        self.stub('check_throws.py')
        code, out, _ = self.runner()
        self.assertEqual(code, 1)
        self.assertIn('ERROR  throws  check crashed: RuntimeError: fixture missing', out)

    def test_silent_exit_zero_is_error_not_pass(self):
        self.stub('check_silent.py')
        code, out, _ = self.runner()
        self.assertEqual(code, 1)
        self.assertIn('ERROR  silent  exit 0 but no output', out)
        self.assertNotIn('PASS', out)

    def test_checks_do_not_inherit_a_hooks_git_variables(self):
        self.stub(env='import os\nleaked = [k for k in ("GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE", "GIT_PREFIX") if k in os.environ]\n'
                      'print(("FAIL env: " + ",".join(leaked)) if leaked else "PASS env: clean")\nraise SystemExit(1 if leaked else 0)\n')
        p = subprocess.run([PY, os.path.join(SCRIPTS, 'check.py'), '--scripts-dir', self.dir, '--cwd', self.tmp],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           env=dict(os.environ, GIT_DIR=os.path.join(self.tmp, 'nowhere'), GIT_INDEX_FILE=os.path.join(self.tmp, 'idx')))
        self.assertEqual(p.returncode, 0, p.stdout.decode('utf-8', 'replace'))
        self.assertIn('PASS   env', p.stdout.decode('utf-8', 'replace'))

    def test_exit_zero_without_verdict_line_is_error(self):
        self.stub(chatty='print("all good")\n')
        code, out, _ = self.runner()
        self.assertEqual(code, 1)
        self.assertIn('ERROR  chatty', out)

    def test_fail_line_with_exit_zero_is_error(self):
        self.stub(liar='print("FAIL liar: 1")\n')
        code, out, _ = self.runner()
        self.assertEqual(code, 1)
        self.assertIn('ERROR  liar', out)

    def test_fail_lines_then_crash_is_error_not_fail(self):
        self.stub(half='print("FAIL x: 1")\nimport nonexistent_module_xyz\n')
        code, out, _ = self.runner()
        self.assertEqual(code, 1)
        self.assertIn('ERROR  half', out)

    def test_other_exit_code_is_error(self):
        self.stub(odd='print("PASS odd: fine")\nraise SystemExit(3)\n')
        code, out, _ = self.runner()
        self.assertEqual(code, 1)
        self.assertIn('ERROR  odd  exit 3', out)

    def test_pass_and_skip_only_exit_zero(self):
        self.stub('check_ok.py', 'check_skipme.py')
        code, out, _ = self.runner()
        self.assertEqual(code, 0)
        self.assertIn('2 checks: 1 pass, 0 fail, 0 error, 1 skip', out)

    def test_name_argument_runs_one_check(self):
        self.stub('check_ok.py', 'check_bad.py')
        code, out, _ = self.runner('ok')
        self.assertEqual(code, 0)
        self.assertIn('1 checks: 1 pass', out)
        self.assertNotIn('bad', out)

    def test_unknown_name_exits_2(self):
        self.stub('check_ok.py')
        code, out, _ = self.runner('nope')
        self.assertEqual(code, 2)
        self.assertIn('no check named', out)

    def test_empty_directory_is_error(self):
        os.makedirs(self.dir)
        code, out, _ = self.runner()
        self.assertEqual(code, 2)
        self.assertIn('ERROR', out)


SKILL = """---
name: demo
description: A demo skill.
---

# Demo

## Start

1. Ground
2. Sketch

## Phase A: Ground it

Ground the thing.

## Phase B: Agree

Pause for sign-off here.

## Phase C: Build

Build it.

## Hand-off

Send it.
"""


class SkillsCheckCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.root = os.path.join(self.tmp, 'skills')
        write(os.path.join(self.root, 'demo', 'SKILL.md'), SKILL)

    def check(self, reference):
        write(os.path.join(self.root, 'demo', 'references', 'ref.md'), reference)
        return run([os.path.join(SCRIPTS, 'check_skills.py'), '--root', self.root])

    def assertFails(self, reference, *needles):
        code, out, _ = self.check(reference)
        self.assertEqual(code, 1, out)
        self.assertEqual(out.strip().splitlines()[-1].split()[0], 'FAIL')
        findings = [l for l in out.splitlines() if l.startswith('FAIL  ')]
        self.assertEqual(len(findings), 1, out)
        for n in needles:
            self.assertIn(n, findings[0])


class CrossReferenceTests(SkillsCheckCase):
    def test_correct_references_pass(self):
        code, out, _ = self.check(
            '# Ref\n\nCompanion to "Hand-off" in SKILL.md. Companion to step 2 in SKILL.md.\n'
            'Phase A grounds, Phase B sign-off, Phase C builds. Steps 1 and 2 in SKILL.md.\n'
            'A quoted "word" elsewhere, and in a skill file the "Missing" is not claimed.\n')
        self.assertEqual(code, 0, out)
        self.assertEqual(out.strip().splitlines()[-1], 'PASS 1 skills (1 auto-routable, 0 hidden), 0 failures, 0 over budget')

    def test_quoted_section_that_does_not_exist(self):
        self.assertFails('# Ref\n\nCompanion to "Reviewer" in SKILL.md.\n',
                         'demo/references/ref.md:3', '"Reviewer" in SKILL.md',
                         'Start; Phase A: Ground it', 'Hand-off')

    def test_step_that_does_not_exist(self):
        self.assertFails('# Ref\n\nCompanion to step 10 in SKILL.md.\n',
                         'ref.md:3', 'step 10 in SKILL.md', '1, 2')

    def test_phase_letter_that_does_not_exist(self):
        self.assertFails('# Ref\n\nRules for Phase F work.\n', 'ref.md:3', 'Phase F', 'A, B, C')

    def test_phase_gate_named_for_the_wrong_phase(self):
        self.assertFails('# Ref\n\nAfter Phase C sign-off, continue.\n', 'ref.md:3', 'Phase C sign-off',
                         '"sign-off" only under Phase B')

    def test_phase_mentions_ignored_when_skill_has_no_lettered_phases(self):
        write(os.path.join(self.root, 'demo', 'SKILL.md'), SKILL.replace('Phase A:', 'Part 1:').replace('Phase B:', 'Part 2:').replace('Phase C:', 'Part 3:'))
        code, out, _ = self.check('# Ref\n\nPhase D of someone else\'s process.\n')
        self.assertEqual(code, 0, out)

    def test_bad_root_is_not_a_pass(self):
        code, out, _ = run([os.path.join(SCRIPTS, 'check_skills.py'), '--root', os.path.join(self.tmp, 'missing')])
        self.assertEqual(code, 2)
        self.assertNotIn('PASS', out)

    def test_version_in_frontmatter_fails(self):
        write(os.path.join(self.root, 'demo', 'SKILL.md'), SKILL.replace('---\n\n# Demo', 'metadata:\n  version: "2.0.0"\n---\n\n# Demo'))
        self.assertFails('# Ref\n', 'demo/SKILL.md', 'frontmatter carries a version')

    def test_version_number_in_vendoring_note_fails(self):
        write(os.path.join(self.root, 'demo', 'VENDORED.md'), '# Vendored\n\n- Source: upstream at commit abc1234.\n- Skill v2.1.0.\n')
        self.assertFails('# Ref\n', 'demo/VENDORED.md:4', 'record the upstream commit')


class OmpFirstTests(SkillsCheckCase):
    def add_skill(self, name, frontmatter='', description='Another skill.'):
        write(os.path.join(self.root, name, 'SKILL.md'),
              '---\nname: %s\ndescription: %s\n%s---\n\n# Other\n' % (name, description, frontmatter))
        write(os.path.join(self.root, name, 'scripts', 'tool.py'), 'pass\n')

    def assertPasses(self, reference):
        code, out, _ = self.check(reference)
        self.assertEqual(code, 0, out)
        self.assertEqual([l for l in out.splitlines() if l.startswith('FAIL')], [], out)

    def test_omp_tools_and_internal_urls_pass(self):
        self.assertPasses(
            '# Ref\n\nAsk through `ask`, track with `todo`, fan out with one `task` item per slice and `wait`.\n'
            'Ground with `lsp` and `ast_grep` before `grep`; rewrite with `ast_edit`; step with `debug`.\n'
            'Drive the page with `browser` in `eval`, or `computer` when it is enabled.\n'
            'Read `pr://12`, `pr://12/diff/all`, `issue://3`, `agent://Runner/summary` and `conflict://1`.\n')

    def test_another_harness_tool_still_fails(self):
        self.assertFails('# Ref\n\nAsk with `ask_user_question`.\n', 'ref.md:3', "one harness's tool name")

    def test_posix_temp_path_still_fails(self):
        self.assertFails('# Ref\n\nWrite it to /tmp/out.json.\n', 'ref.md:3', 'OS temp directory')

    def test_path_into_another_skill_fails_from_skill_md(self):
        self.add_skill('other')
        write(os.path.join(self.root, 'demo', 'SKILL.md'), SKILL + '\nRun `../other/scripts/tool.py`.\n')
        self.assertFails('# Ref\n', 'demo/SKILL.md', '../other/ leaves the skill', 'skill://other/<path>')

    def test_path_into_another_skill_fails_from_a_reference(self):
        self.add_skill('other')
        self.assertFails('# Ref\n\nSee [the tool](../../other/scripts/tool.py).\n', 'ref.md:3', '../other/ leaves the skill')

    def test_path_into_a_skill_that_is_not_there_fails(self):
        self.assertFails('# Ref\n\nSee ../../ghost/references/notes.md.\n', 'ref.md:3', '../ghost/ leaves the skill')

    def test_parent_path_inside_the_skill_passes(self):
        write(os.path.join(self.root, 'demo', 'playbooks', 'ship.md'), '# Ship\n')
        self.assertPasses('# Ref\n\nBack to [Start](../SKILL.md#start), then [ship](../playbooks/ship.md).\n'
                          'In the target repo, compare against `../sibling-repo/src`.\n')

    def test_skill_uris_that_resolve_pass(self):
        self.add_skill('other')
        self.assertPasses('# Ref\n\nRead skill://demo and skill://demo/references/ref.md.\n'
                          'Run `python skill://other/scripts/tool.py list`, described in skill://other/SKILL.md.\n'
                          'A placeholder such as `skill://<name>/<path>` is not a reference.\n')

    def test_skill_uri_to_a_missing_skill_fails(self):
        self.assertFails('# Ref\n\nRead skill://ghost first.\n', 'ref.md:3', 'skill://ghost names no skill')

    def test_skill_uri_to_a_missing_file_fails(self):
        self.assertFails('# Ref\n\nRead skill://demo/references/missing.md.\n', 'ref.md:3',
                         'skill://demo/references/missing.md does not exist')

    def test_skill_uri_that_climbs_out_of_its_skill_fails(self):
        self.add_skill('other')
        self.assertFails('# Ref\n\nRead skill://demo/../other/SKILL.md.\n', 'ref.md:3',
                         'skill://demo/../other/SKILL.md climbs with `..`')

    def test_cited_parent_path_inside_the_skill_must_exist(self):
        playbook = os.path.join(self.root, 'demo', 'playbooks', 'ship.md')
        write(playbook, '# Ship\n\nTriage per `../references/ref.md`.\n')
        self.assertPasses('# Ref\n')
        write(playbook, '# Ship\n\nTriage per `../references/gone.md`.\n')
        self.assertFails('# Ref\n', 'demo/playbooks/ship.md:3', 'cited path does not exist: ../references/gone.md')

    def test_named_skill_that_exists_passes(self):
        self.add_skill('other')
        self.assertPasses('# Ref\n\nShip through the **other** skill. The **demo** skill covers the rest.\n')

    def test_named_skill_that_is_not_there_fails(self):
        self.assertFails('# Ref\n\nShip through the **ghost** skill.\n', 'ref.md:3', '"the **ghost** skill"', 'if installed')

    def test_named_skill_marked_optional_passes(self):
        self.assertPasses('# Ref\n\nUse the **ghost** skill\'s `contract` block, if installed. If the **phantom** skill is installed, run it.\n'
                          'If installed, use the **wraith** skill.\n')

    def test_optional_marker_in_a_later_sentence_does_not_excuse_the_name(self):
        self.assertFails('# Ref\n\nShip through the **ghost** skill. Use tmux if installed.\n', 'ref.md:3', '"the **ghost** skill"')

    def test_verdict_counts_hidden_skills(self):
        self.add_skill('other', 'disable-model-invocation: true\n', 'Manual only. Load it when the user names it.')
        self.add_skill('third', 'disable-model-invocation: false\n')
        code, out, _ = self.check('# Ref\n')
        self.assertEqual(code, 0, out)
        self.assertEqual(out.strip().splitlines()[-1], 'PASS 3 skills (2 auto-routable, 1 hidden), 0 failures, 0 over budget')

    def test_hidden_skill_must_say_manual_only(self):
        self.add_skill('other', 'disable-model-invocation: true\n', 'Use when editing a skill.')
        self.add_skill('folded', 'disable-model-invocation: true\n', '>-\n  Manual only. Load it when the user names it.')
        code, out, _ = self.check('# Ref\n')
        self.assertEqual(code, 1, out)
        self.assertIn('other: disable-model-invocation is true, so the description must start "Manual only."', out)
        self.assertNotIn('folded:', out)


class TestsCheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.tests = os.path.join(self.tmp, 'tests')

    def check(self):
        return run([os.path.join(SCRIPTS, 'check_tests.py'), '--tests-dir', self.tests])

    def test_passing_suite(self):
        write(os.path.join(self.tests, 'test_a.py'), 'import unittest\nclass T(unittest.TestCase):\n    def test_a(self):\n        pass\n')
        code, out, _ = self.check()
        self.assertEqual(code, 0, out)
        last = out.strip().splitlines()[-1]
        self.assertEqual(last, 'PASS tests: unittest 1 ran')

    def test_failing_suite(self):
        write(os.path.join(self.tests, 'test_a.py'), 'import unittest\nclass T(unittest.TestCase):\n    def test_a(self):\n        self.assertEqual(1, 2)\n')
        code, out, _ = self.check()
        self.assertEqual(code, 1, out)
        self.assertTrue(out.strip().splitlines()[-1].startswith('FAIL tests: unittest failed'))

    def test_no_tests_is_not_a_pass(self):
        write(os.path.join(self.tests, 'notes.txt'), 'x')
        code, out, _ = self.check()
        self.assertEqual(code, 2)
        self.assertNotIn('PASS', out)


if __name__ == '__main__':
    unittest.main()
