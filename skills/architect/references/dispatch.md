# Dispatching implementation slices

Phase D rules for filling in the sketch through `task` subagents. Children write the code; you scope the slices, review every diff and run the validation gates.

- **One `task` call, one item per slice.** Shared `context` carries the sketch, the settled cross-slice interfaces and the gates. Each item's `task` names the slice's file list and its end-to-end proof. Results deliver on their own; `wait` blocks until they do.
- **Size each slice to one child's budget.** An oversized slice ends mid-edit with call sites still pointing at whatever the child deleted.
- **Settle cross-slice interfaces first.** Decide who owns a call, who narrates it, and which error class crosses a boundary in the dispatch text before parallel slices write against it. Otherwise each slice implements its own reading and the merged code does both (doubled narration, double writes).
- **Parallelize only over disjoint file sets.** Every slice works in the one checkout and edits only the files its item lists. When `task.isolation.enabled` is on, `isolated: true` on an item gives that slice its own worktree and merges its changes back as a patch (kept unapplied when `task.isolation.apply` is off). While an interface is still moving, sequence instead.
- **Rename and move before you dispatch.** `lsp` `rename` and `rename_file` rewrite call sites and imports in files that other slices own, so run them yourself first. Put the `path:line` call sites from `lsp` `references` in each slice's `task`.
- **Verify before building on a slice.** A child's summary is a self-report: build the combined result, run `lsp` `references` on each deleted function and `diagnostics` on the touched files, import the modules, and check the output of a few concrete calls by hand. Keep throwaway check programs in the sketch dir, not the repo.
- **Budget constrained resources per slice.** On a resource-constrained target, put each slice's budget from the plan in its dispatch and check the sum on the full build, on the real target, before the next slice builds on it: per-slice builds pass while the combined one overflows. Fix an overflow by shrinking state, not by relocating it.
- **One shared device, one operator.** When variants must be measured on shared hardware, record the baseline first, have children build only, and run each variant yourself, one at a time, with a known-good build ready to restore.
- **Finish capped children with their own list.** When a child stops incomplete and names what remains, dispatch a finisher `task` item whose spec is that exact list; it is cheaper and more accurate than re-deriving the work.

## When a design runner fails (Phase B)

If a Phase B runner dies, times out, or returns nothing (check that `agent://<id>/type_sketch` and `agent://<id>/rationale` read back, not only that it reported done; a reply that is not valid JSON is read whole at `agent://<id>`), rerun it once as a single `task` item with a narrower brief: one lens, a smaller output, the same grounding artifact. If the rerun also fails, proceed with the surviving candidates and say in the synthesis which runner is missing and which lens went unexplored. Still require two structurally distinct candidates; if only one survives, write the second yourself from the unexplored lens.

## Signals to scrap (Phase E)

Check each reviewed slice for these. One instance is noise, and a few edge cases don't condemn an architecture: complexity in the data is not complexity in the design. The same signal across unrelated slices means the sketch is wrong, and Phase E in SKILL.md applies.

- The same shape of workaround or Phase D deviation recurs across unrelated code.
- Unrelated edge cases all need special-case branches.
- Types need escape hatches (`any`, casts, optional fields always set in practice) to compile.
- Someone reaches for a lock where the sketch said the state wasn't shared.
- Callers have to know the abstraction's internal rules to use it.
- Reviewers' critical findings cluster around coordination mechanisms (queues, handles, ownership handoffs) rather than logic. Fold the mechanism into a single owner instead of patching each finding.
