#!/usr/bin/env python3
"""Runs the repo's tests with Python unittest.

Usage: python scripts/check_tests.py [--tests-dir <dir>]
"""
import argparse
import os
import re
import subprocess
import sys

DEFAULT_TESTS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tests'))
TIMEOUT = 600


def main():
    ap = argparse.ArgumentParser(description='Run the unittest suite.')
    ap.add_argument('--tests-dir', default=DEFAULT_TESTS)
    tests = os.path.abspath(ap.parse_args().tests_dir)
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(errors='replace')
    if not os.path.isdir(tests):
        print('ERROR tests directory not found: %s' % tests)
        sys.exit(2)

    env = dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONUTF8='1')
    p = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', tests, '-p', 'test_*.py'],
                       cwd=os.path.dirname(tests), env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, timeout=TIMEOUT)
    text = p.stdout.decode('utf-8', 'replace')
    print(text, end='' if text.endswith('\n') or not text else '\n')
    ran = re.search(r'^Ran (\d+) tests?', text, re.M)
    if p.returncode == 0 and ran and int(ran.group(1)) > 0:
        print('PASS tests: unittest %s ran' % ran.group(1))
    elif p.returncode == 1 and ran:
        print('FAIL tests: unittest failed')
        sys.exit(1)
    else:
        print('ERROR unittest exited %d without a result (no tests found, or the runner crashed)' % p.returncode)
        sys.exit(2)


if __name__ == '__main__':
    main()
