---
name: no-comments
description: "Use when asked to strip, audit, or clean up code comments: deletes unproven, narrating, and stale comments from a diff or file set, in the current session."
---

# No comments

Delete comments that are not provably true and useful. A comment is written after the fact to rationalize the code, and agents and people then treat it as the truth after the code changes. A wrong comment is worse than none.

Do the whole job yourself, in this session. Do not call `task` on your own initiative.

- The user asks for subagents to find or judge candidates: they produce findings or decision files only. Every edit, and the check that only comments changed, stays in this session.
- The user orders subagents to make the edits: give each `task` item a disjoint file list, forbid `git checkout`/`restore`/`stash`/`reset`/`clean` in the brief, and re-run the comment-only proof yourself (`references/edit-mechanics.md`, "Proving only comments changed"). An agent's own pass report does not count, and a subagent running this skill leaves the proof to its parent.

Docstrings are comments for this pass. When the user says comments, include them, and the same keep test applies. For Python, read `references/python-docstrings.md`. `scripts/docstring_inventory.py` and `scripts/docstring_apply.py` do the mechanical halves.

## Scope

1. Files or paths the user named.
2. Otherwise the diff against the base branch (default `main`), working tree included. In a multi-repo or junctioned workspace, resolve the scope per repo (`references/edit-mechanics.md`).

An empty diff is not a result. Do not report zero and stop. If the user already said project, codebase, or end to end, run on the whole project without asking. Otherwise ask once, through `ask`, whether to run on the whole project, which is what the user usually means.

Never touch anything outside the scope, including pre-existing comments beside the diff.

Out of scope even when named: data and resource files (font atlases, lookup tables, constant arrays, dump JSON, generated output, test fixtures). A comment-looking line inside a data blob is data. Classify by what the bytes are, not the extension. Hash these files before and after the pass and confirm they are unchanged.

## What dies

- Narration that restates the code, phase markers, banners, section dividers.
- Top-of-file headers, module overviews, author blocks. Exception: legal or license text.
- Commented-out code.
- Dated workaround sermons and long justifications.
- Notes about history, ticket chatter, "fixed for X", "new", "temporary".
- Claims about mechanism or callers that are false on the current code. Verify every header comment that says who uses a symbol, what cleans it up, or what its lifetime is: run `lsp` `references` (`grep` where no language server covers the language) on the claimed consumer and the claimed cleanup path. If either is gone, delete or replace the comment in the same unit that changes the behavior.
- Anything speculative, assumed, or unverifiable ("probably", "should", "I think").
- Lint and type suppressions (`eslint-disable`, `@ts-ignore`, `@ts-expect-error`, `#pragma warning(disable)`, `# noqa`) unless the rule is faulty, pedantic, or style-only. If the rule guards correctness or safety, delete the suppression only when you can fix the underlying code in scope. Otherwise leave it and list it as an open flag.

**In agent-written code that was never reviewed (the user says so, or commit authorship shows it), everything dies.** No comment there was verified against a working build, and a later agent quotes them back as evidence. Do not run the keep test per comment. The only survivors are license headers and tooling pragmas. Say so in the report.

## What survives

A comment survives only if all three hold:

1. It is about something the code cannot show: a non-obvious reason, or behavior forced by an external dependency, platform, vendor, or protocol we cannot change.
2. You verified the claim this session against the code, the docs, or by running it. Reading the comment is not verification.
3. It is clear, concise, and states facts only.

Always kept:
- Legal and license headers.
- Doc comments that define a public API contract, if still accurate.
- Issue or RFC links explaining a constraint the code cannot express.
- Tooling directives (`prettier-ignore`, `clang-format off`, `// @ts-nocheck` that is truly needed).
- Self-labeling log or output strings. They are data, not prose.

When unsure whether a keep applies, delete the comment.

## Verifying a claim

For `IMPORTANT`, `do not remove`, `too risky`, `fine for now`, or any long justification, find out whether it is true before you decide:

- Read the named symbol and its callers (`lsp` `definition` and `references`, else `grep`).
- Check history for why it exists (`git log -S`, `git blame`).
- If it claims external behavior, check the dependency's docs or reproduce it.

Proven true and about something we cannot change: keep it, trimmed to the fact. Refuted, unprovable, or about our own code: delete it. If our own code is surprising enough to need the comment, the comment is hiding a design problem. Delete it and add a one-line flag naming the symbol and the rename, extract, or type change that would make it obvious. Do not make that change unless the user asked.

## Constraint comments

For `do not change wording`, `talk to X before editing`, or `must match Y`: offer the cheapest in-scope encoding (type, test, assertion, lint rule, CI check). Wait for approval. If approved, add the encoding, then delete the comment. If not approved, delete the comment and report the constraint as unenforced.

## Editing safely

Read `references/edit-mechanics.md` before editing. Keep inventory and strip scripts in the OS temp directory so they never enter the diff. The core rules:

- **Diff-scoped passes touch added lines only.** Derive the spans from `git diff -U0 <base> -- <file>` hunk headers and match only comments inside them, so pre-existing comments and unchanged lines stay byte-identical. Whole-file strips are for files you created this session.
- **Opener protection.** End each replacement at the last comment line. Never include the opener or code below it.
- **Parse each file right after you edit it,** before any test suite: `ast.parse(code, filename=path)` for Python, `node --check <file>` for JavaScript, `bash -n <file>` for shell, the build otherwise.
- **Generated files.** A comment in generated output comes from a string in the generator. Delete it there and regenerate, then check the generator still parses and the regenerated diff is comment lines only. Editing the output alone is undone on the next run.
- **Find comments by syntax node, not regex.** Where tree-sitter has a grammar, `ast-grep run -k comment <path>` in `bash` lists every comment node and no string that looks like one. With no grammar, follow "Bulk full-line strips" in the reference.
- **Strip a repeated comment with `ast_edit`:** its exact text as `pat`, an empty `out`. The preview lists every copy and `resolve <reason>` applies them. Check `git diff` after: a failure partway leaves earlier files changed.

## Check your work

- Re-read each edited region.
- Confirm no added comment survives in the diff that you did not mean to keep (commands in the reference).
- Confirm only comment lines changed: every other line in the diff is byte-identical.
- Run the project's tests if they exist and are cheap. If a coverage floor fails a partial run, disable coverage for it (pytest: `--no-cov`).

## Report

Files touched, comments deleted, comments kept with the reason and the evidence for each, flags on code (symbol and suggested change, one line each), suppressions left open, unenforced constraints, and anything skipped or out of scope. When asked what was removed, also report what remains (plain comments, suppressions, docstrings, vendored files) as counts.
