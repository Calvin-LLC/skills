---
name: readme-clean
description: "Use when asked to clean up, optimize, rewrite, or de-slop a README: rewrites it plain and concise, checks every claim against the repo, and proves no technical fact was dropped."
---

# README clean

Rewrite a README so a tired engineer understands it in one pass. The deliverable is prose a human wrote on purpose, not a template. Preserve every technical fact. Kill every AI tell.

## Load first

Read the **unslop** skill before editing. Its pattern list is the checklist. This skill adds the README workflow on top and does not restate the patterns.

## Scope

The caller names the file, directory, or explicit file list. Otherwise `README.md` in the cwd. If none exists, stop and report. Do not invent one for an empty repo.

The same workflow covers any text the user wants plain and factual for a technical reader, not only READMEs.

- For page or site text read at a glance (an HTML caption page, a demo walkthrough, a status dashboard, a run log digest), read `references/page-text.md`.
- For a directory, a file list, or "all docs", read `references/doc-sets.md`: one pass per file, tiers by reader, scripted tell sweeps.

Rules for every scope:

- Delete text you cannot make truthful. If a claim cannot be checked against the artifact right now, cut the sentence or the whole step instead of hedging it. A wrong line gets removed, not softened. A page that says only true things beats a fuller page that overclaims.
- Persona and agent-instruction files (`AGENTS.md`), to-do lists, and data tables are out of scope unless the caller names them. "All docs" does not cover them.
- Keep each file's line endings.
- Do not commit unless asked. Offer one commit line at the end.

## Workflow

1. **Inventory facts.** Read the README and list every technical fact: names, versions, commands, flags, paths, URLs, limits, defaults. This list is the contract for the rewrite. Nothing on it may vanish. If the docs already carry uncommitted edits from an earlier or sibling pass, read that diff first and build on the working tree. Never re-fix what a pending edit already fixes.
2. **Verify against the artifact.** Read the code or files the README describes. A README that documents behavior the artifact does not have is wrong in a way prose polish cannot fix. Verify in bulk, before any edit, so the corrections land in one pass. Correct what fails. Report what you could not verify as unverified, per claim.
   - Existence-check every referenced path, command file, and script in one pass (a short script or a batch of file-existence checks), and check each script name inside a command example separately. A file deleted from the tree is the most common stale claim.
   - Re-count every number from its source instead of trusting the prose: counts from directory listings and manifests, flags from the config that sets them, intervals and TTLs from the constants that read them. Prose numbers drift silently.
   - Measure size and line-count claims (`cloc` for code lines; count bytes with your file tools). Raw line counts overstate code lines.
   - Grep env defaults, ports, and timeouts in the file that reads them, not the file that installs them.
   - When the doc describes a live system, measure the system, not the repo, and record the audit date in the doc.
   - Look for a duplicated or truncated tail left by an earlier bad edit: a closing section pasted twice, a fragment starting mid-word.
   - A path with no findable replacement stays in the doc with a plain note that it is missing and where it used to live. Do not delete the pointer and do not invent a new one.
   - Never write a secret's value into a tracked doc. Put it in a gitignored env file (confirm with `git check-ignore -v <file>`), add a tracked `*.env.example` with the key and no value, and document only the variable name and the script that reads it. Then grep the tree and `git log -S` for the value and report any hit with the value masked.
3. **Check structure.** A README needs, in roughly this order: what it is (one paragraph), install, usage with real examples, and anything the reader must not do. Sections beyond that earn their place by being read by someone. Delete empty boilerplate sections: a badges row with no badges, "Contributing" with no process, "Roadmap" with one done item. Do not add sections the project does not need.
4. **Rewrite.** Apply the unslop checklist. The patterns that pay most in a README are active voice with a named actor, the mechanism instead of the feeling ("evidence-driven" says nothing, "audits X and reports findings" does), one idea per sentence, sentence-case headings, and no em dashes. Two README rules on top:
   - Describe every file in a layout block. A bare filename in a tree tells the reader nothing.
   - Code examples stay untouched unless they reference something that does not exist.
5. **Fact audit.** Diff old against new. For each item in the inventory from step 1, confirm it appears in the rewrite (possibly reworded). Report any that dropped and why. A dropped fact is a bug in the rewrite, not a style choice.
6. **Self-audit.** Ask: "What makes this obviously AI generated?" Fix remaining tells. Then ask: "Could this paragraph appear unchanged in another project's README?" If yes, it says nothing about this project. Cut it or make it specific.

## Report

- Files changed, lines before/after (bytes is fine when the artifact is generated).
- Facts preserved (count) and any dropped, with reason.
- Claims checked against the artifact and their result (verified, unverified, corrected).
- Sections deleted, if any.
