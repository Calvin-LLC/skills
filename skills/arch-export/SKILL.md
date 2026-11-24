---
name: arch-export
description: Use for /arch-export or to get an outside model (Perplexity, ChatGPT, Claude) with no repo access to review a design, a defect or a planned fix. Writes a sanitized brief to paste; the reply comes back through arch-import.
author: Calvin-LLC
license: MIT
metadata:
  hermes:
    tags: [architecture, review, sanitization]
    related_skills: [arch-import]
---

# Arch export

Produce, locally, a sanitized, evidence-backed brief an outside model can review with no repo access.

The deliverable is the brief. When the ask reads like a fix or debug request, write the brief about that problem. Gather only the evidence the brief needs. Do not fix, debug or edit the subject in the same turn unless the user asks for that separately.

## Rules

- **No leaks.** No source code, identifiers, paths, URLs, string literals, schema field names, or business logic. Pseudocode only, with generic, underscore-free names. Structural bounds (buffer sizes, entry caps, record widths) and measured sizes are required evidence, not leaks; the banned literals are tree constants: magic values, offsets, signatures, hardcoded addresses. Hardware by capability (year class, capacity), never vendor or model.
- **Your own artifacts leak too.** Never name a sibling brief, the `.arch/` path or the alias-map file in the brief; write "a companion brief covers the rest" and "the alias map is kept separately".
- **Roles instead of names.** `OrderService` becomes `Component A (write-heavy aggregator)`. Keep the alias map local and never emit it: keys are role names, values the real file/symbol names that translate the reply back. Phrase role lines differently from the values, or the alias check fails on your own prose.
- **Measure before writing; never estimate a number.** Every claim carries a measurement or the label "hypothesis". Recompute every derived percentage.
- **Fix the brief, never loosen the redaction.** Advice that doesn't fit usually means the data shape was described wrong. A distinctive algorithm or domain rule is itself sensitive: generalize it to its complexity-relevant shape.

## Before measuring

- **Is the target reachable?** When the ask is "get to N nines / under X ms / below Y% error", first measure whether any algorithm can reach it, over the whole input space, not a sample. If the floor rules the target out, the deliverable is that measurement and a re-aimed metric, not a brief: `references/reachability-gate.md`.
- **Scope.** A run scoped to one subsystem covers that slice; other components get one context line each.
- **Mine prior work** on the target: session-history search, the repo's docs and findings files, leftover probe scripts. A prior audit's numbers are the strongest evidence; an ask that never landed is open work for Pain. Numbers whose suites or artifacts are gone from the tree are history: cite them labeled unauditable and list the absence under Pain.

## Steps

1. **Stack:** languages, frameworks, datastores, runtime, deployment shape, with versions.
2. **Topology:** components by role, sync/async edges, data flow, concurrency model, failure handling.
3. **Data shape, not data:** per hot structure give cardinality, growth, key distribution (uniform or skewed), value size, R/W ratio, access pattern, ordering or locality.
4. **Algorithms:** per hot path give pseudocode steps, big-O, input size N, measured cost.
5. **Evidence:** top 5 hotspots, anonymized: % time, call counts, p50/p95/p99, allocations, query counts and plan shapes. With no runtime profile (offline corpus, static analysis, generated artifact, docs question) the slot takes coverage, cardinalities, defect counts, retry yield and a failure taxonomy: read `references/analysis-artifact-briefs.md`, which also structures step 8.
6. **Constraints:** latency and memory budget, hardware, consistency needs, non-goals ("no new infra unless measured").
7. **Pain:** what is slow, flaky, or hard to change, with symptoms.
8. **Honest boundary:** what is claimed versus not: which numbers are measured and which are inference (fact / inference / placeholder), failures (count per class, what retry recovered, what survived), scope limits, what the validation proves versus assumes. Each item ends with the conclusion a consumer must not draw.
9. **Leak check.** Build a token file, one token per line: curated domain vocabulary, each identifier whole, plus every alias-map value; curation and triage in `references/leak-check.md`. Run `scripts/leak_check.py` from this skill's folder: `python <skill folder>/scripts/leak_check.py --draft <brief> --tokens <tokens> --aliases <aliases.json> --hits-out <hits.txt>`. On FAIL, classify each hit. A real leak: reword the draft. Noise: add a `hit<TAB>reason` line to a noise file and pass it with `--noise`. Alias-value and own-artifact hits are never noise. Re-run with `--baseline <previous hits file>` until PASS. ERROR means the sweep is broken, not that the draft is clean.
10. **Emit.** List `.arch/` first. Default files are `.arch/brief.md` and `.arch/aliases.json`; when another session owns them, write `brief-<topic>.md` / `aliases-<topic>.json` instead. Create the alias map with a no-clobber write. Write the brief from the template with the Ask appended verbatim. When missing, add `.arch/` to the ignore file of every git root that can see it: the alias map must never reach a remote. For a targeted ask (fix these defects, a mechanism or detection question, hardware or placement), put a scope paragraph above the verbatim block naming the items and the option space to enumerate; section shapes: `references/brief-variants.md`.

## Brief template

```markdown
## Stack and runtime
## Topology (components by role, edges, concurrency)
## Hot data structures (table: role, cardinality, growth, distribution, R/W, access)
## Hot algorithms (role, pseudocode, complexity, N, measured cost)
## Measurements (anonymized)
## Honest boundary — what is claimed, and what is not
## Constraints and non-goals
## Pain points
## Ask (verbatim to the reviewer)
```

## The ask

Append verbatim to the bottom of every brief:

```markdown
You have no repo access. Work only from this brief.
1. For each hot algorithm/structure: list every known alternative (including approximate, amortized, batched, SIMD/bitset, and reductions to classic problems) with complexity, constants, cache behavior, and the input regimes where it wins or loses. Flag any assumption you're making about my data.
2. Rank by expected gain / effort. Cite the measurement each gain would address.
3. Architectural changes: only those justified by the measurements. Name what to measure first if the evidence is insufficient.
4. For each recommendation, give: pseudocode, the invariants to preserve, a differential test idea, and what benchmark would prove it.
5. Reply as a table (id, target role, change, expected gain, risk, test, benchmark), then notes.
Do not ask for code. Do not suggest new infrastructure without a measured reason.
```

For a search-capable reviewer (e.g. Perplexity), also append verbatim: `(For this run: survey the current best-known tools/libraries/approaches per area — searches allowed; cite benchmarks or specs where they exist, and flag quality/latency tradeoffs.)`

## Hand-off

The brief leaves by the user's paste: never deliver or post it yourself. Done when you have stated, in plain words:

- the brief's path and the alias-map path, and the leak-check outcome with each hit classified;
- that the brief passed the leak check, names nothing beyond its listed deliberate retentions, and can be pasted into an ordinary account (retention settings are not a gate);
- that the reply comes back through the **arch-import** skill;
- for a fix or debug ask, that nothing was changed.

When the user asks for a headless run ("to an opus session") or to compare reviewers, or a reviewer refuses or the user cannot use the named one, read `references/reviewers.md`.
