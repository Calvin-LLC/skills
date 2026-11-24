"""Install, drift check and hooks, against a temp home and a temp source repo.

Windows drives install.ps1 and POSIX drives install.sh. The real home is never touched:
SKILLS_HOME moves every path the installer and the checker derive from it.
"""
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
WINDOWS = os.name == "nt"
POWERSHELL = shutil.which("powershell") or shutil.which("pwsh")
SKIP_REASON = None
if WINDOWS and not POWERSHELL:
    SKIP_REASON = "install.ps1 needs powershell or pwsh on PATH"
elif not WINDOWS and not shutil.which("sh"):
    SKIP_REASON = "install.sh needs sh on PATH"

SOUL = "# soul\nkeep it short\n"
STUB_CHECK = "import os, sys\nsys.exit(1 if os.path.exists('BLOCK') else 0)\n"
SKILL_ROOTS = [".agents/skills", ".claude/skills", ".pi/agent/skills",
               ".hermes/skills", ".config/muse/skills", ".codex/skills"]
SOUL_LINKS = [".pi/agent/SOUL.md", ".hermes/SOUL.md", ".agents/SOUL.md", ".omp/agent/RULES.md", ".config/muse/AGENTS.md"]


def forget_readonly(func, path, _exc):
    os.chmod(path, stat.S_IWRITE)
    func(path)


def remove_link(path):
    # unlink fails on a Windows junction, rmdir fails on a POSIX symlink
    (os.rmdir if WINDOWS else os.unlink)(path)


