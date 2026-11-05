---
name: correct
description: "Find the mistakes agents keep repeating in this repo and make each one impossible. Try architecture first, then types, then a lint whose error names the fix, then a test, and write docs last. Prove each check fails on a real past mistake. Repeat this each time the operator corrects you. Use for /correct."
disable-model-invocation: true
---

# Correct

The operator keeps correcting agents in this repo for the same mistakes. Change the repo so the next agent can't make them.

Assume every contributor is an agent that sees only the files it opened, copies the nearest example, and takes the shortest path that compiles. Design the repo so a change that looks right from one file is right for the whole repo.

## Find the mistake classes

First, read recent commits, reverts, agent instruction files (`AGENTS.md`), and comments that explain workarounds. Then read how the operator corrected agents in past agent sessions: the **recall** skill's session sources (`session export --format jsonl --only user-prompts --cwd <absolute-repo-path> --yes <file>`) give the operator's own words, and a correction there that names a file or pattern is a mistake class candidate. Group the mistakes into classes. A class counts once it has happened twice. Three or more consecutive `fix` commits on one symptom in the same file mean each one patched a single call site: the class is the missing shared function, so the fix is one helper that owns the behavior plus a check that rejects the raw call anywhere else.

## Find mistakes that nobody reported

An operator correction is one source. It misses the class that produces no
complaint: money taken and not granted, a ledger that drifted, a webhook that
returned 200 and did nothing. Those never become a correction, so find them by
reconciling your state against the system of record instead of reading code.

- Pull the provider's own view (API, export, dashboard) and diff it against the
  local table on the shared identifier. Every disagreement is either a lost
  effect or a stale local mark. Both are mistakes the operator will never report.
- Compare each writer's *predicate* for the same transition, not each writer's
  output. Two paths can both look correct and still disagree on units, on
  lifetime cases, and on which failure statuses mean paid.
- Count effects against inputs: N invoices opened, M marked paid, K grants
  written. The gap between the first and last number is the bug, and it survives
  code review because every individual path is correct in isolation.
- **A cached column is not the source of truth, and its vocabulary drifts.** A table
  written years ago can store a legacy numeric id (`2`) where the current code stores
  a product name (`2pcvalo`). Code that prefers the cache over the value it parsed
  builds a key from the wrong vocabulary — a column named `2_exp` — and every effect
  on those historical rows throws. Prefer the identifier the current code generates,
  treat the cached column as a fallback, and validate it against the known registry
  before using it to construct anything. Check the distribution, not one row:
  `GROUP BY` on the column shows a mixed vocabulary in a single query, while the
  first row you happen to read looks perfectly fine.
- **A job that retries a deterministic failure forever is its own incident.** Nothing
  about a permanently broken row changes between attempts, so a short interval turns
  one defect into millions of log lines, a hot database, and a signal nobody can read.
  Give the failure a terminal state (mark it failed, stop selecting it) or a backoff,
  and size the interval against how fast the external state can actually change. Log
  volume is the tell: megabytes of one repeated message is not a busy job.
- **A test schema that differs from the real one passes what production silently
  mangles.** A test database built by a hand-written schema script can type a column
  as free text where the deployed table has a fixed list, so a new value passes every
  check and is stored blank (or truncated) on the real server, which is not in strict
  mode. Query the real column type (`information_schema.COLUMNS`), `GROUP BY` the
  column for blank or unexpected values, and add one check that the test schema's
  type equals the type the migration doc names, so the two cannot drift apart.
- **A missing `require` turns a silent side path into a permanent one.** A helper
  loaded from the wrong directory throws on every call, and if that throw sits inside
  a `catch` that logs and continues, the feature is dead for months while the primary
  effect looks healthy. When a post-success hook fails, check the path resolves before
  assuming the remote service is refusing you.

## Prove the check runs

`Prove each check fails on a real past mistake` assumes the check executes.
Prove that first. A cron with a fatal `require`, a monitor whose output goes
nowhere, or a guard with no caller has never once said no, and reads as coverage
in the file listing. Run it, show it returning a verdict on known-good input,
then show the failure verdict on the past mistake.

Enumerate the callers before trusting any check. List every check and every
place that invokes it, and treat both of these as broken: a check with no caller
at all, and a check that has a caller while sitting red and ignored. The second
is worse, because it trains everyone to read red as background noise. Fix it by
running every check through one runner that enumerates the directory, so a check
that exists is a check that runs, and by naming each one in CI as its own step
so a failure reports itself.

A generated map or index with a `--check` flag next to its generator drifts
exactly on the files being edited, because the generator runs only when someone
remembers it. A `--check` flag that no scheduled step invokes is the no-caller
case in disguise: wire the flag into whatever gate already runs on the machine
where the edits land (cron, pre-stage runner), and treat a stale verdict as a
FAIL whose fix is regenerate, not a prose reminder next to the generator.

