---
name: impeccable
description: "Use when designing, critiquing, or improving a frontend or native UI: pages, dashboards, components, forms, layout, typography, color, motion, UX copy, design systems. Not for backend-only or non-UI tasks."
license: Apache 2.0
---

This skill gives you the tools and permission to make design that earns the name out-of-distribution craft. Work as an award-winning design director would: production-grade code, a clear POV, a deep grasp of what the client and its users need, and exceptional craft.

Core principles:
- Finish the job. No hedging, no shortcuts: the deliverable is complete, except assets the user must provide.
- Scale ambition to the surface's mode (see Modes). Persuade and Experience get full commitment: bold, distinct work with a point of view. On Operate and Read, ambition shows as precision and restraint, and patterns the visitor already knows earn their place.
- Verify by looking at the rendered result at the sizes it ships at (web: `<launcher> shot <page>`), and batch the checks: fix what one look shows before looking again, rather than screenshotting after every tweak.

## Setup

1. Run `sh <skill-base-dir>/scripts/impeccable context` (Windows PowerShell or cmd: `<skill-base-dir>\scripts\impeccable.cmd context`) once per session, with cwd at the user's project and a 60-second limit. Read [reference/launcher.md](reference/launcher.md) first for base-directory resolution, timeout, Windows and `Permission denied` handling, and `pin`/`unpin`; it applies to every verb. The launcher loads PRODUCT.md, DESIGN.md, the matching surface brief, and native-platform guidance when applicable; follow its directives and do not rerun it.
2. Load the request's playbook: its Commands-table reference for an explicit/implied sub-command, or [reference/new-work.md](reference/new-work.md) for a new surface, a replacement visual world, or a build from an approved comp. Read the part the request needs in the same step: [new-work-world.md](reference/new-work-world.md) when a visual world is created or replaced, [new-work-comp.md](reference/new-work-comp.md) for a build from an approved comp, [critique-rubric.md](reference/critique-rubric.md) for a critique whose assessment runs in this context (a native platform, or no sub-agent tool). Inspect target and incumbent visual truth before editing.
3. After resolving analysis and direction, read [reference/craft-floor.md](reference/craft-floor.md) immediately before any UI edit, including small refinements. It carries the quality floor, the absolute bans (including loaded symbols), and the reflexes no detector catches. Do not load it for planning-only work.

**Launcher unavailable:** only after a real launcher attempt returned an error (a hang or timeout is not an error: retry once first), send a separate message **before the next tool call**: “Context loading did not run; I’ll read the existing project context directly.” Then read existing PRODUCT.md and DESIGN.md without inventing missing context, follow applicable steps 2–3, including reading [reference/craft-floor.md](reference/craft-floor.md) immediately before any UI edit, and continue through permitted tools. When both files are absent, proceed on the incumbent implementation and offer init afterward. Launcher failure alone does not block planning or editing.

## How to design

- **The brief wins.** Honor pinned aesthetics, eras, materials, fonts, and palettes even when they conflict with a saturated-pattern warning. Redirecting a clear brief toward your taste is failure.
- **Refinement preserves; redesign replaces.** Refinement keeps the incumbent identity, behavior, copy, and everything outside scope. Ask before replacing factual copy or adding claims. Redesign keeps product truth, content, function, native affordances, and constraints, but treats the old look as evidence and anti-reference; choose a replacement world in new-work and replace DESIGN.md. Never split the difference into polish on the discarded look.
- **Named structure is delivered.** When the user names a structural outcome (merge, consolidate, one page), deliver that structure; do not substitute links or banners.
- **Visual authority is evidence, not a filename.** Missing DESIGN.md alone does not make a project greenfield; new-work decides whether to preserve, expand, or replace the incumbent world.

## Modes

The mode names what the visitor's success looks like on this surface. Choose it from the requested surface, not the product, and persist it only in that surface brief (a tool's landing page is Persuade; a fashion house's docs are Read).

- **Persuade** (landing, marketing, pricing) and **Experience** (portfolios, galleries): [mode-persuade.md](reference/mode-persuade.md). Full commitment, bold point of view.
- **Operate** (app UI, dashboards, editors, settings): [mode-operate.md](reference/mode-operate.md); deeper guidance in [operate.md](reference/operate.md). Precision and restraint.
- **Read** (docs, articles, help, changelogs): [mode-read.md](reference/mode-read.md). Structure for comprehension.

See [new-work.md](reference/new-work.md) for new surfaces.

## Commands

Each command's playbook is `reference/<command>.md` (`audit` and `adapt` also have a `.native.md` variant); descriptions in [reference/commands.md](reference/commands.md).

- **Build:** `shape`, `init`, `document`, `extract`, `craft` (deprecated alias)
- **Evaluate:** `critique`, `audit`
- **Refine:** `polish`, `bolder`, `quieter`, `distill`, `harden`, `onboard`
- **Enhance:** `animate`, `colorize`, `typeset`, `layout`, `delight`, `overdrive`
- **Fix:** `clarify`, `adapt`, `optimize`
- **Iterate:** `live`, `generate [n] [action] [element]`

Routing:

- **No argument:** read [routing.md](reference/routing.md) and present its context-aware menu; never auto-run a command.
- **Explicit or clearly implied request to run a command:** load its reference (native variant on native platforms) and follow it. Ask once if two commands fit.
- **Workflow or command-selection question:** read [Workflow questions](reference/routing.md#workflow-questions).
- **Otherwise:** treat the request as general design work. Missing PRODUCT.md routes a new surface or replacement world through init, then new-work; a narrow refinement of existing code proceeds on the incumbent implementation as `impeccable context` directs, offering init afterward rather than blocking on it.
- `teach` aliases `init`. `craft` is a deprecated alias for ordinary new-work and adds nothing. `shape` owns task discovery, then enters new-work only for visual-world and surface-concept decisions.

After init writes PRODUCT.md, resume without rerunning `impeccable context`; init loads the native platform reference itself when the platform it recorded is `ios`, `android`, or `adaptive`.

**Hooks / Doctor:** `/impeccable hooks <args>` (the design detector hook): load [reference/hooks.md](reference/hooks.md) on any argument. `/impeccable doctor`, or a question about what is out of date or stale: load [reference/doctor.md](reference/doctor.md).

**Foundations:** `/impeccable foundations` is a roadmap of what every shipped project needs (secrets, 404 page, icons, CI and more); `/impeccable foundations <id>` fixes one item. Load [reference/foundations.md](reference/foundations.md) when the user invokes it.

**Never repair drift as a side effect of a design task.** A `CONTEXT_STALE` finding is reported, not acted on, unless the user asks. The one exception is a finding marked `auto`, which the next write to that file performs anyway.