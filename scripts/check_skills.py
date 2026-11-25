#!/usr/bin/env python3
"""Gate for skills/: OMP-first wording, resolvable paths and skill references, size budget.

OMP's own tools and internal URLs (skill://, pr://, issue://, agent://, conflict://) pass.
Fails (exit 1) on another harness's tool, CLI, path or config key, a broken frontmatter,
a version number in a frontmatter or a VENDORED.md, a path a skill cites that does not
exist, a `../` path that leaves its skill for another one, a skill:// URI or a
"the **name** skill" reference that names nothing under skills/, or a reference file that
names a part of its own SKILL.md that is not there.
Prints a warning for a SKILL.md over the size budget.
The verdict counts the skills a model can route to on its own and the hidden ones
(`disable-model-invocation: true`). A hidden skill's description starts "Manual only.",
because Muse Code loads it as an ordinary skill and routes on that description.
The last line is the verdict, `PASS ...` or `FAIL ...`.
Run from anywhere: python scripts/check_skills.py [--root <skills dir>]
"""
import argparse
import os
import re
import sys

DEFAULT_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'skills'))
BUDGET = 8000  # bytes of SKILL.md, about 2,000 tokens
VENDORED = {'declauding'}  # upstream text, checked for frontmatter only
VERSION_NUMBER = re.compile(r'\bv?\d+\.\d+\.\d+\b')  # goes stale on every upstream release; the commit hash is the record

# Another harness's tool, CLI, path or config key. OMP's tools and internal URLs are the target and pass.
LEAKS = [
    (r'~/\.hermes|hermes/cache|HERMES_HOME', 'Hermes path'),
    (r'\bstate\.db\b|\bsession export\b|\bhermes sessions\b|\bsession_search\b', 'Hermes session store; use the recall skill\'s scripts/sessions.py'),
    (r'\bsubagent chat\b|delegation\.model|quick_commands|trusted_project_dirs', 'Hermes CLI or config key'),
    (r'`(?:search_files|delegate_task|ask_user_question|skill_view|skill_manage)`', 'one harness\'s tool name'),
    (r'`tasks` per call|up to \d+ `tasks`', 'one harness\'s subagent call shape'),
    (r'pi-dotfiles|/mnt/skills|[A-Z]:\\Users\\|/home/[a-z]+/|/Users/[a-z]+/', 'machine-specific path'),
    (r'\bHermes-only\b|\bpi sessions\b|\bin Hermes\b(?! *[:,])', 'harness named outside a labelled branch'),
    (r'(?<![\w}:.-])/tmp/', 'POSIX-only temp path; say the OS temp directory (it does not resolve for native Windows tools)'),
]
HEADING = re.compile(r'^ {0,3}#{1,6}\s+(.*?)\s*#*\s*$')
PHASE_HEADING = re.compile(r'\bPhase ([A-Z])\b')
STEP_ITEM = re.compile(r'^\s*(\d+)\.\s')
QUOTED_SECTION = re.compile(r'["\u201c]([^"\u201d\n]{1,80})["\u201d]\s+(?:section\s+)?in\s+(?:the\s+)?SKILL\.md')
STEP_REF = re.compile(r'\bsteps?\s+(\d+(?:\s*(?:,|and|to|-|\u2013)\s*\d+)*)\s+in\s+(?:the\s+)?SKILL\.md', re.I)
PHASE_REF = re.compile(r'\bPhase ([A-Z])\b(?:\s+((?i:sign-off|checkpoint|approval))\b)?')

WORD = re.compile(r'[a-z][a-z-]+')
CITED = re.compile(r'`((?:\.\./)?(?:references|reference|scripts|playbooks|agents|schemas)/[A-Za-z0-9_./-]+\.[a-z]+)`')
SKILL_PARTS = {'SKILL.md', 'references', 'reference', 'scripts', 'playbooks', 'agents', 'schemas'}
CLIMB = re.compile(r'(?<![\w./])((?:\.\./)+)([A-Za-z0-9_-]+)/([A-Za-z0-9_.-]*)')
SKILL_URI = re.compile(r'skill://([a-z0-9][a-z0-9-]*)((?:/[A-Za-z0-9_.-]+)*)')
NAMED_SKILL = re.compile(r'\b[Tt]he \*\*([a-z0-9][a-z0-9-]*)\*\* skill\b')
SENTENCE_END = re.compile(r'[.;:](?:\s|$)')
OPTIONAL_SKILL = re.compile(r'\b(?:if|is) installed\b', re.I)
FRONTMATTER = re.compile(r'---\r?\n(.*?)\r?\n---\r?\n', re.S)
HIDDEN = re.compile(r'^disable-model-invocation:\s*true\s*$', re.M)
MANUAL = re.compile(r'^description:\s*(?:[>|]-?\s+)?["\']?Manual only\.', re.M)


