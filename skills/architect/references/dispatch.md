# Dispatching implementation slices

Phase D rules for filling in the sketch through subagents. Children write the code; you scope the slices, review every diff and run the validation gates.

- **Size each slice to one child's budget.** An oversized slice ends mid-edit with call sites still pointing at whatever the child deleted.
- **Settle cross-slice interfaces first.** Decide who owns a call, who narrates it, and which error class crosses a boundary in the dispatch text before parallel slices write against it. Otherwise each slice implements its own reading and the merged code does both (doubled narration, double writes).
- **Parallelize only over disjoint file sets.** While an interface is still moving, sequence instead.
- **Verify before building on a slice.** A child's summary is a self-report: build the combined result, grep for call sites of deleted functions, import the modules, and check the output of a few concrete calls by hand. Keep throwaway check programs in the sketch dir, not the repo.
- **Budget constrained resources per slice.** On a resource-constrained target, put each slice's budget from the plan in its dispatch and check the sum on the full build, on the real target, before the next slice builds on it: per-slice builds pass while the combined one overflows. Fix an overflow by shrinking state, not by relocating it.
- **One shared device, one operator.** When variants must be measured on shared hardware, record the baseline first, have children build only, and run each variant yourself, one at a time, with a known-good build ready to restore.
- **Finish capped children with their own list.** When a child stops incomplete and names what remains, dispatch a finisher whose spec is that exact list; it is cheaper and more accurate than re-deriving the work.

## When a design runner fails (Phase B)

If a Phase B runner dies, times out, or returns nothing (check that its output files exist, not only that it reported done), rerun it once with a narrower brief: one lens, a smaller output, the same grounding artifact. If the rerun also fails, proceed with the surviving candidates and say in the synthesis which runner is missing and which lens went unexplored. Still require two structurally distinct candidates; if only one survives, write the second yourself from the unexplored lens.
