# Installing the sprawl gate

`scripts/sprawl.py` is one file with no dependencies. Copy it to the target repo's tooling folder (for example `tools/` or `scripts/`) and commit it with its baseline.

## Baseline

```
python tools/sprawl.py --write-baseline .sprawl-baseline.json
python tools/sprawl.py --baseline .sprawl-baseline.json
```

The baseline lists findings by class and path. Only findings missing from it fail. The verdict also counts baseline entries that no longer exist; when that number is above zero, regenerate the baseline in a cleanup commit and check that the diff only removes lines. The baseline file is never reported as a finding.

## Why the hook skips `untracked`

A hook sees the working tree, and files the operator is still writing are untracked. Failing every commit for them teaches people to bypass the hook. Scratch folders and throwaway names still fail, tracked or not. CI runs on a clean checkout, so it keeps all classes. Agents run the full check, untracked included, before their final reply.

## Wiring, by what the repo already has

- A runner that executes every `check_*.py` in a folder: save the script as `sprawl.py` beside them and add `check_sprawl.py`:
  ```python
  import os, subprocess, sys
  here = os.path.dirname(os.path.abspath(__file__))
  root = os.path.dirname(here)
  sys.exit(subprocess.call([sys.executable, os.path.join(here, 'sprawl.py'), '--root', root,
                            '--baseline', os.path.join(root, '.sprawl-baseline.json'), '--skip', 'untracked']))
  ```
- `package.json`: `"check:sprawl": "python tools/sprawl.py --baseline .sprawl-baseline.json --skip untracked"`, and add it to the existing `check` or `test` script.
- `Makefile` or task runner: a `sprawl` target running the same command, added to the default check target.
- A hooks folder: in the existing pre-commit script add `python tools/sprawl.py --baseline .sprawl-baseline.json --skip untracked || exit 1`. With the pre-commit framework:
  ```yaml
  - repo: local
    hooks:
      - id: sprawl
        name: sprawl
        entry: python tools/sprawl.py --baseline .sprawl-baseline.json --skip untracked
        language: system
        pass_filenames: false
        always_run: true
  ```
- CI: one step after checkout, `python tools/sprawl.py --baseline .sprawl-baseline.json`.

On Windows use `python`; on POSIX use `python3` when `python` is absent. The script needs Python 3.8 or newer and git on the path for git repos.

## Reach

Each pattern is anchored so normal source stays quiet:

- Name suffixes (`_final`, `_fixed`, `.bak`) count only on the last name part, so `final_report.py` passes.
- `_v2`, `_copy` and similar fire only beside the unsuffixed file, or as a run of three numbered versions with no base file. Two schema generations (`schema_v1.json`, `schema_v2.json`) pass.
- `probe_*` and `tmp_*` prefixes fire only on script, text and data files, not compiled source or a folder named for the file.
- `check_*` and `fix_*` fire only in the repo root; the same name inside a scripts folder passes.
- `out`, `output`, `logs`, `old` and `backup` folders pass when they hold only `.gitkeep`, a readme or `.gitignore`, or are a package (`__init__.py`, `package.json` and similar).
- Duplicates need 64 bytes or more and skip licenses, `__init__.py` and fixture folders.
- `fixtures`, `testdata`, `snapshots`, `migrations` and `versions` folders are skipped for every name check.
- A new untracked file beside tracked files of the same type is ordinary work in progress.

To quiet a legitimate hit, baseline it. If a whole class does not fit the repo, drop it with `--skip <class>`.
