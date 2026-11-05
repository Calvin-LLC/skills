---
name: how
description: How a subsystem works, where it lives, and what owns it. Motivation is why.
---

# How

Explore the codebase to answer "how does X work?" questions. Produce clear architectural explanations at the level of a senior engineer onboarding onto a subsystem. Enough to build a working mental model, not annotated source code.

Three modes:

1. **Explain** (default). Explore the codebase and produce a clear explanation
2. **Status audit.** Explain the mechanism, then say whether it exists at all: implemented, parked plan, or reference-only clone
3. **Critique.** Explain first, then spawn multiple models to independently identify architectural issues

## Explain Mode

### Step 1. Understand the Question and Assess Complexity

Parse what the user is asking about:

- "How does the rate limiter work?", a subsystem
- "How do we handle billing for on-demand usage?", a feature flow
- "How is the auth service structured?", an architectural overview
- "Walk me through what happens when a user submits a form", a runtime trace

Identify the scope. If ambiguous, state your best-guess interpretation before exploring. Don't ask. Let the user redirect if you're off.

**Calibrate vocabulary to the user's stated background.** If they say they know OS/assembly basics, do not re-teach pages, threads, stacks, or virtual memory; spend the words on the project-specific mechanism. Expand local shorthand and codenames on first use (path names, seat names, internal abbreviations) or replace them with the concrete mechanism. Measured counts and file:line anchors beat keyword-dense summary language.

**Assess complexity to decide the approach:**

- **Simple** (a single module, a small utility, a narrow question like "how does function X work"): skip explorer agents; the explainer explores and explains in a single pass. Go to Step 2b.
- **Complex** (a subsystem spanning multiple files/services, a cross-cutting feature, a full architectural overview): spawn parallel explorer agents first, then hand off to the explainer. Go to Step 2a.

When in doubt, lean simple. You can always spawn explorers if the explainer hits a wall.

### Step 2a. Explore (complex questions only)

Decompose the question into 2-4 parallel exploration angles, each a distinct slice of the subsystem so explorers don't duplicate work. Example split for "how does the rate limiter work?":

- Explorer 1: data model and state management
- Explorer 2: request path and enforcement
- Explorer 3: configuration and metrics infrastructure

The right decomposition depends on the question. Use your judgment. Narrow questions: 2 explorers is fine. Broad subsystems: up to 4.

Spawn all explorers in one `task` call (up to 3 `tasks`; batch the rest). Read-only.

Each explorer gets the same base prompt from `references/explorer-prompt.md` plus a specific exploration angle naming its slice. Each explorer should:
- Start broad: Glob for relevant directories, Grep for key types/interfaces/class names
- Follow the thread: from an entry point, trace the call chain (callers, callees, data flow, type definitions)
- Read the actual code, don't guess from file names
- Stop when it can describe the full path from input to output (or trigger to effect) without hand-waving any step
- Note things that are surprising, non-obvious, or that a newcomer would get wrong

Each explorer returns structured findings: components found, flow traced, files read, anything non-obvious. Overlap between explorers is fine; the explainer reconciles.

Then proceed to Step 3.

### Step 2b. Direct Explain (simple questions)

Spawn a single `task` worker that explores and explains in one pass. Read-only.

The agent does its own exploration (Glob, Grep, Read) and writes the explanation directly. Read `references/explainer-prompt.md` for the communication style and output format. Same structure, just no explorer findings as input.

Proceed to Step 4.

### Step 3. Synthesize (complex questions only)

Once all explorers return, spawn a single `task` worker to synthesize their findings into one coherent explanation. Read-only.

The explainer gets all explorers' findings and writes the human-facing explanation (output format below). Read `references/explainer-prompt.md` for the full prompt template. The explainer reconciles overlapping findings, resolves contradictions, and weaves the slices into a unified picture.

### Step 4. Present