The runner must separate three outcomes, never two:

- `PASS` — exit 0 **and** the check printed a verdict line. Exit 0 with no
  output is `ERROR`: a silent check cannot be trusted to have run.
- `FAIL` — the check rejected something and named what it rejected.
- `ERROR` — the check itself threw (a file it asserts on is gone) or printed
  nothing. Never read this as a pass, and never as a product failure: a broken
  check has said nothing about the thing it guards.
- `SKIP` — stated with its reason (needs a build tree, needs network). Print it
  rather than omitting the check from the list, since omission is how checks go
  unnoticed in the first place.

A check runner must write its build artifacts outside the repo. A compile step run from the repo root drops object files there on every run, and the clutter looks like the check's output when it is the runner's bug: build in the temp directory or pass an explicit output path.

A check whose subject was deleted is deleted with it. A guard that outlives the
file it asserts on is permanently red and teaches everyone to ignore red.

A check must scan the tree the work actually happens in. Workspaces assembled
from junctions, symlinks, or submodules mean the source tree and the live tree
are different roots; a gate that scans only the former reads as coverage for
work that happened entirely in the latter.

A shared runner's `$root` is not the check tool's home. A stage/gate script
that resolves its repo from its own path can live in one tree while the check
script exists only in a satellite workspace, so the flag runs a tool that is
not there (version error, silent 0). Test the tool's path exists from the
runner's resolved root before calling it, and when it lives in another
workspace, take the pattern the repo already established for that split — an
env-var root override defaulting to the satellite path, or a forwarder in the
runner's scripts dir — rather than a hard-coded sibling guess. The fix is the
same shape in either direction: one authority for where the tool lives, and
the gate proving it fires from the root the runner actually uses.

A proof for an untracked file cannot cite a commit. Harness scripts, share-folder
scratch, and anything gitignored have no pre-fix revision to check out, so
"check out the pre-fix commit" is not available. Reproduce the mistake in place
(copy the file aside, re-insert the offending line, run the check, restore from
the copy) and show both verdicts. Verify the restore actually took — a failed
copy-back leaves the bug in the tree and the gate red for the next agent.

Read the runner's exit status through the shell's own capture (`cmd > out 2>&1;
rc=$?`), never through a pipe tail — `| tail` reports tail's status as the
proof's rc. When the runner wraps a child check in PowerShell, a `Write-Error`
plus `exit 2` lands as rc=1 at the shell: the verdict line and rc must both be
asserted in the proof output, and a pass verdict on a healthy tree plus a fail
verdict on the injected mistake shown from the SAME runner invocation, not two
log files later. If the proof runs the mutated file in place, copy it aside
first and verify the restore by grepping for the marker line — a zero-hit grep
and a fresh `--check` PASS are the two facts that close the proof loop.

Notes that agents copy from (a resume source text, talk tracks, a letter archive) are where a retracted claim survives: the live files get corrected and the copy source keeps the old number. Scan them with the common rules, and mark a line that must quote the wrong value on purpose with an exemption token the check honors, so a correction note does not fail its own gate.

A text pattern written for plain prose is blind to the same fact in another encoding: `86%` in a note is `86\%` in LaTeX source and arrives line-wrapped or ligatured in text extracted from a PDF. Scan the source format and the rendered output, give each format its own must-fail case in the proof, and when a rule only matters for outgoing documents (game names, an unsupported skill), keep a separate, narrower rule set for internal notes so internal files do not drown the real hits.

Keep the check's reach narrower than its mechanism. A predicate that fires on
any `ok=1` substring fails legitimate call sites that check a different
component's output, and a gate that rejects correct code gets disabled or
worked around. Scope the pattern to lines that inspect the component under
discussion, and add an explicit exemption marker for the one file that must
reproduce the bug on purpose (`GATE_VERDICT_TOKENS_EXEMPT` with a reason in the
same comment), rather than excluding it by filename where nobody can see why.

## Fix each class at the highest level that works

1. **Eliminate it with architecture.** Give each piece of state one owner and each task one supported way. Hide internals so the wrong import fails. Replace hand-synced lists with one source of truth. Delete old ways and dead code an agent would copy. For an effect that leaves the codebase — a charge, a grant, a send — "one supported way" means one function, an idempotency key that makes a retry a no-op, and a reconciler against the external source of truth that turns a silent miss into a finding.
2. **Enforce it with types so the bad state can't be written.** If bad code still compiles, add a lint or CI check whose error names the file, type, or function to use instead. If the pattern is already common, fail only when a change adds more. A mode switch that people edit by hand in a shared header (`#define DEV_` in a precompiled header turns the security threads off) will eventually ship: derive it from the build configuration only (the Debug `PreprocessorDefinitions`), and add a compile-time `#error` for the forbidden combination (`defined(DEV_) && defined(NDEBUG)`) whose message says where the switch is allowed to be set. Prove it through the real build system: compile the one translation unit per configuration and require Release to fail and Debug to pass.
3. **Test the behavior.** Fix or delete any test that still passes when the behavior it checks breaks, or that fails when only the internals change.
4. **Write docs or agent rules last, only for judgment calls.** Nothing fails when an agent skips them.

