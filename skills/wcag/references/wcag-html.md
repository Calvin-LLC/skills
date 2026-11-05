# WCAG 2.2 HTML rules

Load when editing HTML, JSX, TSX, Vue, Svelte, Astro, PHP, ERB, Handlebars,
EJS, or Nunjucks templates.

## Page structure

- `html lang` is required (3.1.1).
- `title` must be unique and descriptive: "[Page] - [Site]" (2.4.2).
- Headings go in logical order (1.3.1). Multiple `h1` elements are fine.
- A skip link is the first focusable element and targets `main` (2.4.1).
- Use semantic elements: `header`, `nav`, `main`, `footer`, `article`,
  `section` (1.3.1).
- DOM order must match visual reading order (1.3.2).
- Never reference content by position, shape, or color alone (1.3.3).

## Images

- Every `img` needs `alt`. Informative images describe content. Decorative
  images use `alt=""`. Complex images use `figure` plus `figcaption` (1.1.1).
- `input type="image"` needs `alt` (1.1.1).
- Never use `alt="image"` or `alt="photo"`. Describe the purpose.

## Forms

- Every `input` must have a `label` with matching `for` and `id`, or
  `aria-label`/`aria-labelledby` (3.3.2).
- Errors use `aria-invalid="true"` plus `aria-describedby` pointing to an
  error paragraph with `role="alert"` (3.3.1).
- Suggest corrections when possible (3.3.3).
- Group related inputs with `fieldset` plus `legend` (1.3.1).
- Never use `placeholder` as the only label.
- Pre-populate previously entered data in multi-step forms (3.3.7).
- Add a confirm or review step for legal, financial, or data-deletion
  actions (3.3.4).

### Autocomplete values (1.3.5)

Use `autocomplete` on any input collecting personal data:

| Value | Purpose |
|-------|---------|
| `name` / `given-name` / `family-name` | Name fields |
| `email` | Email |
| `tel` | Phone |
| `street-address` / `postal-code` / `country-name` | Address |
| `cc-number` / `cc-exp` / `cc-csc` | Payment |
| `username` / `current-password` / `new-password` | Auth |

## Links and buttons

- Links need descriptive text. Never "click here" or "read more" (2.4.4).
- Interactive elements must be `button` or `a`, not `div onclick` (2.1.1).
- Icon buttons need `aria-label`, with the SVG marked `aria-hidden="true"`.
- The accessible name must contain the visible label text (2.5.3).

## Media (1.2.1-1.2.5)

- Audio-only (prerecorded): provide a text transcript (1.2.1).
- Video-only (prerecorded): provide a transcript or audio description (1.2.1).
- Video with audio (prerecorded): synchronized captions through
  `track kind="captions"` (1.2.2), plus audio description through
  `track kind="descriptions"` or a media alternative (1.2.3, 1.2.5).
- Live audio: real-time captions (1.2.4).
- Audio or video with `autoplay` must have controls (1.4.2).

## ARIA

- Prefer native HTML over ARIA. Use ARIA only when no native element exists.
- Custom components must expose name, role, and value (4.1.2).
- Modals: `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, close on
  Escape, trap focus while open.
- Status messages: `role="status"` plus `aria-live="polite"`, or
  `role="alert"` plus `aria-live="assertive"` (4.1.3).
- Toggle states: `aria-expanded`, `aria-pressed`, `aria-checked`.

## Help and navigation

- A help mechanism (link, chat, phone) sits in the same relative position on
  every page (3.2.6).
- Provide multiple ways to find pages: nav plus search or a sitemap (2.4.5).
- Navigation order stays consistent across pages (3.2.3).
- Components with the same function use the same labels (3.2.4).
- Mark language changes: `span lang="fr"` (3.1.2).

## Authentication (3.3.8)

- Use `autocomplete="username"` and `autocomplete="current-password"`.
- Allow paste in password fields.
- No text CAPTCHAs. Object recognition or audio alternatives are fine.
- Offer passkey, biometric, or magic-link alternatives when possible.

## Timing and interaction

- No unexpected context changes on focus (3.2.1) or on input (3.2.2).
- Time limits must be adjustable or extendable (2.2.1).
- Auto-updating content must have pause or stop controls (2.2.2).
