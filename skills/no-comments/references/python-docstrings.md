# Python docstrings under the no-comments test

A docstring is a string literal, not a comment token, so tokenize-based comment passes skip it. It is still prose that narrates, restates signatures and tells history, and the same keep test applies. A comment-only pass that leaves docstrings alone has not answered "did you delete all comments": report both counts.

## Scripts

`scripts/docstring_inventory.py OUT_DIR --chunks 6` writes the inventory and judge chunks; `scripts/docstring_apply.py dry|apply INVENTORY DECISIONS... [--protect PATH...]` enforces the constraints below and the AST-equality proof, auto-protecting any file that mentions `__doc__`. Dry-run first. The apply step does not format: run the repo formatter after it, then the length re-trim if `line-too-long` rose.

## Inventory

`ast.walk` every tracked `.py` (skip vendored, backups, reference trees); a docstring is `body[0]` of a Module, ClassDef, FunctionDef or AsyncFunctionDef when it is an `Expr(Constant(str))`. Record file, line, end line, kind, owner, line count and whether it is the only statement in its body. Measure size buckets first: the multi-line ones usually hold about 90 percent of the lines.

## Decision per docstring

- KEEP: states something the code cannot show, verified against the code now, short.
- TRIM: rewrite to one plain line that keeps only the surviving fact.
- DELETE: only for function or method docstrings that are not the sole statement of the body.

Constraints that make the mechanical apply safe:
- Never DELETE a module or class docstring: pylint missing-module/class-docstring is ratcheted and the docs page may count modules without a docstring. TRIM to one line instead.
- Never DELETE a docstring that is the only statement in a body (the body would become empty).
- Skip files that print `__doc__` as CLI help (`argparse description=__doc__`): grep for `__doc__`, `getdoc`, `get_docstring` first.
- Skip files the repo marks ask-first or parked, even if the judges covered them; revert any such file a mass pass touched.
- Pylint's docstring-min-length exempts short functions, so deleting those costs nothing; check `.lint/pylintrc` before assuming.

## Length budget

A trimmed line replaces triple-quote delimiters plus indent: budget = line-length minus indent minus 6. Hand the judges that budget per item, or the formatter-checked line-too-long count rises (it did by over 100 findings when one-liners were written without a budget). A second pass that only re-shortens over-budget one-liners, with `len(new) <= max` asserted in code, fixes it.

## Judging and applying

- Judges (subagents are fine when the user asks for them) read the code that follows each docstring, not the docstring alone, and write a decisions JSON keyed by inventory id. Expect roughly 3 to 6 percent of docstrings to make a claim the code refutes (a "best effort" that does not catch, "event-driven" that polls, a caller list naming a function that no longer calls it, a doc path that does not exist). Those are TRIMmed to the true part or deleted; they are the evidence that docstrings rot.
- Apply with one script: edit each file bottom-up by recorded line, refuse if the text at the recorded line no longer matches the inventory, then prove the edit by comparing `ast.dump` of the old and new trees with every docstring stripped (a body emptied to nothing becomes `pass` on both sides). Zero differing files, then run the formatter, py_compile, and the lint ratchet.
- Dry-run the whole decision set first; refusals (protected files, forbidden deletes) show up as a problem list instead of a half-applied tree.
- After applying, fix doc citations that pointed past a file's new end (`make cite`-style linters flag them).
