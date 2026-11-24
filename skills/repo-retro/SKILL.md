---
name: repo-retro
description: Use for /repo-retro, a retro of recent agent sessions in a repo (wasted navigation, failed searches, stale docs, command loops), or a count of which skills get used across all projects. Proposes only; edits nothing until approved.
disable-model-invocation: true
---
# Repo retro

Session history comes from the **recall** skill's reader, `../recall/scripts/sessions.py` relative to this skill's directory, run as `python <path>/sessions.py` (below, `sessions.py` means that command; `--help` lists its commands). It reads every agent harness's store on the machine, so the sample is every agent that worked in the repo, not only the harness you are running in. Write its output to a scratch directory outside the repo (the OS temp directory) and analyse it with a script file, not a shell heredoc.

## Workflow

1. **Select.** `sessions.py list --cwd <repo> --days 30 --limit 10` returns the newest root sessions that ran in the repo. `<repo>` is `git rev-parse --show-toplevel`, or the workspace path when that is not a git repo; repeat for each linked worktree (`git worktree list`), since sessions are keyed to the directory they ran in. If the operator names a harness or a session, filter with `--harness NAME` or `--session ID` and skip the newest-10 default; otherwise say which harnesses the sample covers. Drop the session you are in (the newest root session whose first prompt matches your task text) unless the operator names it, and drop scheduled or automated runs. Unless the operator asks for a re-measure, skip session ids named in the newest `.arch/retro-log.md` row and say how many were skipped. With fewer than 10, use what exists and say so; do not widen to other repos. If the window returns nothing, say so and widen `--days` once (state the new window) or ask. Sessions older than the repo's last rewrite are stale-tree evidence. A forked or resumed session replays its parent's calls, so a dump counts them twice (24,000 of 166,000 rows in one real dump). Dedupe rows by `id` before any count, as `references/mining-recipes.md` says.

2. **Measure each session.** `sessions.py calls --session <id> --children` gives every tool call and clipped result, subagents included (`--session` lifts `--days` and `--limit`). For up to about 10 sessions, spawn one subagent per session (respect the tool's per-call limit and batch the rest; with no subagent tool, run them yourself in sequence), each returning only this table. For more, or for any session over about 300 calls, compute the table in one script pass (`references/mining-recipes.md`); a dispatched worker (an agent that was itself started as a subagent) uses the script pass.
   - orientation: every non-mutating call (reads, searches, listings, web lookups, builds, probes) before the first file-mutating call, with the reads-and-searches-only count beside it
   - files read 2+ times
   - searches that returned nothing (list the patterns)
   - doc reads followed by an error that contradicts the doc (doc path + what failed)
   - shell commands run 3+ times (command + failure cause)
   - one-line verdict: what in the repo caused the wasted work

   `sessions.py prompts --session <id>` gives the operator's own words. The same correction typed in 2+ sessions means a rule exists and nothing enforces it.

3. **Aggregate.** Cluster by cause repeated across sessions and rank by total wasted calls. Read `git log` for the window too: 3+ consecutive `fix` commits on one symptom in one file mean each patched a single call site, so propose one shared function plus a check that rejects the raw call elsewhere. Check every cluster against HEAD before ranking it (count the lines of or list the files that were re-read, search the docs for the paths the sessions used) and mark it fixed, stale-doc, or still-open. If the repo was rewritten or reset inside the window, split the sessions at that commit and propose only for causes present in the current tree.

4. **Map each cluster to a fix.**
   - slow find -> a pointer in a file the agent already reads (AGENTS.md or README index, module header)
   - stale or contradicted doc -> repoint it at something that resolves today, or delete it when code is the source of truth. Grep the repo's plans and decision records for the filename first: unindexed is not dead.
   - preventable mistake -> an automated check (lint, type, test, hook), not prose. Read what an existing gate scopes to before assuming it covers the defect.
   - expensive repeated search -> rename, split, or add an index
   - missing instructions -> commands and environment requirements in AGENTS.md
   - dead prose in steering files -> delete
   - information the agent could not reach (service logs, a read-only API) -> give it access
   - no hook or CI job runs the repo's checks -> that absence is itself a finding

5. **Present** the ranked proposals with session ids and call counts. Edit nothing until the user picks. Counts come from measured transcripts only; a verdict is a hypothesis, so label it one.

6. **Log.** Append to `.arch/retro-log.md`: date, session ids measured, median orientation calls before first edit (all non-mutating calls, and the reads-and-searches-only median beside it), empty-search count, doc-contradiction count, fixes applied, and the definitions used. Compare with the previous row by that row's definitions; when you cannot reproduce them, mark the row non-comparable instead of printing a new number beside the old one. A session with no file-mutating call has no first-edit index: report it that way. A pass that only checks whether the retro could run writes no row.

7. **After approval,** implement every approved fix in the same turn and re-measure. For an AGENTS.md or docs rewrite, follow `references/docs-rewrite.md`.

## Skill usage mode

When the operator asks which skills get used, measure every working directory, not one repo. Run `scripts/skill_usage.py <skills dir>` and follow `references/skill-usage.md`. Skip the workflow above.

## Measurement rules

- State the denominator. Count every tool result, not only the ones your parser likes; a shrunken denominator manufactures an improvement.
- Compute a property in the scope where the behavior happens. A root session plus its subagents is many conversations; a family total is not a per-session ratio. Write the scope into the log row.
- Read a command's own exit status. `cmd | head` returns `head`'s status, so a broken tool reports clean.
- Ground a `path:line` claim on the basename appearing in tool output, never on the literal `path:line` string; file readers render line numbers in their own format.
- A moved file keeps its basename. Resolve it against the tree before trusting an old `file:line`.
- Orientation is the one definition in step 2. Before blaming docs for an outlier, read its first 15 commands: context rebuilding (`git log`, `ls`, reading AGENTS.md) points at a missing map; builds and probes are real work.
- Wall-clock cost (sleeps, polling, recovery scripts) is its own category; keep it out of the call ranking.
- When the operator says "stop doing X" and a loaded steering file already forbids X, measure the rate before and after the rule was added: split the rows on `ts` at the commit time (`git log` on that file). A flat rate means the rule never worked: propose an enforcer, and say the rule existed and was ignored.
- Rarely needed cases (shell-automation sessions, a steering doc describing deleted code, gitignored directories, one filename in two repos): `references/measurement-edge-cases.md`.

## Notes

- For a steering file that loads in every workspace (SOUL.md, a global AGENTS.md) use `references/steering-file-review.md`.
- Transcripts hold plaintext file contents. Keep them local; share aggregated numbers only.
