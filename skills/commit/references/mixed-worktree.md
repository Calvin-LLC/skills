# Mixed worktrees

Read when a file you must commit also holds hunks that are not yours, or when other uncommitted work stays in the tree after your commit.

## Split by hunk (changes in separate regions)

When a file mixes two changes whose hunks are cleanly separable (a refactor and a feature in different regions), split by hunk instead of rebuilding blobs:

1. Write `git diff -U0 --output=<path> -- <file>` to a native scratch path (`--output` must come before the path, and avoids shell redirection, which re-encodes the diff as UTF-16 in Windows PowerShell 5).
2. Classify each `@@` hunk with a small script (by content markers or old line number) and write one diff per group with the original header. When a group leaves earlier hunks out, rewrite each kept hunk's `+start` (old start plus the net lines the kept hunks before it add): `git apply` places a pure insertion (`-N,0`) by its new-side line, so a stale `+start` lands the lines in the wrong place without an error.
3. `git apply --cached --unidiff-zero <group>.diff`, check `git diff --cached --stat` shows only that unit, and commit that group. Repeat for the next group.
4. Verify the remaining worktree diff still holds exactly the other group's hunks.

`-U0` matters: hunks with context lines overlap and refuse to apply alone.

## Rebuild the staged blob (hunks overlap or interleave)

1. `git show HEAD:<path>` for each mixed file. HEAD blobs are LF even when the worktree is CRLF: build from HEAD, not the worktree.
2. Apply your exact edits as string replacements against that content; assert each old string occurs exactly as expected before replacing.
3. `git hash-object -w <rebuilt>` then `git update-index --cacheinfo 100644,<sha>,<path>`.
4. Stage untouched files normally with `git add`.

## Prove the staged tree

Clone HEAD to scratch, apply `git diff --cached`, and run the project's gate there. CI builds the committed tree, and uncommitted or untracked files can make a green worktree a red commit. If the clone lacks the installed project package (`ModuleNotFoundError`), run the suite with the original environment's interpreter and point its module path (`PYTHONPATH`) at the clone's source:

```
POSIX:                PYTHONPATH=<clone>/src python3 -m pytest
Windows (PowerShell): $env:PYTHONPATH='<clone>\src'; python -m pytest
```

## Line-ending churn

A file `git status` marks modified with zero diff hunks is line-ending churn (LF vs CRLF) left by tooling that touched it. It belongs to no feature work; decide whether the normalization rides your commit instead of inheriting it blind.

## A whole-tree add swept in too much

In a tree that also holds scratch, generated settings, or a sibling repo behind a junction, `git add -A` / `git add .` sweeps all of it into a commit whose message describes one change. Check `git status --short` for directories you did not mean to touch before committing. When it happened anyway: `git reset --soft HEAD~1` followed by `git reset` unwinds the commit and returns everything to the worktree with nothing lost. Then add the scratch directory to `.gitignore`, and verify that `git ls-files <dir>` lists nothing, so the directory really was never tracked.

## Generated aggregators

A generated aggregator (an index or manifest rebuilt from the whole tree) embeds rows for other sessions' untracked work in the same change as yours. Check the repo's own precedent first: `git show HEAD:<aggregator>` often already lists paths that are untracked today. Where that precedent exists, commit the regenerated aggregator with your unit; never hand-edit foreign rows out of it. Where it does not, stage only your unit's files and leave the aggregator for whoever lands the rest. Byte-level caches (`*.cache.json`), scratch files, and generated output the repo does not track stay out of the commit: commit the generator and the regenerated artifact, not the cache.
