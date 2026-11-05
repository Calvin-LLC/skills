---
name: arch-import
description: Take an external model's architecture reply (role-based) and turn it into a local bakeoff plan. Use after pasting a reviewer's response.
---

# Arch import

Takes the reviewer's structured reply (produced from an `arch-export` brief)
and runs the bakeoff locally against the real code.

## Steps

1. Read the pasted reply. Find every `.arch/aliases*.json` and brief; use the set whose scope and roles match this reply — don't default to `aliases.json` when a scoped alias/brief pair exists. Translate roles to real components from that set.
2. Start with the reply's own assumptions-to-verify list when it carries one: check each assumption against the code before reading the recommendations — that list is the cheapest place to drop advice built on shapes the system does not have. Check the reviewer's environment premises against the RUNNING system too (database journal mode, proxy buffering and timeouts, what the deployment actually sets): a reviewer guesses at your infrastructure and those guesses are often wrong. Then verify each recommendation against the real code and profile. The reply's cited paths, names, and junction maps are frequently stale - check every quoted file path and count against disk before implementing, and implement the intent, not the quoted text. Search the reply's exact identifiers, counters, and structure names in the tree. A zero hit has three causes and only two belong to the reviewer: never existed, renamed by the reviewer, or existed when the brief was written and deleted since. Resolve which with `git log --oneline -S<symbol>` and by dating the commits the brief names (`git log -1 --date=iso --format='%h %ad %s' <commit>`): a mechanism removed AFTER the brief was authored makes the premise dead, not the advice wrong, and every recommendation resting on it drops. Say so in the report's first line, then stamp the brief itself with an `> OBSOLETE as of <date> — <commit> <subject>; do not re-export` block naming what replaced the mechanism. An unstamped brief gets re-exported and the same review returns a third time, burning a whole adjudication to rediscover the same deletion. Check git history and evidence for each recommendation — it may already be landed, partially landed under another name, or attempted and falsified; re-proposing a falsified shape without naming what changed wastes the bakeoff. If the user's current direction contradicts a brief assumption (a fixed size, capacity, or workload premise), the user's direction wins: drop or reshape every recommendation that depends on the dead premise, and say the brief premise is obsolete rather than quietly designing against it. Drop any that assume wrong data shapes. Note the mismatch — if advice doesn't fit, the data shape was usually described wrong; fix the brief next time rather than loosening the redaction. Read the decision ledger (`.arch/decision.tsv`) before classifying anything: the same review is often imported twice, and earlier rows may already name the survivors. Do not inherit those verdicts — re-check that the survivors still exist, because the tree can delete them between imports.
3. For each surviving candidate: implement behind one interface in its own
   worktree, differential-test against the original, benchmark with the frozen
   harness.
   When the target is a live machine/system rather than code, there is no worktree: verify assumptions with
   read-only probes, build changes as inactive and reversible artifacts, and log them in `.arch/decision.tsv` as
   "built, not active" with the undo steps. Re-measure counts the brief quoted before acting; they drift.
   Before trusting any baseline, check the harness reproduces the brief's own numbers. A probe that reports all zeros (or numbers wildly off the brief) is a broken harness, not a finding: read how its stub/include path is resolved (a same-named stub header earlier on the include path silently shadows the probe's own, so the stage under test never sees it) and fix the runner before judging any recommendation.
   Isolate one stage per claim: write a minimal probe that drives only the component the recommendation targets, sweeping the full parameter range, with a control that holds the suspected cause constant (e.g. same input, identity not rotating). Confirm the cause by the control flipping the result, then re-run the full-chain probe after the fix; report sub-cases that still fail (they usually belong to a recommendation you deferred) instead of calling the fix complete.
   When the user names a reference configuration (one setting that was the only one ever tested or tuned), it is the source of truth: every kept change must leave that configuration's behavior unchanged, and a fix that cures other configurations but moves the reference is reverted or held, not shipped. Gate on the original build, not on memory of it: run the unmodified code twice to get the run-to-run noise floor, then the patched code, and require the patched-vs-original difference to sit inside that floor. Compare what is actually emitted (per-tick integer outputs on every axis), not a derived cumulative curve on one axis, because different emission streams can sum to the same curve. A free-running wall-clock gate (`steady_clock` in the generator) makes full-chain runs non-reproducible; for an exact diff, record the stage's inputs as a tape from one run and replay it through both builds of the stage, or inject a fake clock, and compare the output files byte for byte. A cumulative-curve check is a weak proxy: say so instead of calling the reference "unchanged".
   Before promising real historical data, find what the producing system persists: read the service's code and journal for what it keeps. A bot that scores uploads and deletes the temp file holds no history, and a logger that only runs when toggled leaves nothing unless someone toggled it. If no real recording exists, say so and propose capturing one at the reference setting.
   Slow probes (minutes) run in the background with notify; never launch a second build of the same exe while one is running, since the live process holds the file and the link fails.
4. Classify every candidate before keeping any: fits as written, reshape to the live shape, defer behind a named falsifier/measurement, or reject (wrong shape, already landed, or falsified). Keep winners only, with measured gains. Log every candidate and its class to
   `.arch/decision.tsv`, then re-profile. When the brief itself is the casualty, log a row for it (`<prefix>-BRIEF | obsolete`) alongside the candidates — the ledger records why the export was retired, not only how each recommendation was classified.

## Verification

Run the project's existing property/contract suites before and after each kept change, and cite their pass counts alongside the gain.

Every kept candidate carries a measured gain in `.arch/decision.tsv`; every
dropped candidate carries its reason. Re-profile after the winners land and
report before/after numbers.

An imported table is derived tooling, not product progress: when you report
it landed, say explicitly that the project's own goal state did not move and
name the next goal item it unblocks — unlabeled tool reports read as work on
the wrong project.
