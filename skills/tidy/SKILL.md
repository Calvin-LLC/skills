---
name: tidy
description: Use when asked to organize, debloat, clean up the repo, tidy files, fix sprawl, or decide where a new file goes, and before leaving scripts, output or notes inside a repo. Not code-level dead code (deslop) or README rewrites (readme-clean).
---

# Tidy

Agent sprawl is mostly one-off scripts, captured output and report notes, dropped in scratch-like folders. A cleanup at the end of a turn does not hold, so there are three parts: clean what exists, gate what comes next, place new files right the first time.

## Inventory

Run `scripts/sprawl.py --root <repo>`. It is read-only, stdlib only, and needs no install. It prints one line per finding, `class: path (reason)`, and ends with `PASS`, `FAIL` or `ERROR sprawl: ...` (exit 0, 1, 2). `ERROR` is never a pass. Outside a git repo it says so and skips the untracked checks.

| Class | Fires on |
|---|---|
| `scratch-dir` | `_scratch`, `tmp`, `out`, `output`, `logs`, `.audit`, `.sketch` and kin that git tracks or does not ignore |
| `throwaway-name` | `x_final`, `x_fixed`, `x.bak`, `tmp.py`, `probe_*`, `tmp_*` |
| `versioned-sibling` | `build_v2.py` or `build_copy.py` beside `build.py`; three or more `_vN` versions |
| `duplicate` | byte-identical text or code files |
| `report-md` | `*_REPORT`, `*_SUMMARY`, `ANALYSIS` notes outside a docs folder |
| `top-level` | one-off scripts (`check_*`, `fix_*`) and captured output in the repo root |
| `untracked` | scripts or text that git neither tracks nor ignores |

Vendored trees, virtualenvs, build output, fixtures and anything git ignores are skipped. Details and tuning: `references/gate.md`.

## Part 1: Cleanup

1. Run the inventory. Run `git status` first and note the operator's uncommitted work; untracked is not the same as junk.
2. Group findings by class and folder. Scratch folders and `probe_*` runs are usually one decision each.
3. Prove every delete is safe before proposing it:
   - Search for the name, the stem and the path in code, config, CI, docs and scripts. A hit is a blocker until fixed in the same change.
   - Check history: `git log --follow` for tracked files, modification time for untracked.
   - For a duplicate, confirm which copy the references point to; that one stays.
   - For a version pile, diff the newest against the rest; fold unique content into the live file.
4. Present one plan table: `path | class | evidence | action | risk`. Actions are delete, `git mv <dest>`, ignore, keep. Then stop and wait for approval. Do no partial cleanup first.
5. Act on approved rows only. Use `git mv` and `git rm`, one reviewable commit per class or folder (see the `commit` skill), and fix references in the commit that moves the file.
6. Never delete untracked work without the operator's explicit yes. On a yes, move it to a dated folder in the OS temp directory and give the path; delete it for good only when told.
7. Re-run the inventory and report counts before and after. Dead code inside live files is `deslop`; stale prose is `readme-clean`.

## Part 2: Gate

Cleanup without a gate regrows. Install one in the target repo, built from what it already has.

1. Find the existing runner: a checks directory, `Makefile`, `package.json` scripts, a task file, a pre-commit hook or config, CI workflows. Add to it; do not add a second convention.
2. Copy `scripts/sprawl.py` into the repo's tooling folder. Record today's mess with `--write-baseline` and commit the baseline file with the script.
3. Wire `sprawl.py --baseline <file> --skip untracked` into the local hook and the same command without `--skip` into CI. `references/gate.md` has the snippets.
4. Prove it: in a temp copy of the repo, add one throwaway file and confirm `FAIL` names it. Then confirm `PASS` on the real tree.
5. Pay down later. When a run reports baseline entries gone, regenerate the baseline in a cleanup commit; its diff must only remove lines. Never regenerate to silence a new finding.

## Part 3: Where things go while working

- One-off scripts, probes, captured output and test dumps go in the OS temp directory (`tempfile.gettempdir()`), or in one scratch folder that `.gitignore` lists. Write there from the first command, so nothing needs cleaning later.
- Edit the existing file. Do not write a sibling named `_v2`, `_fixed`, `_final` or `_copy`; git keeps the old version.
- The summary goes in the reply. Create a report, notes or handoff markdown file only when asked. Durable facts go into the doc that already owns the topic, in the repo's docs location.
- Name a file by what it is, not by the attempt that produced it.
- Before creating any file in the repo, name who runs or reads it next week. If nobody does, it belongs in temp.
- Before the final reply, run the inventory if the repo has it. A new finding is yours: remove your own scratch; leave other people's and ask.