Present the explainer's output to the user. You may lightly edit for clarity or add context from the conversation, but don't substantially rewrite. The explainer's communication is the product.

### Output Format

Follow this structure, adapted to the question. Not every section is needed for every question.

**Overview.** 1-2 paragraphs. What it is, what it does, why it exists. Enough to decide whether to keep reading.

**Key Concepts.** The important types, services, or abstractions. Brief definition of each. Not exhaustive, just the ones needed to understand the rest.

**How It Works.** The core of the explanation. Walk through the flow: what triggers it, what happens step by step, where data goes, the decision points. Prose, not pseudocode. Reference specific files and functions so the reader can go look, but don't dump code blocks unless a snippet is genuinely necessary.

**Where Things Live.** A brief map of the relevant files/directories. Not every file, just the ones needed to start working in this area.

**Gotchas.** Non-obvious or surprising things that would trip someone up. Historical context that explains why something looks weird. Known sharp edges.

## Status Audit Mode

Triggered when the question carries "has this been implemented?", "is it in the SDK?", "or is it still reference-only?". Explain the mechanism first, then deliver the verdict; the verdict is the decision the user is actually making. A skipped audit that answers only "how it would work" reads as a claim that it works.

Audit in this order, and stop when one verdict fits every fact:

1. **Live source, build manifest included.** Grep the candidate trees for the mechanism's own symbols (the kernel/OS calls it must make, not the feature name). A header, API table, or helper proves an interface, never an implementation: check `CMakeLists.txt` / `*.vcxproj` for a target that builds it, then grep for callers of the declared entry points. Declared-but-unreferenced is a leftover, and say so.
2. **Live docs.** Grep the docs tree for the feature name and for the mechanism. One hit in an index or split-document table that files the item under "archive" is a pointer, not a description.
3. **Git history for retired docs.** `git log --all --oneline -S '<term>' -- <docs path>` finds the commit that carried the doc; `git show <commit>:<path>` still reads it after it left the disk. Retired plans usually carry their own status line ("PARKED", "superseded by") and the acceptance criteria nobody met.
4. **Reference clones.** Third-party trees under `references/` are evidence for the technique, not for the product. Cite `file:line` there to explain how the mechanism works, and state plainly that they are not ported.

Verdict vocabulary, in plain terms: **implemented** (built target + callers + wired into a real path), **parked plan** (design doc exists, no code; name the doc and quote its status line), **reference-only** (the technique exists only in a cloned repo). Never blur these. When an older audit and a later plan disagree, report both and name which one the live tree reflects.

Command recipes, junction-workspace traps, and retired-doc recovery: `references/status-audit.md`.

## Critique Mode

Triggered when the user asks for architectural issues, problems, or improvements, not just understanding.

### Step 1. Explain First

Run the full explain flow above (Steps 1-4). You must understand the architecture before critiquing it.

### Step 2. Spawn Critics

After the explanation is complete, spawn one architectural critic per model in the configured how-critics list, all in a single message. Spawn the critics via `task`, up to 3 `tasks` per call. Read-only. `task` has no per-call model field, so a per-model critic list needs `subagent chat -q -m <model>` per critic. Model choice lives in that list, not here.

Read `references/critic-prompt.md` for the prompt template. Each critic gets:
1. The explanation from Step 1 (so they don't re-explore)
2. The relevant file paths (so they can read the actual code)
3. The architectural critique rubric from `references/critique-rubric.md`

### Step 3. Lead Judgment

Same lead-judgment buckets as **grill-me** review. You're a pragmatic lead, not an aggregator.

Categorize findings:
- **Act on.** Architectural problems worth fixing now
- **Consider.** Real concerns, but the cost/benefit is unclear
- **Noted.** Valid observations, low priority
- **Dismissed.** Wrong, missing context, or style preference

Present the explanation first (from Step 1), then the critique verdict below it. The explanation should stand on its own; someone who just wants to understand the system shouldn't wade through critique.
