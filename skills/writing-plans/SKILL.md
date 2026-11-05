---
name: writing-plans
description: Write an implementation plan from a spec or when the user asked for a plan, before touching code.
---

# Writing plans

Save to `docs/plans/YYYY-MM-DD-<feature-name>.md` unless the user named another path. Named acceptance criteria, or write them. Follow an architecture decision already in the repo. Do not invent `docs/adr/` or a triage ceremony to satisfy this skill.

Stay read-only until the plan is written. Independent subsystems get separate plans.

**Order.** Draw the dependency graph first. Implement bottom-up so later tasks only use things that already exist.

**Slice vertically.** One task is one working path (schema + API + UI for that path), not "all of the database, then all of the API."

**Map files** before tasks: create / modify / test, each with a path. Follow the repo's existing file shapes.

**Trace the spec.**

| Requested behavior | Task | Verification |
|---|---|---|
| `/login` is the real entry | Tasks 1-2 | Playwright login |

For a user-facing app, list the real routes. No marketing-page stand-ins.

Each task:

- **Files:** exact paths
- **Acceptance criteria:** testable bullets
- **Dependencies:** earlier task numbers, or none
- **Steps:** the actual code or command, including the test and the expected result

Split a task that touches two subsystems, needs more than one session, or has an "and" in the title.

No placeholders: no TBD, "add validation", "similar to Task N", or "implement the feature." Repeat the code if a later task needs it.

Checkpoints after every 2-3 tasks (tests, build, the user-visible path). End with risks and open questions, or "None."