## Fix and prove

**A fix you cannot find in the file was never applied.** Editing, intending to edit,
and describing the fix in a summary all feel identical afterwards, and a later session
inherits the claim rather than the change. After every fix, prove it landed: grep the
file for the old construct and require zero hits, grep for the new one and require a
hit, and re-run the failing path. Do this in the same call that makes the edit, not at
the end of the session. A broken chain between "I fixed it" and "it is in the tree" is
how one bug survives two rounds of repair and gets reported as solved twice. The same
applies to a fix a summary credits to someone else: verify against the tree, because
the summary is a claim and the file is evidence.

**Prefer the smallest change that removes the class.** The most efficient fix usually
is not new code: it is an existing registry, library, setting, or config value doing
the job the new code was about to duplicate. Deriving a column list from the registry
that already exists, instead of re-deriving it with a hand-built query, is both the
smaller diff and the higher-level fix — the two goals agree more often than they look.
Reach for settings and existing helpers first; write new logic only when nothing
existing owns the fact.

Then fix the most frequent classes now, one commit each. Prove each new check fails on a real past mistake: check out the pre-fix commit or reintroduce the mistake in a scratch worktree, run the check, and show the failure output. Run the same command locally and in CI. Exceptions go on the offending line with a reason, an expiry date, and a human's approval.

If the export for the current path returns 0 prompts, the history was recorded under an earlier project path (for example the repo before it was split out). Export that cwd as well and read both.

## Mistake classes that recur in docs-heavy repos
- Docs that cite `file:line` rot as soon as the file moves. Replace them with function or type names, and add a CI check that fails on any `path:line` citation or untracked path in tracked Markdown, with an error naming the fix. Prove it by putting an old pre-rewrite version of the doc into the tree and counting the findings.
- A scripted regex or index-splice edit to a file that builds strings (JSON, HTML) can build clean and break at runtime, and a deleted block can take a needed statement with it. Make such edits with the patch tool, then run the end-to-end smoke check before committing.

**Prove the harness exercised the file.** A silent result only counts if the same harness can say no. A compiler handed a header alone prints a warning, does nothing, and exits 0, which reads as "guard silent" in every case, including the one that must fail. Compile a tiny translation unit that includes the header, and require the must-fail case to fire before believing the must-pass cases stayed quiet.

**Prove the proof is not vacuous.** Before trusting a must-fail demonstration, run the OLD rule against the real recorded input and confirm it actually fires. A proof that passes because the old bug never reproduced on that fixture proves nothing while reading as validation. Assert both halves in the same script: the old rule produces the wrong verdict, the new rule produces the right one — and fail if either half stops holding, so the proof cannot quietly decay into a tautology.

Write the proof against the verbatim recorded line, not a paraphrase of it. The detail that makes a predicate wrong is usually one trailing field, and a cleaned-up copy of the input drops exactly that field. Keep the real artifact in the check as a fixture and cite where it came from.

## Keep the rule table

Last, keep a table in the agent instruction file that pairs each rule with what enforces it. If the repo has no agent instruction file, create `AGENTS.md` with the table; write "judgment" in the enforcer column for a rule nothing checks, so the gap stays visible and a later pass can close it. When the operator corrects you, fix the mistake and add the rule. If the rule was already there and nothing enforces it, that's a repeat, so fix it at the highest level in the same change. Drop a rule once its mistake can't happen.

When the tree the work happens in is itself git-excluded, a CI step cannot reach it: put the runner inside that tree, call it from a local pre-commit hook for the tracked repo around it, and say in the report that the hook is unversioned and runs on this machine only.

A gitignored instruction file is the same problem in another form: the table only reaches the checkout that has it. Check `git check-ignore -v AGENTS.md`; when it is ignored, keep the authoritative table in a tracked file beside the checks and let the ignored file point at it.

Agent instruction files are frequently protected: the write raises an approval
prompt, and a timed-out prompt is a refusal, not consent. Do not retry it and do
not route around it through `terminal` or a script. Write the table to a file
that is not protected (`tools/gates/RULES.md` next to the checks it names),
point at it from wherever the agent already looks, tell the user in one line that
the protected file needs their approval and that the table is ready to move, and
carry on. Losing the whole pass because one file needed a signature is the worse
outcome. When the user later approves, copy the staged file into place with an ordinary `cp` (the approval is the consent the earlier prompt lacked), diff the destination against the staged copy, and re-run the checks.
