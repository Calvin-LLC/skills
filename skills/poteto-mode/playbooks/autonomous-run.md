### Autonomous run

**You own the exit condition. Define done, then drive to it without stopping.**

1. State the exit condition as a checkable predicate before the first iteration (tests green, repro fixed, N commits on `main`, pixel-diff zero). A vague goal stalls; a predicate lets you stop.
2. Drive it under mitsupi's `/loop`. `/loop tests` until tests pass, `/loop custom <predicate>` for anything else, `/loop self` when you own done. Each turn ends, the extension injects the same prompt as a follow-up. Stop only by calling `signal_loop_success` when the predicate is true. There is no event watcher and no heartbeat. Do not invent a second sleep loop.
3. Each iteration makes the smallest change the evidence justifies, verifies it against the predicate, commits if it advanced, discards changes that didn't help. Belt-and-suspenders that "might help" gets reverted, not left to ride.
   Verify each unit before the next instead of batching checks at the end.
4. Mid-run discoveries are yours. Address broken skills, related bugs, flaky verifiers, review noise, tooling failures, orphaned follow-ups, and fixable drift yourself via poteto-mode. Put out-of-band fixes in their own commit on `main`. Do not park reversible work for the human. Questions go through **grill-me**; skip them when the pick is already clear. Keep the predicate as the main drive, and return to it after each side fix.
5. Checkpoint every iteration via the **show-me-your-work** skill, a row for what changed and whether the predicate moved. A run with no trail can't be audited or resumed.
6. Stop when the predicate is met. A plateau is not a stop, so keep going and pivot your approach to push past it. Surface a genuine dead end rather than spinning, and never relax the predicate to declare victory.

**Reply:** the exit condition, iterations run, what landed, what was discarded, final predicate state.
