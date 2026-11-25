---
name: diagnosing-bugs
description: "Diagnose a hard bug or performance regression by first building one command that reproduces the exact symptom. Use when something is broken, throwing, failing, flaky or slow and the cause is not obvious. Use how for how code works, why for history."
---

# Diagnosing bugs

The skill is Phase 1. With a command that goes red on this bug in seconds, every later phase is mechanical. Without one, reading code produces theories, not answers. No theory, no fix, and no production edit before that command exists.

This skill owns the debugging method for every bug. Two cases start in a poteto-mode playbook and return here with a cause: a live process that spins, leaks or glitches (`skill://poteto-mode/playbooks/runtime-forensics.md`), and a capture that already exists (`skill://poteto-mode/playbooks/trace-forensics.md`).

## Redact first

Every command, output and captured artifact you show has secrets replaced with `<REDACTED>`: auth headers, cookies, tokens, keys. Build loops against environment variables so the credential stays out of what you quote. Quote only the lines that carry the signal. Do this on HAR files and log dumps before they go in a report.

## Phase 1: build the loop

Pick the highest rung you can reach. Each runs the real system end to end:

1. A `curl` (PowerShell: `curl.exe`, since bare `curl` aliases `Invoke-WebRequest`) or HTTP script against the running service.
2. The real CLI on a fixture input, diffing stdout against a known-good capture.
3. A real page driven by `browser` in `eval` (JS cell: `const tab = await browser.open({ name, url })`), asserting on DOM, console or network.
4. A replay of a captured real request, payload or event log through the code path, run as an `eval` cell so the replay writes no file.
5. `git bisect run` when the bug appeared between two known states.
6. Old build versus new build on the same input, diffing outputs.
7. A fuzz loop of 1000 random inputs in an `eval` cell when the output is only sometimes wrong.

Tighten it: faster (cache setup, skip unrelated init), sharper (assert the specific symptom, not "did not crash"), more deterministic (pin time, seed RNG, isolate the filesystem). A 2-second deterministic loop is a superpower; a 30-second flaky one is barely better than none. For an intermittent bug, raise the reproduction rate (loop 100 times, add stress, narrow timing windows) until it is debuggable.

Phase 1 is done when you can name one command you already ran, showing invocation and redacted output, that is red-capable (asserts the user's exact symptom), deterministic, fast, and runs unattended. If you cannot build one, stop, list what you tried, and ask for access to the environment that reproduces it or a redacted captured artifact.

## Phase 2: reproduce and minimise

Run it and watch it go red. Confirm it shows the failure the user described, not a neighbouring one, and record the exact symptom. Then cut inputs, callers, config and steps one at a time, re-running after each cut, until every remaining element is load-bearing: removing any one turns the loop green.

## Phase 3: hypothesise

Write 3 to 5 ranked hypotheses before testing any. Each states its prediction: "if X is the cause, changing Y makes the bug disappear." A hypothesis without a prediction is a vibe; sharpen or drop it. Seed the list by diffing the broken path against a working sibling (similar code, the last good commit) and listing every difference. Then test them in rank order yourself. A run answers the question faster than a person can.

## Phase 4: instrument

One variable at a time, each probe tied to a prediction.

Start with the `debug` tool, which drives one DAP session and picks the adapter for the runtime (`lldb-dap`, `dlv` and `debugpy` are three of them). `launch` the Phase 1 command and confirm the reply says `Status: stopped`; when it says `running`, `pause` before anything else. `set_breakpoint` at the line or function the hypothesis names, with a `condition` when only one input fails, then `continue`. At the stop, read `stack_trace`, `scopes` and `variables`, check the prediction with `evaluate`, then `step_over`, `step_in` or `step_out` to the point where the state first goes wrong. `terminate` when done. Adapter setup, the exact replies to expect and what to do when it does not stop are in `references/debugger.md`.

Fall back to source logs when no debug adapter fits the runtime, the adapter will not start, or the fault only shows in a long-running or remote process. Keep the logs targeted. Tag every debug line with a unique prefix such as `[DEBUG-a4f2]` so cleanup is one grep.

When the failure crosses components (CI to build to deploy, API to service to database), log what enters and leaves each boundary in one run to find which boundary breaks, then dig into that one. For a performance regression, skip logs: record a baseline (timing harness, profiler, query plan), bisect, then fix, with the strategy families in `skill://poteto-mode/playbooks/perf-issue.md`.

## Phase 5: fix and prove

Fix the root cause. Prove it by re-running the Phase 1 command against the original, un-minimised scenario and showing it go from red to green, plus the neighbouring paths that share the flaw. Keep the proof as the loop script itself or in the final reply.

After three failed fixes, stop fixing. Each fix exposing a new problem elsewhere means the shared design is wrong, not the last hypothesis. Tell the user and discuss the design before a fourth attempt.

## Phase 6: clean up

- The Phase 1 command is green.
- A repo-wide search for the debug prefix returns zero hits.
- No debug session is left open (`debug` `sessions`).
- Throwaway prototypes are deleted.
- The commit message states the hypothesis that turned out right.
