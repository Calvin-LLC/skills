---
name: architect
description: "Use for /architect, 'architect this', 'design this', a code change that adds or reshapes types, signatures or module boundaries, or to find what to restructure, consolidate or dedupe across a codebase."
---

# Architect

Sketch types, function signatures, class shapes, and module boundaries with `not implemented` bodies and pseudocode; choose among candidate sketches, then fill in code against the winner.

## Start

Open a todolist with one entry per phase: Ground, Sketch, Agree, Implement, Scrap.

When no change is named yet (what to restructure, consolidate, dedupe or simplify), run `references/survey.md` first. Start Phase A once the user picks a candidate.

## Phase A: Ground the problem

Build a traced model of every system the new code touches: run the **how** skill over those subsystems (critique mode when existing structure is the constraint), and the **why** skill on the existing shape when the design redefines ownership or layering. Naming a file isn't grounding. Skip only for greenfield work with no surrounding system.

Write a grounding artifact in a sketch dir (a scratch directory outside the repo):

- **Facts with evidence.** A claimed constraint ("X must exist before Y", "A cannot reach B", what the platform does) is a hypothesis until measured: grep what depends on X or run the probe, and record the result. Where two designs both work, name each one's cost. On a resource-constrained target, measure the real limits and budget each new component from what remains.
- **The code's own identifiers** (function and flag names, `path:line`), never a paraphrase; runners drift a paraphrase until it matches nothing.
- **Numbered invariants**: every "X does not change" the user states, with the `path:line` citations that define X today, plus what the environment cannot do.
- **Scope boundary**: when the user limits the work to one subsystem, record it and repeat it in every runner task.

Before Phase B, triangulate direction from the binding direction docs, the executable product path, and the user's stated model: code wins on what the system does today, the user on what it should be, docs are a claim to reconcile. If they name different product shapes, stop and ask; candidates built on a contested premise are wasted.

User pushback on a constraint or on the shape, in any phase, is Phase A evidence: re-ground instead of defending, then re-run Phase B before writing more code.

Read the matching section of `references/grounding.md` when the request changes product direction or replaces a documented one, the direction sources conflict or the direction doc holds no architecture, two code paths compete for "the product path", the design unifies duplicates into a shared library, the ask is an audit or clean state, or a new constraint arrives after runners are dispatched.

Before sketching anything that charges, grants, revokes, deletes, or sends, build the writer census per `references/writer-census.md`; when it shows an invariant held by convention plus a repair helper, enforce it in the schema per `references/enforced-invariants.md`.

## Phase B: Sketch

Spawn two or more design runners as subagents (respect your harness's per-call limit and batch the rest; with no subagent tool, run the candidates yourself in sequence). Runners start without your conversation: open each brief with scope, constraints and output format (the **swarm** skill's worker-contract block, if installed), pass `references/runner-prompt.md` as the prompt, and hand over the grounding artifact and templates as file paths in the sketch dir, not inline text. A runner that fails or returns nothing: follow `references/dispatch.md`.

Design it twice: require at least two structurally distinct candidates (whole shapes, not point fixes inside one shape) even when the first looks sufficient. State a distinct structural lens in each runner's task, e.g. enforcement vs ownership boundary, single-owner vs per-actor state, push vs pull; unlensed runners converge on a safe middle.

Each candidate is a design package per `references/rationale-template.md`: the caller's usage first, then the type sketch, signatures, module map and rationale derived from it.

Before synthesis:

- Screen every candidate against `references/design-red-flags.md`; reject or revise what it flags.
- Spot-verify each mechanism a load-bearing tradeoff names against the live function that implements it.
- Recount from the source every number a candidate leans on, above all one that would become an assertion coupling two independently maintained lists. A runner's count is a self-report.
- Compare on interface depth: prefer the design that hides more complexity behind a smaller public surface.

Synthesis picks one candidate as the base and grafts only pieces that shrink or preserve the public surface; a merge that grows the surface means the base was wrong. Fill the rationale's "Synthesis decision" with the base, the grafts, and the specific red flag that lost each rejected candidate.

## Phase C: Agree (opt-in)

Default: proceed directly to implementation with the synthesized design; no human checkpoint. A request for only a design or plan ends after Phase B with the sketch and rationale.

Checkpoint only when the invoker asks ("/architect with checkpoint", "stop and show me before implementing", "plan this out with me", "nail down the wanted behavior", or similar): present the design per `references/checkpoint.md` and pause for sign-off before updating binding docs or writing code.

Either way the synthesis can ship as its own "scaffold first" commit; later commits fill in bodies. For adversarial pressure before implementing, run the **grill-me** skill on the sketch.

## Phase D: Implement against the sketch

Replace `not implemented` bodies with code and pseudocode with logic. The sketch is the contract: a deviation is signal to surface, not friction to absorb. If a function needs a parameter the sketch didn't anticipate, ask whether the sketch was wrong, a requirement was missed, or the implementation is overreaching. Planned, scoped breakage during fill-in is fine.

- If the repo has an equivalence gate (golden benchmark, `--check` diff, golden dataset), slice 1 is behavior-preserving code motion that passes it; the new shape lands only after it is green.
- Slice the rest by module boundary: one module or file set per slice, each proven by an end-to-end run of the real path it serves, with no unit or mock test files.
- With subagents available, they write the code and you review every diff and run the gates, following `references/dispatch.md`. Writing the implementation yourself is the deviation to justify.

## Phase E: Scrap when the architecture is wrong

If implementation keeps producing friction the sketch can't absorb, throw the sketch out; don't bolt fixes onto a wrong design. The signal is a pattern, not a single instance:

- The same shape of workaround or Phase D deviation recurring across unrelated code.
- Unrelated edge cases that all need special-case branches.
- Types that need escape hatches (`any`, casts, optional fields always set in practice) to compile.
- The "we need a lock" reflex when the sketch said the state wasn't shared.
- Callers having to know the abstraction's internal rules to use it.
- Reviewers' critical findings clustering around coordination mechanisms (queues, handles, ownership handoffs) rather than logic: fold the mechanism into a single owner instead of patching each finding.

A few edge cases don't condemn an architecture; complexity in the data is not complexity in the design.

When you scrap:

1. Re-run the **how** skill over what's been built, so implementation lessons enter the new design as inputs.
2. Redesign as if the new constraints had been day-one assumptions.
3. Subtract before adding: the new sketch should be smaller than the old one before it grows.
4. Return to Phase B and re-run the design runners.

## Outputs

- The sketch, derived from the caller's usage: one file of new types and signatures for a small change; a module map plus type definitions for larger work.
- The rationale, in the same template.
- Diagrams: wherever the sketch or rationale proposes or explains architecture, ownership boundaries or state transitions, a labeled fenced `mermaid` block per `references/diagrams.md`.

Land the synthesis in the repo's own design/plans home (check the convention), not the sketch dir. Register it wherever the repo indexes live plans, then check `git status`: an unindexed or untracked plan is not a landed contract.

When the user names a board, tracker or ticket system as the home for the work, one task per phase is part of the deliverable: follow `references/tracker-tasks.md`.
