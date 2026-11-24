# Driving the plan from a board or tracker

A plan whose phases live only in a document is not tracked. When the user names a board, tracker, or ticket system as the home for the work, one task per phase is the deliverable: the document is the contract, the board is how it gets driven and how the user follows along.

- **Create tasks in the board's own read order** (ground, build, prove, measure, re-measure for reliability) and put the phase id in each title so the doc and the board cross-reference without a lookup.
- **Carry one measurement into each task's first comment.** "Prove X" invites re-litigating whether X is already done; a comment quoting what was actually observed (the grep result, the count, the failing status code) starts the worker from evidence. If nothing was measured, say that instead of implying the task is scoped from data you never gathered.
- **State the blocker edge explicitly.** If phase N cannot start before phase N-1 lands, say so in the task text: priorities sort a column, and only prose says what cannot start.
- **Mark the blocking phase as such and start there.** When one phase is a prerequisite for the rest, tell the user plainly and offer it as the next action rather than ending on the full list.
- **Correct the board when the doc was wrong.** If the plan document and a task description disagree on a number, fix the task and say which one is authoritative; a stale tracker entry reads as recorded fact to the next session.
