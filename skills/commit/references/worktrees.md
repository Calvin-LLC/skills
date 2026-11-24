# Side worktrees

Read before removing any worktree, or when commits made on a side branch must move onto the user's branch.

## Removing a side worktree

`git worktree remove --force` and recursive deletes (`rm -rf`, `Remove-Item -Recurse`) follow directory junctions and symlinks, so a junction or symlink inside the worktree that points at untracked data in the primary tree (a build-output or dependency install dir) deletes the REAL contents. Before removing any worktree:

1. List every symlink, junction and other reparse point inside it (search the tree for links), and remove each link itself, never its target:
   POSIX: `unlink <link>` (no trailing slash)
   Windows (PowerShell): `[IO.Directory]::Delete(path)` from a `.ps1` file; test `Attributes -band ReparsePoint` while listing with `Get-ChildItem -Recurse -Force`. `rmdir` through bash `cmd //c` is unreliable.
2. Re-list; only an empty result means the folder is safe to delete.
3. Then `git worktree remove`.

Prefer not creating such junctions: record baseline sizes and outputs in the user's tree before editing instead of building a second copy.

## Replaying side-branch commits onto the user's branch

1. Save `git diff` and the untracked list to a scratch file, then stash only the user's dirty tracked files (`git stash push -- <paths>`).
2. Cherry-pick the commits. Skip any whose patch is already upstream (`git range-diff` or `git cherry` shows it as already applied).
3. Restore the stash. After a folder rename, rewrite the old paths in the saved patch (the `a/` and `b/` prefixes), then `git apply --check` and `git apply`.

A "file location" conflict means upstream added a file under the renamed folder; git already placed it at the new path, so `git add` it.
