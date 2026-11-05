---
name: commit
description: "Read this skill before making git commits. One major feature per commit on main, 1-2 line overview, no push until proven locally."
---

# Commit

Git is source tracking and a restore point. Work on `main`, in the folder
the user has open. Do not create a feature branch, a pull request, or a
separate `git worktree` for the work itself unless the user named one: a
side worktree hides the changes from the folder the user is watching, and
replaying them later costs conflicts, a stash dance and a second round of
builds. Run `git worktree list` at the start; if the session cwd is a linked
worktree and the repo's primary folder is elsewhere, the primary folder is
where the work goes.

A read-only baseline worktree (pre-change builds for before/after receipts)
is the one allowed exception, and it is removed per "Removing a side
worktree" below.

## When to commit

One commit is one major feature, one bug fix, or one coherent restore
point. Do not mix unrelated work. Do not sprinkle micro-commits through
an unfinished change. Finish the unit, prove it locally, then commit.

## Checkpoint on order

When the user orders the whole dirty tree committed — a hard stop, a
preservation checkpoint before a restart or deploy window — commit
rather than refuse, but never as one mixed commit: first the verified
unit(s) as normal feature commits, then every remaining path in one
`chore(wip): ...` commit that honestly labels unreviewed parallel
state. Take the checkpoint BEFORE the supervised window starts: the
commits are the restore point the window is survived from.

**Splitting a tree that spans sessions.** When the dirty tree holds hundreds of paths from several
sessions, classify every path into an outcome group (moved skills, merged sources, dead trees, docs,
tooling) before staging anything. A small script over `git status --porcelain` that prints the group
per path proves the groups cover the tree; a path that fits no group means the group list is
incomplete, not that the path is unreviewable.

- Stage one group at a time with `git add -A -- <paths>`, never `git add -A` at the root.
- A rename's deletion and addition must land in the same commit. Classifying by path prefix splits
  `old/name` from `new/name` and leaves the tree missing that file for one commit; match on the
  module or skill name, not on the root.
- Clear a stale index first: `git reset -q` empties it without touching the worktree, so a previous
  session's staged blob cannot ride into your first commit.
- Prove the split: after the last commit `git status --porcelain` is empty and the sum of the group
  sizes equals the original path count. A remainder is an unclassified path.
- Re-squashing local commits the user finds too many: park the old tip first
  (`git branch backup/pre-squash-<stamp> HEAD`), then `git reset -q --soft <base>` and `git reset -q`
  so the whole range returns to the worktree, classify every path with the same script, and commit
  group by group. Paths the user owns (their dirty files, generated binaries, unrelated untracked
  probes) go in a `left` group that is never staged; before each commit assert the staged name list
  contains none of them, and afterwards diff the new tip against the backup for the paths you
  committed. Print the group counts in a dry run first and apply with a flag.

