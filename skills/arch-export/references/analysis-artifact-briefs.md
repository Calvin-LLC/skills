# Briefs about analytical artifacts (no runtime profile)

Use when the thing being reviewed is not a running service but a produced artifact: a
decompiled corpus, a generated dataset, a static-analysis pipeline, a scraped index. There are
no latency percentiles to quote, so the "Measurements" slot has to carry a different kind of
evidence and the brief has to defend its own coverage claims.

## Substituting the evidence slot

| service brief | artifact brief |
|---|---|
| p50/p95/p99 latency | coverage: entities processed / entities discovered, to 4 decimals |
| top-5 hotspots by % time | stages by wall cost, plus per-module cardinalities |
| QPS, allocation rate | artifact size (files, bytes, entries), edges/rows produced |
| error budget, SLO | retry yield, residual failure count, defect checks at zero |
| query plans | per-entity metadata header shape, index and edge records |

Take every number from the machine-readable summary the pipeline emitted (`SUMMARY.json`,
`VERIFY.json`, manifest), never from a prose report and never from memory. Recompute derived
percentages yourself and check the denominators: a ledger row count is not an entity count, and
quoting one as the other inflates coverage by a few percent.

## The honest-boundary section

Five parts, in this order. Each ends with the conclusion a consumer must not draw, because that
is the sentence an outside reviewer will otherwise supply on their own — wrongly.

1. **Coverage and failures.** Entities discovered, entities with a usable body, residual count.
   Break the residual into named failure classes with counts, say what a retry pass recovered
   (numerator and denominator), and state that nothing was synthesised for the survivors. Name
   the consequence: "present" and "analysed" are different predicates.
2. **Non-entities in the same index.** Rows that exist for address/coverage reasons but are not
   entities (tails, fragments, padding entries). Give the count, the reason they are retained,
   and what treating them as entities would inflate.
3. **Provenance tiers.** Name the tiers explicitly — measured fact, inference with confidence
   and evidence, placeholder for absence of evidence — and warn that all three share one
   namespace. Mixing tiers silently launders a guess into a fact.
4. **Scope.** What the pipeline did not do (no execution, no instrumentation, no dynamic trace).
   Redefine overloaded words: "reachable" means statically reachable; "caller" means a code
   reference. If a large fraction is unreachable, say the fraction and say the corpus still
   includes it — "we have the whole binary" is not "we have the code that runs".
5. **What validation proves, and what it does not.** List the checks and their zero-defect
   result, then state the bound: structural consistency is not semantic fidelity. If that would
   need differential recompilation or a dynamic comparison, say so and say it is out of scope.

Close with the consumer's read: "treat this as a high-coverage, structurally verified artifact,
not as ground truth about behaviour."

## Ask adaptation (Perplexity reviewer)

Keep the standard ask, then append: state the current best-known approach for each item with
citations from the last few years, and say explicitly where the state of the art still cannot
beat the residual failure classes. That second clause is what keeps the reply from proposing
solutions the artifact already established are impossible.

## Sanitization notes specific to artifact briefs

- Failure class names, mangled symbols, product names inside class labels and corpus paths are
  the leaks. Translate failure classes to plain descriptions ("bad stack-pointer model") and
  keep the mapping in `.arch/aliases.json` beside the role map.
- Version strings of the analysis tool are usually safe and useful to the reviewer; the subject's
  product name is not. Decide once and stay consistent for the whole brief.
- Numbers with distinctive values (a 4-decimal coverage figure, an exact byte count) can act as
  fingerprints. Keep them — they are the evidence — but never pair them with a path or a name.
