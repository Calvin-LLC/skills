#!/usr/bin/env python3
"""Runs every scripts/check_*.py and reports one verdict per check.

A check's last stdout line is its verdict:
  exit 0, last line `PASS ...`   -> PASS
  exit 0, last line `SKIP ...`    -> SKIP (the reason is printed)
  exit 1, last line `FAIL ...`    -> FAIL
  anything else                   -> ERROR (crash, other exit code, no verdict line)
ERROR means the check said nothing about what it guards; it fails the run like FAIL.

Usage: python scripts/check.py [name]      name is the part after check_, e.g. skills
"""
import argparse
import glob
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TIMEOUT = 900


def classify(code, out, err):
    lines = [l for l in out.splitlines() if l.strip()]
    last = lines[-1].strip() if lines else ''
    if 'Traceback (most recent call last)' in err and code != 0:
        tail = [l for l in err.splitlines() if l.strip()]
        return 'ERROR', 'check crashed: ' + (tail[-1].strip() if tail else 'traceback')
    if code == 0 and last.startswith('PASS '):
        return 'PASS', last[5:].strip()
    if code == 0 and last.startswith('SKIP '):
        return 'SKIP', last[5:].strip()
    if code == 1 and last.startswith('FAIL '):
        return 'FAIL', last[5:].strip()
    if code == 0:
        return 'ERROR', 'exit 0 but %s' % ('last line is not a verdict: ' + last if last else 'no output')
    tail = [l for l in err.splitlines() if l.strip()]
    why = tail[-1].strip() if tail else (last or 'no output')
    return 'ERROR', 'exit %d: %s' % (code, why)


def run_check(path, cwd):
    # Run from a commit hook, git's own variables would point every git call a check makes,
    # temp repos in tests included, at the repository being committed.
    env = {k: v for k, v in os.environ.items() if k not in ('GIT_DIR', 'GIT_INDEX_FILE', 'GIT_WORK_TREE', 'GIT_PREFIX')}
    env.update(PYTHONIOENCODING='utf-8', PYTHONUTF8='1')
    try:
        p = subprocess.run([sys.executable, path], cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        return 'ERROR', 'timed out after %ds' % TIMEOUT, ''
    out = p.stdout.decode('utf-8', 'replace')
    err = p.stderr.decode('utf-8', 'replace')
    verdict, detail = classify(p.returncode, out, err)
    return verdict, detail, out + err


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('name', nargs='?', help='run only scripts/check_<name>.py')
    ap.add_argument('--scripts-dir', default=HERE, help='directory holding check_*.py (default: this one)')
    ap.add_argument('--cwd', default=None, help='working directory for the checks (default: repo root)')
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(errors='replace')

    scripts_dir = os.path.abspath(args.scripts_dir)
    cwd = os.path.abspath(args.cwd) if args.cwd else os.path.dirname(HERE)
    paths = sorted(glob.glob(os.path.join(scripts_dir, 'check_*.py')))
    names = {os.path.basename(p)[len('check_'):-len('.py')]: p for p in paths}
    if args.name:
        want = args.name[len('check_'):] if args.name.startswith('check_') else args.name
        want = want[:-3] if want.endswith('.py') else want
        if want not in names:
            print('ERROR  no check named %r; have: %s' % (args.name, ', '.join(sorted(names)) or 'none'))
            return 2
        names = {want: names[want]}
    if not names:
        print('ERROR  no check_*.py in %s' % scripts_dir)
        return 2

    counts = {'PASS': 0, 'FAIL': 0, 'ERROR': 0, 'SKIP': 0}
    for name in sorted(names):
        verdict, detail, output = run_check(names[name], cwd)
        counts[verdict] += 1
        print('%-5s  %s  %s' % (verdict, name, detail))
        if verdict in ('FAIL', 'ERROR'):
            for line in output.splitlines():
                print('       | ' + line)
    print('%d checks: %d pass, %d fail, %d error, %d skip' % (
        len(names), counts['PASS'], counts['FAIL'], counts['ERROR'], counts['SKIP']))
    return 1 if counts['FAIL'] or counts['ERROR'] else 0


if __name__ == '__main__':
    sys.exit(main())
