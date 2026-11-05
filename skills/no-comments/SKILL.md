---
name: no-comments
description: "Use when asked to strip, audit, or clean up code comments. Deletes unproven, narrating, and stale comments from a diff or file set, in the current session."
disable-model-invocation: true
---

# No comments

Delete comments that are not provably true and useful. A comment is usually written after the fact to rationalize the code, and that rationalization is often wrong or meaningless — yet once it exists, agents and people treat it as the source of truth and keep acting on it after the code changes, locking in the very design it was invented to justify. A wrong comment is worse than none.

Do the whole job yourself, in this session. Do not spawn subagents, workers, or other sessions on your own initiative. When the user explicitly asks for subagents to find or judge candidates, let them produce findings or decision files only; every edit, and the check that only comments changed, stays in this session. When the user explicitly orders subagents to make the edits, give each a disjoint file list, forbid `git checkout`/`restore`/`stash`/`reset`/`clean` in the brief, and re-run the comment-only proof yourself on the result (`references/edit-mechanics.md`, "Proving only comments changed"); an agent's own pass report does not count.

Docstrings are comments for this pass. When the user says comments, include them and the same keep test applies, even though Python stores them as string literals. See `references/python-docstrings.md` for the inventory, the delete/trim rules, and the AST-equality proof; `scripts/docstring_inventory.py` and `scripts/docstring_apply.py` do the mechanical halves. When asked what was removed, report what remains (plain comments, suppressions, docstrings, vendored files) as counts.

## Scope

1. Files or paths the user named.
2. Otherwise the diff against the base branch (default `main`), working tree included. In a multi-repo or junctioned workspace, resolve the scope per repo (see `references/edit-mechanics.md`).

Never touch anything outside the scope, including pre-existing comments beside the diff.

Out of scope even when named: data and resource files (font atlases, lookup tables, constant arrays, dump JSON, generated output, test fixtures). A comment-looking line inside a data blob is data. Classify by what the bytes are, not the extension. Hash these files before and after the pass and confirm they are unchanged.

## What dies

- Narration that restates the code, phase markers, banners, section dividers.
- Top-of-file headers, module overviews, author blocks. Exception: legal or license text.
- Commented-out code.
- Dated workaround sermons and long justifications.
- Notes about history, ticket chatter, "fixed for X", "new", "temporary".
- Claims about mechanism or callers that that are false on the current code. Verify every header comment that says who uses a symbol, what cleans it up, or what its lifetime is — those go stale when the cleanup mechanism changes shape. Grep the claimed consumer and the claimed cleanup path; if either is gone, the comment is deleted or replaced in the same unit that changes the behavior, never left.
- Anything speculative, assumed, or unverifiable ("probably", "should", "I think").
- Lint and type suppressions (`eslint-disable`, `@ts-ignore`, `@ts-expect-error`, `#pragma warning(disable)`, `# noqa`) unless the rule is faulty, pedantic, or style-only. If the rule guards correctness or safety, delete the suppression only when you can fix the underlying code in scope. Otherwise leave it and list it as an open flag.

**In agent-written code that was never reviewed, "what dies" is everything, and the keep test collapses.** A tree an agent produced comment-by-comment has no comment whose claim was ever verified against a working build: justifications cite measurements taken while the code beneath them was broken (`split-view was tried ... measured: <failure symptom>` where the failure was the surrounding subsystem, not the change). Those are worse than no comment, because a later agent quotes them back as evidence — one such comment was asserted at the operator as proof during a live investigation and had to be retracted. Rule: in a never-reviewed tree, do not evaluate keeps per comment; the whole class goes, and the only survivors are license headers and tooling pragmas. Say so when reporting, because the operator asked for deletion precisely because the comments had already misled someone.

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

- Read the named symbol and its callers (grep, language server).
- Check history for why it exists (`git log -S`, `git blame`).
- If it claims external behavior, check the dependency's docs or reproduce it.

