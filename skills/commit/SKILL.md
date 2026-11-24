---
name: commit
description: "Use before making any git commit: one major feature per commit on main, a one-line message with no body, never push without explicit user approval."
---

# Commit

Git is source tracking and a restore point. Work on `main`, in the folder the user has open. Create no feature branch, pull request, or `git worktree` for the work unless the user named one: a side worktree hides the changes from the folder the user is watching. Run `git worktree list` first; if the session cwd is a linked worktree, the work goes in the repo's primary folder. A read-only baseline worktree (pre-change builds for before/after receipts) is the one exception.

## When to commit

One commit is one major feature, one bug fix, or one coherent restore point. Do not mix unrelated work or sprinkle micro-commits through an unfinished change. Finish the unit, prove it locally, then commit.

## Steps

1. Infer paths or extra instructions from the prompt.
2. `git status` and `git diff` (limit to specified files). `git diff` omits untracked files, so read each untracked path. A scratch, log, or report file this unit did not need stays out of the commit, and you delete it only if you made it.
3. Confirm the set is one feature. Split if it isn't. If `git status` is clean and `HEAD` already holds the work, make no commit: name the commit that holds it and offer a split.
4. Confirm local proof exists for this unit: the project's real tests, run on a fresh build of this tree. If it doesn't, test first.
5. Stage only that unit, by explicit path; never `git add -A` or `git add .` at the repo root (`git add -A -- <explicit paths>` is fine). Ask if extra files are ambiguous. If a file also carries uncommitted work that is not yours, never `git add` it: use Mixed worktrees below. After a `stash pop` or a merge, run `git reset -q` before staging.
6. Read `git diff --cached --name-only` as its own call, before committing: it must list this unit and nothing else, because the index can already hold another session's staged paths (`git reset -q` empties it without touching the worktree). Then `git commit -m "<subject>"` as a separate call, with one `-m` and no body. Never chain add, commit, and push in one command.
7. If a hook rejects the commit, nothing landed: fix the cause, restage, and commit again. Never bypass a hook with `--no-verify`.
8. Do not push from this skill; Push below says when a push is allowed.

## Message

`<type>(<scope>): <overview>`

- `type` required: `feat`, `fix`, `docs`, `refactor`, `chore`, `test`, `perf`.
- `scope` optional: short noun (`api`, `ui`, `nav`).
- Overview required: one line, imperative, <= 72 chars, no trailing period.
- No body: no second line, paragraph, bullet list or recap. Write a body only when the user asks for one in so many words.
- No breaking-change markers, footers, or `Signed-off-by`. No decorative emoji. Apply the **unslop** skill.
- Assert only what the diff proves: the overview names what landed, not what the work claims to achieve and not the files touched.

Good: `feat(nav): load spot HTML from the summary endpoint`
Bad: a paragraph of what you thought about, or a list of every file.

## Mixed worktrees

The worktree often carries other sessions' uncommitted work, sometimes inside the files you touched; `git add <file>` then commits their hunks under your message. A file is mixed when any hunk is not yours, cosmetic ones (a formatter reflow, a default-value tweak) included, so review the staged diff hunk by hunk. Filtering `git diff` hunks by marker is not safe: a hunk spanning both changes carries the other's lines into the index.

For a mixed file, read `references/mixed-worktree.md`: split by `-U0` hunk when the changes sit in separate regions, rebuild the staged blob from `HEAD` when they interleave. It also covers line-ending-only churn, generated aggregators, and unwinding a commit that swept in too much.

Whenever uncommitted work stays behind, prove the staged tree, not the worktree: clone `HEAD` to a scratch directory outside the repo, apply `git diff --cached`, and run the project's gate there. CI builds the committed tree.

## Checkpoint on order

When the user orders the whole dirty tree committed (a hard stop, "make a clean tree", a checkpoint before a restart or deploy window), commit rather than refuse or re-ask, whoever wrote the changes. Never as one mixed commit: first the verified unit(s) as normal feature commits, then every remaining path in one `chore(wip): ...` commit that honestly labels unreviewed parallel state. Take the checkpoint BEFORE the window starts: the commits are the restore point it is survived from.

A dirty child repo (submodule) gets its remainder committed as a `chore(wip)` commit in the child, the leaf pushed first, then the gitlink bumped (`references/submodules.md`). A stash is not a checkpoint.

An explicit order for one simple commit of the whole tree overrides the split: make the single one-line commit without re-asking, then name in the report what unrelated work it swept in so the user can ask for a split.

## Push

**Hard rule: never push without the user's explicit approval for that specific push.** No exceptions: features, fixes, reverts and force-pushes all wait. Commit locally, show what is ready (commits and diff), ask, and push only after a clear yes. Instructions like "merge it", "keep it", "remove it" or "revert it" are not approval to push. Nothing gets pushed while a plan is still under discussion, and nothing gets pushed before the project's real tests and the feature path pass locally. Force-pushes and other irreversible writes also pause for the user's go-ahead (the Pause section of `AGENTS.md`, where the repo has one).

Before any push, read `.github/workflows/*.yml` (or the equivalent) for a trigger on the target branch. If a push deploys, publishes, or runs against production:

- An instruction to commit is not an instruction to ship. Unless the user said "push", state the coupling in one line first: "this branch auto-deploys on push, so committing is local but pushing is live — say the word."
- A red gate job on the same branch is not a safety mechanism: it disappears when someone fixes the unrelated job.
- Propose weakening the pipeline to an explicit dispatch-triggered deploy.

## Read when the case applies

- Hundreds of dirty paths from several sessions, a request to squash or re-group commits (local, or before a push), or a push that must be undone: `references/history.md`.
- A repo with submodules or gitlinks, before committing or pushing: `references/submodules.md`. Leaf repos push first.
- A file that carries credentials, sessions, or a database, before committing or pushing it even to a private repo: `references/shared-data.md`. It is a one-way door that needs the user's explicit choice.
- Removing any worktree, or replaying side-branch commits onto the user's branch: `references/worktrees.md`. Removal can follow a junction and delete real data.
- Proof that rests on a build log, prebuilt test binaries, or changed `.ps1` files: `references/local-proof.md`.
