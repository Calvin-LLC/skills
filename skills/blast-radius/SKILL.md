---
name: blast-radius
description: "Find what a change could break outside the diff and prove the one fact it is safe because of by running real code. Use for 'blast radius of X', 'what could this break', or a small diff you do not trust. Use how for what code does, why for motivation."
---

# Blast radius

Companion to `how` and `why`. `how` says what the code does, `why` says why it is shaped that way, blast radius says what it breaks somewhere else. Listing callers is a one-second grep and is not the job. The job is the breakage grep will not show.

## Do not trust your own writeup

A blast-radius writeup that sounds right is worthless, because it reads the same whether or not it is true. Find the one or two facts the whole change depends on and prove them by running code.

For each such fact, get it as far down this ladder as is cheap and say where it stopped:

1. You said so. Worthless alone.
2. You pointed at the line: a real `file:line`, or the library's own source.
3. You walked the failure step by step and it does not reach.
4. You ran it: code that calls the real code and fails loudly if you are wrong.
5. You reproduced it in the running app.

Step 4 is usually one small `eval` cell that imports the library the app ships and calls the exact function you worry about.

## Steps

1. Read the change: the diff, the symbols it adds, changes and deletes, and what it now does differently, including what the diff does not spell out. Pull the PR and commits with `why`.
2. Find the one fact it is safe because of (for example "this call only drops already-dead cache entries"). If it holds, most risky cases clear at once. Spend your time here, not on a long list of maybes.
3. Look where grep stops, with the narrowest tool that answers:
   - `lsp` for exact answers. `references` lists every caller of a changed symbol. `definition` lands in the dependency's own code, so read the source of the library you call there, at its pinned version, with any local patch.
   - Structural search for call shapes and patterns the language server cannot answer (every call passing a given argument, every `await` inside a loop): `ast-grep run -p '<pattern>' -l <lang> <path>` in `bash`, or the `ast_grep` tool when `astGrep.enabled` is on.
   - `grep` only for what neither sees: strings, config, dynamic dispatch by name.

   Work out when things run (microtasks, unmount and teardown). Follow what symbol search misses: JSON an API returns, a DB column, a wire format another language reads, a feature flag, code three hops downstream. Search history for the commit that introduced each deleted or rewritten line (`git log -S<symbol>`): code a fix added encodes a past failure, and removing it, or re-adding what an earlier commit dropped, brings the bug back. Name changed lines no test runs.
4. Give each risk a real chance and a real cost. Cite a real `file:line`; a search that finds nothing is still an answer; never invent a caller or an API.
5. Prove the one fact in `eval`, writing no file: a Python or JS cell that runs the real code, exercises the suspected breakage and prints the result. Paste the output.
6. For a wide change, ask more than one model the same question with one `task` call. Put the diff and the blast-radius question in the shared `context`, and add one `tasks[]` item per worker, each a default worker (no `agent`). For different models, set `model` on each item when `task.perCallModel` is on, or use custom agents whose `model:` lines differ. With neither, every worker runs on one model: spawn one and say model diversity was unavailable. Tell each worker to reply with one JSON object and nothing else (`risks`, each with `file:line`, likelihood and cost, plus `cleared`). Read the findings through `agent://<id>/<key>`, or `agent://<id>` whole when the reply is not valid JSON, and reconcile the disagreements yourself: a risk only one worker found gets checked against the code, not outvoted.

## Hand back

- What it does, including the non-obvious part.
- The one fact it is safe because of, the ladder step reached, and the proof. Write `unproven` if you could not prove it.
- Risks: how it breaks, `file:line`, likelihood, cost, how to check.
- Cleared: what you checked and why it is fine.
- Before you merge: the cheapest repro that catches the real bug, including your `eval` cell.
