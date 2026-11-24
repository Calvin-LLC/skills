#!/usr/bin/env python3
"""Where a repository's change effort goes, from git history alone.

Prints two rankings for a recent window: files by how often they changed (with churn and
current size beside it), and pairs of files that keep changing in the same commit. Both are
language-agnostic. They say where to look, not what is wrong: read the code before proposing
anything.

Usage: python hotspots.py [--root DIR] [--days 180] [--top 15] [--min-shared 3]
                          [--max-files 40] [--json]
Read-only. Stdlib only. Last line is `OK hotspots: ...` (exit 0) or `ERROR hotspots: ...`
(exit 2); an ERROR is never a result.
"""
import argparse
import collections
import itertools
import json
import os
import re
import subprocess
import sys

HOOK_ENV = ('GIT_DIR', 'GIT_INDEX_FILE', 'GIT_WORK_TREE', 'GIT_PREFIX')
# Regenerated, vendored or bulk-edited content inflates churn without being a design signal.
SKIP_DIRS = {'node_modules', 'vendor', 'vendors', 'third_party', 'thirdparty', 'external', 'dist', 'build', 'out',
             'target', '.git', '__pycache__', '.venv', 'venv', 'site-packages', 'generated', 'gen', 'migrations',
             'snapshots', '__snapshots__', 'fixtures', 'testdata'}
SKIP_NAMES = re.compile(r'(^|/)(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|bun\.lockb?|composer\.lock|cargo\.lock|'
                        r'poetry\.lock|uv\.lock|go\.sum|gemfile\.lock|pipfile\.lock|.*\.min\.(js|css)|.*\.map|'
                        r'.*\.(pb\.go|g\.dart|designer\.cs))$', re.I)
TEXT_SKIP = re.compile(r'\.(md|mdx|txt|rst|adoc|csv|tsv|log|svg|lock)$', re.I)
TEST_PART = re.compile(r'(^|[/_.\-])(tests?|spec|specs|__tests__|e2e)([/_.\-]|$)', re.I)
RENAME = re.compile(r'\{([^{}]*) => ([^{}]*)\}')


class HotspotError(Exception):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise HotspotError('bad arguments: ' + message)


def git(root, *args):
    env = {k: v for k, v in os.environ.items() if k not in HOOK_ENV}
    try:
        p = subprocess.run(('git', '-C', root, '-c', 'core.quotepath=off') + args, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, stdin=subprocess.DEVNULL, env=env)
    except OSError as exc:
        raise HotspotError('cannot run git: %s' % exc)
    if p.returncode != 0:
        raise HotspotError('git %s failed: %s' % (args[0], p.stderr.decode('utf-8', 'replace').strip()[:200]))
    return p.stdout.decode('utf-8', 'replace')


def rename_sides(path):
    """`src/{old => new}/f.py` and `old.py => new.py` as (path before, path after); (None, path) otherwise."""
    if ' => ' not in path:
        return None, path
    if RENAME.search(path):
        old = RENAME.sub(lambda m: m.group(1), path)
        new = RENAME.sub(lambda m: m.group(2), path)
    else:
        old, new = path.split(' => ', 1)
    return old.replace('//', '/'), new.replace('//', '/')


def skipped(path):
    parts = path.lower().split('/')
    return any(p in SKIP_DIRS for p in parts[:-1]) or bool(SKIP_NAMES.search(path)) or bool(TEXT_SKIP.search(path))


def is_test(path):
    return bool(TEST_PART.search(path))


def stem(path):
    name = path.rsplit('/', 1)[-1].lower()
    name = name.split('.', 1)[0]
    return re.sub(r'(^test_|_test$|_spec$|\.test$|\.spec$|test$)', '', name)


def read_history(root, days):
    out = git(root, 'log', '--since=%d.days' % days, '--no-merges', '-M', '--numstat', '--format=@@%H')
    commits, current = [], None
    renamed = {}  # the log runs newest first, so a rename is seen before the older commits that used the old name
    for line in out.splitlines():
        if line.startswith('@@'):
            current = []
            commits.append(current)
        elif line.strip() and current is not None:
            parts = line.split('\t')
            if len(parts) != 3:
                continue
            old, path = rename_sides(parts[2])
            path = renamed.get(path, path)
            if old:
                renamed[old] = path
            if parts[0] == '-':  # a binary file
                continue
            changed = int(parts[0]) + int(parts[1])
            if old and not changed:  # a move with no edit is not work on the file
                continue
            current.append((path, changed))
    return commits


def line_count(root, path):
    try:
        with open(os.path.join(root, path), 'rb') as handle:
            return handle.read().count(b'\n')
    except OSError:
        return 0


