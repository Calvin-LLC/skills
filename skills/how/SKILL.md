---
name: how
description: Use when asked how a subsystem, feature, or flow works, where it lives, or what owns it, including whether it is implemented yet or what is architecturally wrong with it. For why it exists, use the why skill.
---

# How

Answer "how does X work?" by exploring the codebase and explaining it at the level of a senior engineer onboarding onto the subsystem: enough for a working mental model, not annotated source.

Modes:

- **Explain** (default).
- **Status audit**: the question also asks whether it exists ("has this been implemented?", "is it in the SDK?", "still reference-only?").
- **Critique**: the user asks for architectural issues, problems, or improvements.

## Explain

### Step 1. Scope and complexity

Identify what is asked: a subsystem, a feature flow, an architectural overview, or a runtime trace. If ambiguous, state your best-guess interpretation and explore. Don't ask; the user redirects if you're off.

**Calibrate to the user's stated background.** Skip fundamentals they say they know and spend the words on the project-specific mechanism. Expand local shorthand, codenames and internal abbreviations on first use, or replace them with the concrete mechanism. Measured counts and `file:line` anchors beat keyword-dense summary.

- **Simple** (one module, a small utility, "how does function X work"): go to Step 2b.
- **Complex** (spans several files or services, a cross-cutting feature, a full overview): go to Step 2a.

When in doubt, lean simple; spawn explorers later if the explanation hits a wall.

### Step 2a. Explore (complex only)

Split the question into 2-4 distinct angles so explorers don't duplicate work (e.g. data model and state; request path and enforcement; configuration and metrics).

Locate before you dispatch. An explorer is a `scout`: it has `read`, `find`, `grep`, `glob` and `web_search` (plus `ast_grep` when `astGrep.enabled` is on) and no `lsp` or `bash`, so the symbol lookups are yours. Run `lsp` on the question's key types and entry points: `symbols` with `file: "*"` and a `query` to find them, then `definition` and `references` to follow them. For a structural question (every implementer, every call of one shape), use `ast_grep` when `astGrep.enabled` is on, otherwise `ast-grep run -p '<pattern>' -l <lang> <path>` in `bash`. With no language server for the language (`lsp` `status` lists them), locate with structural search and `grep`. Stop when each angle has exact files and symbols to start from.

Spawn the explorers in one `task` call, one `tasks[]` item per angle with `agent: "scout"` (the `smol` model role). Build each item's `task` from `references/explorer-prompt.md`, filled with its angle and its starting files and symbols. The template has explorers start from those locations rather than from a text search. Explorers return components, flow, files read and non-obvious findings; overlap is fine. Go to Step 3.

### Step 2b. Direct explain (simple only)

One read-only pass that explores and explains. Find the entry point with `lsp` as in Step 2a, then spawn one `task` item with no `agent` (the default worker; tell it to stay read-only). Its `task` is `references/explainer-prompt.md`, minus the explorer findings, plus the entry point's file and symbol. Go to Step 4.

### Step 3. Synthesize (complex only)

Spawn one `task` item with no `agent` (the default worker; tell it to stay read-only). Its `task` is the template in `references/explainer-prompt.md` filled with every explorer's output, read from `agent://<id>`. It reconciles overlap, resolves contradictions against the code, and writes one explanation.

### Step 4. Present

Present the explainer's output. Edit lightly for clarity or conversation context; don't substantially rewrite.

### Output format

Adapt to the question; drop sections that add nothing.

- **Overview.** 1-2 paragraphs: what it is, what it does, why it exists. Enough to decide whether to keep reading.
- **Key Concepts.** The types, services, or abstractions needed to follow the rest, each briefly defined.
- **How It Works.** The core: what triggers it, what happens step by step, where data goes, the decision points. Prose, not pseudocode. Cite files and functions; code blocks only when a snippet is necessary.
- **Where Things Live.** The files and directories needed to start working in this area.
- **Gotchas.** Surprising behaviour, sharp edges, history that explains why something looks odd.

## Status audit

Explain the mechanism first, then give the verdict: it is the decision the user is making, and answering only "how it would work" reads as a claim that it works. Verdicts, never blurred:

- **implemented**: built target + callers + wired into a real path.
- **parked plan**: a design doc exists, no code; name the doc and quote its status line.
- **reference-only**: the technique exists only in a cloned third-party repo.

A header, API table, or helper proves an interface, never an implementation. When an older audit and a later plan disagree, report both and name which one the live tree reflects. Before auditing, read `references/status-audit.md` for the audit order, commands, traps, and report shape.

## Critique

1. **Explain first.** Run Explain Steps 1-4; you must understand the architecture before critiquing it.
2. **Spawn critics.** One `task` call, one `tasks[]` item per critic, each a default worker (no `agent`): the bundled `reviewer` reviews a patch in its own format and does not follow the template. For different models, set `model` on each item when `task.perCallModel` is on, or use custom agents whose `model:` lines differ. With neither, every critic runs on one model: spawn one and say model diversity was unavailable. Build each prompt from `references/critic-prompt.md`: the explanation (so critics don't re-explore), the relevant file paths, and the rubric in `references/critique-rubric.md`. Tell each critic to stay read-only. The template has each critic reply with one JSON object: a `findings` array whose entries carry `severity`, `title`, `components`, `finding`, `evidence` and `impact`. Read them through `agent://<id>/findings/<index>`, or `agent://<id>` whole when the reply is not valid JSON. When `task.structured` is on, pass the same shape as each item's `outputSchema`.
3. **Lead judgment.** You are a pragmatic lead, not an aggregator. Sort findings into the **grill-me** skill's buckets: **Act on** (worth fixing now), **Consider** (real, cost/benefit unclear), **Noted** (valid, low priority), **Dismissed** (wrong, missing context, or style preference).

Present the explanation first, then the critique verdict below it. The explanation must stand on its own for a reader who only wants to understand the system.
