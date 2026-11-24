---
name: deslop
description: Use for a code hygiene or cleanup audit that measures complexity, nesting, file length, duplicates, dead code, type escapes, and coverage against numeric ceilings; not for subjective style review.
license: MIT
---

# Deslop

Quantitative complexity audit. Measures the tree against numeric ceilings and ranks violations. Default is audit and report; change code only when the user asks.

## Ceilings and metrics

| Metric | Ceiling | Target |
|---|---|---|
| **Cyclomatic complexity (CCN)** | < 15 per function | Control-flow branching (if, match, loops, try-catch) |
| **Nesting depth** | < 4 levels | Deeply nested conditionals and loops |
| **Parameters per function** | < 5 parameters | Excessive argument signatures |
| **Lines of code per file** | < 500 LOC | Overly broad single-file modules |
| **Redundant code** | 0 duplicate clusters at a stated minimum clone size | Cut-and-paste clones |
| **Dead code** | 0 unused functions | Exported or private dead paths |
| **Type escapes** | 0 `any` and untyped casts | Typed languages only; TypeScript `unknown` is the safe type, not an escape; N/A where the language has no such escape |
| **Test coverage** | The repo's own coverage gate when it defines one; otherwise N/A | Paths that gate requires covered |

## Behavior

Needs a shell tool: it runs local static tools, ranks findings by severity, and presents clean metrics. Run the measurement yourself in a session that has a shell. Never delegate it to a read-only subagent; it cannot run the tools and can only hand-count.

- Exclude vendor directories (`node_modules/`, `vendor/`, `dist/`, `build/`) and generated, embedded-data, and third-party files (byte-array tables, serialized models or images, minified bundles). Decide by content, not name, and list the excluded files separately in the report.
- A metric that reports 0 is not PASS until you confirm the tool ran and its column is populated; otherwise report "not measured".
- Measure coverage only when the repo defines its own coverage gate (a threshold in its config or CI). With no gate, report coverage as N/A and recommend no tests to raise it.
- Report duplicates as clusters above a minimum clone size, not raw block counts. Search the whole repo for uses of an exported symbol before calling it dead.
- When fixing on request, do not refactor a dispatcher or table-driven function for the complexity number alone.

## Tools

Defaults, in the order of the table. Use the repo's own equivalent when it has one.

- **Complexity, nesting, parameters, file length:** `lizard` (`pip install lizard`; if `pip` is not on `PATH`, `python -m pip install lizard`). Run `lizard` with the `-C`, `-a`, and `-End` options for the ceilings above; its per-file NLOC column covers file length.
- **Duplicates:** `jscpd` (`npx jscpd`, needs Node), limited to the languages the repo actually uses with `--format`, and with `--min-lines`/`--min-tokens` stated in the report.
- **Dead code and type escapes:** the language's own linter or compiler (for example `tsc --noUnusedLocals`, ESLint, `ruff`, `vulture`, `staticcheck`, `cargo clippy`).
- **Coverage:** the repo's own coverage command, run only when the repo has a coverage gate.

A tool that is missing, or that fails to run, gives "not measured" for its metrics, with the install command in the report. Never replace it with a hand count or an estimate presented as a measurement.

## Report

One table: metric, ceiling, measured, verdict, worst offenders (file:line). Below it, the excluded files.
