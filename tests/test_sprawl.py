import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPT = os.path.join(ROOT, "skills", "tidy", "scripts", "sprawl.py")
CLEAN = os.path.join(HERE, "fixtures", "sprawl", "clean")
BODY = "".join("line %d of a script that is long enough to be hashed\n" % i for i in range(6))


# Run inside a commit hook these tests inherit the committing repo's git variables.
ENV = {k: v for k, v in os.environ.items() if k not in ("GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE", "GIT_PREFIX")}


def git(cwd, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args],
                   cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=ENV)


class SprawlCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = os.path.realpath(self._tmp.name)

    def path(self, *parts):
        return os.path.join(self.tmp, *parts)

    def put(self, repo, rel, text=None):
        if text is None:
            text = BODY + "# unique to " + rel + "\n"
        full = os.path.join(repo, *rel.split("/"))
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)

    def repo(self, tracked=(), untracked=(), clean=False, init=True):
        """A temp repo: optionally the clean fixture, plus tracked and untracked synthetic files."""
        repo = self.path("repo")
        if clean:
            shutil.copytree(CLEAN, repo)
        else:
            os.makedirs(repo)
        if init:
            git(repo, "init", "-q")
        for rel in tracked:
            self.put(repo, rel)
        if init:
            git(repo, "add", "-A")
            git(repo, "commit", "-q", "-m", "base", "--allow-empty")
        for rel in untracked:
            self.put(repo, rel)
        return repo

    def run_sprawl(self, repo, *args):
        proc = subprocess.run([sys.executable, SCRIPT, "--root", repo, *args], capture_output=True, text=True,
                              encoding="utf-8", stdin=subprocess.DEVNULL)
        lines = proc.stdout.strip().splitlines()
        return proc.returncode, (lines[-1] if lines else ""), proc.stdout

    def verdict(self, result, code, word):
        status, last, full = result
        self.assertEqual((status, last.split(" ")[0]), (code, word), full)
        self.assertTrue(last.startswith(word + " sprawl:"), full)
        return full

    def fires(self, full, cls, path):
        self.assertTrue(any(l.startswith("%s: %s " % (cls, path)) for l in full.splitlines()),
                        "%s: %s missing from\n%s" % (cls, path, full))

    def quiet(self, full, path):
        hits = [l for l in full.splitlines() if (": " + path + " ") in l]
        self.assertEqual(hits, [], full)


class CleanTreeTests(SprawlCase):
    def test_clean_fixture_passes(self):
        full = self.verdict(self.run_sprawl(self.repo(clean=True)), 0, "PASS")
        self.assertIn("no findings", full)

    def test_run_changes_nothing_in_the_target(self):
        repo = self.repo(clean=True, untracked=["scratch/x.py"])
        def snapshot():
            return sorted((d, f, os.path.getsize(os.path.join(d, f))) for d, _, fs in os.walk(repo) for f in fs)
        before = snapshot()
        self.run_sprawl(repo)
        self.assertEqual(before, snapshot())

    def test_venv_and_vendor_trees_are_skipped(self):
        repo = self.repo(clean=True)
        self.put(repo, "myenv/pyvenv.cfg", "home = x\n")
        self.put(repo, "myenv/Lib/notes_final.py")
        self.put(repo, "node_modules/pkg/index_final.js")
        self.verdict(self.run_sprawl(repo), 0, "PASS")


