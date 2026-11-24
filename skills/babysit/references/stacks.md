# Stacks in a merge queue

Read when the babysat PR belongs to a stack that drains through a merge queue. Step numbers refer to `SKILL.md`.

- **Queued mode never reaches `READY`.** A blocker-free frontier is a non-terminal `WAITING` with reason `merge-queue`. Report that frontier merge-ready and stop the loop. Do not leave it running until merges happen; that is the landing job. If another actor merges the frontier (`ADVANCE`), continue with the new frontier. `COMPLETE` is also terminal if another actor finishes the queue.
- **Stop verdicts.** Only an explicit stop ends the loop before the stop verdict: `READY` in single or stack mode, or a `WAITING`/`merge-queue` report (or `COMPLETE`) in queued mode.
- **Freeze the queue list.** Capture the PR list bottom-to-top once and pass the same frozen list to every loop re-arm. Rediscovering the stack after a parent merges can lose retargeted descendants. Revise the list only for the sanctioned follow-up PR from step 4: append it at the end, drop the merged owner, and re-arm with the corrected snapshot. Step 4 creates that PR on top of the stack, so it merges last.
- **Merge-when-ready hazards.** A stacked PR whose parent has no required checks may merge immediately into that parent when merge-when-ready is armed. This collapses review granularity. A lost-ref race can also mark it merged without updating the parent ref.
