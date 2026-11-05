---
name: deslop
description: Programmatic scan of standard code quality indexes against deterministic numeric thresholds (CCN < 15, nesting depth < 4, file length < 500 LOC, duplication, and dead code).
license: MIT
---

# Deslop

Quantitative complexity audit. Measures the tree against numeric ceilings and ranks violations.

## Ceilings and metrics

| Metric | Ceiling | Target |
|---|---|---|
| **Cyclomatic complexity (CCN)** | < 15 per function | Control-flow branching (if, match, loops, try-catch) |
| **Nesting depth** | < 4 levels | Deeply nested conditionals and loops |
| **Parameters per function** | < 5 parameters | Excessive argument signatures |
| **Lines of code per file** | < 500 LOC | Overly broad single-file modules |
| **Redundant code** | 0 duplicate blocks | Cut-and-paste clones |
| **Dead code** | 0 unused functions | Exported or private dead paths |
| **Type escapes** | 0 `any` / `unknown` | Strict typing violations |
| **Test coverage** | >= 60% line coverage | Untested functional paths |

## Behavior

Runs local static tools, ranks findings by severity, and presents clean metrics. Excludes vendor directories (`node_modules/`, `vendor/`, `dist/`, `build/`).