An explicit instruction to make one simple commit of the whole tree ("just make it a simple commit
message") overrides the split above: do it as a single one-line commit, without re-asking, and
afterwards name in the report what unrelated work it swept in so the user can ask for a split.

## Message

`<type>(<scope>): <overview>`

- `type` required: `feat`, `fix`, `docs`, `refactor`, `chore`, `test`, `perf`.
- `scope` optional: short noun (`api`, `ui`, `nav`).
- Overview required: one line, imperative, <= 72 chars, no trailing period.
  A second line is allowed when the first cannot name the restore point.
- No paragraph body. No bullet list. No "this commit does X, Y, and Z"
  recap. A body exists only when a later restore would be unsafe without
  one extra fact (migration, data loss, required env). That is rare.
- No breaking-change markers, footers, or `Signed-off-by`.
- Apply **unslop**. No decorative emoji. The message is a real overview of
  what landed, not a changelog of files touched.
- Assert only what the diff proves. The overview names what landed, not
  what the work claims to achieve — a fact the committed files do not
  contain is a lie baked into the restore point.

Good: `feat(nav): load spot HTML from the summary endpoint`
Bad: a paragraph of what you thought about, or a list of every file.

## Push

Commit only. Do not push until the change has been tested extensively
locally: run the project's real tests and exercise the feature path.
Never push untested work. Force-push and the other irreversible writes
pause per the Pause section of `AGENTS.md`; push when the user asked to
ship, or when leaving the work would lose the restore point.

### Check what a push *does* before pushing

`git push` is not always a restore-point operation. Read
`.github/workflows/*.yml` (or the equivalent) for a trigger on the target
branch and determine whether a push deploys, publishes, or otherwise runs
against production. If it does:

- **A push is a one-way door, and the user's instruction to commit is not
  an instruction to ship.** Commit is a local restore point; pushing is a
deploy. Treat them as separate decisions unless the user said "push".
- **State the coupling back before pushing.** One line: "this branch
auto-deploys on push, so committing is local but pushing is live — say the
word." Silence here is how an unvalidated commit reaches production.
- A red gate job on the same branch is not a safety mechanism to rely on.
It is incidental, and it disappears the moment someone fixes the unrelated
job it was failing on.
- When a pipeline already auto-deploys on push, propose weakening that to an
explicit dispatch-triggered deploy. Push-triggered deploys make every push
irreversible and train the user to fear committing.

### Undoing a push the user did not authorise

Commit locally, push only on request. When a push happened anyway, revert
the remote without destroying the work:

```bash
git branch local-work-<stamp> HEAD        # park the commits first
git reset --hard <last-known-good-sha>    # move local back
git push --force-with-lease origin <last-known-good-sha>:main
```

Park the branch **before** the reset. `--force-with-lease` refuses when
someone else pushed in the meantime, so no third party's commits are
clobbered; never plain `--force` here. Then verify all three states agree
and report them as three lines — remote, local, and whatever the deploy
target is actually running. A revert that leaves the deployed host ahead of
the repo has not finished the job.

## Squash before push

When the user asks to squash and push ("don't spam commits"), finish with the fewest
commits that each name one outcome: ONE when the work is a single outcome, two only when
new tooling is truly separable. Never one commit per step.

Build the final commit set before the FIRST push. Every fix found while testing folds into
that set locally (amend or rebuild it); pushing a fix commit and collapsing it afterwards
makes the user watch a force-push for something that was avoidable.

1. `git fetch`, then `git merge-base --is-ancestor origin/main HEAD`. True means a plain
   fast-forward push; no force. Only when commits are ALREADY on the remote and the user
   asks to collapse them, rewrite and push with `--force-with-lease=main:<sha you just
   read>` after the tree-equality proof in step 4; the order is: tree check, then one
   pinned force, then compare `origin/main` with `HEAD`. Tell teammates who pulled the
   old commits to `git fetch && git reset --hard origin/main`.
2. Finish edits, docs, and gates first. Commit everything so the final tree is a real
   object, and note the old head sha (the reflog keeps it; no file copies).
3. Build the squash from existing tree objects, not by re-staging:
   `c1=$(git commit-tree <work-tree> -p origin/main -m "...")`,
   `c2=$(git commit-tree <final-tree> -p $c1 -m "...")`, `git reset -q --soft $c2`.
   Rebuilding with `reset --soft origin/main` + `reset` + a selective `git add` silently
   drops files (edits and deletions outside the listed paths); selective adds classify a
   tree, they do not reproduce one.
4. Prove it: `git rev-parse HEAD^{tree}` equals the pre-squash tree, `git status --porcelain`
   is empty, and `git diff --name-only origin/main HEAD` holds no `.env`, `secrets/`,
   `data/`, credentials, or backup path.
5. `git push origin HEAD:main`, then `git fetch` and compare `origin/main` with `HEAD`.

The user's "push" is the authorization; still read the workflows first (see above).

## Publishing data to a shared repo

A file that carries credentials, sessions, or a database is a one-way door even in a
private repo. Check `gh repo view --json isPrivate` and list readers with
`gh api repos/{owner}/{repo}/collaborators --jq '.[].login'`, state the exposure plainly
(who can read it, and whether the sealing key is itself committed), and take one explicit
choice from the user. That choice covers the run; do not re-ask.

- **Put it where the team will look.** "Share it on GitHub" means a tracked file in the
  repo (for example `shared/<name>.db.gz`), not a release asset: a release is invisible on
  the Code tab and adds a second path to learn. Pick the obvious location first and give
  the trade-off (history growth) in one line; do not take the harder route unasked.
- **One command each way.** A publisher (`make share`: snapshot into the tracked path,
  refuse a public repo, no commit) and a loader (`make load-shared`: check the sealing key
  matches and write nothing on a mismatch, replace the data, then fix whatever the data
  does not carry, such as the sign-in password). Hand the user the three or four exact
  lines to send the team, and say plainly if `make` or any tool is new or pre-existing.
- **Test the teammate's whole flow before any push.** Run the exact commands from a fresh
  `git clone` in an isolated compose project (ports, project name and volume all
  separate), ending in a real login over HTTP. A loader that only copies the file passes
  every file-level check and still leaves a desk nobody can sign in to; pushing first and
  testing after is the failure the user called out.
- **The test must be exactly what teammates run.** Do not strip or disable data in the
  scratch copy (VPN login, stored sessions, boot restore): the user wants the real login
  and a real restore exercised, and a sanitised run proves a different flow. In a test
  environment the user has declared fake, real side effects are authorised; state the
  consequence (two desks on one VPN login) in the report instead of preventing it. Only
  deviate for host limits (ports, project name), and name each deviation.
- Host limits are ports and the compose project name only. If `make up` dies on a PyPI
  lookup, do not write "no DNS on this host": query each nameserver in a bridge container's
  `/etc/resolv.conf` with a 3 s timeout and report the per-server timings (the cause seen
  was a host VPN leaving only one of three copied resolvers answering, which makes lookups
  flaky rather than dead; the same build passed with the VPN off). Prebuild with
  `docker build --network host -t <image tag compose uses> .` then `docker compose up -d
  --no-build` only as a named workaround, and say the user's plain `make up` was not proven
  on that run. Never call the machine "another host": it is the project's real environment.
  A tracked `docker-compose.override.yml` bind-mounts source into the container; do not
  overwrite it in the clone. Wait on `healthy`, the tunnel row and the run state, never on
  a fixed sleep.
- The pass criteria are every supervised program `RUNNING` (`supervisorctl status`, not a
  hand-picked subset), zero tracebacks in the log, and the boot-restore run reaching a
  terminal state. Run the fresh clone more than once after a change that touches boot
  order or database writers: first-boot races do not show on a warm desk and one pass does
  not clear them.
- Tear the scratch project down (containers, volume, network, image tags, clone) and
  confirm the live container is still healthy and its image tag unchanged.
- When a feature branch has been folded into `main`, delete it locally and on the remote
  only after `git log origin/main..origin/<branch>` is empty and no PR is open; if the
  user asked for a recommended step "exactly", do that step without re-asking.

## Submodules and multi-repo trees

- **Push leaf repos first, then bump and push the parent.** A superproject stores a gitlink SHA; bumping it before the submodule's commit exists upstream points every clone at an object nobody can fetch.
- **Verify each repo against its own remote.** A clean parent says nothing about the submodule: run `git ls-remote origin refs/heads/main` per repo and compare to local `HEAD`. A submodule pointer at the old SHA reads as "clean parent, behind child" and nobody notices until a fresh clone lands on stale code. A dirty submodule and a moved pointer both render as `M <path>` in the parent's status; the parent's `git diff` tells them apart — a `-Subproject commit <sha>` / `+Subproject commit <sha>-dirty` pair is uncommitted work inside the child, not a pointer that moved, and it must be committed and pushed in the child before the parent's "clean" means anything.
- **A submodule checkout is normally detached, so `git push origin main` there sends the stale local `main` branch, not your commit.** `git status -sb` reads `## HEAD (no branch)`. Push the commit itself: `git push <remote> HEAD:main`. A rejection reading `non-fast-forward` while `git rev-list --left-right --count HEAD...origin/main` reports `1 0` is this exact trap — the client is sending a ref that is not HEAD — so check for a detached HEAD before theorizing about the remote's state.
- **The submodule's `origin` is often a local working mirror, not the upstream named in `.gitmodules`.** It refuses pushes to its checked-out branch (`! [remote rejected] HEAD -> main (branch is currently checked out)`), and fast-forwarding that mirror in place is a detour, not the fix. Read `.gitmodules` for the real URL, add it as a named remote, fetch it, confirm the divergence is ahead-only before pushing, then `git push <remote> HEAD:main` and verify with `git ls-remote <remote> refs/heads/main`. Never force.
- **A gitlink whose `.gitmodules` URL is a local absolute path (`C:/Users/...`) is unpushable** — no clone can resolve it. Either give that repo a real remote (push `main`, then point `.gitmodules` at it) or drop the gitlink and vendor the source. A private repo under the owner's own org is a reversible door worth taking without a question; a public one is not.
- **A tracked gitlink with no `.gitmodules` entry breaks every fresh clone** (`fatal: no submodule mapping found in .gitmodules for path ...`). Add the mapping in the same commit that touches submodules, and re-run `git submodule status` afterwards — it should list every path instead of dying.
- **Build output inside a submodule path is not parent cleanliness.** Ignore it in the owning repo (e.g. `panoptes/build/`) rather than committing megabytes of `.dll/.lib/.exp` just to make `git status` quiet.

## Removing a side worktree

`git worktree remove --force` and `rm -rf` follow directory junctions and
symlinks, so a junction inside the worktree that points at untracked data in
the primary tree (a build-output or dependency install dir) deletes the
REAL contents. Before removing any worktree:

1. List reparse points inside it (`Get-ChildItem -Recurse -Force`, test
   `Attributes -band ReparsePoint`) and remove each link itself with
   `[IO.Directory]::Delete(path)` from a `.ps1` file. Deleting the link
   leaves the target alone; `rmdir` through bash `cmd //c` is unreliable.
2. Re-list; only an empty result means the folder is safe to delete.
3. Then `git worktree remove`.

Prefer not creating such junctions: record baseline sizes and outputs in the
user's tree before editing instead of building a second copy.

## Replaying side-branch commits onto the user's branch

Stash only the user's dirty tracked files (`git stash push -- <paths>`) after
saving `git diff` and the untracked list to a scratch file. Cherry-pick the
commits. If the branch had a commit with the same patch already upstream,
skip it (`git range-diff` or `git cherry` shows it as already applied).
After a folder rename, restore the stash by rewriting the old paths in the
saved patch (`sed` on the `a/` and `b/` prefixes), then `git apply --check`
and `git apply`. A "file location" conflict means upstream added a file under
the renamed folder; git already placed it at the new path, so `git add` it.

## Local proof

Proof means fresh binaries, not available ones. Suites are standalone
exes: they execute happily whether or not the code compiles, so a suite
run right after a failed or clipped build reports green over an
uncompileable commit. Capture the build output and require an explicit
success line (`0 Error(s)` or the `-> <target>` line) before running any
test, in the same chain, from binaries that build just produced.

- Never trust a clipped build view (`tail -3`, truncation) as proof —
  failure lines live where the clip cut. Grep the captured output for
  `error` and read the matches; then confirm the success line.
- `grep -c` exits 1 on zero matches, so `grep -c error && run-tests`
  skips the tests exactly when the build is clean. Structure the chain
  so a clean build is the success path (`grep -v`/exit-code check, or
  run steps unconditionally and inspect).
- When grepping log lines, `grep -E 'A|B'` treats `|` as alternation —
  escape it (`A\|B`) or use `grep -F` for literal receipt tokens,
  otherwise one broad pattern matches everything and the count means
  nothing.
- When the build graph is already up to date nothing rebuilds, and a
  green-looking control build over an unchanged tree proves nothing
  fresh. Read the target arrow line and the artifact mtime, and force
  a real build (`/t:Rebuild`, or delete the target's intermediate
  output) whenever the claim is "this tree builds."
- PowerShell edits need a parse check before commit:
  `[System.Management.Automation.Language.Parser]::ParseFile` per changed
  `.ps1`, one invocation per file — an array `-Files` argument arrives as
  one mangled string and a shell loop's path substitution corrupts
  Windows paths, so drive the per-file calls from Python `subprocess`.
  A syntax error in a lab/harness script deploys as a dead harness.

## Steps

1. Infer paths or extra instructions from the prompt.
2. `git status` and `git diff` (limit to specified files).
3. Confirm the staged set is one feature. Split if it isn't.
4. Confirm local proof exists for this unit. If it doesn't, test first.
5. Stage only that unit. Ask if extra files are ambiguous. If the worktree
   carries unrelated uncommitted work in the same files, use the Mixed
   worktrees procedure below — never `git add` a mixed file.
6. `git commit -m "<subject>"`. Add a second `-m` line only for the rare
   restore-safety fact.
7. Do not push from this skill.

## Mixed worktrees

The worktree often carries uncommitted work from other sessions, sometimes
inside the very files you touched. `git add <file>` then commits the foreign
hunks too and deploys unreviewed work. Marker-filtering `git diff` hunks is
NOT safe either: a hunk spanning both changes carries the other change's
context lines into the index silently. Foreign hunks are not always
functional: another session's whole-file formatter reflow or a one-line
default-value tweak makes a file mixed too — review the staged diff
hunk-by-hunk and rebuild whenever any hunk is not yours, cosmetic included.

When a file mixes two changes whose hunks are cleanly separable (a refactor and a
feature in different regions), split by hunk instead of rebuilding blobs: write
`git diff -U0 <file>` to a native scratch path, classify each `@@` hunk with a small
script (by content markers or old line number), write one diff per group with the original
header, then `git apply --cached --unidiff-zero <group>.diff` and commit that group.
Repeat for the next group; `git diff --cached --stat` before each commit must show only
that unit. `-U0` matters: hunks with context lines overlap and refuse to apply alone.
Verify the remaining worktree diff still holds exactly the other group's hunks.

Rebuild the staged blob instead when hunks overlap or interleave:

1. `git show HEAD:<path>` for each mixed file (HEAD blobs are LF even when
   the worktree is CRLF — build from HEAD, not the worktree).
2. Apply your exact edits as string replacements against that content;
   assert each old string occurs exactly as expected before replacing.
3. `git hash-object -w <rebuilt>` then
   `git update-index --cacheinfo 100644,<sha>,<path>`.
4. Stage untouched files normally with `git add`.

Prove the **staged tree**, not the worktree: clone HEAD to scratch, apply
`git diff --cached`, run the project's gate there — CI builds the committed
tree, and uncommitted tests can make a green worktree a red commit. In a fresh
clone `uv run` may not install the project package
(`ModuleNotFoundError: aio_proxy`); run the suite with the original venv's
python and `PYTHONPATH` pointed at the clone's `src/`.

A file `git status` marks modified with zero diff hunks is line-ending
churn (LF vs CRLF) left by tooling that touched it — it belongs to no
feature work; decide whether the normalization rides your commit instead
of inheriting it blind.

**Never `git add -A` / `git add .` to stage one unit.** In a tree that also
holds scratch, generated settings, and a sibling repo behind a junction, a
whole-tree add sweeps all of it into a commit whose message describes one
change — the diff reads as vandalism hours later when someone wonders why 237
`.tmp/` files and an unrelated deletion landed. Stage the unit's paths
explicitly, and check `git status --short` for directories you did not mean to
touch before committing. When it happens anyway: `git reset --soft HEAD~1`
followed by `git reset` unwinds the commit and returns everything to the
worktree with nothing lost, then add the scratch directory to `.gitignore` so
the next attempt cannot repeat it. Verify with `git ls-files <dir> | wc -l`
that the directory really was never tracked.

**A `cp` into a path that does not exist can exit 0 under a trailing redirect.**
A directory you are sure exists because a sibling workspace has one may not
exist here; a loop with `2>/dev/null` and a piped tail hides the failure and the
"copied" files are nowhere. Before relying on a staged artifact, list the
destination directory and confirm the files are in it — the same rule as hashing
a guest binary after a push instead of trusting the verb.

A generated aggregator (an index or manifest rebuilt from the whole tree)
embeds rows for other sessions' untracked work in the same change as yours.
Check the repo's own precedent first: `git show HEAD:<aggregator>` often
already lists paths that are untracked today (evidence/defect indexes built
from the worktree do by design). Where that precedent exists, commit the
regenerated aggregator with your unit — never hand-edit foreign rows out of
it. Where it does not, stage only your unit's files and leave the aggregator
for whoever lands the rest. Byte-level caches (`*.cache.json`), scratch
files, and generated output the repo does not track stay out of the commit;
commit the generator and the regenerated artifact, not the cache.
