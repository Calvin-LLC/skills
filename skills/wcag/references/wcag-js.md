# WCAG 2.2 JavaScript rules

Load when editing JS, JSX, TS, TSX, Vue, Svelte, MJS, or CJS.

## Keyboard support (2.1.1)

- Custom interactive elements must handle Enter and Space through `keydown`.
- Call `preventDefault()` on Space to stop page scroll.
- All functionality works through the keyboard. No mouse-only interactions.
- No keyboard traps. The user can always Tab away (2.1.2).

## Focus management

- After DOM insertion (modal open, dynamic content): focus the new content.
- After removal (modal close, item delete): return focus to the trigger.
- Modal focus trap: Tab cycles through the modal, Shift+Tab wraps backward.
- After route changes in SPAs: focus the main heading or announce the page.

## ARIA state updates

- Update `aria-expanded` on disclosure, accordion, and menu toggles.
- Update `aria-pressed` on toggle buttons.
- Update `aria-checked` on custom checkboxes and radios.
- Set `aria-busy="true"` during async loading, remove it when done.
- Set `aria-invalid="true"` on fields with validation errors.

## Live regions (4.1.3)

- Use `role="status"` plus `aria-live="polite"` for non-urgent updates
  (search result counts, save confirmations).
- Use `role="alert"` plus `aria-live="assertive"` for errors and urgent
  messages.
- Insert text into an existing live region. Never create a region and fill it
  in the same tick.

## Pointer cancellation (2.5.2)

- Block `pointerdown` or `mousedown` for triggering actions.
- Use `click` (fires on pointerup) for all actions.
- Native click lets the user abort by moving the pointer off target.

## Pointer gestures (2.5.1)

- Multipoint gestures (pinch, multi-finger swipe) need single-pointer
  alternatives.
- Provide button controls (zoom in/out, next/prev) beside gesture input.

## Escape to dismiss (1.4.13)

- Tooltips, popovers, and hover or focus content must close on Escape.
- Content must be hoverable (the pointer can reach it) and persistent (it
  stays until dismissed).

## Character key shortcuts (2.1.4)

- Single-character shortcuts must be remappable or disableable.
- Never fire single-key shortcuts when focus is in `input`, `textarea`,
  `select`, or `contenteditable`.
- Provide a settings UI to remap or disable shortcuts.

## Motion actuation (2.5.4)

- Device-motion features (shake to undo) need a UI alternative (a button).
- Provide a setting to disable motion responses.
- Exception: motion essential to function (pedometer).

## Dragging (2.5.7)

- Drag operations need single-pointer click alternatives (up/down buttons,
  click-to-place).
- Announce reorder changes through a live region.

## Context changes (3.2.1, 3.2.2)

- No navigation or popups on focus.
- No auto-submit on select change. Use an explicit submit button.
- No unexpected context changes on input.

## Timing (2.2.1, 2.2.2)

- Warn before session timeout and allow extension.
- Auto-updating content (feeds, tickers) must have pause or stop controls.
