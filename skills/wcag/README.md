# wcag

Audit a web page against WCAG 2.2 Level A and AA standards using a headless Chromium browser, identify violations, test fixes, and re-verify results.

The audit evaluates pages across five browser passes (desktop, mobile viewport, dark mode, high contrast, and reduced motion) without making outside network calls beyond the target URL.

## Setup

When using the [Calvin-LLC/skills](https://github.com/Calvin-LLC/skills) monorepo:

```bash
npx -y skills add Calvin-LLC/skills -g -y
```

To run the skill across different agent harnesses:

| Harness | Invocation |
|---|---|
| Claude Code | `/wcag <url|file.html>` |
| Codex | `$wcag <url|file.html>` |
| OpenClaw | `/wcag <url|file.html>` |
| Hermes | `/wcag <url|file.html>` |
| Pi | `/skill:wcag <url|file.html>` |
| OMP | `/skill:wcag <url|file.html>` |

## Usage

Provide a URL, a local HTML file, or a local dev server address:

```bash
/wcag http://localhost:3000
```

The generated audit report lists violations by WCAG success criterion with DOM selectors, code snippets, and suggested fixes.

## Requirements

- Node.js 22 or newer
- Chromium-based browser installed and available on `PATH` (or set via `CHROME_BIN`)

## License

- Skill and scripts: MIT
- Bundled rule engine (`scripts/vendor/axe.min.js`): MPL-2.0 (see `scripts/vendor/AXE-LICENSE`)
