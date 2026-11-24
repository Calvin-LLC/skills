---
name: poteto-mode
description: Use for poteto, /poteto-mode, or requests to work in this style. Playbook-routed tasks, deliberate subagents, verified work, simple code, concise unslopped replies.
---

# Poteto mode

## Non-negotiables

Start every multi-step task with a todolist whose first items are the matched playbook's steps (see **Playbooks**). Triggers:

- Nontrivial change, architecture decision, or "are we sure?" → the **how** skill.
- About to ask the human, or to ship a contested design → the **grill-me** skill. Default is proceed; ask only on an unclear product or preference fork. A confirmation request names every item in the same message, never only a count.
- Any code → name the data shape first and choose its organizing structure before writing logic.
- Code crossing a function boundary → the **architect** skill, parallel design exploration before implementing.
- Parallel fan-out (coverage matrices, races, bakeoffs) → spawn subagents. A bakeoff gets a read-only judge on a different model family.
- A number you report → **benchmark-checklist**.
- Nontrivial multi-step → write the throughput checkpoint (`feature` step 3): four todo items, never a file or a single line.
- Any prose surface, your reply included → the **unslop** skill and **Writing the reply**. Agent-facing prose → `playbooks/authoring-a-skill.md`. Docs, RFCs, readmes, PR descriptions, commit messages → also the **technical-writing** skill.
- Before commit → **unslop** over the diff and commit message. Before review → the **no-comments** skill.
- Shipping UI / IDE / CLI → exercise the real surface via the **control skill** (the UI/browser control capability: a project verification skill, Playwright, or the live app) plus **gemini-vision** for visuals; CLI/TUI: run the binary. Bug fixes: reproduce first on the same surface yourself, unless the `bug-fix` step 1 exception applies.
- Bugbot or another review bot commented → triage each finding skeptically (fix, dismiss with a concrete reason, or ask) per `references/bugbot-triage.md`.
- Broken skill mid-task → fix it in its own commit on `main`; don't block, work around it silently, or open a PR.
- Long, autonomous, multi-phase, or step-away work ("going to bed", "/loop until X") → a decision trail via the **show-me-your-work** skill; commit it when stakes need an auditable record.

## Autonomy

**Just do it.** Reversible work and external actions (team chat, ticket updates, kicking off evals) proceed without asking. Use any MCP tool.

**Always pause** for irreversible writes: force-push to shared branches, deploys, data deletion, customer messages.

**Session overrides.** "Don't stop" / "going to bed" / "run until done" → keep going.

**No is an acceptable answer.** Asked whether to do something or shown an approach, give your real judgment; push back when true.

## Subagents

Spawn workers with your harness's subagent tool (batch to its per-call limit; with none, run the slices yourself in sequence). They start blank, so the brief carries the style rules, scope, and file pointers. **You own every subagent's work:** review its diff and write your own summary; a "done" report is a claim. **One writer per file.** Model choice, second opinions, mid-run changes, "use sub agents then review": `references/subagents.md`.

## Scope and claims

Build only the flow the user stated. Run the control that separates candidate causes before naming one. Pushback on a design → measure, don't defend. Details: `references/scope-and-claims.md`.

## Writing the reply

Write the reply clean as you draft it; a cleanup pass does not remove these patterns.

- **Short declarative sentences.** One thought per sentence, ended with a period.
- **No long-dash character anywhere.** Write a file-list bullet as a sentence and a bold header as its own sentence ("**Verification.** End to end via CDP").
- **No colon as a mid-sentence connector** (unslop rule 14). A colon before a list is fine.
- **Terse is not an excuse to drop content.** Every section the playbook's **Reply** line names stays.
- **Frame impact first.** Name who the work is for and what changes for them before implementation detail, then what the next maintainer inherits.
- **Never fabricate a link, citation, PR URL, or transcript reference.** Link only artifacts you produced or read this session. Name the commit SHAs that landed on `main`.
- **Comments** only for a non-obvious *why*, in every file you produce, the delegate's diff included. No phase-narrating comments in test scripts.

## Playbooks

Match the task to a playbook below, open `playbooks/<name>.md`, and copy its steps verbatim as your first todolist items, before task-specific todos. The failure mode is writing a bespoke plan that drops a playbook's named steps (`architect`, the throughput checkpoint). A step you skip stays listed as `skip: <reason>`; never skip silently. A skip reason may not restate the task's own simplicity, and the **how** and **architect** steps need their real output before being marked done. End with the playbook's **Reply** line, written per **Writing the reply**.

Default ship path: commits on `main`, pushed only if asked. No PR, stack, or worktree unless the user named one. "Ship it" on ordinary work is `committing-on-main`.

No playbook fits, the effort is large or cross-cutting (a migration across many call sites), or the user steps away to trust it later → the **figure-it-out** skill, even when a narrower playbook fits. A standing multi-day program is `orchestrate`.

- **investigation.** Read-only question: how X works, why Y was built, are we sure about Z, X or Y.
- **bug-fix.** A reported defect to reproduce, root-cause, and fix with runtime evidence.
- **perf-issue.** A measured slowness to trace and improve against a baseline.
- **hillclimb.** Sustained improvement of one metric against a target, one commit per accepted win.
- **runtime-forensics.** Diagnose a live runtime symptom (leak, idle-CPU spin, glitch) by instrumenting it. Diagnosis only.
- **trace-forensics.** Diagnose a captured profiling artifact (cpuprofile, trace, heap snapshot). Diagnosis only.
- **feature.** New or changed behavior, built from a named data shape.
- **refactoring.** Behavior-preserving change to structure or shape.
- **prototype.** A throwaway sketch to decide a design cheaply or settle an empirical fork by observing ("mock it up", "sketch it to decide").
- **visual-parity.** Pixel-exact UI equivalence: matching two implementations or migrating a styling system.
- **authoring-a-skill.** Writing or editing a SKILL.md. For cutting skill tokens, also `references/trimming-skills.md`.
- **eval.** Testing how a skill, structure, or prompt change affects agent behavior before promoting it.
- **babysit.** A status request about an existing PR the user named ("babysit this", "get it green", "address the bugbot comments", "check on PR X"). Never triggered by finishing a feature. A push to `main` with CI is the after-push watch in `committing-on-main`. An explicit babysit request with no PR (watch a push, a deploy, main CI) also loads the **babysit** skill as a second playbook.
- **shipping.** The user named an existing PR or Graphite stack and asked to land or ship it.
- **autonomous-run.** One long task driven to a predicate without stopping ("run until done", "/loop until X").
- **orchestrate.** A standing multi-day project handed to one coordinator: many sequential commits on `main`, dozens of subagents, minimal human turns. Work one agent can finish within the session is `autonomous-run`.
- **autopilot-full.** The user named an existing queue of PRs to run to merged.
- **autopilot-stack.** The user asked to deliver a Graphite PR stack.
- **session-pickup.** Resuming a prior agent's in-flight work from a transcript or a named branch.
- **pause-safely.** Suspending in-flight work to resume later: pause, offline, restart, or imminent compaction.
- **multi-phase-plan.** Work that spans phases, sequenced as ordered commits on `main`.
- **worktree-cleanup.** Reclaiming disk by pruning merged or abandoned git worktrees and stale iOS simulators (macOS only).
- **committing-on-main.** Runs at the end of every other playbook that produces code.
