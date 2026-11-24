# WCAG 2.2 CSS rules

Load when editing CSS, SCSS, Less, or Sass.

## Focus styles (2.4.7)

- Require `:focus-visible` with a visible outline on all interactive elements.
- Block `outline: none` or `outline: 0` without a `:focus-visible` replacement.
- Minimum: `outline: 2px solid [color]; outline-offset: 2px`.
- The focus indicator needs 3:1 contrast against adjacent colors (1.4.11).

## Contrast (1.4.3, 1.4.11)

| Content | Minimum ratio | Pass example | Fail example |
|---------|---------------|-------------|-------------|
| Normal text | 4.5:1 | #595959 on #fff (7:1) | #999 on #fff (2.8:1) |
| Large text (24px and up, or 18.66px bold and up) | 3:1 | #949494 on #fff (3.03:1) | #aaa on #fff (2.32:1) |
| UI components, borders, icons | 3:1 | #767676 on #fff | #ccc on #fff (1.6:1) |

Color must never be the sole indicator of state. Combine it with text,
icons, or borders (1.4.1).

## Target sizes (2.5.8)

```css
/* WCAG 2.2 minimum: 24x24 CSS px */
button, a, [role="button"] { min-width: 24px; min-height: 24px; }

/* Recommended: 44-48px */
button, a, [role="button"] { min-width: 48px; min-height: 48px; }

/* Minimum spacing between targets: 8px */
```

Exceptions to 2.5.8: the target has 24 CSS px of clear space (a 24 px circle
centered on it touches no other target), an equivalent control exists, the
target is an inline text link, the size is set by the user agent, or the size
is essential. `scripts/checks/targets.mjs` applies the spacing test by
geometry.

## Reflow (1.4.10)

- Content must work at 320 CSS px width without horizontal scroll.
- Use `max-width: 100%`, responsive grids, `overflow-wrap: break-word`.
- No fixed-width layouts. Use `minmax()` or `auto-fit`/`auto-fill`.
- Exception: data tables, maps, and toolbars may use 2D scrolling.

## Text sizing and spacing (1.4.4, 1.4.12)

- Prefer `rem`/`em` for font-size. `px` is fine because browsers zoom it.
  The failure is clipping at zoom or with adjusted spacing, not the unit.
- Never set a fixed `height` with `overflow: hidden` on text containers.
- Use `min-height: auto; overflow: visible` on text containers.

## Orientation (1.3.4)

- Never lock orientation through CSS or a meta tag.
- Adapt layout per orientation. Never hide content.
- Exception: essential orientation (piano app, check deposit).

## Reduced motion

```css
.banner { animation: slide-in 400ms ease-out; }
@media (prefers-reduced-motion: reduce) {
    .banner { animation: fade-in 200ms linear; }
}
```

Remove spatial movement (slides, parallax, zoom, looping drift) and keep
opacity, color, and state changes that carry meaning. A blanket
`animation-duration: 0.01ms !important` also erases feedback such as a
confirmation fade and a progress change. The script's
reduced-motion pass verifies this.

No animation may flash more than 3 times per second (2.3.1).

## Focus not obscured (2.4.11)

```css
a:focus, button:focus, input:focus, [tabindex]:focus {
    scroll-margin-top: 5rem;
    scroll-margin-bottom: 5rem;
}
```

Account for sticky headers with scroll margin.

## Pointer queries

```css
@media (hover: hover) and (pointer: fine) { /* mouse or trackpad */ }
@media (hover: none) and (pointer: coarse) { /* touch */ }
```

Never assume input type from viewport width.

## Images of text (1.4.5)

Use styled text, not images of text. Exception: logos.

## Dynamic numbers

Use `font-variant-numeric: tabular-nums` on any number that updates
dynamically.
