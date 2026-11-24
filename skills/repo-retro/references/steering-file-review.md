# Reviewing a global steering file (SOUL.md, a global AGENTS.md)

The file loads in every workspace, so a per-repo sample is the wrong one. Measure across all workspaces.

1. **Find the live file and its copies.** Each harness loads its own path, often a link to one source. `git log --format='%h %ad %s' --date=short -- <file>` on the source gives the last change, which is the before/after cut-off. The copies must be identical; edit them in the same step.
2. **Export what the user typed, everywhere.** `sessions.py prompts --days <N> --limit 0` with no `--cwd`. Drop automated runs, texts under 20 characters, compaction summaries, and pasted skill bodies; count the skill bodies separately as skill invocations.
3. **Repeated typed instructions are the signal.** A rule the user re-types is missing from the file or not reaching the agent. Cluster by regex, then read the prompts behind each top cluster; regex counts are upper bounds.
4. **Check delivery before judging wording.** Subagents often start without steering files. Read a child session (`sessions.py transcript --session <id>`, child ids from `list --children`): a rule the orchestrator had to paste into the brief did not reach the child by itself, so rules for delegated work belong in the dispatch brief too.
5. **Measure compliance** from `transcript` output. For a format rule, test each assistant message that ends a turn after 3+ tool results for the required shape, split at the cut-off, and report the count and which sessions missed. Mid-work status updates count; only a message whose main job is a question is exempt.
6. **Propose, then edit only what was approved.** State what is measured and what is assumed.