class ClassTests(SprawlCase):
    def test_scratch_dir_tracked_and_untracked(self):
        repo = self.repo(clean=True, tracked=["_scratch/a.py", "output/result.json"], untracked=["tmp/run.py"])
        status, last, full = self.run_sprawl(repo)
        self.verdict((status, last, full), 1, "FAIL")
        self.fires(full, "scratch-dir", "_scratch/")
        self.fires(full, "scratch-dir", "tmp/")
        self.fires(full, "scratch-dir", "output/")
        self.assertIn("1 tracked files", full)
        self.assertIn("1 untracked files, not ignored", full)
        self.quiet(full, "_scratch/a.py")  # rolled up into the directory finding

    def test_scratch_dir_look_alikes_stay_quiet(self):
        repo = self.repo(clean=True)
        self.put(repo, "logs/run.log")  # ignored by the fixture's .gitignore
        self.put(repo, ".scratch/notes.py")
        self.verdict(self.run_sprawl(repo), 0, "PASS")

    def test_throwaway_names(self):
        repo = self.repo(clean=True, tracked=["src/app/main_final.py", "src/app/helper.py.bak", "src/probe_x.py"],
                         untracked=["src/tmp.py", "src/app/util_fixed.py"])
        full = self.verdict(self.run_sprawl(repo), 1, "FAIL")
        for p in ["src/app/main_final.py", "src/app/helper.py.bak", "src/probe_x.py", "src/tmp.py", "src/app/util_fixed.py"]:
            self.fires(full, "throwaway-name", p)
        self.assertIn("next to main.py", full)

    def test_throwaway_look_alikes_stay_quiet(self):
        # final_report.py, deep_copy.py, temp_sensor.py, scripts/check_style.py and the test files are in the clean tree
        full = self.verdict(self.run_sprawl(self.repo(clean=True)), 0, "PASS")
        for name in ["final_report.py", "deep_copy.py", "temp_sensor.py", "check_style.py", "test_main.py"]:
            self.assertNotIn(name, full)

    def test_versioned_sibling_and_runs(self):
        repo = self.repo(clean=True, tracked=["src/build.py", "src/build_v2.py", "src/build_copy.py",
                                              "src/step_v0.py", "src/step_v1.py", "src/step_v2.py"])
        full = self.verdict(self.run_sprawl(repo), 1, "FAIL")
        self.fires(full, "versioned-sibling", "src/build_v2.py")
        self.fires(full, "versioned-sibling", "src/build_copy.py")
        self.fires(full, "versioned-sibling", "src/step_v0.py")
        self.fires(full, "versioned-sibling", "src/step_v1.py")
        self.quiet(full, "src/step_v2.py")  # the newest of a run is the one to keep
        self.quiet(full, "src/build.py")
        self.quiet(full, "src/schema_v2.json")  # two schema generations without a base file are not a pile

    def test_numbered_names_without_v_are_not_versions(self):
        repo = self.repo(clean=True, tracked=["src/pistol.c", "src/pistol2.c", "src/part_2.py", "src/part.py"])
        self.verdict(self.run_sprawl(repo), 0, "PASS")

    def test_duplicate_files(self):
        repo = self.repo(clean=True, tracked=["tools/convert.py", "tools/convert_old_name.py"])
        self.put(repo, "tools/convert.py", BODY)
        self.put(repo, "tools/convert_old_name.py", BODY)
        self.put(repo, "tools/other.py", BODY.replace("line", "row"))
        git(repo, "add", "-A")
        full = self.verdict(self.run_sprawl(repo), 1, "FAIL")
        self.fires(full, "duplicate", "tools/convert_old_name.py")
        self.assertIn("same content as tools/convert.py", full)
        self.quiet(full, "tools/other.py")
        self.quiet(full, "packages/b/LICENSE")  # conventional duplicate
        self.quiet(full, "tests/fixtures/old_dump_copy.txt")  # fixtures repeat on purpose

    def test_same_size_different_content_is_not_a_duplicate(self):
        repo = self.repo(clean=True, tracked=["tools/a.py", "tools/b.py"])
        self.put(repo, "tools/a.py", "a" * 100 + "\n")
        self.put(repo, "tools/b.py", "b" * 100 + "\n")
        self.verdict(self.run_sprawl(repo), 0, "PASS")

    def test_report_markdown_outside_docs(self):
        repo = self.repo(clean=True, tracked=["ANALYSIS_REPORT.md", "src/app/FIX_SUMMARY.md", "src/results.txt"])
        full = self.verdict(self.run_sprawl(repo), 1, "FAIL")
        self.fires(full, "report-md", "ANALYSIS_REPORT.md")
        self.fires(full, "report-md", "src/app/FIX_SUMMARY.md")
        self.fires(full, "report-md", "src/results.txt")
        self.quiet(full, "docs/report.md")
        self.quiet(full, "docs/IMPLEMENTATION_SUMMARY.md")
        self.quiet(full, "README.md")

    def test_top_level_entries(self):
        repo = self.repo(clean=True, tracked=["check_env.py", "output.txt", "run.log", "nohup.out"])
        full = self.verdict(self.run_sprawl(repo), 1, "FAIL")
        for p in ["check_env.py", "output.txt", "run.log", "nohup.out"]:
            self.fires(full, "top-level", p)
        self.quiet(full, "requirements.txt")
        self.quiet(full, "setup.py")
        self.quiet(full, "scripts/check_style.py")

    def test_untracked_files_and_dirs(self):
        repo = self.repo(clean=True, untracked=["notes.txt", "newtool/run.py", "newtool/lib.py", "src/app/extra.py",
                                                "README.old.md", "assets/logo.png"])
        full = self.verdict(self.run_sprawl(repo), 1, "FAIL")
        self.fires(full, "untracked", "notes.txt")
        self.fires(full, "untracked", "newtool/")
        self.assertIn("2 script or text files", full)
        self.quiet(full, "src/app/extra.py")  # new file beside tracked files of its kind is ordinary work
        self.quiet(full, "assets/")  # images are not undecided scripts or text
        self.quiet(full, "assets/logo.png")

    def test_skip_hides_a_class(self):
        repo = self.repo(clean=True, untracked=["notes.txt"])
        self.verdict(self.run_sprawl(repo, "--skip", "untracked"), 0, "PASS")
        self.verdict(self.run_sprawl(repo), 1, "FAIL")

    def test_unknown_skip_class_is_error(self):
        full = self.verdict(self.run_sprawl(self.repo(clean=True), "--skip", "nope"), 2, "ERROR")
        self.assertIn("nope", full)


