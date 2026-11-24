# Criteria no script settles

`scripts/wcag.mjs` marks 14 of the 55 Level A and AA criteria `manual`, and
31 `partial-no-failures`. This file says how a person closes each gap. Record
the browser, the OS, and the assistive technology used.

## Never automated

| Criterion | What to do |
|-----------|-----------|
| 1.2.4 Captions (Live) | Join a live stream and confirm captions run in real time |
| 1.3.2 Meaningful Sequence | Turn CSS off or read the DOM order; the reading order must still make sense |
| 1.3.3 Sensory Characteristics | Search copy for "the button on the right", "the red link", "the round icon" |
| 1.4.5 Images of Text | Find text rendered as an image; logos are exempt |
| 2.3.1 Three Flashes | Run the Harding/PEAT analyzer on any video or animation with rapid change |
| 2.4.5 Multiple Ways | Confirm at least two of: navigation, search, sitemap, links between pages |
| 3.2.3 Consistent Navigation | Compare the navigation order across three pages |
| 3.2.4 Consistent Identification | Same function, same label and icon, on every page |
| 3.2.6 Consistent Help | Help link or chat sits in the same relative place across pages |
| 3.3.1 Error Identification | The script submits empty forms; judge whether the wording names the field and the problem |
| 3.3.3 Error Suggestion | Each error says how to fix it, where the fix is known |
| 3.3.4 Error Prevention | Legal, financial, and delete actions can be reviewed, confirmed, or undone |
| 3.3.7 Redundant Entry | A multi-step flow does not ask for the same value twice |
| 4.1.3 Status Messages | Trigger each toast, count, and loading change with a screen reader on |

## Screen reader pass

Five minutes on the main flow, with NVDA and Firefox on Windows, or VoiceOver
and Safari on macOS:

1. Page title is read on load.
2. List headings and landmarks; the outline makes sense.
3. Tab to every control; each is announced with name, role, and state.
4. Complete one form. Labels, required state, and errors are read.
5. Open and close a dialog; focus enters and returns.
6. Trigger a status message; it is read without moving focus.

## Judgments inside automated criteria

The script finds candidates; a person decides:

- 1.1.1: alt text describes the purpose of the image, not only its content.
- 1.2.x: captions are accurate and audio description covers the visual
  information.
- 1.3.1: visual structure (lists, tables, groups) matches the markup.
- 1.4.1: a link inside body text is told apart by more than colour.
- 2.4.4 and 2.4.6: link and heading text still makes sense out of context.
- 2.4.3: the order flagged by `keyboard:order-vs-visual` is acceptable.
- 2.5.1, 2.5.7: complex gestures and drags have a single-pointer path. Try it
  with a mouse, then with a touch screen.
- 2.5.4: shaking or tilting the device does nothing that has no button.
- 3.1.2: foreign-language passages carry `lang`.
- 3.3.8: a password manager can fill the sign-in; there is no puzzle test.

## Devices the script cannot reach

- Touch: tap every control on a phone; confirm gestures and the 44 px
  comfort size.
- Forced colours: the script runs a forced-colors pass, which approximates
  Windows High Contrast. Confirm icons and borders survive on a real Windows machine.
- Zoom: browser zoom to 400% on a desktop, not only a narrow viewport.
