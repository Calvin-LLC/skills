---
name: figure-it-out
description: "Use for /figure-it-out, 'figure it out', a large migration, an ambitious multi-part change, work a human reviews after stepping away, or when no narrower playbook fits. Designs an auditable bespoke playbook with rigor scaled to the task."
---

# Figure it out

When the task matches no playbook, design one. The deliverable before any code is the workflow itself: a sequence of phases that scales rigor to the task, runs the scientific method, and leaves a decision trail a human can audit after stepping away. Bias toward more rigor.

## Start

If the **poteto-mode** skill is installed, read its Non-negotiables section now, before step one. Then add the phases below as todos.

## Phase A: Frame

Ground first, then commit. Don't start the run until you can state:

- The definition of done as a falsifiable predicate. "Done well" has to be checkable.
- Scope, quantified: what is in and what is explicitly out, rough units and effort, plus the blockers grounding surfaced. Raise them before spending hours.
- The rigor level, biased high. One-way doors and high blast radius get more; reversible low-stakes steps get less. Rigor is gates and artifacts, not "try harder".
- Any standard or quality phrase the operator used, restated as a checkable rule (floor or exact, in or out). If one reading removes or rewrites working code, confirm it before landing.

Present the framing and tradeoffs before committing to a long run. Reversible work proceeds without asking, but a multi-hour run earns one checkpoint.

## Phase B: Design the workflow

Decompose into atomic, independently-landable units. Sequence riskiest-unknown-first so option value stays high. Scaffold and verification come before features.

- Build the verification harness before the work, with the baseline captured from the pre-change state, so the check reads as "old value vs new value".
- For one-way-door design decisions, run the **architect** skill with diverse, isolated, opinionated candidates and a read-only judge on a different model family. With no second family available, say so in the trail and use a fresh-context subagent. Skip it for mechanical work whose shape is already concrete. A second design round over a settled design is over-engineering.
- Decide what fans out. Parallelize only across genuine seams, and give each worker its own scratch dir so two writers never share one. Land accepted work as sequential commits on the repo's default branch.
- Write the designed phase list down. That list is what the human reviews.

Then execute the design. Add a log row as the closing step of every unit todo. Run each unit under the Phase C loop discipline, weaving the Phase D log through them as each step lands rather than saving the whole trail for the end.

## Phase C: Run the loop

Each unit is an experiment: state the hypothesis, make the smallest change, measure against the predicate on the real artifact, keep it if it advanced, revert it if it didn't.
Verify each unit before starting the next instead of batching checks at the end.

- Verify by inspecting the artifact, never a self-report. When something passes too easily, suspect the observation method before the system.
- Pair delegated work with a judge. If a worker games the gate, reset and harden the contract. If the gate itself is wrong, fix the gate in its own change rather than routing around it.
- A verdict is VERIFIED, NOT VERIFIED, or INCONCLUSIVE. Inconclusive is not a pass. Don't hide a negative.

## Phase D: Keep the audit trail

Log the run via the **show-me-your-work** skill, one canonical TSV with a row per decision and per unit, evidence as links. Put the trail where the reviewer will read it: a tracked path on the default branch when confidence has to be shown, otherwise say where it lives. Prefer evidence produced by committed scripts so a reviewer can re-run it.

## Long runs under a standing goal

If the harness runs a standing-goal loop, a turn that ends on a question or a progress report can pause it.

- Do not end a turn to ask. Before any behaviour question, read the code for the behaviour that already exists. Decide, log the row, move on; when the user delegates a choice with a standard (for example OWASP practice), take the secure-by-default, fail-safe option.
- A question that truly needs the user goes in the repo's existing docs location for open questions (create one only if none exists) with a recommendation, then switch to a unit that does not depend on it. End the turn only when every remaining unit is blocked on such a question or a listed hard stop.
- Put progress in a committed file, not in turn endings.
- Write process lessons from the run into the goal text itself when re-issuing it, so the next loop starts with them.

## Phase E: Verify and hand back

Check the whole against the Phase A predicate on the real product, not just the harness. Encode any recurring correction as a gate, a lint rule, a check, or a script, so the win can't silently regress.

**Reply:** the playbook you designed, the rigor level and why, the decision-trail path, what's verified against the predicate, and what's still open.