Proven true and about something we cannot change: keep it, trimmed to the fact. Refuted, unprovable, or about our own code: delete it. If our own code is surprising enough to need the comment, the comment is hiding a design problem. Delete it and add a one-line flag naming the symbol and the rename, extract, or type change that would make it obvious. Do not make that change unless the user asked.

## Constraint comments

For `do not change wording`, `talk to X before editing`, or `must match Y`: offer the cheapest in-scope encoding (type, test, assertion, lint rule, CI check). Wait for approval. If approved, add the encoding, then delete the comment. If not approved, delete the comment and report the constraint as unenforced.

## Editing safely

Read `references/edit-mechanics.md` before editing. The core rules:
- **Diff-scoped span targeting:** For diff-scoped passes, derive line spans directly with `git diff -U0 <base> -- <file>`. Parse `@@ -old,count +new,count @@` hunks to touch added comment lines only, leaving pre-existing comments and unchanged lines byte-identical.
- **Opener protection:** End each replacement at the last comment line, never include the opener or code below it.
- **Syntax verification per file:** Immediately validate AST/syntax before test suites (`ast.parse` for Python, `node --check` for JS, `bash -n` for Shell).
- **Generated files:** a comment inside a generated header comes from a string in the generator, so delete it there and regenerate (`--apply`), then check the generator still parses and the regenerated output diff is comment lines only. Editing the output alone is undone on the next run.
- **Whole-file strips for files you created this session, hunk-scoped strips for files that already existed:** derive added-line spans from `git diff -U0 <base>` for existing files and match only full-line `//` or `#` comments inside those spans, so the owner's older comments stay byte-identical.
- **False-positive traps:**
  - CSS selectors: Universal (`* {`) or attribute selectors mimic comment syntax (`/*`, `* `). Always require full comment delimiters.
  - Embedded docs: Scripts that clean or generate templates often contain markdown strings (`## Heading`) inside multiline string literals. Never strip `#` inside string constants.

Python docstrings: `references/python-docstrings.md`.

## Bulk full-line strips

For a whole-tree pass where the user wants every comment gone, a script is right — but only for the subset that is mechanically safe. Two traps cost a build each:

- **Full-line `//` only. Never handle `/* */` without a lexer.** A block-comment branch enters block mode on any `/*`, including one inside a string literal, and then eats every line until it finds a `*/` — deleting live code. The build catches it (`undeclared identifier` on a symbol whose declaration vanished) but only after the damage is written. If the tree needs block comments removed too, do those by hand or skip them; a partial strip that builds beats a complete strip that quietly deleted a declaration.
- **Preserve each file's original line endings.** Splitting on a detected newline and rejoining with the majority style converts every LF file to CRLF and puts thousands of phantom changed lines in the diff, hiding the real change entirely. Compare each file's CRLF count against `HEAD` before and after and normalise back to what that file had. A pure comment pass shows deletions only in `git diff --stat`; a suspiciously large insertion count means the endings moved.
- **The build is the only proof.** Run the project's build (and a cheap test binary if one exists) after the strip and before committing. `git diff -U0 | grep '^[+-]' | grep -v '^[+-]\s*//'` should print only `+++`/`---` and submodule pointer noise.

## Check your work

- Re-read each edited region. Run the language's parser or build immediately after modifying each file:
  - Python: `ast.parse(code, filename=path)`
  - JavaScript / Node: `node --check <file>`
  - Shell: `bash -n <file>`
- Confirm no added comment survives in the diff that you did not mean to keep (commands in the reference).
- Confirm only comment lines changed. Every other line in the diff must be byte-identical.
- Run the project's tests if they exist and are cheap. If strict coverage floors fail partial test runs, pass `--no-cov` to verify behavior.
- For diff-scoped passes across modified trees, isolate added spans via zero-context hunks (`git diff -U0 <base> -- <file>`) so pre-existing comments outside the diff are preserved untouched.

## Report

Files touched, number of comments deleted, comments kept with the reason and the evidence for each, flags on code (symbol and suggested change, one line each), suppressions left open, unenforced constraints, and anything skipped or out of scope.
