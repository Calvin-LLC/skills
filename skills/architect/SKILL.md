---
name: architect
description: "Sketch types, signatures, and module structure before code, then stay in the loop while implementation fills in. Use for /architect, 'architect this', 'design this', or non-trivial work where jumping to code would lock in the wrong shape."
disable-model-invocation: true
---

# Architect

Sketch types, function signatures, class shapes, and module boundaries with `not implemented` bodies and pseudocode. Synthesize across multiple model perspectives, then fill in code against the chosen sketch.

## Start

Open a todolist with one entry per phase before starting.

1. Ground
2. Sketch
3. Agree
4. Implement
5. Scrap

## Phase A: Ground the problem

Build a real mental model of every system the new code touches. Run the **how** skill over the relevant subsystems. Critique mode if existing structure is the constraint or the design must push back on it.

Naming a file isn't grounding. Produce the traced model `how` prescribes. If the design redefines ownership or layering, also run the **why** skill on the existing shape so the rationale becomes a constraint, not a guess.

When the request changes product direction, separate the user's wanted behavior from inherited roadmap gates before sketching. For every inherited gate, verify whether code or finite resources enforce it, whether it is only documented, and whether the new direction keeps, deletes, or defers it. A documented target is not a design constraint until that check is done.

Treat every "X must exist before Y" and "process A cannot reach B" claim the same way: it is a hypothesis until measured. Start order, supervisor priority and the unix user a process runs as are configuration, and a design that cites them as a reason has not grounded anything. Before a constraint enters the plan, name what actually depends on X (grep the callers, read the entrypoint order) or run the probe (a write as the other user, a cold start), and record the result as a fact with its evidence. When the user pushes back on a stated constraint, re-ground it instead of defending it: the correction is Phase A evidence, and the plan's fact table changes before any sketch does. Where two designs both work, say so and name the cost of each, so the user decides on cost and not on an invented necessity.

Triangulate direction from three sources before Phase B: the binding direction docs (AGENTS.md / product architecture), the executable product path in code, and the user's stated current model. They answer different questions — code wins on what the system does today, the user wins on what it should be, docs are a claim to reconcile. Check what the named direction file actually contains before treating it as binding: a repo's `AGENTS.md` is frequently a voice-and-conduct card with no product architecture in it, and reading it for direction yields nothing — when that is all it holds, the binding direction is the plan docs, the README, or the executable path, and the artifact should say which one you used. If the three name different product shapes, stop: the contradiction is the first agree question, not grounding flavor. A decision list inside a plan does not reopen a fork the binding docs already settle. Adopt the option that implements the binding doc, log it as a standing decision, and reserve human gates for choices the docs leave open or irreversible writes the docs do not authorize. Never hand runners a premise one source contests and another forbids; candidates built on a contested shape are wasted whole, including the ones slated to lose — a "loser" candidate that matches the user's actual model means Phase A, not the runner, was wrong.

When two executable paths compete for "the product path," settle which one is live before sketching: grep the artifacts that have actually run (payloads, fixtures, proven configs) for each candidate's contract markers — the metadata it requires, the exports it looks up, the flags it reads. A path whose required contract no artifact in the tree satisfies is dead by construction, not an alternative, and a name that sounds like the binding doc's vocabulary is not evidence it implements the doc. Attribute defects to the exact flow, too: a banned behavior often lives in a separate verb beside the install flow, not inside it — grounding that blames the flow for the verb's sins recommends the wrong survivor.

When the design unifies duplicate client stacks into one shared library or SDK, ground it as a merge, not a pick. Diff the declared surfaces both ways (each copy holds functions the others lack, and that two-way drift is the requirements list); census per-function call sites in every consumer so the unified surface is the union actually called, shaped by how the old client was used, not by the header alone; build the chosen base against the current shared ABI before offering it as a candidate — a clean typed layer that references an opcode or contract since deleted is unbuildable, not a candidate; and hash every copy of the shared definitions to find which copies actually diverged (the base may already include the shared one, leaving a third copy elsewhere as the only single-sourcing work). Split the library by consumer runtime up front: code that freestanding consumers link carries no CRT or OS-runtime dependency, hosted consumers get the rest, and that split is drawn in the sketch, not discovered at link time. Port the layer first under its old public names, signatures, and globals so each consumer move collapses to include-path and translation-unit edits; rename only in a consumer unit, if at all. Route a global-state old layer through the typed layer's existing default-session singleton instead of inventing new global accessors, and turn app-specific log calls into a library-declared function the consumer defines — the library owns no sink. When the typed layer collapses two old return codes into one status, name the lost distinction as an accepted capability gap with a named closing unit; the port unit never invents a channel to recover it. A move unit does not restyle ported bodies to meet the new target's warning bar: compile the ported target without warnings-as-errors on purpose and record the warning count instead.