def outline(path):
    """Headings, numbered step items and per-phase vocabulary of one SKILL.md."""
    headings, steps, phases = [], set(), set()
    words = {}  # word -> phase letters (None outside any phase) whose text uses it
    phase = None
    for line in open(path, encoding='utf-8'):
        h = HEADING.match(line)
        if h:
            text = re.sub(r'[`*_]', '', h.group(1)).strip()
            headings.append(text)
            m = PHASE_HEADING.search(text)
            phase = m.group(1) if m else None
            if m:
                phases.add(phase)
        m = STEP_ITEM.match(line)
        if m:
            steps.add(int(m.group(1)))
        for w in WORD.findall(line.lower()):
            words.setdefault(w, set()).add(phase)
    return headings, steps, phases, words


def has_heading(name, headings):
    name = re.sub(r'[`*_]', '', name).strip().lower()
    return any(h.lower() == name or re.match(re.escape(name) + r'\b', h.lower()) for h in headings)


def check_xrefs(skill, base, rel, text, out):
    headings, steps, phases, words = out
    found = []
    for n, line in enumerate(text.splitlines(), 1):
        for name in QUOTED_SECTION.findall(line):
            if not has_heading(name, headings):
                found.append('%s:%d: "%s" in SKILL.md does not exist; headings there: %s'
                             % (rel, n, name, '; '.join(headings)))
        for group in STEP_REF.findall(line):
            for num in map(int, re.findall(r'\d+', group)):
                if num not in steps:
                    found.append('%s:%d: step %d in SKILL.md does not exist; numbered steps there: %s'
                                 % (rel, n, num, ', '.join(map(str, sorted(steps))) or 'none'))
        if not phases:
            continue
        for letter, word in PHASE_REF.findall(line):
            if letter not in phases:
                found.append('%s:%d: Phase %s does not exist in SKILL.md; phases there: %s'
                             % (rel, n, letter, ', '.join(sorted(phases))))
                continue
            # "Phase D sign-off" where the gate word only appears under Phase C: a mislabelled phase
            where = words.get(word.lower()) if word else None
            if where and letter not in where and None not in where:
                found.append('%s:%d: "Phase %s %s": SKILL.md uses "%s" only under Phase %s'
                             % (rel, n, letter, word, word.lower(), ', '.join(sorted(where))))
    return found


def check_links(rel, n, line, depth, names, root):
    """Paths and names on one line that point at another skill."""
    found = []
    for ups, first, second in CLIMB.findall(line):
        if ups.count('../') == depth + 1 and (first in names or second in SKILL_PARTS):
            found.append('%s:%d: ../%s/ leaves the skill and OMP\'s skill:// resolver rejects `..`; write skill://%s/<path>'
                         % (rel, n, first, first))
    for name, tail in SKILL_URI.findall(line):
        tail = tail.rstrip('.').lstrip('/')
        if name not in names:
            found.append('%s:%d: skill://%s names no skill under skills/' % (rel, n, name))
        elif '..' in tail.split('/'):
            found.append('%s:%d: skill://%s/%s climbs with `..`, which OMP\'s skill:// resolver rejects' % (rel, n, name, tail))
        elif tail and not os.path.exists(os.path.join(root, name, *tail.split('/'))):
            found.append('%s:%d: skill://%s/%s does not exist' % (rel, n, name, tail))
    for m in NAMED_SKILL.finditer(line):
        sentence = SENTENCE_END.split(line[:m.start()])[-1] + m.group(0) + SENTENCE_END.split(line[m.end():], 1)[0]
        if m.group(1) not in names and not OPTIONAL_SKILL.search(sentence):
            found.append('%s:%d: "the **%s** skill" names no skill under skills/; fix the name or add "if installed"'
                         % (rel, n, m.group(1)))
    return found


