---
name: architect
description: "Use for /architect, 'architect this', 'design this', a code change that adds or reshapes types, signatures or module boundaries, or to find what to restructure, consolidate or dedupe across a codebase."
---

# Architect

Sketch types, function signatures, class shapes, and module boundaries with `not implemented` bodies and pseudocode; choose among candidate sketches, then fill in code against the winner.

## Start

Open a `todo` list with one entry per phase: Ground, Sketch, Agree, Implement, Scrap.

When no change is named yet, run `references/survey.md` first. Start Phase A once the user picks a candidate.

## Phase A: Ground the problem

Build a traced model of every system the new code touches: run the **how** skill over those subsystems (critique mode when existing structure is the constraint), and the **why** skill on the existing shape when the design redefines ownership or layering. Naming a file isn't grounding. Skip only for greenfield work with no surrounding system.

Ground with `lsp` first (`definition`, `references`, `symbols`, `diagnostics`) where a language server covers the language, then structural search (`ast-grep` in `bash`, or the `ast_grep` tool when `astGrep.enabled` is on), and text `grep` last, for what those cannot see.

Write a grounding artifact in a sketch dir (a scratch directory outside the repo):

- **Facts with evidence.** A claimed constraint ("X must exist before Y") is a hypothesis until measured: list what depends on X or run the probe, and record the result. Where two designs both work, name each one's cost. On a resource-constrained target, measure the real limits and budget each new component from what remains.
- **The code's own identifiers** (function and flag names, `path:line`), never a paraphrase; runners drift a paraphrase until it matches nothing.
- **Numbered invariants**: every "X does not change" the user states, with the `path:line` citations that define X today, plus what the environment cannot do.
- **Scope boundary**: when the user limits the work to one subsystem, record it and repeat it in every runner task.

Before Phase B, triangulate direction from the binding direction docs, the executable product path, and the user's stated model: code wins on what the system does today, the user on what it should be, docs are a claim to reconcile. If they name different product shapes, stop and ask.

User pushback on a constraint or on the shape, in any phase, is Phase A evidence: re-ground instead of defending, then re-run Phase B before writing more code.

Read the matching section of `references/grounding.md` when the request changes product direction, direction sources conflict, two code paths compete for the product path, the design unifies duplicates, the ask is an audit, or a constraint arrives after dispatch.

Before sketching anything that charges, grants, revokes, deletes, or sends, build the writer census per `references/writer-census.md`; when it shows an invariant held by convention plus a repair helper, enforce it in the schema per `references/enforced-invariants.md`.

## Phase B: Sketch

Spawn two or more design runners in one `task` call: one `tasks[]` item per runner, with shared `context` carrying scope, constraints, output format and the grounding artifact's path. Each item's `task` names its lens and tells the runner to read `skill://architect/references/runner-prompt.md`. Each runner replies with one JSON object in the shape that file defines (`outputSchema` enforces it when `task.structured` is on), a design package per `references/rationale-template.md`; read its fields through `agent://<id>/<key>`. A runner that fails or returns nothing: follow `references/dispatch.md`.

Design it twice: require at least two structurally distinct candidates (whole shapes, not point fixes inside one shape) even when the first looks sufficient. Give each runner a distinct structural lens, e.g. enforcement vs ownership boundary, single-owner vs per-actor state, push vs pull; unlensed runners converge on a safe middle.

Before synthesis:

- Screen every candidate against `references/design-red-flags.md`; reject or revise what it flags.
- Spot-verify each mechanism a load-bearing tradeoff names against the live function that implements it.
- Recount from the source every number a candidate leans on, above all one that would become an assertion coupling two independently maintained lists. A runner's count is a self-report.
- Compare on interface depth: prefer the design that hides more complexity behind a smaller public surface.

Synthesis picks one candidate as the base and grafts only pieces that shrink or preserve the public surface; a merge that grows the surface means the base was wrong. Fill the rationale's "Synthesis decision" with the base, the grafts, and the specific red flag that lost each rejected candidate.

## Phase C: Agree (opt-in)

Default: proceed to implementation with the synthesized design, no human checkpoint. A request for only a design or plan ends after Phase B with the sketch and rationale.

Checkpoint only when the invoker asks ("/architect with checkpoint", "stop and show me before implementing", or similar): present the design per `references/checkpoint.md` and pause for sign-off before updating binding docs or writing code.

Either way the synthesis can ship as its own "scaffold first" commit; later commits fill in bodies. For adversarial pressure before implementing, run the **grill-me** skill on the sketch.

## Phase D: Implement against the sketch

Replace `not implemented` bodies with code and pseudocode with logic. The sketch is the contract: a deviation is signal to surface, not friction to absorb. If a function needs a parameter the sketch didn't anticipate, ask whether the sketch was wrong, a requirement was missed, or the implementation is overreaching. Planned, scoped breakage during fill-in is fine.

- If the repo has an equivalence gate (golden benchmark, `--check` diff, golden dataset), slice 1 is behavior-preserving code motion that passes it, done with `lsp` `rename` and `rename_file` (`ast_edit` with no language server), not text edits. The new shape lands only after the gate is green.
- Slice the rest by module boundary: one module or file set per slice, each proven by an end-to-end run of the real path it serves, with no unit or mock test files.
- Subagents write the code: one `task` item per slice, each owning a disjoint file list, or its own worktree through `isolated: true` when `task.isolation.enabled` is on. You review every diff and run the gates, per `references/dispatch.md`. Writing the implementation yourself is the deviation to justify.

## Phase E: Scrap when the architecture is wrong

When implementation keeps producing friction the sketch can't absorb, throw the sketch out instead of bolting fixes onto it. The signal is a pattern, not one instance: check every reviewed slice against "Signals to scrap (Phase E)" in `references/dispatch.md`.

When you scrap:

1. Re-run the **how** skill over what's been built, so its lessons feed the new design.
2. Redesign as if the new constraints had been day-one assumptions.
3. Subtract before adding: the new sketch starts smaller than the old one.
4. Return to Phase B and re-run the design runners.

## Outputs

- The sketch and its rationale: one file of new types and signatures for a small change; a module map plus type definitions for larger work.
- Diagrams: wherever the sketch or rationale explains architecture, ownership boundaries or state transitions, a labeled fenced `mermaid` block per `references/diagrams.md`.

Land the synthesis in the repo's own design/plans home, not the sketch dir. Register it wherever the repo indexes live plans, then check `git status`: an unindexed or untracked plan is not a landed contract.

When the user names a board, tracker or ticket system as the work's home, add one task per phase per `references/tracker-tasks.md`.
