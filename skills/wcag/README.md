# wcag

Audit a web page against WCAG 2.2 Level A and AA in a headless Chromium-based browser and report the violations it measures. The skill is audit-only. It recommends fixes and leaves the page for you to change.

The script runs nine checks in five browser passes: desktop (1280x800), phone (390x844), dark color scheme, reduced motion, and forced colors. The scripts make no network requests of their own. The browser loads the target page and whatever that page references, and the script blocks every request that is not a GET, HEAD, or OPTIONS, so a run changes nothing on the server.

## Setup

Install the [Calvin-LLC/skills](https://github.com/Calvin-LLC/skills) collection:

```bash
npx -y skills add Calvin-LLC/skills -g -y
```

Each harness invokes the skill its own way:

| Harness | Invocation |
|---|---|
| Claude Code | `/wcag <url\|file.html>` |
| Codex | `$wcag <url\|file.html>` |
| OpenClaw | `/wcag <url\|file.html>` |
| Hermes | `/wcag <url\|file.html>` |
| Muse Code | `/wcag <url\|file.html>` |
| Pi | `/skill:wcag <url\|file.html>` |
| OMP | `/skill:wcag <url\|file.html>` |

## Usage

Provide a URL, a local HTML file, or a local dev server address:

```bash
/wcag http://localhost:3000
```

The script prints a summary and writes the full JSON report to `.tmp/wcag/report.json` in the working directory. It exits `0` when it finds no failures, `2` when it finds failures, and `1` when the run broke. A run takes 1 to 10 minutes per page.

From that JSON the skill writes the audit report. It lists each measured failure by WCAG success criterion with its DOM selector, code snippet, and a recommended fix. It also lists what a person must review and which criteria still need manual testing. A run with no failures is not proof of conformance.

## Requirements

- Node.js 22 or newer
- Chromium-based browser installed and available on `PATH` (or set via `CHROME_BIN`)

## License

- Skill and scripts: MIT
- Bundled rule engine (`scripts/vendor/axe.min.js`): MPL-2.0 (see `scripts/vendor/AXE-LICENSE`)