def is_hidden(path):
    m = FRONTMATTER.match(open(path, encoding='utf-8').read()) if os.path.isfile(path) else None
    return bool(m and HIDDEN.search(m.group(1)))


def check(skill, root, names):
    errors, warnings = [], []
    base = os.path.join(root, skill)
    path = os.path.join(base, 'SKILL.md')
    if not os.path.isfile(path):
        return ['%s: no SKILL.md' % skill], warnings
    text = open(path, encoding='utf-8').read()
    m = re.match(r'---\r?\n(.*?)\r?\n---\r?\n', text, re.S)
    front = m.group(1) if m else ''
    name = re.search(r'^name:\s*(\S+)', front, re.M)
    if not name or name.group(1).strip('"\'') != skill:
        errors.append('%s: frontmatter name must equal the directory name' % skill)
    if not re.search(r'^description:\s*\S', front, re.M):
        errors.append('%s: frontmatter has no description' % skill)
    elif HIDDEN.search(front) and not MANUAL.search(front):
        errors.append('%s: disable-model-invocation is true, so the description must start "Manual only."' % skill)
    if re.search(r'^\s*version:', front, re.M):
        errors.append('%s/SKILL.md: frontmatter carries a version; delete the line' % skill)
    vendored = os.path.join(base, 'VENDORED.md')
    if os.path.isfile(vendored):
        for n, line in enumerate(open(vendored, encoding='utf-8'), 1):
            if VERSION_NUMBER.search(line):
                errors.append('%s/VENDORED.md:%d: version number; record the upstream commit and nothing else' % (skill, n))
    if skill in VENDORED:
        return errors, warnings
    size = len(text.encode('utf-8'))
    if size > BUDGET:
        warnings.append('%s: SKILL.md is %d bytes (budget %d)' % (skill, size, BUDGET))
    out = outline(path)
    for dirpath, _, files in os.walk(base):
        for fn in files:
            if not fn.endswith('.md') or fn == 'README.md':
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root).replace('\\', '/')
            depth = rel.count('/') - 1
            if full != path:
                errors += check_xrefs(skill, base, rel, open(full, encoding='utf-8').read(), out)
            for n, line in enumerate(open(full, encoding='utf-8'), 1):
                for pattern, why in LEAKS:
                    if re.search(pattern, line):
                        errors.append('%s:%d: %s' % (rel, n, why))
                errors += check_links(rel, n, line, depth, names, root)
                for cited in CITED.findall(line):
                    # a cited path resolves against the skill root or the citing file's directory
                    if not any(os.path.exists(os.path.normpath(os.path.join(d, cited))) for d in (base, dirpath)):
                        errors.append('%s:%d: cited path does not exist: %s' % (rel, n, cited))
    return errors, warnings


def main():
    ap = argparse.ArgumentParser(description='Gate for skills/.')
    ap.add_argument('--root', default=DEFAULT_ROOT, help='skills directory (default: the repo\'s skills/)')
    root = os.path.abspath(ap.parse_args().root)
    if not os.path.isdir(root):
        print('ERROR skills root is not a directory: %s' % root)
        sys.exit(2)
    errors, warnings = [], []
    skills = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))
    if not skills:
        print('ERROR no skill directories under %s' % root)
        sys.exit(2)
    names = {s for s in skills if os.path.isfile(os.path.join(root, s, 'SKILL.md'))}
    hidden = sum(1 for s in names if is_hidden(os.path.join(root, s, 'SKILL.md')))
    for skill in skills:
        e, w = check(skill, root, names)
        errors += e
        warnings += w
    for line in warnings:
        print('warn  ' + line)
    for line in errors:
        print('FAIL  ' + line)
    print('%s %d skills (%d auto-routable, %d hidden), %d failures, %d over budget' % (
        'FAIL' if errors else 'PASS', len(skills), len(names) - hidden, hidden, len(errors), len(warnings)))
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
