import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "skills", "architect", "scripts", "hotspots.py")
ENV = {k: v for k, v in os.environ.items() if k not in ("GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE", "GIT_PREFIX")}


class HotspotsTests(unittest.TestCase):
    def setUp(self):
        self.repo = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.repo, True)
        self.git("init", "-q", "-b", "main")
        self.n = 0

    def git(self, *args):
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args],
                       cwd=self.repo, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=ENV)

    def commit(self, *paths):
        """One commit that appends a line to each path."""
        self.n += 1
        for rel in paths:
            full = os.path.join(self.repo, rel)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "a", encoding="utf-8", newline="\n") as handle:
                handle.write("line %d\n" % self.n)
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "c%d" % self.n)

    def run_script(self, *args, root=None):
        proc = subprocess.run([sys.executable, SCRIPT, "--root", root or self.repo, *args], capture_output=True,
                              text=True, encoding="utf-8", stdin=subprocess.DEVNULL, env=ENV)
        lines = proc.stdout.strip().splitlines()
        return proc.returncode, (lines[-1] if lines else ""), proc.stdout

    def result(self, *args):
        code, last, out = self.run_script("--json", *args)
        self.assertEqual(code, 0, out)
        self.assertTrue(last.startswith("OK hotspots: "), out)
        return json.loads(out.strip().splitlines()[-2])

    def test_most_changed_file_ranks_first_with_its_counts(self):
        for _ in range(4):
            self.commit("src/hot.py")
        self.commit("src/cold.py")
        files = self.result()["files"]
        self.assertEqual(files[0]["path"], "src/hot.py")
        self.assertEqual((files[0]["touches"], files[0]["churn"], files[0]["lines"]), (4, 4, 4))

    def test_cross_folder_pair_reports_both_rates(self):
        for _ in range(3):
            self.commit("api/orders.py", "ui/cart.js")
        self.commit("ui/cart.js")
        self.commit("api/orders.py", "api/users.py")
        pairs = self.result()["pairs"]
        pair = next(p for p in pairs if {p["a"], p["b"]} == {"api/orders.py", "ui/cart.js"})
        self.assertEqual(pair["shared"], 3)
        self.assertTrue(pair["cross_dir"])
        self.assertEqual(sorted([pair["a_rate"], pair["b_rate"]]), [0.75, 0.75])
        self.assertFalse(any({p["a"], p["b"]} == {"api/orders.py", "api/users.py"} for p in pairs))

    def test_bulk_commit_is_skipped_and_counted(self):
        many = ["pkg/f%d.py" % i for i in range(6)]
        self.commit(*many)
        self.commit("pkg/f0.py")
        result = self.result("--max-files", "5")
        self.assertEqual(result["bulk_skipped"], 1)
        self.assertEqual({f["path"]: f["touches"] for f in result["files"]}, {"pkg/f0.py": 1})
        self.assertEqual(result["pairs"], [])

    def test_lockfiles_vendored_trees_and_prose_are_not_ranked(self):
        for _ in range(3):
            self.commit("src/app.py", "package-lock.json", "vendor/lib/x.js", "docs/notes.md")
        result = self.result()
        self.assertEqual([f["path"] for f in result["files"]], ["src/app.py"])
        self.assertEqual(result["pairs"], [])

    def test_test_with_its_subject_is_marked_expected_and_not_printed(self):
        for _ in range(3):
            self.commit("src/parser.py", "tests/test_parser.py")
        pair = self.result()["pairs"][0]
        self.assertEqual(pair["expected"], "test with its subject")
        code, _, out = self.run_script()
        self.assertEqual(code, 0, out)
        self.assertIn("none above the shared-commit floor", out)
        self.assertIn("1 expected pairs not shown", out)

    def test_history_follows_a_rename(self):
        for _ in range(3):
            self.commit("src/old_name.py")
        self.git("mv", "src/old_name.py", "src/new_name.py")
        self.git("commit", "-q", "-m", "rename")
        self.commit("src/new_name.py")
        files = {f["path"]: f["touches"] for f in self.result()["files"]}
        self.assertEqual(files, {"src/new_name.py": 4})

    def test_sparse_history_is_called_out(self):
        self.commit("src/a.py")
        code, _, out = self.run_script()
        self.assertEqual(code, 0, out)
        self.assertIn("fewer than 20 usable commits", out)

    def test_errors_are_never_a_result(self):
        plain = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, plain, True)
        for root, extra in ((plain, ()), (os.path.join(plain, "missing"), ()), (self.repo, ())):
            code, last, out = self.run_script(*extra, root=root)
            self.assertEqual(code, 2, out)
            self.assertTrue(last.startswith("ERROR hotspots: "), out)
        code, last, out = self.run_script("--nope")
        self.assertEqual(code, 2, out)
        self.assertTrue(last.startswith("ERROR hotspots: bad arguments"), out)


if __name__ == "__main__":
    unittest.main()
