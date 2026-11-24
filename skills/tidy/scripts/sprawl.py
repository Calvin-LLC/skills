#!/usr/bin/env python3
"""Read-only sprawl inventory for a repository.

Reports files an agent tends to leave behind: scratch folders, throwaway or
versioned names, exact duplicates, report-style notes, one-off scripts and
captured output in the root, and files git neither tracks nor ignores.
Reads the target and writes nothing there (only --write-baseline writes, to
the path you give). Python 3.8+, stdlib only, Windows and POSIX.

    python sprawl.py [--root <repo>] [--baseline <file>] [--write-baseline <file>]
                     [--skip <class,...>] [--json]

Each finding is one line: `<class>: <path> (<reason>)`.
The last stdout line is the verdict. `PASS sprawl: ...` exits 0, `FAIL sprawl: ...`
exits 1, `ERROR sprawl: ...` exits 2 (bad root, git failure, unreadable baseline;
an error is never a pass). With --baseline only findings absent from the
baseline count, so an existing mess can be gated today and paid down later.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

CLASSES = ['scratch-dir', 'duplicate', 'throwaway-name', 'versioned-sibling',
           'report-md', 'top-level', 'untracked']

# Never inspected: vendored trees, tool caches, build output, virtualenvs.
SKIP_DIRS = {'.git', 'node_modules', 'bower_components', 'vendor', 'third_party', 'third-party',
             '.venv', 'venv', '.virtualenv', 'site-packages', '__pycache__', '.tox', '.nox',
             '.mypy_cache', '.pytest_cache', '.ruff_cache', '.cache', '.next', '.nuxt', '.gradle',
             '.idea', '.vs', 'dist', 'build', 'target', 'coverage', '.eggs', 'bin', 'obj'}
# Legitimate homes of look-alike names: test data, schema versions, migrations.
EXEMPT_DIRS = {'fixtures', 'fixture', '__fixtures__', 'testdata', 'test_data', 'snapshots',
               '__snapshots__', 'migrations', 'versions', 'alembic'}
DOC_DIRS = {'docs', 'doc', 'documentation', 'wiki', 'adr', 'adrs', 'rfc', 'rfcs', 'design',
            'references', 'reference', 'playbooks', 'playbook', 'guides', 'guide', 'templates', '.github'}

STRONG_SCRATCH = {'scratch', '_scratch', '.scratch', 'tmp', '.tmp', '_tmp', 'temp', '.temp', '_temp',
                  '.audit', '.sketch', '.sketches', 'sandbox', 'junk', 'trash', '_trash', 'wip',
                  'scratchpad', '_old', '.old'}
WEAK_SCRATCH = {'out', 'output', 'outputs', '_out', '_output', 'log', 'logs', '_logs', 'old',
                'backup', 'backups', 'bak', 'drafts', '_drafts'}
PACKAGE_MARKERS = {'__init__.py', 'package.json', 'cargo.toml', 'go.mod', 'pom.xml', 'build.gradle',
                   'pyproject.toml', 'setup.py', 'index.js', 'index.ts', 'mod.rs', 'lib.rs'}
PLACEHOLDERS = {'.gitkeep', '.keep', '.gitignore', 'readme', 'readme.md', 'readme.txt'}

CERTAIN_SUFFIX = {'final', 'fixed', 'bak', 'orig', 'wip', 'tmp', 'draft'}
SIBLING_SUFFIX = {'copy', 'old', 'new', 'fix', 'latest', 'revised', 'temp', 'backup', 'bkp'}
THROWAWAY_PREFIX = {'tmp', 'scratch', 'probe', 'junk', 'wip', 'old', 'backup'}
ROOT_PREFIX = {'check', 'fix', 'verify', 'debug', 'repro', 'analyze', 'analyse', 'inspect', 'dump',
               'patch', 'hack', 'try', 'quick'}
LONE_STEMS = {'tmp', 'temp', 'scratch', 'junk'}
BACKUP_EXTS = {'.bak', '.orig', '.old', '.tmp', '.swp', '.swo', '.rej', '.save'}
SCRIPT_EXTS = {'.py', '.sh', '.ps1', '.bat', '.cmd', '.js', '.mjs', '.ts', '.rb', '.pl'}
ONE_OFF_EXTS = SCRIPT_EXTS | {'.md', '.txt', '.json', '.csv', '.log', '.html'}
OUTPUT_EXTS = {'.log', '.out', '.err', '.dump', '.trace', '.pid'}
OUTPUT_TOKENS = {'output', 'outputs', 'out', 'dump', 'debug', 'trace', 'stdout', 'stderr', 'capture',
                 'response', 'scan', 'log', 'logs'}
OUTPUT_DATA_EXTS = {'.txt', '.json', '.csv', '.html'}
REPORT_TOKENS = {'report', 'reports', 'summary', 'summaries', 'analysis', 'audit', 'findings',
                 'handoff', 'postmortem', 'retrospective', 'investigation', 'progress', 'status',
                 'results', 'recap', 'cleanup', 'implementation', 'verification', 'completion'}
REPORT_EXTS = {'.md', '.mdx', '.txt'}
DUP_EXTS = {'.py', '.js', '.mjs', '.cjs', '.ts', '.tsx', '.jsx', '.sh', '.bash', '.ps1', '.bat', '.cmd',
            '.md', '.mdx', '.txt', '.json', '.csv', '.yml', '.yaml', '.html', '.css', '.sql', '.rb',
            '.go', '.rs', '.java', '.c', '.cc', '.cpp', '.h', '.hpp', '.log', '.ipynb', '.toml', '.xml'}
DUP_CONVENTIONAL = {'license', 'license.md', 'license.txt', 'copying', 'notice', 'notice.md',
                    '.gitignore', '.gitattributes', '.editorconfig', '.npmrc', '__init__.py',
                    'conftest.py', 'py.typed', 'tsconfig.json'}
CONVENTIONAL = {'readme', 'agents', 'claude', 'gemini', 'license', 'licence', 'copying', 'notice', 'authors',
                'contributing', 'changelog', 'security', 'codeowners', 'makefile', 'dockerfile', 'justfile'}
DUP_MIN, DUP_MAX = 64, 10 * 1024 * 1024

SIB_RE = re.compile(
    r'^(.+?)[_\- ]+(?:v\d+(?:\.\d+)*|copy|old|new|fix|latest|revised|temp|backup|bkp'
    r'|final\d*|fixed\d*|wip|draft|bak|orig|tmp)$', re.I)
VERSION_RE = re.compile(r'^(.+?)[_\- ]+v(\d+)$', re.I)
VERSION_RUN = 3  # this many numbered versions of one file in a folder is a pile, not two API generations
COPY_MARK = re.compile(r'(?:\s\(\d+\)|\s-\s+copy(?:\s\(\d+\))?|^copy of\s.+)$', re.I)


class SprawlError(Exception):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message):
        print('ERROR sprawl: bad arguments: %s' % message)
        sys.exit(2)


# A git hook exports these; left in place they override --root and point at the committing repo.
HOOK_ENV = ('GIT_DIR', 'GIT_INDEX_FILE', 'GIT_WORK_TREE', 'GIT_PREFIX')


def run_git(root, *args):
    env = {k: v for k, v in os.environ.items() if k not in HOOK_ENV}
    try:
        p = subprocess.run(('git', '-C', root, '-c', 'core.quotepath=off') + args, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, stdin=subprocess.DEVNULL, env=env)
    except OSError as exc:
        raise SprawlError('cannot run git: %s' % exc)
    return p.returncode, p.stdout, p.stderr.decode('utf-8', 'replace').strip()


def inside_git(root):
    """True in a work tree, False when git says this is no repository; anything else is an error."""
    try:
        code, out, err = run_git(root, 'rev-parse', '--is-inside-work-tree')
    except SprawlError:
        here = root
        while True:  # no git binary: fine for a plain folder, an error for a repo
            if os.path.exists(os.path.join(here, '.git')):
                raise SprawlError('root is a git repository but git cannot be run')
            parent = os.path.dirname(here)
            if parent == here:
                return False
            here = parent
    if code == 0:
        if out.strip() == b'true':
            return True
        raise SprawlError('root is inside a .git directory or a bare repository')
    if 'not a git repository' in err.lower():
        if os.path.exists(os.path.join(root, '.git')):
            raise SprawlError('root has a .git entry that git cannot read: %s' % err)
        return False
    raise SprawlError('git failed: %s' % (err or 'exit %d' % code))


def git_list(root, *args):
    code, out, err = run_git(root, 'ls-files', '-z', *args)
    if code != 0:
        raise SprawlError('git ls-files failed: %s' % (err or 'exit %d' % code))
    return [p.decode('utf-8', 'surrogateescape') for p in out.split(b'\0') if p]


def segments(path):
    return path.rstrip('/').split('/')


def skipped(path, venvs):
    segs = segments(path)
    for seg in segs[:-1] if not path.endswith('/') else segs:
        if seg.lower() in SKIP_DIRS or seg.lower().startswith('.venv'):
            return True
    return any(path.startswith(v) for v in venvs)


def walk_files(root):
    found = []
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d.lower() not in SKIP_DIRS and not d.lower().startswith('.venv')
                         and not os.path.exists(os.path.join(dirpath, d, 'pyvenv.cfg')))
        rel = os.path.relpath(dirpath, root).replace('\\', '/')
        for name in sorted(files):
            found.append(name if rel == '.' else rel + '/' + name)
    return found


def tokens_of(stem):
    stem = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', stem)
    return [t for t in re.split(r'[_\-. ]+', stem.lower()) if t]


def base_of(stem):
    while True:
        m = SIB_RE.match(stem)
        if not m:
            return stem
        stem = m.group(1)


def exempt(path):
    segs = segments(path)
    return any(s.lower() in EXEMPT_DIRS for s in (segs if path.endswith('/') else segs[:-1]))


class Inventory:
    def __init__(self, root, use_git, ignore_files):
        self.root = root
        self.git = use_git
        if use_git:
            tracked = git_list(root)
            untracked = git_list(root, '--others', '--exclude-standard')
            collapsed = git_list(root, '--others', '--exclude-standard', '--directory', '--no-empty-directory')
        else:
            tracked, untracked, collapsed = walk_files(root), [], []
        everything = tracked + untracked
        self.venvs = sorted({p[:-len('pyvenv.cfg')] for p in everything if p.endswith('pyvenv.cfg')
                             and (p == 'pyvenv.cfg' or p[-len('pyvenv.cfg') - 1] == '/')})
        self.venvs = [v for v in self.venvs if v]

        def keep(path):
            if path in ignore_files or skipped(path, self.venvs):
                return False
            full = os.path.join(root, path)
            return os.path.isfile(full) and not os.path.islink(full)  # deleted-but-tracked, links, submodules

        self.tracked = [p for p in tracked if keep(p)]
        self.untracked = [p for p in untracked if keep(p)]
        self.files = self.tracked + self.untracked
        self.untracked_dirs = [d for d in collapsed if d.endswith('/') and not skipped(d, self.venvs)
                               and not os.path.exists(os.path.join(root, d, '.git'))]
        self.state = {p: 'tracked' for p in self.tracked}
        self.state.update({p: 'untracked' for p in self.untracked})


def scratch_dirs(inv):
    """Topmost scratch-like directories that hold something real, with a count of what is in them."""
    groups = {}
    for path in inv.files:
        segs = segments(path)
        for i, seg in enumerate(segs[:-1]):
            if seg.lower() in EXEMPT_DIRS:
                break
            low = seg.lower()
            if low in STRONG_SCRATCH or low in WEAK_SCRATCH:
                groups.setdefault('/'.join(segs[:i + 1]) + '/', []).append(path)
                break
    found = {}
    for d, members in groups.items():
        names = [m.rsplit('/', 1)[-1].lower() for m in members]
        if all(n in PLACEHOLDERS for n in names):
            continue
        weak = segments(d)[-1].lower() in WEAK_SCRATCH
        direct = {m.rsplit('/', 1)[-1].lower() for m in members if m.count('/') == d.count('/')}
        if weak and direct & PACKAGE_MARKERS:
            continue
        tracked = sum(1 for m in members if inv.state[m] == 'tracked')
        untracked = len(members) - tracked
        if not inv.git:
            why = '%d files; no git, so ignore state unknown' % len(members)
        elif tracked and untracked:
            why = '%d tracked, %d untracked and not ignored' % (tracked, untracked)
        elif tracked:
            why = '%d tracked files' % tracked
        else:
            why = '%d untracked files, not ignored' % untracked
        found[d] = (why, set(members))
    return found


def file_findings(inv, files):
    """Name-based classes: throwaway-name, versioned-sibling, report-md, top-level."""
    out = []
    by_dir = {}
    for p in files:
        d, _, name = p.rpartition('/')
        by_dir.setdefault(d, {}).setdefault(name.lower(), name)
    for path in files:
        if exempt(path):
            continue
        d, _, name = path.rpartition('/')
        stem, ext = os.path.splitext(name)
        ext = ext.lower()
        toks = tokens_of(stem)
        at_root = d == ''
        siblings = by_dir[d]
        in_docs = any(s.lower() in DOC_DIRS for s in segments(path)[:-1])

        if ext in BACKUP_EXTS or name.endswith('~'):
            out.append(('throwaway-name', path, 'backup or editor leftover extension'))
        elif COPY_MARK.search(stem):
            out.append(('throwaway-name', path, 'file-manager copy marker in the name'))
        elif len(toks) == 1 and (toks[0] in LONE_STEMS or re.fullmatch(r'(?:untitled|tmp|temp|scratch)\d*', toks[0])):
            out.append(('throwaway-name', path, 'placeholder name'))
        elif len(toks) >= 2 and (toks[-1] in CERTAIN_SUFFIX or re.fullmatch(r'(?:final|fixed)\d+', toks[-1])):
            base = base_of(stem)
            note = ''
            if base != stem and (base + ext).lower() in siblings:
                note = ', next to %s' % siblings[(base + ext).lower()]
            out.append(('throwaway-name', path, "'%s' suffix marks a second copy%s" % (toks[-1], note)))
        elif (len(toks) >= 2 and toks[0] in THROWAWAY_PREFIX and ext in ONE_OFF_EXTS
              and stem.lower() != d.rsplit('/', 1)[-1].lower()):
            out.append(('throwaway-name', path, "'%s' prefix marks a throwaway" % toks[0]))
        else:
            base = base_of(stem)
            if base != stem and (base + ext).lower() in siblings:
                out.append(('versioned-sibling', path,
                            'next to %s; edit that file instead of keeping a variant' % siblings[(base + ext).lower()]))
        if at_root and len(toks) >= 2 and toks[0] in ROOT_PREFIX and ext in SCRIPT_EXTS:
            out.append(('top-level', path, "one-off script ('%s_' prefix) in the repo root" % toks[0]))
        elif at_root and (ext in OUTPUT_EXTS or name.lower() == 'nohup.out' or
                          (ext in OUTPUT_DATA_EXTS and set(toks) & OUTPUT_TOKENS)):
            out.append(('top-level', path, 'captured output in the repo root'))
        if ext in REPORT_EXTS and not in_docs and set(toks) & REPORT_TOKENS:
            out.append(('report-md', path, "report-style note outside a docs folder ('%s')" % sorted(set(toks) & REPORT_TOKENS)[0]))
    flagged = {p for _, p, _ in out}
    runs = {}
    for path in files:
        d, _, name = path.rpartition('/')
        stem, ext = os.path.splitext(name)
        m = VERSION_RE.match(stem)
        if m and not exempt(path) and path not in flagged and (m.group(1) + ext).lower() not in by_dir[d]:
            runs.setdefault((d, m.group(1).lower(), ext.lower()), []).append((int(m.group(2)), path))
    for (_, base, _), versions in runs.items():
        if len(versions) >= VERSION_RUN:
            versions.sort()
            newest = versions[-1][1].rsplit('/', 1)[-1]
            for _, path in versions[:-1]:
                out.append(('versioned-sibling', path, '%d numbered versions of %s; newest is %s; fold in or delete the rest'
                            % (len(versions), base, newest)))
    return out


def duplicate_findings(inv, files):
    by_size = {}
    for p in files:
        name = p.rsplit('/', 1)[-1].lower()
        if exempt(p) or name in DUP_CONVENTIONAL or os.path.splitext(name)[1] not in DUP_EXTS:
            continue
        try:
            size = os.path.getsize(os.path.join(inv.root, p))
        except OSError:
            continue
        if DUP_MIN <= size <= DUP_MAX:
            by_size.setdefault(size, []).append(p)
    out = []
    for group in by_size.values():
        if len(group) < 2:
            continue
        by_hash = {}
        for p in group:
            h = hashlib.sha256()
            try:
                with open(os.path.join(inv.root, p), 'rb') as handle:
                    for chunk in iter(lambda: handle.read(1 << 20), b''):
                        h.update(chunk)
            except OSError:
                continue
            by_hash.setdefault(h.hexdigest(), []).append(p)
        for same in by_hash.values():
            if len(same) < 2:
                continue
            keep = min(same, key=lambda p: (inv.state[p] != 'tracked', p.count('/'), len(p), p))
            for p in same:
                if p != keep:
                    out.append(('duplicate', p, 'same content as %s' % keep))
    return out


def undecided(path):
    """An untracked file worth a decision: script, text or data, not an image or a standard project file."""
    name = path.rsplit('/', 1)[-1]
    return os.path.splitext(name)[1].lower() in ONE_OFF_EXTS and name.split('.')[0].lower() not in CONVENTIONAL


def find(root, use_git, ignore_files, skip):
    inv = Inventory(root, use_git, ignore_files)
    findings = {}

    def add(cls, path, why):
        if cls not in skip:
            findings.setdefault((cls, path), why)

    scratch = scratch_dirs(inv)
    rolled = set()
    for d, (why, members) in scratch.items():
        add('scratch-dir', d, why)
        rolled |= members
    live = [p for p in inv.files if p not in rolled]
    for cls, path, why in duplicate_findings(inv, live) + file_findings(inv, live):
        add(cls, path, why)
    if use_git:
        covered = {p for (_, p) in findings}
        for d in inv.untracked_dirs:
            if exempt(d) or any(d.startswith(s) for s in scratch):
                continue
            n = sum(1 for p in inv.untracked if p.startswith(d) and undecided(p))
            if n:
                add('untracked', d, '%d script or text files neither tracked nor ignored' % n)
        homes = {}  # (directory, extension) pairs that already hold tracked files
        for p in inv.tracked:
            homes[(p.rpartition('/')[0], os.path.splitext(p)[1].lower())] = True
        for p in inv.untracked:
            if p in rolled or p in covered or exempt(p) or not undecided(p) or any(p.startswith(d) for d in inv.untracked_dirs):
                continue
            if (p.rpartition('/')[0], os.path.splitext(p)[1].lower()) in homes and '/' in p:
                continue  # a new file beside tracked files of its kind is ordinary work in progress
            add('untracked', p, 'neither tracked nor ignored')
    ordered = sorted(findings, key=lambda k: (CLASSES.index(k[0]), k[1]))
    return inv, [(c, p, findings[(c, p)]) for c, p in ordered]


def load_baseline(path):
    try:
        with open(path, encoding='utf-8') as handle:
            data = json.load(handle)
        entries = data['findings']
        return {(e['class'], e['path']) for e in entries}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise SprawlError('cannot read baseline %s: %s' % (path, exc))


def write_baseline(path, findings):
    body = {'tool': 'sprawl', 'version': 1,
            'findings': [{'class': c, 'path': p} for c, p, _ in findings]}
    try:
        with open(path, 'w', encoding='utf-8', newline='\n') as handle:
            json.dump(body, handle, indent=1)
            handle.write('\n')
    except OSError as exc:
        raise SprawlError('cannot write baseline %s: %s' % (path, exc))


def tally(findings):
    counts = {}
    for c, _, _ in findings:
        counts[c] = counts.get(c, 0) + 1
    return ', '.join('%s %d' % (c, counts[c]) for c in CLASSES if c in counts)


def main(argv=None):
    ap = Parser(description='Read-only sprawl inventory of a repository.')
    ap.add_argument('--root', default='.', help='repository or folder to inspect (default: current directory)')
    ap.add_argument('--baseline', help='JSON file of accepted findings; only findings not in it fail')
    ap.add_argument('--write-baseline', dest='write_baseline', help='record current findings to this file and exit 0')
    ap.add_argument('--skip', default='', help='comma-separated classes to leave out: ' + ', '.join(CLASSES))
    ap.add_argument('--json', action='store_true', help='print one JSON line of results before the verdict line')
    args = ap.parse_args(argv)
    skip = {s.strip() for s in args.skip.split(',') if s.strip()}
    if skip - set(CLASSES):
        raise SprawlError('unknown class in --skip: %s' % ', '.join(sorted(skip - set(CLASSES))))
    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        raise SprawlError('root is not a directory: %s' % root)
    baseline = load_baseline(args.baseline) if args.baseline else None
    ignore = set()
    for given in (args.baseline, args.write_baseline):
        if given:
            full = os.path.abspath(given)
            if full.startswith(root + os.sep):
                ignore.add(os.path.relpath(full, root).replace('\\', '/'))

    use_git = inside_git(root)
    inv, findings = find(root, use_git, ignore, skip)
    if use_git:
        print('info: git, %d files (%d tracked, %d untracked and not ignored)' %
              (len(inv.files), len(inv.tracked), len(inv.untracked)))
    else:
        print('info: no git, %d files' % len(inv.files))
        print('info: not a git repository; untracked and ignore checks skipped')

    if args.write_baseline:
        write_baseline(args.write_baseline, findings)
        print('PASS sprawl: baseline of %d findings written to %s' % (len(findings), args.write_baseline))
        return 0

    current = {(c, p) for c, p, _ in findings}
    shown = [f for f in findings if baseline is None or (f[0], f[1]) not in baseline]
    gone = sorted(baseline - current) if baseline is not None else []
    for c, p, why in shown:
        print('%s: %s (%s)' % (c, p, why))
    if args.json:
        print(json.dumps({'root': root, 'git': use_git, 'files': len(inv.files),
                          'findings': [{'class': c, 'path': p, 'reason': w} for c, p, w in shown],
                          'baselined': len(findings) - len(shown),
                          'gone': [{'class': c, 'path': p} for c, p in gone]}, sort_keys=True))
    if baseline is None:
        verdict = '%d findings (%s)' % (len(shown), tally(shown)) if shown else 'no findings in %d files' % len(inv.files)
    else:
        extra = '%d baselined, %d baseline entries gone%s' % (
            len(findings) - len(shown), len(gone), '; refresh with --write-baseline' if gone else '')
        verdict = ('%d new findings (%s); %s' % (len(shown), tally(shown), extra)) if shown else \
            'no new findings; %s' % extra
    if shown:
        print('FAIL sprawl: ' + verdict)
        return 1
    print('PASS sprawl: ' + verdict)
    return 0


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    try:
        code = main()
    except SprawlError as exc:
        print('ERROR sprawl: %s' % exc)
        code = 2
    except Exception as exc:  # a crash must never read as a pass
        print('ERROR sprawl: unexpected %s: %s' % (type(exc).__name__, exc))
        code = 2
    sys.exit(code)
