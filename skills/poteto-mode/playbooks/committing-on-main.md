### Committing on main

Invoked at the end of every other playbook that produces code. This is the
ship path. Where the repo's agent-instruction file has a Git section, branch
rules belong there, and the message format to the `commit` skill. What follows is what this playbook adds.

**Isolation.** Parallel workers write to their own scratch dirs, not to git
branches. Land accepted work onto `main` as sequential commits. Handoff
worktrees created by an orchestration tool are spawn plumbing; they are not GitHub feature branches and they do
not get PRs.

**Commits.** Finish the unit, prove it locally, then commit. Do not sprinkle
micro-commits through unfinished work. Follow-up features are later commits on
`main`, not a stack of PRs. Amend when the fix belongs in a just-made unpushed
commit; new commit when separable.

**Push.** Prove the unit on the real tests and the feature path before pushing.
Force-push and the other irreversible writes pause per the Pause section of the
repo's agent-instruction file, where it has one.

**After push, watch CI if the repo has it.** This is not babysit.
Babysit is a named PR. After pushing `main`, take the SHA.
No `.github/workflows/` means stop. Otherwise loop per
`playbooks/autonomous-run.md` step 2 until the pushed SHA's CI
conclusion is success. Each turn: `gh run list
--commit <sha> --json databaseId,status,conclusion,name,url,headSha`.
Empty list is GitHub lag, not no CI; wait for the next turn.
In progress, wait. Failure: `gh run view <id> --log-failed`, classify
(flake, our diff, stale base), fix on `main`, prove locally, push,
continue on the new SHA. One flake rebuild via `gh run rerun <id>
--failed` if the log is infrastructure; a second identical failure is
not flake. Do not
open a PR so you can watch it.

A subagent that finishes code runs `grill-me` review when the design is
contested, **unslop**, and **no-comments**, returns the commit SHAs, and
does not open a PR. Return to the parent.
