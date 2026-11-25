# Review

Multi-model review of a contested design or diff. Read-only. Do not auto-apply anything. Paths below are relative to the skill directory.

1. Scope. The files or diff they pointed at. On `main`, `git diff` / `git log`. Package that plus the context the reviewers need.
2. Intent. One paragraph: what this change is trying to do. From the user, the commits, and the code. Reviewers challenge the execution, not the goal. If you cannot state the intent, that is an Ask, not a Review.
3. Spawn. One `task` call: the filled prompt goes in the shared `context`, so every reviewer gets the same one, and `tasks[]` holds one item per reviewer. Fill `references/reviewer-prompt.md` with the intent, the diff, `references/rubric.md`, and `references/code-quality-review.md`. Read-only. Do not flatten onto one model.
   - Models. Every reviewer is a default worker (no `agent`): the bundled `reviewer` agent reports in its own format and does not follow the template. For different models, set `model` on each item when `task.perCallModel` is on, one item per model the user names, or use custom agents whose `model:` lines differ. With neither, every reviewer runs on one model: spawn one and say model diversity was unavailable.
   - Output. The template has each reviewer reply with one JSON object: a `findings` array whose entries carry `severity`, `title`, `location`, `finding`, `evidence` and an optional `suggestion`. Read them through `agent://<id>/findings/<index>`, or `agent://<id>` whole when the reply is not valid JSON. When `task.structured` is on, pass the same shape as each item's `outputSchema`.
4. Synthesize. Consensus (2+ models) is high signal. Lone findings still get read. Merge duplicates. Note disagreements.
5. Judge. You are the lead, not an aggregator. Filter with `references/lead-judgment.md`. Bucket every finding: Act on / Consider / Noted / Dismissed. Include which models raised it and one line why you bucketed it that way. Cap Act on at a handful. Show Dismissed so they can override you.

Output: Intent, Reviewers, the four buckets, then where the models agreed or split.
