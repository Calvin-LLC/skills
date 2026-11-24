# Mechanism hunts and cross-platform references

## "Mine reference X for mechanism Y" with no repo to improve

The target is the tree the mechanism will feed into. Read that tree's equivalent paths before the references, so every delta cites the target's own `file:line` instead of a claim from memory.

- Hunts often end in a negative. "No reference in the set does Y" is a result when Y is the target's design point: state it, then contrast the target's mechanism with the nearest reference behavior.
- For questions about what a platform guarantees, read the vendor's manual before the corpus. References show what practitioners do; the manual states what is permitted, and both belong in the verdict row.
- A reverse-engineering writeup is citable for behavior, not for code: quote it and name what it analysed; never invent line numbers for it. A writeup about another build is a cross-build comparison, so pin versions first.
- A mechanism-relevant file in a tree outside the hunt's mandate is recorded as "not examined, open first next round", not mined.
- When the reference ships an evaluator or benchmark, score the target with that evaluator's own code on the same inputs, and read what the evaluator itself excludes or distrusts. Say what was not run.
- A reference that produces data but has no way to act on it adopts at the planning layer only; state the layer in the verdict.
- When a term in the brief resolves to nothing in the target, state your assumed mapping in one line at the top of the report.
- When the reference's name collides with a common word, search for vocabulary only that project uses.
- Extract archives beside the archive, matching existing naming, and flag the side effect in the report.

## Reference and target on different platforms

Similarity is not portability. Each "portable" verdict must name the target-side field, flag, or code path it lands in. Grep the target's headers for that carrier before any adopt or adapt verdict; with no carrier, the verdict is defer with the missing carrier named.
