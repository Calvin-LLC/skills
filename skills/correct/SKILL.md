---
name: correct
description: "Use when the user is correcting the same agent mistake again, or for /correct: find the mistakes agents repeat in this repo and make each one impossible, by architecture, then types, then a lint, then a test, docs last."
---

# Correct

The operator keeps correcting agents in this repo for the same mistakes. Change the repo so the next agent can't make them. If the invocation names a specific failure, that failure is the first class: fix it and prove the fix, then mine for sibling mistakes only if asked.

Assume every contributor is an agent that sees only the files it opened, copies the nearest example, and takes the shortest path that compiles. Design the repo so a change that looks right from one file is right for the whole repo.

## Find the mistake classes

First, read recent commits, reverts, agent instruction files (`AGENTS.md`), and comments that explain workarounds. Then read how the operator corrected agents in past sessions: the **recall** skill's `scripts/sessions.py prompts --cwd <absolute-repo-path>` gives the operator's own words across every harness, and a correction there that names a file or pattern is a mistake class candidate. If it returns 0 prompts, the history was recorded under an earlier project path (the repo before a move or split): export that cwd too and read both.

Group the mistakes into classes. A class counts once it has happened twice. Three or more consecutive `fix` commits on one symptom in the same file mean each one patched a single call site: the class is the missing shared function, so the fix is one helper that owns the behavior plus a check that rejects the raw call anywhere else.

Corrections miss mistakes that produce no complaint: money taken and not granted, a drifted ledger, a webhook that returned 200 and did nothing. When the repo has effects that leave the codebase, find them by reconciling local state against the system of record: read `references/unreported-mistakes.md`.

## Prove the check runs

"Fails on a real past mistake" assumes the check executes. Prove that first: a cron with a fatal import, a monitor whose output goes nowhere, or a guard with no caller has never said no. Run it, show its verdict on known-good input, then its failure verdict on the past mistake.

List every check and every place that invokes it. Two cases are broken: a check with no caller (including a `--check` flag no scheduled step invokes), and a check with a caller that sits red and ignored. Fix both with one runner that enumerates the directory, so a check that exists is a check that runs, and name each check in CI as its own step so a failure reports itself.

The runner separates four outcomes:

- `PASS`: exit 0 **and** a printed verdict line. Exit 0 with no output is `ERROR`.
- `FAIL`: the check rejected something and named what it rejected.
- `ERROR`: the check itself threw (a file it asserts on is gone) or printed nothing. Never a pass and never a product failure: a broken check has said nothing about what it guards.
- `SKIP`: printed with its reason (needs a build tree, needs network), never omitted from the list.

Rules for every check:

- Delete a check when its subject is deleted. A permanently red guard teaches everyone to ignore red.
- Scan the tree the work happens in. With junctions, symlinks, or submodules, the source tree and the live tree are different roots.
- Keep its reach narrow: scope the pattern to the component it guards, because a gate that rejects correct code gets disabled. Exempt the one line that must reproduce the bug with a marker and a reason on that line, not by filename.
- Write build artifacts outside the repo.

When a check involves a second workspace, a git-excluded work tree, PowerShell exit codes, a generated index, docs that cite paths, several text encodings (LaTeX, PDF), notes agents copy from, a build-mode switch, or edits to files that build strings (JSON, HTML), read `references/check-pitfalls.md`.

## Fix each class at the highest level that works

1. **Eliminate it with architecture.** Give each piece of state one owner and each task one supported way. Hide internals so the wrong import fails. Replace hand-synced lists with one source of truth. Delete old ways and dead code an agent would copy. For an effect that leaves the codebase (a charge, a grant, a send), that means one function, an idempotency key that makes a retry a no-op, and a reconciler against the external source of truth.
2. **Enforce it with types so the bad state can't be written.** If bad code still compiles, add a lint or CI check whose error names the file, type, or function to use instead. If the pattern is already common, fail only when a change adds more.
3. **Test the behavior.** Fix or delete any test that still passes when the behavior it checks breaks, or that fails when only the internals change.
4. **Write docs or agent rules last, only for judgment calls.** Nothing fails when an agent skips them.

Prefer the smallest change that removes the class: an existing registry, library, setting, or helper that already owns the fact beats new code, and is usually the higher-level fix too.

## Fix and prove

Fix the most frequent classes now, one commit each. Prove each new check fails on a real past mistake: check out the pre-fix commit or reintroduce the mistake in a scratch worktree, run the check, and show the failure output. Run the same command locally and in CI. Exceptions go on the offending line with a reason, an expiry date, and a human's approval.

- **Prove the fix landed.** A fix you cannot find in the file was never applied. In the same call as the edit, search for the old construct (zero hits) and the new one (a hit), then re-run the failing path. Do the same for a fix that a summary credits to an earlier session: the summary is a claim, the file is evidence.
- **Prove the proof is not vacuous.** Run the OLD rule against the real recorded input and confirm it gives the wrong verdict, then the new rule the right one, both asserted in one script that fails if either half stops holding. Use the verbatim recorded line as the fixture and cite where it came from; a paraphrase drops the one trailing field that made the predicate wrong.
- **Show both verdicts from the same runner:** PASS on the healthy tree and FAIL on the injected mistake, asserting the verdict line and the exit status. A silent pass counts only once the must-fail case has fired, because a tool handed input it ignores also exits 0. Capture the status directly, never through a pipe (POSIX `cmd > out 2>&1; rc=$?`; PowerShell `cmd *> out; $rc = $LASTEXITCODE`).
- **Untracked or gitignored files have no pre-fix commit.** Reproduce in place: copy the file aside, re-insert the offending line, run the check, restore from the copy, then verify the restore with a zero-hit search for the marker line and a fresh PASS. A failed copy-back leaves the bug in the tree.

## Keep the rule table

Last, extend the repo's existing rules table, wherever it lives, so it pairs each rule with what enforces it, and make sure the agent instruction file points to it. If the repo has no table, create one in `AGENTS.md`; write "judgment" in the enforcer column for a rule nothing checks, so the gap stays visible. A rule left with no enforcer is reported to the operator as an open gap in the final message. When the operator corrects you, fix the mistake and add the rule. If the rule was already there and nothing enforces it, that's a repeat, so fix it at the highest level in the same change. Drop a rule once its mistake can't happen.

- **Gitignored instruction file** (`git check-ignore -v AGENTS.md`): the table only reaches the checkout that has it. Keep the authoritative table in a tracked file beside the checks and let the ignored file point at it.
- **Protected instruction file** (a write needs approval): read `references/protected-instruction-file.md`.
