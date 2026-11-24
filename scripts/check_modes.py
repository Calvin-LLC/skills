#!/usr/bin/env python3
"""Tracked shell scripts keep their executable bit.

Git on Windows cannot see the bit, so a commit made there can drop it silently and the
script then fails with "Permission denied" on POSIX. Covers `*.sh` and extensionless files
that start with a shebang.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    p = subprocess.run(['git', '-C', ROOT, 'ls-files', '-s', '-z'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    if p.returncode != 0:
        print('ERROR modes: git ls-files failed: %s' % p.stderr.decode('utf-8', 'replace').strip())
        return 2
    bad, seen = [], 0
    for entry in p.stdout.decode('utf-8', 'replace').split('\0'):
        if not entry:
            continue
        meta, path = entry.split('\t', 1)
        mode = meta.split()[0]
        name = os.path.basename(path)
        if mode == '120000' or not (name.endswith('.sh') or '.' not in name):
            continue
        try:
            with open(os.path.join(ROOT, path), 'rb') as f:
                shebang = f.read(2) == b'#!'
        except OSError:
            continue
        if not shebang:
            continue
        seen += 1
        if mode != '100755':
            bad.append(path)
    for path in bad:
        print('%s is mode 100644; run: git update-index --chmod=+x "%s"' % (path, path))
    if bad:
        print('FAIL modes: %d of %d shell scripts lost their executable bit' % (len(bad), seen))
        return 1
    if not seen:
        print('ERROR modes: found no shell scripts to check')
        return 2
    print('PASS modes: %d shell scripts are executable' % seen)
    return 0


if __name__ == '__main__':
    sys.exit(main())