class BaselineTests(SprawlCase):
    def mess(self):
        return self.repo(clean=True, tracked=["src/app/main_final.py", "_scratch/a.py"], untracked=["notes.txt"])

    def test_write_baseline_then_pass(self):
        repo = self.mess()
        base = self.path("base.json")
        full = self.verdict(self.run_sprawl(repo, "--write-baseline", base), 0, "PASS")
        self.assertIn("baseline of 3 findings", full)
        with open(base, encoding="utf-8") as handle:
            saved = json.load(handle)
        self.assertEqual({(f["class"], f["path"]) for f in saved["findings"]},
                         {("scratch-dir", "_scratch/"), ("throwaway-name", "src/app/main_final.py"),
                          ("untracked", "notes.txt")})
        full = self.verdict(self.run_sprawl(repo, "--baseline", base), 0, "PASS")
        self.assertIn("3 baselined, 0 baseline entries gone", full)
        self.assertNotIn("throwaway-name:", full)

    def test_new_finding_fails_and_old_stay_hidden(self):
        repo = self.mess()
        base = self.path("base.json")
        self.run_sprawl(repo, "--write-baseline", base)
        self.put(repo, "src/app/util_v2.py")
        full = self.verdict(self.run_sprawl(repo, "--baseline", base), 1, "FAIL")
        self.fires(full, "versioned-sibling", "src/app/util_v2.py")
        self.assertNotIn("src/app/main_final.py", full)
        self.assertIn("1 new findings", full.strip().splitlines()[-1])

    def test_paid_down_entries_are_counted_gone(self):
        repo = self.mess()
        base = self.path("base.json")
        self.run_sprawl(repo, "--write-baseline", base)
        os.remove(os.path.join(repo, "notes.txt"))
        full = self.verdict(self.run_sprawl(repo, "--baseline", base), 0, "PASS")
        self.assertIn("2 baselined, 1 baseline entries gone", full)

    def test_baseline_inside_the_repo_is_not_a_finding(self):
        repo = self.mess()
        base = os.path.join(repo, "sprawl-baseline.json")
        self.run_sprawl(repo, "--write-baseline", base)
        full = self.verdict(self.run_sprawl(repo, "--baseline", base), 0, "PASS")
        self.assertNotIn("sprawl-baseline.json:", full)

    def test_unreadable_baseline_is_error(self):
        repo = self.mess()
        self.verdict(self.run_sprawl(repo, "--baseline", self.path("missing.json")), 2, "ERROR")
        bad = self.path("bad.json")
        for text in ("not json", '{"findings": 3}', '{"other": []}'):
            with open(bad, "w") as handle:
                handle.write(text)
            self.verdict(self.run_sprawl(repo, "--baseline", bad), 2, "ERROR")


class RootTests(SprawlCase):
    def test_bad_root_is_error(self):
        self.verdict(self.run_sprawl(self.path("does-not-exist")), 2, "ERROR")
        afile = self.path("afile")
        open(afile, "w").close()
        self.verdict(self.run_sprawl(afile), 2, "ERROR")

    def test_broken_git_dir_is_error_not_pass(self):
        repo = self.repo(clean=True, init=False)
        os.makedirs(os.path.join(repo, ".git"))
        self.verdict(self.run_sprawl(repo), 2, "ERROR")

    def test_non_git_root_says_so_and_still_finds(self):
        repo = self.repo(clean=True, init=False, tracked=["_scratch/a.py", "src/app/main_final.py"], untracked=["notes.txt"])
        status, last, full = self.run_sprawl(repo)
        if "not a git repository" not in full:
            self.skipTest("temp directory sits inside a git repository")
        self.verdict((status, last, full), 1, "FAIL")
        self.assertIn("info: no git", full)
        self.fires(full, "scratch-dir", "_scratch/")
        self.assertIn("ignore state unknown", full)
        self.fires(full, "throwaway-name", "src/app/main_final.py")
        self.assertNotIn("untracked:", full)  # no git, so no untracked class

    def test_non_git_clean_root_passes(self):
        repo = self.repo(clean=True, init=False)
        status, last, full = self.run_sprawl(repo)
        if "not a git repository" not in full:
            self.skipTest("temp directory sits inside a git repository")
        self.verdict((status, last, full), 0, "PASS")

    def test_subdirectory_of_a_repo_is_scoped(self):
        repo = self.repo(clean=True, tracked=["pkg/x_final.py", "other/y_final.py"])
        full = self.verdict(self.run_sprawl(os.path.join(repo, "pkg")), 1, "FAIL")
        self.fires(full, "throwaway-name", "x_final.py")
        self.assertNotIn("y_final", full)

    def test_json_line_precedes_the_verdict(self):
        repo = self.repo(clean=True, tracked=["src/app/main_final.py"])
        status, last, full = self.run_sprawl(repo, "--json")
        self.verdict((status, last, full), 1, "FAIL")
        data = json.loads(full.strip().splitlines()[-2])
        self.assertEqual([(f["class"], f["path"]) for f in data["findings"]],
                         [("throwaway-name", "src/app/main_final.py")])
        self.assertTrue(data["git"])

    def test_bad_arguments_end_with_a_verdict(self):
        proc = subprocess.run([sys.executable, SCRIPT, "--nope"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)
        self.assertTrue(proc.stdout.strip().splitlines()[-1].startswith("ERROR sprawl:"), proc.stdout)


if __name__ == "__main__":
    unittest.main()
