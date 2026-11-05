---
name: benchmark-checklist
description: "Vet a performance measurement (limiter, tuning, limits, errors, repeatability, relevance, whether the work ran) before reporting a speedup or regression. Use when you run a benchmark or report a number you measured."
disable-model-invocation: true
---

# Benchmark checklist

Use before you report any performance number: a before and after, a regression claim, a library or config choice. Answer each question from a run, not from reading the code.

A ballpark the user asked for needs one run plus questions 4 and 7, and a note that it was one run. A choice between options is never a ballpark.

## Before running

- Write the claim in the words you would ship ("export is 30% faster at p50 on the 60k-row dataset"). The questions test that sentence.
- Read the measurement script: what it times, counts and ignores.
- Check machine load and core count first (`uptime` and `nproc` on Linux, Task Manager or `Get-CimInstance Win32_Processor` on Windows). If the machine is busy and you cannot quiet it, interleave the sides and say so.

## Questions

1. **Why not double?** Name the limiter. Profile in a run you do not report, since profilers slow the work. Use per-process CPU, a runtime profiler (`perf`, `py-spy`, `node --cpu-prof`), I/O wait and syscall counts (`strace -c`), then map the hot spot to source. If the load generator saturates first, you measured the load generator.
2. **Was it tuned?** Run every side as production runs it: release builds, production flags, batching, pools, cache warmth, same versions and data. A limiter that is a setting (commit per row, debug build, missing index) means that side is untuned: tune it and measure again.
3. **Did it break limits?** Do the arithmetic against disk and network bandwidth, cores, and the share of time the changed piece takes. Removing a piece that is 10% of the run makes it at most about 11% faster. A result past a limit measured something other than the work.
4. **Did it error?** Count failures and non-success responses and check outputs are correct, not just present. Rejections are fast, timeouts and retries are slow.
5. **Does it reproduce?** At least 5 runs per side, alternating A B A B. Report median and range. A gap smaller than run-to-run variation is no measurable difference.
6. **Does it matter?** Measure the end-to-end path a user waits on and report the micro result as a share of the whole.
7. **Did it happen?** Confirm the work ran inside the timed region: the request arrived, the rows were written, the result was used. Lazy generators, unawaited promises and discarded results time nothing.

## Report

Lead with the verdict: faster, slower, no measurable difference, or inconclusive. Give the number, unit, run count, range and limiter ("p50 41 ms to 33 ms, median of 7 runs per side, range 32 to 35 ms, bound by JSON parsing on one core"). Call it inconclusive when you cannot name the limiter, a side ran untuned, or you could not check questions 4 and 7, and name the gap.
