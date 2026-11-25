# Survey: what to restructure

Read when the ask is what to refactor, consolidate, dedupe or simplify across a codebase and no single change is named yet. The output is a short ranked list in the reply. "Nothing here is worth restructuring" is a valid result.

A candidate is a place where one change keeps costing edits in several places, or where a caller must know what a module should hide. Size, age and ugliness are not candidates. A stable file nobody touches can wait.

## 1. Measure where the effort goes

If the user named a module or a pain, start there and use the scan to check it. Otherwise the scan picks the area.

Run `scripts/hotspots.py --root <repo>` from this skill's folder. It reads git history only, so it works in any language. It prints:

- **Most-changed files** in the window: commits touching each, lines changed, lines now. Frequency first, size second.
- **Files that change together**: shared commits, and the share of each file's commits that were shared. A pair in different folders with no import between them is a dependency the code does not declare.

Read its first line: the window, commits read, commits skipped as bulk. Under 20 usable commits the rates are anecdotes: widen `--days` or say the history is too thin and fall back to reading. `ERROR` means the scan did not run, not that the repo is clean.

When the repo already has an analyzer for its language (a dependency-graph or cycle checker, a duplicate finder, a dead-code tool), run it and add its rows. In-file complexity, duplication and dead code belong to the **deslop** skill.

## 2. Read before you believe

The scan says where to look, not what is wrong. For each of the top files and its strongest partners, read the code and three or four of the shared commits (`git log -p --follow` on the pair). Then name what you saw:

- **Scattered rule.** The same condition, constant, schema or format is edited in several files. One owner would take those edits.
- **Committed output.** A built or generated file changes with its source in almost every commit. Generate it in the build.
- **Leaky module.** A caller changes whenever the module's insides change. The interface exposes what it should hide.
- **Pass-through.** A layer forwards calls and adds nothing. Delete-test it: if deleting it moves no complexity anywhere, it earns nothing.
- **Two things in one file.** Two groups of commits touch disjoint halves for unrelated reasons.

Drop a pair when the reason is innocent: a test with its subject, a header with its source, a feature built across layers in one commit, a formatter or rename sweep. Check the repo's decision records and the comments around the code before proposing something it already tried and rejected.

Check each name against the code in this order:

1. `lsp`. `references` counts a module's callers (leaky module, pass-through), `symbols` lists what one file defines (two things in one file), `definition` finds the owner of a rule, `diagnostics` shows what already fails.
2. Structural search for the repeated condition or call shape: `ast-grep run -p '<pattern>' -l <lang> <path>` in `bash`, or the `ast_grep` tool when `astGrep.enabled` is on.
3. Text `grep`, for what those two cannot see: strings, config, comments, generated code.

## 3. Rank and report

Keep at most five candidates. Each one carries all three parts:

| Part | Content |
|---|---|
| **Finding** | The scan rows and the commits you read: files, shared count, both rates, window. What you did not examine. |
| **Cost** | What it has cost here, counted: "9 of the last 12 changes to the price format edited these 3 files". |
| **Change** | The smallest structural move that removes that cost, what stays untouched, and the before and after number that would prove it (the same change touching one file, not three). |

Rank by cost removed per unit of risk. A candidate backed only by "large file" or "many dependents" is labelled **investigate**. Mark each **strong**, **worth exploring** or **speculative**. If every candidate is speculative, say the scan found nothing worth doing.

Give the list as a table in the reply, with the top recommendation and why, then stop: the user picks.

## 4. After the user picks

Take one candidate per session into Phase A in SKILL.md, with its finding as the first grounding fact. Before a move that could break callers, run **blast-radius**. After it lands, re-run the scan and compare the number named under Change.
