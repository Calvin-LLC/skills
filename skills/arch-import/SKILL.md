---
name: arch-import
description: Use when the user pastes an outside reviewer's reply to an `arch-export` brief, usually a table with columns id, target role, change, expected gain, risk, test, benchmark. Not for other pasted reviews.
---

# Arch import

Takes the reviewer's structured reply (produced from an `arch-export` brief)
and runs the bakeoff locally against the real code.

## Steps

1. Save the pasted reply verbatim beside the brief before adjudicating. Find every `.arch/aliases*.json` and brief; use the set whose scope and roles match this reply, not `aliases.json` by default. Translate roles to real components from that set.
2. Adjudicate the reply before building anything:
   - Check its assumptions-to-verify list first, if it has one: the cheapest place to drop advice built on shapes the system lacks.
   - Check its environment premises against the RUNNING system (journal mode, proxy buffering and timeouts, deployed settings); reviewers guess infrastructure wrong.
   - Treat cited paths, names, counts, and junction maps as possibly stale: verify each on disk, implement the intent, not the quoted text, and search its exact identifiers in the tree. A zero hit means never existed, renamed by the reviewer, or deleted since; resolve which with `git log --oneline -S<symbol>` and by dating the commits the brief names.
   - A mechanism removed AFTER the brief was written makes the premise dead, not the advice wrong: drop every recommendation resting on it, say so in the report's first line, and stamp the brief `> OBSOLETE as of <date> — <commit> <subject>; do not re-export`, naming the replacement.
   - If the user's current direction contradicts a brief premise (size, capacity, workload), the user wins: drop or reshape dependents and call the premise obsolete. If advice assumes a wrong data shape, fix the brief rather than loosening redaction.
   - Check git history and evidence per recommendation: it may be landed, partly landed under another name, or tried and falsified; don't re-propose a falsified shape without naming what changed.
   - Read `.arch/decision.tsv` before classifying: earlier rows may name survivors, but re-check that they still exist.
3. For each surviving candidate: implement behind one interface in its own
   worktree, differential-test against the original, benchmark with the frozen
   harness.
   When the target is a live machine/system rather than code, there is no worktree: verify assumptions with
   read-only probes, build changes as inactive and reversible artifacts, and log them in `.arch/decision.tsv` as
   "built, not active" with the undo steps. Re-measure counts the brief quoted before acting; they drift.
   Before trusting any baseline, check the harness reproduces the brief's own numbers. A probe reporting zeros (or numbers wildly off the brief) is a broken harness, not a finding: fix the runner before judging any recommendation. If the harness differs from production (rate, scale, data), state that on every gain and prefer rate-parameterised changes over tuned constants.
   Isolate one stage per claim: write a minimal probe that drives only the component the recommendation targets, sweeping the full parameter range, with a control that holds the suspected cause constant (e.g. same input, identity not rotating). Confirm the cause by the control flipping the result, then re-run the full-chain probe after the fix; report sub-cases that still fail (they usually belong to a recommendation you deferred) instead of calling the fix complete.
   When the user names a reference configuration (one setting that was the only one ever tested or tuned), it is the source of truth: every kept change must leave that configuration's behavior unchanged, and a fix that cures other configurations but moves the reference is reverted or held, not shipped. Gate on the original build, not on memory of it: run the unmodified code twice to get the run-to-run noise floor, then the patched code, and require the patched-vs-original difference to sit inside that floor. Compare what is actually emitted (per-tick integer outputs on every axis), not a derived cumulative curve, because different emission streams can sum to the same curve. A free-running clock makes full-chain runs non-reproducible; for an exact diff, replay a recorded input tape through both builds or inject a fake clock, and compare outputs byte for byte. A cumulative-curve check is a weak proxy: say so instead of calling the reference "unchanged".
   Before promising real historical data, find what the producing system persists: read the service's code and journal for what it keeps. A bot that scores uploads and deletes the temp file holds no history, and a logger that only runs when toggled leaves nothing unless someone toggled it. If no real recording exists, say so and propose capturing one at the reference setting.
   Slow probes (minutes) run in the background with notify; never launch a second build of the same exe while one is running, since the live process holds the file and the link fails.
4. Classify every candidate from measurement, not only from reading: `live` (fits as written), reshape to the live shape, defer behind a named falsifier, or reject (wrong shape, already landed, falsified). Log every candidate in `.arch/decision.tsv` with columns `id | class | gain-or-reason | evidence`, then re-profile. Brief rows (`<prefix>-BRIEF`) use `live`, `corrected` (append a dated correction to the brief), or `obsolete`; the ledger records why an export was retired. Apply in this run the items that fit as written and are cheap and reversible (docs, copy, one test); otherwise end with the ledger plus the chosen build order. Doc-only changes need no separate worktree.

## Verification

Run the project's existing property/contract suites before and after each kept change, and cite their pass counts alongside the gain.

Every kept candidate carries a measured gain in `.arch/decision.tsv`; every
dropped candidate carries its reason. Re-profile after the winners land and
report before/after numbers.

An imported table is derived tooling, not product progress: when you report
it landed, say explicitly that the project's own goal state did not move and
name the next goal item it unblocks — unlabeled tool reports read as work on
the wrong project.
