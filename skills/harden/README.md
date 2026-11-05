# harden

Audit a codebase for security, supply-chain, reliability, and test failures. Every finding includes a file, line number, quoted excerpt, and severity rating. A validator script verifies each quoted excerpt against the source file. The skill reports findings only and never edits code.

Everything the skill needs lives in this directory. It takes no options, makes no network requests, and scans the whole repository.

## Setup

When using the [Calvin-LLC/skills](https://github.com/Calvin-LLC/skills) monorepo:

```bash
npx -y skills add Calvin-LLC/skills -g -y
```

To run the skill across different agent harnesses:

| Harness | Invocation |
|---|---|
| Claude Code | `/harden` |
| Codex | `$harden` |
| OpenClaw | `/harden` |
| Hermes | `/harden` |
| Pi | `/skill:harden` |
| OMP | `/skill:harden` |

## Usage

Run the command from the root of the target repository:

```bash
/harden
```

The generated report saves to `.tmp/harden/REPORT.md`. Requires Node 18 or newer.

## License

MIT
