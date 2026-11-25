---
name: writing-plans
description: "Write an implementation plan from a spec or when the user asked for a plan, before touching code. Not for designing types, signatures, or module boundaries; use architect."
---

# Writing plans

Save to `docs/plans/YYYY-MM-DD-<feature-name>.md` unless the user named another path. Named acceptance criteria, or write them. Follow an architecture decision already in the repo. Do not invent `docs/adr/` or a triage ceremony to satisfy this skill.

Stay read-only until the plan is written. Independent subsystems get separate plans.

**Order.** Draw the dependency graph first. Implement bottom-up so later tasks only use things that already exist.

**Slice vertically.** One task is one working path (schema + API + UI for that path), not "all of the database, then all of the API." A restructure that makes the change easy is task 1. A wide refactor (one mechanical change that breaks many call sites at once) cannot land as one slice: add the new form beside the old, migrate callers in batches that each stay green, then delete the old form.

**Map files** before tasks: create / modify, each with a path, plus the end-to-end run that proves each path. Follow the repo's existing file shapes. Copy the spec's project-wide requirements (versions, dependency limits, naming rules) verbatim once at the top; every task inherits them.

**Trace the spec.**

| Requested behavior | Task | Verification (end-to-end run on the real path) |
|---|---|---|
| `/login` is the real entry | Tasks 1-2 | Playwright login |

For a user-facing app, list the real routes. No marketing-page stand-ins.

Verification is an end-to-end run along the real user or runtime path, with each step measured. A plan adds no unit or mock test files; where the repo's only seam is a unit test, name the end-to-end run to build instead.

Each task:

- **Files:** exact paths
- **Acceptance criteria:** observable bullets, each checked on the running system
- **Dependencies:** earlier task numbers, or none
- **Interfaces:** names and signatures it uses from earlier tasks and exposes to later ones, exact
- **Steps:** the actual code or command, ending with the end-to-end run of the real path and the expected result of each step

Split a task that touches two subsystems, needs more than one session, or has an "and" in the title.

No placeholders: no TBD, "add validation", "similar to Task N", or "implement the feature." Repeat the code if a later task needs it.

Checkpoints after every 2-3 tasks (build, then the user-visible path run end to end). Before handing over, check that every name and signature matches across tasks. End with risks and open questions, or "None."
