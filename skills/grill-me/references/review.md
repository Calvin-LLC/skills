# Review

Multi-model review of a contested design or diff. Read-only. Do not auto-apply anything. Paths below are relative to the skill directory.

1. Scope. The files or diff they pointed at. On `main`, `git diff` / `git log`. Package that plus the context the reviewers need.
2. Intent. One paragraph: what this change is trying to do. From the user, the commits, and the code. Reviewers challenge the execution, not the goal. If you cannot state the intent, that is an Ask, not a Review.
3. Spawn. One reviewer subagent per review model the user names; with none named, use the harness default and say model diversity was unavailable (respect the tool's per-call limit and batch the rest). Pick the model per subagent when the tool allows it; otherwise run the harness's headless one-shot CLI on that model; if neither is possible, say model diversity was unavailable. Same filled prompt to every reviewer. Fill `references/reviewer-prompt.md` with the intent, the diff, `references/rubric.md`, and `references/code-quality-review.md`. Read-only. Do not flatten onto one model. With no subagent tool, run the slices yourself in sequence.
4. Synthesize. Consensus (2+ models) is high signal. Lone findings still get read. Merge duplicates. Note disagreements.
5. Judge. You are the lead, not an aggregator. Filter with `references/lead-judgment.md`. Bucket every finding: Act on / Consider / Noted / Dismissed. Include which models raised it and one line why you bucketed it that way. Cap Act on at a handful. Show Dismissed so they can override you.

Output: Intent, Reviewers, the four buckets, then where the models agreed or split.
