#!/usr/bin/env python3
"""Check that the clone agents load is the commit of this checkout, untouched, and linked everywhere.

Verdict is the last stdout line: PASS, SKIP or FAIL. SKILLS_HOME replaces the home directory,
as it does for install.ps1 and install.sh.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HOME = Path(os.environ.get("SKILLS_HOME") or Path.home())
CLONE = HOME / ".agents" / "calvin-skills"
OMP_AGENT = HOME / ".omp" / "agent"
LIST_LIMIT = 6


def tool_dirs():
    # install.sh honours these three variables, install.ps1 does not; a test home honours neither.
    if os.name == "nt" or os.environ.get("SKILLS_HOME"):
        return HOME / ".claude", HOME / ".config" / "muse", HOME / ".codex"
    return (Path(os.environ.get("CLAUDE_CONFIG_DIR") or HOME / ".claude"),
            Path(os.environ.get("MUSE_CONFIG_DIR") or HOME / ".config" / "muse"),
            Path(os.environ.get("CODEX_HOME") or HOME / ".codex"))


def soul_links():
    # OMP reads RULES.md and Muse Code reads AGENTS.md; neither reads SOUL.md.
    return [HOME / ".pi" / "agent" / "SOUL.md", HOME / ".hermes" / "SOUL.md", HOME / ".agents" / "SOUL.md",
            OMP_AGENT / "RULES.md", tool_dirs()[1] / "AGENTS.md"]


def skill_roots():
    claude, muse, codex = tool_dirs()
    return [
        HOME / ".agents" / "skills",
        claude / "skills",
        HOME / ".pi" / "agent" / "skills",
        HOME / ".hermes" / "skills",
        muse / "skills",
        codex / "skills",
    ]


def git(path, *args):
    env = {k: v for k, v in os.environ.items() if k not in ("GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE", "GIT_PREFIX")}
    proc = subprocess.run(["git", "-C", str(path)] + list(args), capture_output=True, text=True, env=env)
    return proc.stdout.rstrip("\r\n") if proc.returncode == 0 else None


def real(path):
    return os.path.normcase(os.path.realpath(str(path)))


def short_list(names):
    names = sorted(names)
    shown = ", ".join(names[:LIST_LIMIT])
    return shown + (" and %d more" % (len(names) - LIST_LIMIT) if len(names) > LIST_LIMIT else "")


def status_counts(lines):
    names = {"??": "untracked"}
    counts = {}
    for line in lines:
        code = line[:2]
        if code in names:
            label = names[code]
        elif "U" in code:
            label = "conflicted"
        elif "D" in code:
            label = "deleted"
        elif "R" in code:
            label = "renamed"
        elif "A" in code:
            label = "added"
        else:
            label = "modified"
        counts[label] = counts.get(label, 0) + 1
    return ", ".join("%d %s" % (n, label) for label, n in sorted(counts.items()))


def folder_files(folder):
    files = {}
    for dirpath, dirnames, filenames in os.walk(str(folder)):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for name in filenames:
            path = Path(dirpath) / name
            # Muse keeps a copy whose content is unchanged, so a checkout that only flipped line endings is not stale.
            files[path.relative_to(folder).as_posix()] = path.read_bytes().replace(b"\r\n", b"\n")
    return files


def removed_from_clone(path, skills_dir):
    full = os.path.normcase(str(path).replace("\\\\?\\", ""))
    return full.startswith(os.path.normcase(str(skills_dir)) + os.sep) and not os.path.exists(full)


def dangling_links(root, skills_dir):
    gone = []
    for entry in root.iterdir():
        try:
            target = os.readlink(entry)
        except OSError:
            continue
        if removed_from_clone(target, skills_dir):
            gone.append(entry.name)
    return gone


def muse_leftovers(root, skills_dir):
    try:
        lock = json.loads((root / ".muse" / "lock.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [name for name, entry in (lock.get("skills") or {}).items()
            if removed_from_clone(((entry.get("source") or {}).get("path") or ""), skills_dir)]


def fix_command(dirty):
    if os.name == "nt":
        script = str(REPO / "install.ps1")
        return 'powershell -ExecutionPolicy Bypass -File "%s" -Source "%s"%s' % (script, REPO, " -Stash" if dirty else "")
    return 'sh "%s" --source "%s"%s' % (REPO / "install.sh", REPO, " --stash" if dirty else "")


def main():
    if not CLONE.is_dir():
        print("SKIP install: no clone at %s" % CLONE)
        return 0

    findings, dirty = [], False
    clone_head = git(CLONE, "rev-parse", "HEAD")
    if clone_head is None:
        findings.append("%s is not a git repository" % CLONE)
    else:
        source_head = git(REPO, "rev-parse", "HEAD")
        # The post-commit hook syncs main only, so another branch is not expected to match.
        if source_head and git(REPO, "symbolic-ref", "--short", "-q", "HEAD") == "main" and source_head != clone_head:
            ahead = git(REPO, "rev-list", "--count", "%s..%s" % (clone_head, source_head))
            behind = "%s commits behind" % ahead if ahead else "on a different history from"
            findings.append("clone HEAD %s is %s the checkout HEAD %s" % (clone_head[:7], behind, source_head[:7]))
        porcelain = git(CLONE, "status", "--porcelain")
        lines = [l for l in (porcelain or "").splitlines() if l]
        if lines:
            dirty = True
            findings.append("clone working tree has %d uncommitted paths (%s)" % (len(lines), status_counts(lines)))

    skills = {}
    skills_dir = CLONE / "skills"
    if skills_dir.is_dir():
        skills = {d.name: d for d in sorted(skills_dir.iterdir()) if (d / "SKILL.md").is_file()}
    for root in skill_roots():
        if not root.is_dir():
            continue
        if (root / ".muse").is_dir():
            # Muse copies skills into its folder, so links are the wrong test; compare content.
            missing = [n for n in skills if not (root / n).is_dir()]
            stale = [n for n, d in skills.items() if n not in missing and folder_files(root / n) != folder_files(d)]
            if missing:
                findings.append("%s is managed by Muse and lacks %d skills: %s" % (root, len(missing), short_list(missing)))
            if stale:
                findings.append("%s has %d stale Muse copies (content differs from the clone): %s" % (root, len(stale), short_list(stale)))
            gone = muse_leftovers(root, skills_dir)
            if gone:
                findings.append("%s is managed by Muse and holds %d skills the clone no longer has: %s" % (root, len(gone), short_list(gone)))
            continue
        missing = [n for n in skills if not os.path.lexists(root / n)]
        stray = [n for n, d in skills.items() if n not in missing and real(root / n) != real(d)]
        if missing:
            findings.append("%s lacks %d skills: %s" % (root, len(missing), short_list(missing)))
        if stray:
            findings.append("%s has %d entries that do not resolve into the clone: %s" % (root, len(stray), short_list(stray)))
        gone = dangling_links(root, skills_dir)
        if gone:
            findings.append("%s links %d skills the clone no longer has: %s" % (root, len(gone), short_list(gone)))

    soul = CLONE / "SOUL.md"
    if soul.is_file():
        wanted = soul.read_bytes()
        for installed in soul_links():
            if not installed.parent.is_dir():
                continue
            if not installed.is_file():
                findings.append("%s is missing" % installed)
            elif installed.read_bytes() != wanted:
                findings.append("%s differs from the clone's SOUL.md" % installed)

    if findings:
        for finding in findings:
            print(finding)
        print("FAIL install: %d problems. Fix: %s" % (len(findings), fix_command(dirty)))
        return 1
    print("PASS install: clone at %s is clean and %d skills are linked into it" % (clone_head[:7], len(skills)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
