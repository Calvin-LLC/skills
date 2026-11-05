---
name: wcag
description: Web accessibility audit (WCAG 2.2 A/AA). Measures rendered pages across five browser passes and reports violations deterministically with selectors and snippets.
license: MIT
metadata:
  version: "4.0.0"
---

# WCAG

Invoking this skill measures the page you name against WCAG 2.2 Level A and AA and produces an audit report. The user gives a URL, a local file, or a dev-server address. If they give none, ask for one.

Source inspection alone never settles a criterion, so every report comes from a real browser run.

> **Path Resolution Rule:** All `references/*` and `scripts/*` paths below are relative to this skill's installation directory (or `skill://wcag/` in OMP), NEVER the target repository's working directory.

## Measure

```bash
node <skill-dir>/scripts/wcag.mjs <url|file.html>
```

Needs Node 22 or newer and a Chromium-based browser on `PATH` (or `CHROME_BIN` set to its path). The script runs nine checks in five passes: desktop 1280x800, phone 390x844, dark colour scheme, reduced motion, and forced colours. A run takes about a minute. It prints a summary on stdout and writes the full JSON to `.tmp/wcag/report.json` in the working directory. Exit code: `0` no failures, `2` failures found, `1` the run broke.

Every non-GET request is blocked during form submits and key presses, so a run changes nothing on the server. For a page behind a login, point the script at a static copy of the rendered page.

| Check | Measures | Criteria |
|---|---|---|
| `contrast` | Computed colour pairs with alpha, opacity, and ancestor backgrounds composited. Text over images or gradients is sampled from screenshots taken with the text hidden. Placeholders and field borders | 1.4.3, 1.4.11 |
| `keyboard` | Real Tab key events. Records every stop, detects traps, compares before and after pixels for a focus indicator, samples whether a sticky element covers the focused one | 2.1.2, 2.4.7, 2.4.11, 2.4.3, 2.4.1 |
| `targets` | Box geometry of every pointer target, with the 24 px spacing-circle test | 2.5.8 |
| `reflow` | Re-lays the page at 320 px, at 200% zoom, and with the 1.4.12 text-spacing overrides; finds horizontal scroll and cut-off text; flips orientation | 1.4.10, 1.4.4, 1.4.12, 1.3.4 |
| `ax-tree` | Chromium's accessibility tree: nameless controls, file-name alt text, vague links, heading skips, landmarks | 4.1.2, 1.1.1, 2.4.4, 1.3.1 |
| `input-model` | DevTools event listeners: click-only divs, down-event actions, roles without keys, label in name, hover content dismissal and hoverability. In the first pass it also presses single keys with nothing focused to find shortcuts | 2.1.1, 2.5.2, 2.5.3, 1.4.13, 2.1.4 |
| `dom` | Page facts: lang, title, zoom lock, autoplay, refresh, autocomplete tokens, paste blocking, looping animation | 3.1.1, 2.4.2, 1.4.4, 1.4.2, 1.3.5, 3.3.8 |
| `axe` | axe-core 4.14 with the `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`, `wcag22aa` tags. Contrast and target size are left to the checks above | many |

Each check runs in each pass unless it is marked `pass: "initial"`. `contrast` skips the forced-colours pass, because that mode replaces the author's colours.

## Read the report

`criteria.rows` has one row for each of the 55 criteria:

| Status | Meaning |
|---|---|
| `fail` | A check measured a failure. Report it with its `selector` and `snippet` |
| `review` | A check found a candidate it cannot judge. A person decides |
| `no-failures-found` | A check measured this criterion fully and found nothing |
| `partial-no-failures` | Some aspects are automated and clean; the rest needs a person |
| `manual` | No script settles it. See `references/manual-criteria.md` |

`no-failures-found` is not conformance. Never write "passes WCAG" or "AA compliant". Write what ran: "no failures in the automated checks; N criteria need manual review".

## Present the report

Report in this shape:

```markdown
# WCAG 2.2 AA Audit: <url>

## Summary
- Automated checks: N failures across M criteria
- Needs human review: K candidates
- Still requires manual testing: 18 criteria (screen reader, captions, etc.)

## Measured Failures (Automated)
For each failure:
- **Criterion**: [e.g. 1.4.3 Contrast (Minimum)]
- **Selector**: `form > button.submit`
- **Measured**: computed 2.8:1 ratio (needed 4.5:1)
- **Code snippet**: `<button class="submit">Send</button>`
- **Recommended fix**: Increase contrast ratio using a compliant foreground/background hex pair.

## Needs Review
Candidates the script flagged that a human must judge, with the specific question to answer.

## Manual Testing Still Required
Screen reader pass, caption accuracy, alt-text quality, consistent navigation across pages, error-message wording.
```

## Boundaries

Audit-only. Reports measured findings and recommends fixes for manual remediation.

## Facts that stay true

WCAG 2.2 has 86 success criteria; Level A plus AA is 55 (31 A, 24 AA). 4.1.1 Parsing was removed. Large text is 24 px, or 18.66 px bold. Normal text needs 4.5:1, large text and UI components 3:1. Targets are 24 by 24 CSS px unless an exception applies. `px` font sizes are not failures, and several `h1` elements are not failures. WCAG 3.0 is a Working Draft (10 September 2026) that W3C says does not replace WCAG 2, so this skill targets 2.2.
