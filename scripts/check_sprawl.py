#!/usr/bin/env python3
"""Gate this repo against new file sprawl, using the tidy skill's own script."""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# A hook sees the working tree, where files still being written are untracked.
sys.exit(subprocess.call([
    sys.executable, os.path.join(ROOT, 'skills', 'tidy', 'scripts', 'sprawl.py'),
    '--root', ROOT, '--baseline', os.path.join(ROOT, '.sprawl-baseline.json'), '--skip', 'untracked',
]))
