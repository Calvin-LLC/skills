# Splitting, squashing, and undoing a push

Read for the case you are in: a large dirty tree to split into commits, local commits to re-group, a squash before a push, or a push that has to be undone.

## Split a tree that spans sessions

When the dirty tree holds hundreds of paths from several sessions, classify every path into an outcome group (moved skills, merged sources, dead trees, docs, tooling) before staging anything. A small script over `git status --porcelain` that prints the group per path proves the groups cover the tree; a path that fits no group means the group list is incomplete, not that the path is unreviewable.

- Clear a stale index first: `git reset -q` empties it without touching the worktree, so a previous session's staged blob cannot ride into your first commit.
- Stage one group at a time with `git add -A -- <paths>`, never `git add -A` at the root.
- A rename's deletion and addition must land in the same commit. Classifying by path prefix splits `old/name` from `new/name` and leaves the tree missing that file for one commit; match on the module or skill name, not on the root.
- Prove the split: after the last commit `git status --porcelain` is empty and the sum of the group sizes equals the original path count. A remainder is an unclassified path.

## Re-squash local commits

When the user finds the local commits too many:

1. Park the old tip: `git branch backup/pre-squash-<stamp> HEAD`.
2. When the new commits fall on boundaries of the existing history, build them from existing trees with `git commit-tree` (step 3 of the next section). Otherwise `git reset -q --soft <base>` and `git reset -q` so the whole range returns to the worktree, classify every path with the same script as above, and commit group by group; print the group counts in a dry run first and apply with a flag.
3. Paths the user owns (their dirty files, generated binaries, unrelated untracked probes) go in a `left` group that is never staged; before each commit assert the staged name list contains none of them.
4. Diff the new tip against the backup for the paths you committed.

## Squash before push

When the user asks to squash and push ("don't spam commits"), finish with the fewest commits that each name one outcome: ONE when the work is a single outcome, two only when new tooling is truly separable. Never one commit per step.

Build the final commit set before the FIRST push. Every fix found while testing folds into that set locally (amend or rebuild it); pushing a fix commit and collapsing it afterwards makes the user watch a force-push that was avoidable.

1. `git fetch`, then `git merge-base --is-ancestor origin/main HEAD`. True means a plain fast-forward push; no force. Only when commits are ALREADY on the remote and the user asks to collapse them, rewrite and push with `--force-with-lease=main:<sha you just read>` after the tree-equality proof in step 4; the order is: tree check, then one pinned force, then compare `origin/main` with `HEAD`. Tell teammates who pulled the old commits to run `git fetch`, then `git reset --hard origin/main`.
2. Finish edits, docs, and gates first. Commit everything so the final tree is a real object, and note the old head sha (the reflog keeps it; no file copies).
3. Build the squash from existing tree objects, not by re-staging. Capture each commit id in a variable: POSIX `c1=$(git commit-tree <work-tree> -p origin/main -m "...")`; Windows (PowerShell) `$c1 = git commit-tree <work-tree> -p origin/main -m "..."`. Then `c2` the same way with `<final-tree> -p $c1`, and `git reset -q --soft $c2`. Rebuilding with `reset --soft origin/main` + `reset` + a selective `git add` silently drops files (edits and deletions outside the listed paths); selective adds classify a tree, they do not reproduce one.
4. Prove it: `git rev-parse HEAD^{tree}` equals the pre-squash tree, `git status --porcelain` is empty, and `git diff --name-only origin/main HEAD` holds no `.env`, `secrets/`, `data/`, credentials, or backup path.
5. `git push origin HEAD:main`, then `git fetch` and compare `origin/main` with `HEAD`.

The user's "push" is the authorization; still read the workflows first (SKILL.md, Push).

## Undo a push the user did not authorise

Revert the remote without destroying the work:

```bash
git branch local-work-<stamp> HEAD        # park the commits first
git reset --hard <last-known-good-sha>    # move local back
git push --force-with-lease origin <last-known-good-sha>:main
```

Park the branch **before** the reset. `--force-with-lease` refuses when someone else pushed in the meantime, so no third party's commits are clobbered; never plain `--force` here. Then verify all three states agree and report them as three lines: remote, local, and whatever the deploy target is actually running. A revert that leaves the deployed host ahead of the repo has not finished the job.

## Delete a folded feature branch

When a feature branch has been folded into `main`, delete it locally and on the remote only after `git log origin/main..origin/<branch>` is empty and no PR is open.
