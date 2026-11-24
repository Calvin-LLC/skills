# harden

Audit a codebase for security, supply-chain, reliability, and test failures. Every finding includes a file, line number, quoted excerpt, and severity rating. A validator script checks each quoted excerpt against the cited lines of the source file. The skill reports findings only and never edits code.

Everything the skill needs is in this directory. It takes no options, makes no network requests, and audits the whole repository. It never runs project code, tests, or package managers, and it writes only under `.tmp/harden/`.

## Setup

Install the [Calvin-LLC/skills](https://github.com/Calvin-LLC/skills) collection:

```bash
npx -y skills add Calvin-LLC/skills -g -y
```

Each harness invokes the skill its own way:

| Harness | Invocation |
|---|---|
| Claude Code | `/harden` |
| Codex | `$harden` |
| OpenClaw | `/harden` |
| Hermes | `/harden` |
| Muse Code | `/harden` |
| Pi | `/skill:harden` |
| OMP | `/skill:harden` |

## Usage

Run the command from the root of the target repository:

```bash
/harden
```

The skill writes the report to `.tmp/harden/REPORT.md`. Its validator and report scripts need Node 18 or newer. Without Node the skill writes the report by hand and marks it `validators not run`.

## License

MIT