@unittest.skipIf(SKIP_REASON, SKIP_REASON or "")
class InstallTest(unittest.TestCase):
    def setUp(self):
        tmp = Path(tempfile.mkdtemp(prefix="skills-install-")).resolve()
        self.addCleanup(shutil.rmtree, tmp, onerror=forget_readonly)
        self.home = tmp / "home"
        self.home.mkdir()
        self.source = tmp / "source"
        self.clone = self.home / ".agents" / "calvin-skills"
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        env["SKILLS_HOME"] = self.home.as_posix()
        env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
        self.env = env
        self.make_source()

    def make_source(self):
        self.source.mkdir()
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        self.write("skills/alpha/SKILL.md", "---\nname: alpha\ndescription: First.\n---\nBody.\n")
        self.write("SOUL.md", SOUL)
        self.write("scripts/check.py", STUB_CHECK)
        for name in ("install.ps1", "install.sh", "scripts/check_install.py", "scripts/hooks/pre-commit",
                     "scripts/hooks/post-commit"):
            target = self.source / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO / name, target)
            if name.startswith("scripts/hooks/"):
                target.chmod(0o755)
        self.git("add", "-A")
        self.commit("initial", hooks=False)

    def run_cmd(self, cmd, cwd=None, env=None):
        return subprocess.run([str(c) for c in cmd], cwd=cwd, env=env or self.env, capture_output=True,
                              text=True, encoding="utf-8", errors="replace")

    def git(self, *args, repo=None):
        proc = self.run_cmd(["git", *args], cwd=repo or self.source)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        return proc.stdout.strip()

    def write(self, rel, text, repo=None):
        path = (repo or self.source) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")

    def commit(self, message, hooks=True):
        args = ["commit", "-q", "-m", message]
        if not hooks:
            args = ["-c", "core.hooksPath=" + (self.source.parent / "no-hooks").as_posix()] + args
        return self.run_cmd(["git", *args], cwd=self.source)

    def commit_change(self, rel="skills/alpha/SKILL.md", text=None, hooks=False):
        self.write(rel, text or "---\nname: alpha\ndescription: Second.\n---\nBody.\n")
        self.git("add", "-A")
        proc = self.commit("change", hooks=hooks)
        if not hooks:
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        return proc

    def install(self, *extra):
        if WINDOWS:
            cmd = [POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", self.source / "install.ps1",
                   "-Source", self.source]
            cmd += ["-Stash" if a == "stash" else a for a in extra]
        else:
            cmd = ["sh", self.source / "install.sh", "--source", self.source]
            cmd += ["--stash" if a == "stash" else a for a in extra]
        return self.run_cmd(cmd)

    def installed(self, *extra):
        proc = self.install(*extra)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        return proc

    def check(self):
        return self.run_cmd([sys.executable, self.source / "scripts" / "check_install.py"])

    def assertVerdict(self, proc, verdict, code, fragment=None):
        out = proc.stdout.strip().splitlines()
        self.assertTrue(out and out[-1].startswith(verdict + " "), proc.stdout + proc.stderr)
        self.assertEqual(proc.returncode, code, proc.stdout + proc.stderr)
        if fragment:
            self.assertIn(fragment, proc.stdout)

    def test_other_platform_installer_is_not_driven(self):
        if WINDOWS:
            self.skipTest("install.sh is not driven on Windows, install.ps1 is")
        self.skipTest("install.ps1 is not driven on POSIX, install.sh is")

    def test_first_install_creates_clone_and_links(self):
        self.installed()
        self.assertEqual(self.git("rev-parse", "HEAD", repo=self.clone), self.git("rev-parse", "HEAD"))
        self.assertEqual(self.git("config", "core.hooksPath"), "scripts/hooks")
        self.assertIn("github.com", self.git("remote", "get-url", "origin", repo=self.clone))
        for root in SKILL_ROOTS:
            entry = self.home / root / "alpha"
            self.assertEqual(os.path.realpath(entry), os.path.realpath(self.clone / "skills" / "alpha"), root)
        for link in SOUL_LINKS:
            self.assertEqual((self.home / link).read_text(encoding="utf-8").replace("\r\n", "\n"), SOUL, link)

    def test_check_skips_without_clone(self):
        self.assertVerdict(self.check(), "SKIP", 0)

    def test_check_passes_after_install(self):
        self.installed()
        self.assertVerdict(self.check(), "PASS", 0)

    def test_new_commit_fails_on_head_until_installed(self):
        self.installed()
        self.commit_change()
        failed = self.check()
        self.assertVerdict(failed, "FAIL", 1, "clone HEAD")
        self.assertIn("1 commits behind", failed.stdout)
        self.assertIn(str(self.source / "install"), failed.stdout.splitlines()[-1])
        self.installed()
        self.assertVerdict(self.check(), "PASS", 0)

    def test_amended_commit_moves_the_clone(self):
        self.installed()
        self.commit_change()
        self.installed()
        self.git("-c", "core.hooksPath=" + (self.source.parent / "no-hooks").as_posix(),
                 "commit", "-q", "--amend", "-m", "reworded")
        self.assertVerdict(self.check(), "FAIL", 1, "clone HEAD")
        moved = self.installed()
        self.assertIn("stays in the clone's reflog", moved.stdout)
        self.assertEqual(self.git("rev-parse", "HEAD", repo=self.clone), self.git("rev-parse", "HEAD"))
        self.assertVerdict(self.check(), "PASS", 0)

    def test_hand_edit_in_clone_fails_check_and_installer_refuses(self):
        self.installed()
        edited = self.clone / "skills" / "alpha" / "SKILL.md"
        before = edited.read_text(encoding="utf-8")
        edited.write_text(before + "hand edit\n", encoding="utf-8")
        (self.clone / "stray.txt").write_text("x", encoding="utf-8")
        failed = self.check()
        self.assertVerdict(failed, "FAIL", 1, "2 uncommitted paths (1 modified, 1 untracked)")
        self.assertIn("tash", failed.stdout.splitlines()[-1])
        self.commit_change()
        refused = self.install()
        self.assertNotEqual(refused.returncode, 0, refused.stdout)
        self.assertIn("2 uncommitted paths", refused.stdout + refused.stderr)
        self.assertIn("hand edit", edited.read_text(encoding="utf-8"))
        self.installed("stash")
        self.assertVerdict(self.check(), "PASS", 0)
        self.assertNotIn("hand edit", edited.read_text(encoding="utf-8"))
        self.assertFalse((self.clone / "stray.txt").exists())

    def test_stash_keeps_hand_edits_recoverable(self):
        self.installed()
        edited = self.clone / "skills" / "alpha" / "SKILL.md"
        before = edited.read_text(encoding="utf-8")
        edited.write_text(before + "hand edit\n", encoding="utf-8")
        (self.clone / "stray.txt").write_text("untracked work\n", encoding="utf-8")
        self.commit_change("notes.txt", "n\n")
        proc = self.installed("stash")
        self.assertIn("Stashed 2 uncommitted paths", proc.stdout)
        self.assertIn("stash list", proc.stdout)
        self.assertIn("calvin-skills install", self.git("stash", "list", repo=self.clone))
        self.assertIn("hand edit", self.git("show", "stash@{0}:skills/alpha/SKILL.md", repo=self.clone))
        self.assertEqual(self.git("show", "stash@{0}^3:stray.txt", repo=self.clone), "untracked work")
        self.assertVerdict(self.check(), "PASS", 0)
        self.git("stash", "pop", repo=self.clone)
        self.assertIn("hand edit", edited.read_text(encoding="utf-8"))
        self.assertEqual((self.clone / "stray.txt").read_text(encoding="utf-8").strip(), "untracked work")

    def test_missing_and_foreign_skill_entries_fail(self):
        self.installed()
        remove_link(self.home / ".claude" / "skills" / "alpha")
        failed = self.check()
        self.assertVerdict(failed, "FAIL", 1, "lacks 1 skills: alpha")
        self.assertIn(str(self.home / ".claude" / "skills"), failed.stdout)
        self.installed()
        entry = self.home / ".codex" / "skills" / "alpha"
        remove_link(entry)
        shutil.copytree(self.clone / "skills" / "alpha", entry)
        self.assertVerdict(self.check(), "FAIL", 1, "do not resolve into the clone: alpha")
        self.installed()
        self.assertVerdict(self.check(), "PASS", 0)

    def test_stale_soul_fails(self):
        self.installed()
        soul = self.home / ".hermes" / "SOUL.md"
        soul.unlink()
        soul.write_text("old soul\n", encoding="utf-8")
        self.assertVerdict(self.check(), "FAIL", 1, "SOUL.md differs")
        self.installed()
        self.assertVerdict(self.check(), "PASS", 0)

    def install_muse_stub(self):
        bin_dir = self.home / "bin"
        bin_dir.mkdir()
        stub = bin_dir / "muse_stub.py"
        stub.write_text(
            "import json, os, shutil, sys\n"
            "home = os.environ['SKILLS_HOME']\n"
            "args = sys.argv[1:]\n"
            "with open(os.path.join(home, 'muse-calls.log'), 'a') as log:\n"
            "    log.write(' '.join(args) + '\\n')\n"
            "skills = os.path.join(home, '.config', 'muse', 'skills')\n"
            "lock_path = os.path.join(skills, '.muse', 'lock.json')\n"
            "with open(lock_path) as f:\n"
            "    lock = json.load(f)\n"
            "entries = lock.setdefault('skills', {})\n"
            "src = None\n"
            "if args[:2] == ['skills', 'install']:\n"
            "    src = args[2]\n"
            "    entries[os.path.basename(src)] = {'source': {'path': src}}\n"
            "elif args[:2] == ['skills', 'update']:\n"
            "    src = os.path.join(home, '.agents', 'calvin-skills', 'skills', args[2])\n"
            "elif args[:2] == ['skills', 'uninstall']:\n"
            "    shutil.rmtree(os.path.join(skills, args[2]))\n"
            "    del entries[args[2]]\n"
            "else:\n"
            "    sys.exit(0)\n"
            "with open(lock_path, 'w') as f:\n"
            "    json.dump(lock, f)\n"
            "if src:\n"
            "    shutil.copytree(src, os.path.join(skills, os.path.basename(src)), dirs_exist_ok=True)\n",
            encoding="utf-8")
        if WINDOWS:
            (bin_dir / "muse.cmd").write_text('@"%s" "%s" %%*\r\n' % (sys.executable, stub), encoding="ascii")
        else:
            launcher = bin_dir / "muse"
            launcher.write_text('#!/bin/sh\nexec "%s" "%s" "$@"\n' % (sys.executable, stub), encoding="utf-8")
            launcher.chmod(0o755)
        self.env["PATH"] = str(bin_dir) + os.pathsep + self.env["PATH"]
        return self.home / "muse-calls.log"

    def tree(self, root):
        return {p.relative_to(root).as_posix() for p in root.rglob("*")}

    def test_muse_managed_root_is_compared_by_content_and_updated_by_muse(self):
        muse_skills = self.home / ".config" / "muse" / "skills"
        (muse_skills / ".muse").mkdir(parents=True)
        (muse_skills / ".muse" / "lock.json").write_text("{}", encoding="utf-8")
        (muse_skills / "alpha").mkdir()
        (muse_skills / "alpha" / "SKILL.md").write_text("stale copy\n", encoding="utf-8")
        (muse_skills / "other").mkdir()
        (muse_skills / "other" / "SKILL.md").write_text("not ours\n", encoding="utf-8")

        without_muse = self.installed()
        self.assertIn("muse is not on PATH", without_muse.stdout)
        self.assertEqual((muse_skills / "alpha" / "SKILL.md").read_text(encoding="utf-8"), "stale copy\n")
        failed = self.check()
        self.assertVerdict(failed, "FAIL", 1, "stale Muse copies (content differs from the clone): alpha")
        self.assertNotIn("do not resolve", failed.stdout)

        log = self.install_muse_stub()
        before = self.tree(muse_skills)
        self.installed()
        self.assertTrue(before <= self.tree(muse_skills), before - self.tree(muse_skills))
        self.assertTrue(os.path.isdir(muse_skills / "alpha") and not os.path.islink(muse_skills / "alpha"))
        self.assertEqual((muse_skills / "alpha" / "SKILL.md").read_bytes(),
                         (self.clone / "skills" / "alpha" / "SKILL.md").read_bytes())
        self.assertVerdict(self.check(), "PASS", 0)

        copy = muse_skills / "alpha" / "SKILL.md"
        copy.write_bytes(copy.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
        self.assertVerdict(self.check(), "PASS", 0)
        copy.write_bytes(copy.read_bytes() + b"edited\r\n")
        self.assertVerdict(self.check(), "FAIL", 1, "stale Muse copies (content differs from the clone): alpha")
        self.installed()
        self.assertVerdict(self.check(), "PASS", 0)
        calls = log.read_text(encoding="utf-8").splitlines()
        self.assertIn("skills update alpha", calls)
        self.assertIn("skills enable alpha --scope user", calls)

        self.write("skills/beta/SKILL.md", "---\nname: beta\ndescription: New.\n---\nBody.\n")
        self.git("add", "-A")
        self.assertEqual(self.commit("beta", hooks=False).returncode, 0)
        self.assertVerdict(self.check(), "FAIL", 1, "1 commits behind")
        self.installed()
        self.assertTrue((muse_skills / "beta" / "SKILL.md").is_file())
        self.assertTrue(any(c.startswith("skills install ") and c.endswith("beta --scope user")
                            for c in log.read_text(encoding="utf-8").splitlines()))
        self.assertVerdict(self.check(), "PASS", 0)

    def test_skill_removed_from_the_repo_leaves_every_harness(self):
        muse_skills = self.home / ".config" / "muse" / "skills"
        (muse_skills / ".muse").mkdir(parents=True)
        (muse_skills / ".muse" / "lock.json").write_text("{}", encoding="utf-8")
        path_without_muse = self.env["PATH"]
        log = self.install_muse_stub()
        path_with_muse = self.env["PATH"]
        self.write("skills/beta/SKILL.md", "---\nname: beta\ndescription: New.\n---\nBody.\n")
        self.git("add", "-A")
        self.assertEqual(self.commit("beta", hooks=False).returncode, 0)
        self.installed()
        self.assertTrue((muse_skills / "beta" / "SKILL.md").is_file())
        self.assertTrue(os.path.lexists(self.home / ".claude" / "skills" / "beta"))

        self.git("rm", "-r", "-q", "skills/beta")
        self.assertEqual(self.commit("drop beta", hooks=False).returncode, 0)
        self.env["PATH"] = path_without_muse
        self.installed()
        for root in SKILL_ROOTS:
            if root != ".config/muse/skills":
                self.assertFalse(os.path.lexists(self.home / root / "beta"), root)
        self.assertVerdict(self.check(), "FAIL", 1, "holds 1 skills the clone no longer has: beta")

        self.env["PATH"] = path_with_muse
        self.installed()
        self.assertIn("skills uninstall beta", log.read_text(encoding="utf-8").splitlines())
        self.assertFalse((muse_skills / "beta").exists())
        self.assertVerdict(self.check(), "PASS", 0)

    def test_muse_root_without_dot_muse_is_linked(self):
        (self.home / ".config" / "muse" / "skills").mkdir(parents=True)
        self.installed()
        entry = self.home / ".config" / "muse" / "skills" / "alpha"
        self.assertEqual(os.path.realpath(entry), os.path.realpath(self.clone / "skills" / "alpha"))

    def test_pre_commit_blocks_and_post_commit_syncs(self):
        self.installed()
        self.write("BLOCK", "")
        self.write("skills/alpha/SKILL.md", "---\nname: alpha\ndescription: Third.\n---\nBody.\n")
        self.git("add", "-A")
        head = self.git("rev-parse", "HEAD")
        blocked = self.commit("blocked")
        self.assertNotEqual(blocked.returncode, 0, blocked.stdout + blocked.stderr)
        self.assertIn("scripts/check.py failed", blocked.stderr)
        self.assertEqual(self.git("rev-parse", "HEAD"), head)
        (self.source / "BLOCK").unlink()
        self.git("add", "-A")
        done = self.commit("allowed")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn("post-commit: Synced calvin-skills at", done.stdout + done.stderr)
        self.assertEqual(self.git("rev-parse", "HEAD", repo=self.clone), self.git("rev-parse", "HEAD"))
        self.assertVerdict(self.check(), "PASS", 0)

    def test_post_commit_leaves_other_branches_and_never_fails_the_commit(self):
        self.installed()
        clone_head = self.git("rev-parse", "HEAD", repo=self.clone)
        self.git("checkout", "-q", "-b", "feature")
        self.commit_change("notes.txt", "n\n", hooks=True)
        self.assertEqual(self.git("rev-parse", "HEAD", repo=self.clone), clone_head)
        self.git("checkout", "-q", "main")
        (self.clone / "stray.txt").write_text("x", encoding="utf-8")
        proc = self.commit_change("notes.txt", "m\n", hooks=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("1 uncommitted paths", proc.stdout + proc.stderr)
        self.assertEqual(self.git("rev-parse", "HEAD", repo=self.clone), clone_head)


if __name__ == "__main__":
    unittest.main()
