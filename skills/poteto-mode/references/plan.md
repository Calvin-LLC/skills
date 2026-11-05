# Plan

Produce a phased implementation plan grounded in the **Non-negotiables** section of the `poteto-mode` skill. The plan is the deliverable. Do not implement.

Open a todolist with one item per step below.

## 0. Triage

Skip the plan when the change is one or two files with an obvious approach. Say so and stop.

Plan when the change spans three or more files, introduces architecture, has competing approaches or unclear scope, or the user asked for one.

## 1. Re-read the non-negotiables

Read the `poteto-mode` skill's `SKILL.md` (non-negotiables, autonomy, playbook index) in full before planning.

## 2. Scope and constraints

State your read of scope and constraints in one paragraph. Questions go through **grill-me**. If the pick is already clear, do not ask.

Resolve what is in scope vs explicitly out, technical or platform constraints, patterns to preserve, and the definition of done.

## 3. Explore in subagents

Delegate codebase exploration to a subagent and keep its dump out of the main thread.

- Spawn explorers via `task`.
- Workers inherit the user's default model. Do not pass `--model`.

Each explorer returns file pointers, conventions, dependencies, test infrastructure, and entry points. No inlined dumps.

## 4. Write the plan

The user specifies where the plan lives.

Single file `NN-slug.md` for small plans. For three or more phases, a directory with `overview.md` plus phase files:

```
NN-slug/
├── overview.md
├── phase-1-scaffold.md
├── phase-2-...md
└── testing.md
```

### Phase sizing

- One function or type plus tests, or one bug fix. Not "one file".
- Two to three files touched, max.
- Prefer eight to ten small phases over three to four large ones to preserve option value.
- Split if a phase has more than five test cases or three functions.

### Overview file

- **Context.** Problem and why now.
- **Scope.** Included; explicitly excluded.
- **Constraints.** Technical, platform, dependency, pattern.
- **Alternatives.** Two or three structurally distinct approaches sketched, choice and rationale. Skip when constraints dictate one.
- **Applicable skills.** Domain skills the implementer should invoke, by name.
- **Phases.** Ordered standard-markdown links to phase files.
- **Verification.** Project-level commands.
- **Implementation guidance.** Per section 6.

### Phase files

- Back-link to overview.
- **Goal.** What the phase accomplishes.
- **Changes.** Files affected and the change at a high level. What and why, not how. No code snippets.
- **Data structures.** Name the key types or schemas. One-line sketch only.
- **Verification.** Per section 6.

Order phases so infrastructure and shared types land first. Each phase should be independently shippable.

For changes touching existing code, redesign from first principles: if we'd built this with the new requirement on day one, what would it look like? Redesign holistically; deliver incrementally.

If a phase creates or edits a skill, the phase instructs the implementer to follow **Authoring a skill** (`playbooks/authoring-a-skill.md`).

## 5. Verification per phase

Each phase needs both:

**Static.** Type check, lint, project tests pass.

**Runtime.** Exercise the feature on the matching surface:

- Browser / web: Playwright or the live app, plus **gemini-vision** when a visual check is needed.
- CLIs and TUIs: run the binary.
- Native mobile: whatever simulator-driving skill the repo has.
- No way to reach the surface: flag it in the plan.

For bug fixes, the loop is reproduce on the surface, fix, verify on the same surface. Unit tests show a branch behaves a certain way; they do not prove the bug is gone.

## 6. Implementation guidance

In the overview, name which poteto-mode non-negotiables the implementer must apply, by name:

- the **how** skill over each unfamiliar subsystem before changing it.
- the **grill-me** skill for adversarial review on contested designs before shipping.
- the **unslop** skill over each diff before commit, and over any prose surface.
- the **show-me-your-work** skill to keep a decision trail when the plan is large enough to need an auditable record.
- **Committing on main** after the work is verified. Do not open a PR unless the user asked for one.

## 7. Hand back

Summarize phases, scope boundaries, applicable skills, and verification. Stop. The user decides when implementation starts.
