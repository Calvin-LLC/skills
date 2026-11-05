# WCAG 2.2 core rules (Level A + AA)

Enforce WCAG 2.2 Level A and AA on all user-facing code. 55 criteria total
(31 A + 24 AA). Parsing (4.1.1) was removed in WCAG 2.2. Never reference it.

## Principles (POUR)

- Perceivable: text alternatives, captions, contrast, reflow, text spacing
- Operable: keyboard access, no traps, timing, pointer gestures, drag alternatives
- Understandable: language, predictable behavior, error help, consistent help, accessible auth
- Robust: valid semantics, ARIA, status messages

## Critical anti-patterns: block these

- `img` without an `alt` attribute
- `input` without an associated `label` or `aria-label`/`aria-labelledby`
- `outline: none` or `outline: 0` without a `:focus-visible` replacement
- `div onclick` or `span onclick` for interactive elements (use `button`)
- Missing `html lang`
- Missing `title` or a generic title
- Accessible name that does not contain visible label text (2.5.3)
- Orientation locked without an essential reason (1.3.4)
- Cognitive function tests for authentication: text CAPTCHAs, math puzzles (3.3.8)
- `pointerdown` for triggering actions (use `click`/`pointerup`) (2.5.2)
- Color as the only indicator of state or meaning (1.4.1)
- Auto-playing audio or video without controls (1.4.2)
- Content that flashes more than 3 times per second (2.3.1)

## Key thresholds

| Metric | Value | Criterion |
|--------|-------|-----------|
| Text contrast (normal) | 4.5:1 | 1.4.3 |
| Text contrast (large: 24px and up, or 18.66px bold and up; 18pt / 14pt bold) | 3:1 | 1.4.3 |
| UI component and graphic contrast | 3:1 | 1.4.11 |
| Minimum target size | 24x24 CSS px | 2.5.8 |
| Recommended target size | 44-48px | best practice |
| Target spacing | 8px minimum | best practice |
| Reflow width | 320 CSS px, no horizontal scroll | 1.4.10 |
| Text resize | 200% without loss | 1.4.4 |
| Text spacing | line-height 1.5x, paragraph 2x, letter 0.12em, word 0.16em | 1.4.12 |

`px` for font size is fine. Browsers zoom `px`. Clipping at zoom or with
adjusted spacing is the real failure, not the unit. Multiple `h1` elements
are fine. Neither is a finding.

## Level A criteria reference

1.1.1 Non-text Content | 1.2.1 Audio-only/Video-only | 1.2.2 Captions
(Prerecorded) | 1.2.3 Audio Description or Media Alternative | 1.3.1 Info and
Relationships | 1.3.2 Meaningful Sequence | 1.3.3 Sensory Characteristics |
1.4.1 Use of Color | 1.4.2 Audio Control | 2.1.1 Keyboard | 2.1.2 No Keyboard
Trap | 2.1.4 Character Key Shortcuts | 2.2.1 Timing Adjustable | 2.2.2 Pause
Stop Hide | 2.3.1 Three Flashes | 2.4.1 Bypass Blocks | 2.4.2 Page Titled |
2.4.3 Focus Order | 2.4.4 Link Purpose | 2.5.1 Pointer Gestures |
2.5.2 Pointer Cancellation | 2.5.3 Label in Name | 2.5.4 Motion Actuation |
3.1.1 Language of Page | 3.2.1 On Focus | 3.2.2 On Input | 3.2.6 Consistent
Help | 3.3.1 Error Identification | 3.3.2 Labels or Instructions |
3.3.7 Redundant Entry | 4.1.2 Name Role Value

## Level AA criteria reference

1.2.4 Captions (Live) | 1.2.5 Audio Description (Prerecorded) | 1.3.4
Orientation | 1.3.5 Identify Input Purpose | 1.4.3 Contrast (Minimum) |
1.4.4 Resize Text | 1.4.5 Images of Text | 1.4.10 Reflow | 1.4.11 Non-text
Contrast | 1.4.12 Text Spacing | 1.4.13 Content on Hover or Focus |
2.4.5 Multiple Ways | 2.4.6 Headings and Labels | 2.4.7 Focus Visible |
2.4.11 Focus Not Obscured | 2.5.7 Dragging Movements | 2.5.8 Target Size
(Minimum) | 3.1.2 Language of Parts | 3.2.3 Consistent Navigation |
3.2.4 Consistent Identification | 3.3.3 Error Suggestion | 3.3.4 Error
Prevention | 3.3.8 Accessible Authentication | 4.1.3 Status Messages