When the shared layer is header-only code that names host globals (a config vector, a host mutex, a project-defined flag function, enum slots), do not stub those symbols in each consumer. Pass a small binding struct to the library's entry point: values (counts, flags) plus one function pointer for the write the host must perform under its own lock. The library copies the struct into a private slot before spawning its worker thread (thread creation orders the write), compares against its own last-applied copy, and never takes the host's lock. Store the post-callback values as the compare base, or a host-side clamp makes every poll look like a change. A static-library alternative must first check what the header-only layout was providing implicitly (macros arriving through the host's precompiled header): a move that silently drops protection macros in an unrelated file is worse than the coupling it removes. Prove the boundary with an isolation compile of the public header alone, kept as a script in the library folder.

Skip Phase A only when the work is genuinely greenfield with no surrounding system to integrate.

### Effects that leave the codebase

Before sketching anything that charges, grants, revokes, deletes, or sends, build
the writer census. List every code path that mutates the same authoritative
state, quote each one's predicate for doing so with `path:line`, and diff those
predicates against each other. The divergences are the design's real
requirements, and collapsing them into one owner is the sketch — not a follow-up
cleanup task.

- A duplicated stack is visible because someone decides to unify it. A duplicated
  *effect* is invisible: each new caller looks like a fresh feature, so the fourth
  copy of "grant the subscription" gets written by someone who never saw the
  third. Grounding by reading the neighbourhood of the new code will not find it.
- Grep for the state, not the feature: the column name, the table, the external
  identifier. Every writer names the same thing, whatever it calls the verb.
- Record what each writer reads the *same* input to mean. Two paths that agree on
  "paid" but disagree on which units a money field holds, on a lifetime order, or
  on whether a partial payment counts are already broken against each other, and
  one has been silently winning.
- Name the reconciliation source: the external system that knows the truth, the
  field that keys back to it, and what a disagreement should look like. A design
  with no reconciliation step cannot tell success from silence.
- A safety path (cron, retry worker, backfill) that has never run is not a safety
  path. Check it executed at least once in production. A fatal `require` at the
  top of a cron turns it into a no-op that reports nothing forever, and its
  presence on disk reads as coverage.

- **The owner can be the storage engine, not a module.** When the census shows an
  invariant held by convention across many writers plus a helper that checks and
  repairs it on every request, the repair *is* the defect — two requests interleaving
  through its clear-then-set window put the duplicate back. Enforce it in the schema
  and every writer stays untouched, including one written next year that never learns
  the constraint exists. Recipe, DDL and the measurement to run before shipping:
  `references/enforced-invariants.md`.

When the ask is an audit or a clean state before any other work, Phase A *is* the audit, run the same way: the orchestrator writes a quality-bar artifact first (derived from the user's named bar plus the binding docs, as numbered checks a reviewer can grade against), explorers stay read-only and each writes its full report to a named file with `path:line` citations per check, and chat summaries are rollups only. Verify each report file exists on disk and spot-check its load-bearing citations before synthesis — a summary without its file is a claim, not a finding. When several same-named bar files exist (e.g. multiple `SOUL.md` copies), resolve which one is active before dispatching and put that resolution in the grounding artifact; a stale copy found first is itself a finding, never the bar. Batch explorers at the delegation concurrency cap and dispatch the overflow in the next batch; while they run, the orchestrator runs the host-safe gates itself (path checks, generated-map checks, pin/hash checks) rather than delegating verdicts it can read directly. A compile that passes on the wrong toolset does not clear a pinned baseline — report "builds on X" and "documented build blocked because Y" as separate lines. Never run a built product binary to classify or probe it when the repo bans host execution; classify binaries from their project files. Write grounding artifacts with the file tools, not shell heredocs — quotes and backslashes in paths break heredocs silently. Pin `workdir` or absolute script paths on every gate command: the terminal keeps its directory between calls, so a relative gate path quietly resolves into the wrong tree.

When the user scopes the work to one subsystem and hands siblings to another session, write that boundary into the Phase A artifact and repeat it in every runner task. A design that reaches into the sibling subsystem is out of scope even when the code invites it.

## Phase B: Sketch

Spawn two or more design runners via `task` (one `tasks` entry each) with the design-sketch task and the Phase A grounding artifacts. Runners receive no `SOUL.md`; open each `context` with the block in the swarm skill's `references/worker-contract.md`. Pass `references/runner-prompt.md` as each runner's prompt. They run on the `delegation.model` pin, or the parent's model if none is set. Each candidate produces a design package shaped per `references/rationale-template.md`: the caller's usage written first, then the type sketch, function signatures, module map, and prose rationale derived from it.

Design it twice. Require at least two structurally distinct candidates before synthesis, even when the first looks sufficient. Whole-shape alternatives, not point fixes inside one shape. Give each runner a distinct structural lens — enforcement boundary vs ownership boundary, single-owner vs per-actor state, push vs pull — and state it in its task. Unlensed runners converge on a safe middle, which defeats the exploration.

Write the Phase A traced model and the reference templates into the sketch dir and hand runners file paths, not inline text: they reread the artifacts while working, and the files must outlive the dispatch.

Name mechanisms in the grounding artifact with the code's own identifiers (flag and function names, file:line), never a paraphrase. Runners inherit the paraphrase and drift it further, and a mechanism renamed twice no longer matches any function in the tree. Before presenting a candidate's load-bearing tradeoff to the user, spot-verify each named mechanism against the live function that implements it — a candidate can be internally coherent around a function that does something else.

Recount every number a candidate leans on before adopting it, especially when the recommendation is to add an assertion coupling two independently maintained lists (a `static_assert` on an array length, a schema or key-count check, a parity test). A runner's count is a self-report and can be wrong in either direction; a wrong count becomes an assertion that fails the build or, worse, one that passes while the lists disagree. Derive the number yourself from the source — parse the literal, count the emitted entries — and state the derivation in the synthesis so the assertion has a provenance. Treat a matching count as a finding to confirm, not as confirmation.

Screen every candidate against [`references/design-red-flags.md`](references/design-red-flags.md) before synthesis. Reject or revise shallow modules, information leakage, temporal decomposition, and pass-through methods.

Compare viable candidates on interface depth. Prefer the design that hides more complexity behind a smaller, simpler public surface. A rich interface can keep call chains short by concentrating capability instead of scattering it across layers.

Synthesis picks one candidate as the base and grafts only pieces that shrink or preserve the public surface; record why each rejected candidate lost, naming its specific red flag rather than "merged the best ideas." A merge that grows the surface means the base was wrong. The synthesized package fills the rationale's "Synthesis decision" section with the base, the grafts, and the rejections.

## Phase C: Agree (opt-in)

Default: proceed directly to implementation with the synthesized design. No human checkpoint.

Opt in to a checkpoint when the invoker explicitly asks: "/architect with checkpoint," "stop and show me before implementing," "plan this out with me," "nail down the wanted behavior," or similar. Then surface the synthesized design and pause for sign-off before updating binding docs or writing code.

Present the synthesized design in plain technical language: name who writes what and when. No design-review vocabulary ("interface depth", "shape wins", "grafts", "seams", "blast radius"), no invented compound labels for mechanisms — a reader who was not in the design session must follow every sentence. "Technical and jargon-free" is the bar; impressive-sounding analysis is not.

Checkpoint questions are decision budget: spend them only inside the subsystem the user scoped. For a surface the user has explicitly deprioritized (a proof-of-concept server, a sibling seat's area), take the simplest honest default — e.g. a liveness probe just answers — state it in one line, and move on. Asking the user to adjudicate a component they said they don't care about reads as not listening, and the answer costs more than the default ever will.

When the user asks to be consulted "as constraints arise," treat that as a standing invitation, not a batch. Ask the one fork that blocks the next phase, with a recommendation, then proceed; a form of four questions up front is the failure that instruction was trying to prevent. Expect scope to grow mid-flight — a new constraint arriving after Phase B has dispatched is normal. The correct response is to ground only the newly-named subsystem, append it to the Phase A artifact as a numbered constraint, and keep the running design pass. Do not re-run Phase A whole, and do not cancel dispatched runners: the artifact on disk is what makes the append cheap, which is the real reason grounding is written before dispatch. If the new constraint contradicts a runner's premise, steer that runner with it rather than letting it finish on the old one.

Every "X does not change" the user states is a numbered invariant in the constraints artifact, carrying the `path:line` citations that currently define X. A runner handed an invariant without its citations softens it into a migration. Pair it with the list of what the environment cannot do (shared hosting, no daemons, no queue) so candidates that require those are never proposed.

The synthesis can ship as its own commit either way. That's the "scaffold first" mode: subsequent commits read as filling in bodies against a stable contract. When the agreed design replaces an existing documented direction, updating binding docs means molding the doc tree to the new model in the same change — delete superseded docs and sweep old-model mentions (`code-dedup`'s `references/repo-hygiene-pass/`, direction-change doc mold), not just adding the new doc beside the old ones. Planned and scoped breakage during fill-in is fine. For adversarial pressure on the design before implementing, run **grill-me** review on the synthesized sketch.

If the human pushes back on the shape (in a checkpoint or after the fact), treat that as Phase A evidence. Re-ground and re-run Phase B before writing more code.

## Phase D: Implement against the sketch

Replace `not implemented` bodies with code, pseudocode with logic. The synthesized sketch is the contract. Deviations from it are signal to surface, not friction to absorb silently. If a function needs a parameter the sketch didn't anticipate, ask whether the sketch was wrong, the requirement was missed, or the implementation is overreaching.

Division of labor when delegation is available: subagents write the code on the configured delegation pin; you scope the slices, review every diff, and run the validation gates. This user expects the orchestrator-and-reviewer role — writing the implementation yourself is the deviation to justify, not the default.

When the repo has an equivalence gate (golden benchmark, `--check` diff, golden dataset), slice 1 is behavior-preserving code motion that must pass it, and the new shape lands only after that gate is green. Then slice the fill-in by module boundary: one slice per child, one module or one file set plus its tests per slice. Size slices to fit one child's iteration budget — an oversized slice ends mid-edit with call sites still pointing at whatever the child deleted. Before a later slice builds on an earlier one, verify the earlier child's claims on disk (compile the files, grep for call sites of deleted functions, import the modules): a child's summary is a self-report, and the file-mutation verifier can disagree with it.

Re-verify finished slices yourself, not from the child's report: compile every new header together in one throwaway translation unit for the host (with `-fsanitize=address,undefined`) and for the real target toolchain (`-Os -Werror`), then print hex or output of a few concrete builder calls and check the counts by hand. Keep that scratch program outside the repo. Resolve open platform questions (what the OS or SDK actually does) with a probe build on the hardware before slicing, and record the measured answers in the plan.

For embedded targets, build the resource budget BEFORE sketching and carry it in the plan: measure the platform's real limits first (static RAM by object from the linker map, runtime free heap by the allocator class the other subsystems use, per-task stack headroom, socket and flash limits), list every existing consumer with its size, and assign each new component a number out of what remains, including the web upload/OTA/TLS path's floor. A plan line that says the budget is "to be confirmed" is a guess handed to workers as a spec; they size buffers for a bigger machine. Give each slice a resource budget in the dispatch (static RAM, heap, stack, flash) taken from the plan, and check the sum with a full link before the next slice builds on it. Fix a link overflow by shrinking state, not by moving it to the heap. Per-file compiles pass while the combined image overflows the RAM region. A passing link is not a passing budget: also flash the image and read the runtime free 8-bit heap (largest block and low-water mark) against the baseline build, and put a floor for it in the plan. Other subsystems (web upload, OTA, TLS) allocate buffers from what static RAM leaves, and a new engine that links with room to spare can still starve them. When the user asks for each optimisation to be benchmarked on its own, build the measurement before dispatching: add counters for what each change should move (hits, read counts, microseconds, heap low-water mark), write one fixed-seed benchmark with a report script, record the baseline run, then give each subagent one change in its own `git worktree` with its expected effect stated in the brief. The shared device is a single resource, so subagents compile only; the orchestrator flashes and benches each variant against that baseline, then the combined build. Hardware verification goes one variant per flash with a known-good baseline binary kept ready (a `git worktree` build of the last good commit); if the first flash shows a regression in a path the old firmware handled, stop and isolate with read-only probes before flashing again.

When a plan or sketch file you wrote earlier is rewritten, the write tool may refuse because the file was not read this session: read it first, or delete and recreate it, instead of retrying the same write.

When a capped child reports an incomplete and names what remains, dispatch a finisher whose spec is that exact outstanding list. The child's own plan of its leftovers is cheaper and more accurate than re-deriving the work, and the fresh budget is what the first child lacked.

Settle cross-slice interface questions as explicit orchestrator decisions in the dispatch text BEFORE parallel slices write against them: who owns a call, who narrates it, which error class crosses a boundary. Two slices will otherwise each implement their own reading and the merged code does both (the classic doubled narration or double-write). Run slices in parallel only over disjoint file sets; when an interface is still moving, sequence instead.

## Phase E: Scrap when the architecture is wrong

If implementation keeps producing friction the sketch can't absorb, throw the sketch out. Don't bolt fixes onto a wrong design.

The signal is a *pattern*, not single instances. Tells:

- The same shape of workaround appearing repeatedly across unrelated code.
- Multiple unrelated edge cases that all need special-case branches.
- Types that need escape hatches (`any`, casts, optional fields always set in practice) to compile.
- The "we need a lock" reflex when the sketch said the state wasn't shared.
- Callers having to know the abstraction's internal rules to use it.
- Two or more independent Phase D deviations of the same shape across the implementation.
- Adversarial reviewers' critical findings cluster around the coordination mechanisms (queues, handles, ownership handoffs, recovery ladders) rather than the logic. Each mechanism needs its own timeout, drop policy and ownership rule; remove the mechanism (fold into a single owner) instead of patching each finding. Scrapping at the plan stage costs a document edit, not code.

Use judgment. A few edge cases don't condemn an architecture. Some problems are legitimately complex; complexity in the data is not complexity in the design.

When you scrap:

1. Re-run the **how** skill over what's been built. The implementation lessons enter the new design as inputs, not vibes.
2. Redesign as if the new constraints had been day-one assumptions.
3. Subtract before adding. The new sketch should be smaller than the old one before it grows.
4. Return to Phase B and re-run the design runners.

## Outputs

The caller's usage is written first and the type sketch derived from it. One file with new types and signatures for small changes; module map plus type definitions for larger work. The rationale ships alongside, shaped per `references/rationale-template.md`, including the usage sketch and the synthesis decision. Land the synthesis in the repo's own design/plans home (check the convention — e.g. `docs/plans/YYYY-MM-DD-*.md`), not the sketch dir: scratch dies within a day and the contract must survive for the fill-in phases and later readers. Register the synthesis wherever the repo indexes live plans, then check `git status`. If the plan is intentionally uncommitted, say so in the close-out and make committing it the first restore-point task. An unindexed or untracked plan is not a landed contract.

**A plan whose phases live only in a document is not tracked.** When the user names a board, tracker, or ticket system as the home for the work, one task per phase is the deliverable, not a nice-to-have — the document is the contract, the board is how it gets driven and how the user follows along. Create them in the board's own read order (ground, then build, then prove, then measure, then re-measure for reliability) and put the phase id in the title so the doc and the board cross-reference without a lookup.

- **Carry one measurement into each task's first comment.** A task that says "prove X" invites a re-litigation of whether X is already done; a comment quoting what was actually observed (the grep result, the count, the failing status code) starts the worker from evidence. If nothing was measured, say that instead of implying the task is scoped from data you never gathered.
- **State the blocker edge explicitly.** If phase N cannot start before phase N-1 lands, say so in the task text, because priorities sort a column and only prose says what cannot start.
- **Mark the blocking phase as such and start there.** When one phase is a prerequisite for the rest, tell the user that plainly and offer it as the next action rather than ending on the full list.
- **Correct the board when the doc was wrong.** If the plan document and the task description disagree on a number, fix the task and say which one is authoritative; a tracker entry that quietly teaches a stale premise reads as recorded fact to the next session.