def analyse(root, days, max_files, min_shared):
    live = set(p for p in git(root, 'ls-files').splitlines() if p)
    commits = read_history(root, days)
    touches, churn = collections.Counter(), collections.Counter()
    pairs = collections.Counter()
    bulk = 0
    for files in commits:
        files = [(p, n) for p, n in files if p in live and not skipped(p)]
        # A formatter run, codemod or mass move touches everything and couples every pair it touches.
        if len(files) > max_files:
            bulk += 1
            continue
        for path, changed in files:
            touches[path] += 1
            churn[path] += changed
        names = sorted({p for p, _ in files})
        for a, b in itertools.combinations(names, 2):
            pairs[(a, b)] += 1
    ranked = []
    for path, count in touches.items():
        lines = line_count(root, path)
        ranked.append({'path': path, 'touches': count, 'churn': churn[path], 'lines': lines, 'test': is_test(path),
                       'churn_per_line': round(churn[path] / float(lines), 2) if lines else None})
    # Frequency first, size second: how often it is worked on, then how much there is to hold in mind.
    ranked.sort(key=lambda r: (-r['touches'], -r['lines'], r['path']))
    coupled = []
    for (a, b), shared in pairs.items():
        if shared < min_shared:
            continue
        expected = None
        if is_test(a) != is_test(b) and stem(a) == stem(b):
            expected = 'test with its subject'
        elif os.path.splitext(a)[0] == os.path.splitext(b)[0]:
            expected = 'header with its source'
        coupled.append({'a': a, 'b': b, 'shared': shared, 'a_rate': round(shared / float(touches[a]), 2),
                        'b_rate': round(shared / float(touches[b]), 2),
                        'cross_dir': os.path.dirname(a) != os.path.dirname(b), 'expected': expected})
    coupled.sort(key=lambda c: (c['expected'] is not None, not c['cross_dir'], -c['shared'],
                                -min(c['a_rate'], c['b_rate']), c['a'], c['b']))
    return {'days': days, 'commits': len(commits), 'bulk_skipped': bulk, 'files': ranked, 'pairs': coupled}


def render(result, top):
    lines = ['window: %d days; %d commits read, %d skipped as bulk; %d files ranked'
             % (result['days'], result['commits'], result['bulk_skipped'], len(result['files']))]
    if result['commits'] - result['bulk_skipped'] < 20:
        lines.append('note: fewer than 20 usable commits. Rates from this little history are anecdotes; widen --days.')
    lines += ['', 'most-changed files (commits touching | lines changed | lines now | changed per line)']
    for r in result['files'][:top]:
        lines.append('  %3d | %6d | %5d | %5s  %s%s' % (r['touches'], r['churn'], r['lines'],
                     '-' if r['churn_per_line'] is None else r['churn_per_line'], r['path'], '  [test]' if r['test'] else ''))
    shown = [c for c in result['pairs'] if not c['expected']][:top]
    lines += ['', 'files that change together (shared commits | share of A | share of B)']
    for c in shown:
        lines.append('  %3d | %3d%% | %3d%%  %s  <->  %s%s' % (c['shared'], round(c['a_rate'] * 100), round(c['b_rate'] * 100),
                     c['a'], c['b'], '' if c['cross_dir'] else '  [same folder]'))
    if not shown:
        lines.append('  none above the shared-commit floor')
    hidden = sum(1 for c in result['pairs'] if c['expected'])
    if hidden:
        lines.append('  (%d expected pairs not shown: a test with its subject, a header with its source)' % hidden)
    return lines


def main(argv=None):
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        ap = Parser(description=__doc__.split('\n')[0])
        ap.add_argument('--root', default='.')
        ap.add_argument('--days', type=int, default=180)
        ap.add_argument('--top', type=int, default=15)
        ap.add_argument('--min-shared', type=int, default=3)
        ap.add_argument('--max-files', type=int, default=40)
        ap.add_argument('--json', action='store_true')
        args = ap.parse_args(argv)
        root = os.path.abspath(args.root)
        if not os.path.isdir(root):
            raise HotspotError('root is not a directory: %s' % root)
        root = git(root, 'rev-parse', '--show-toplevel').strip() or root
        result = analyse(root, args.days, args.max_files, args.min_shared)
        if not result['commits']:
            raise HotspotError('no commits in the last %d days; widen --days' % args.days)
        if args.json:
            print(json.dumps(result))
        else:
            print('\n'.join(render(result, args.top)))
        print('OK hotspots: %d files, %d coupled pairs, %d commits' % (
            len(result['files']), sum(1 for c in result['pairs'] if not c['expected']), result['commits'] - result['bulk_skipped']))
        return 0
    except HotspotError as exc:
        print('ERROR hotspots: %s' % exc)
        return 2
    except Exception as exc:  # a crash must not read as an empty, clean result
        print('ERROR hotspots: unexpected %s: %s' % (type(exc).__name__, exc))
        return 2


if __name__ == '__main__':
    sys.exit(main())
