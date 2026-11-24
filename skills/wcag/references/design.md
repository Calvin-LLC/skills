# Design decisions that decide accessibility

Load this when choosing colour, type, spacing, motion, or layout.

## Colour

- Choose the palette first, then measure it. A ramp that looks right and
  fails 4.5:1 is a ramp problem, not a text problem: darken the text token
  until the pair passes instead of adding a one-off override.
- Muted and secondary text is where most failures sit. Hold it to 4.5:1,
  derived from the surface hue, not a neutral grey.
- Light and dark themes are separate designs. The script measures both. A
  token that passes in light often fails in dark.
- Check disabled, hover, selected, error, and placeholder states. Disabled
  controls are exempt from 1.4.3; placeholders are not.
- Meaning carried by colour needs a second cue: text, an icon, a shape, a
  position (1.4.1).
- Translucent layers make contrast depend on what is behind them. Prefer an
  explicit colour. `contrast` composites alpha, but a person reading a design
  file cannot.
- Text over photos or gradients needs a scrim or a position that keeps text
  on a calm region. `contrast` reports the 5th and 25th percentile of the
  real pixels; fail when the 25th percentile is under the requirement.

## Type

- Body text 16 px or larger on mobile. 24 px, or 18.66 px bold, counts as
  large text.
- Measure 45 to 75 characters. Justified text and tight leading hurt
  readability, and 1.4.12 breaks when a fixed-height box clips taller text.
- Never put text in a fixed-height container with `overflow: hidden`.
  `reflow` applies the 1.4.12 overrides and flags the clip.
- Do not lock zoom. `maximum-scale` under 2 or `user-scalable=no` fails 1.4.4.
- Heading levels follow the outline, not the visual size. Style an `h3` to
  look like an `h2`; do not skip a level.

## Motion

- Every looping or entrance animation needs a `prefers-reduced-motion` path.
  Reduce movement, keep opacity and state changes. `dom` reports loops that
  ignore the preference in the reduced-motion pass.
- Nothing flashes more than three times a second (2.3.1). No script measures
  this reliably; keep rapid alternation out of the design.
- Auto-starting motion that lasts over five seconds needs a visible pause
  control (2.2.2).

## Layout and targets

- Pointer targets are 24 by 24 CSS px, or have 24 px of clear space. Aim for
  44 px on touch surfaces; `targets` enforces only the WCAG floor.
- Do not rely on hover to reveal controls or information. Content shown on
  hover or focus must be dismissible with Escape, hoverable, and persistent
  (1.4.13). `input-model` tests all three.
- A sticky header or cookie bar can cover the focused control (2.4.11). Give
  focusable elements `scroll-margin-top` equal to the header height. `keyboard`
  samples the covered area.
- Layout must hold at 320 px wide with no horizontal scroll, except for data
  tables, maps, and toolbars. Fixed pixel widths on cards and grids are the
  usual cause.
- DOM order, tab order, and visual order must agree. A CSS reorder that moves
  a button above its label breaks 2.4.3 and 1.3.2. `keyboard` reports upward
  focus jumps for review.

## Focus styling

- One focus ring for the whole product, 2 px or thicker, at least 3:1 against
  both the element and its surroundings, using `:focus-visible`.
- Theme the ring from the palette with `outline`, not by removing it.
- `keyboard` compares pixels with and without focus. A ring whose strongest
  changed pixel contrasts under 3:1 with the unfocused pixel is flagged for
  review, and a ring that changes nothing fails 2.4.7.
