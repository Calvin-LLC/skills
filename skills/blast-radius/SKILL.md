---
name: blast-radius
description: "Find what a change could break outside the diff and prove the one fact it is safe because of by running real code. Use for 'blast radius of X', 'what could this break', or a small diff you do not trust. Use how for what code does, why for motivation."
disable-model-invocation: true
---

# Blast radius

Companion to `how` and `why`. `how` says what the code does, `why` says why it is shaped that way, blast radius says what it breaks somewhere else. Listing callers is a one-second grep and is not the job. The job is the breakage grep will not show.

## Do not trust your own writeup

A blast-radius writeup that sounds right is worthless, because it reads the same whether or not it is true. Find the one or two facts the whole change depends on and prove them by running code.

For each such fact, get it as far down this ladder as is cheap and say where it stopped:

1. You said so. Worthless alone.
2. You pointed at the line: a real `file:line`, or the library's own source.
3. You walked the failure step by step and it does not reach.
4. You ran it: a script that calls the real code and fails loudly if you are wrong.
5. You reproduced it in the running app.

Step 4 is usually one small script that imports the library the app ships and calls the exact function you worry about.

## Steps

1. Read the change: the diff, the symbols it adds, changes and deletes, and what it now does differently, including what the diff does not spell out. Pull the PR and commits with `why`.
2. Find the one fact it is safe because of (for example "this call only drops already-dead cache entries"). If it holds, most risky cases clear at once. Spend your time here, not on a long list of maybes.
3. Look where grep stops. Read the source of the library you call, its pinned version and any local patch. Work out when things run (microtasks, unmount and teardown). Follow what symbol search misses: JSON an API returns, a DB column, a wire format another language reads, a feature flag, code three hops downstream.
4. Give each risk a real chance and a real cost. Cite a real `file:line`; a search that finds nothing is still an answer; never invent a caller or an API.
5. Prove the one fact: write a script that runs the real code, run it, paste the output.
6. For a wide change, ask more than one model the same question through `arena` and merge the answers.

## Hand back

- What it does, including the non-obvious part.
- The one fact it is safe because of, the ladder step reached, and the proof. Write `unproven` if you could not prove it.
- Risks: how it breaks, `file:line`, likelihood, cost, how to check.
- Cleared: what you checked and why it is fine.
- Before you merge: the cheapest repro that catches the real bug, including your script.
