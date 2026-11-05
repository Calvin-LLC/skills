---
name: init
description: >-
  Build or refresh a repository's AGENTS.md from what the repo actually does.
  Use when asked to run /init, initialize a repo for agents, write or update
  AGENTS.md, onboard an agent into a codebase, or find out how a project is
  built and tested. Detects the command surfaces, runs each candidate command
  before writing it down, and never records a fact it did not verify.
---

# Init

AGENTS.md is a README for agents: the one predictable place a coding agent
looks for how this project builds, tests, and is laid out. This skill writes
that file from evidence. A command lands in it only after it ran here and
printed what the file claims it prints.

## What makes an AGENTS.md worth reading

- Every command in it was run in this session. A plausible command that was
  never executed is a trap, not a tip.
- It names the one command that proves the tree before a push. That is the
  highest-value line in the file.
- It points at where knowledge lives instead of restating it. Restated facts
  drift; pointers do not.
- It is short. An agent reads it every session, so padding costs on every turn.

## Step 1: detect

Find the project's command surfaces and read the ones that exist.

- `Makefile`, `justfile`, `Taskfile.yml`: the target names are the real commands.
- `package.json`: `scripts`, plus the package manager from the lockfile
  (`pnpm-lock.yaml`, `yarn.lock`, `bun.lockb`, `package-lock.json`).
- `pyproject.toml`, `pytest.ini`, `tox.ini`, `ruff.toml`, `mypy.ini`,
  `pyrightconfig.json`: test runner, linter, type checker, coverage gate.
- `docker-compose.yml`, `Dockerfile`: how the thing actually runs.
- `Cargo.toml`, `go.mod`, `CMakeLists.txt`, `build.gradle`, `.csproj`.
- CI config under `.github/workflows` or `.gitlab-ci.yml`: the commands CI
  already trusts.
- An existing `README.md` or `CONTRIBUTING.md`: layout and conventions that
  are written down already. Reuse them instead of re-deriving.

Record each candidate as the exact command plus what "passing" looks like.

## Step 2: verify by running

Run every candidate. Keep the ones that worked, with their real output.

- A test command: read the passed/failed line and keep the count it printed.
- A lint or type command: it must exit clean, or you record what it reported.
- A build or start command: run it if it terminates. If it serves forever, run
  it under a timeout, confirm it came up, then say in the file that it blocks.
- A command whose dependency is missing: that is a skip, not a pass. Write the
  command and what it needs.

Never invent a flag, a target, or a script name. When the surface has no
command for something the project obviously needs, that is a finding worth one
line in the file, not a command you make up.

## Step 3: write

Placement, per the agents.md standard:

- Root `AGENTS.md` is the default.
- Monorepos get nested files, and the closest one to the edited file wins. Add
  a nested file when a subproject has its own toolchain or its own rules.
- Instructions the user gives in chat override the file.

Write these sections and skip any that would be empty:

```markdown
# <Project>

One line on what this is and what runs it.

## Commands
- Install: `<command>` (verified: <what it printed>)
- Test: `<command>` (verified: <count> passed)
- Lint and types: `<command>`
- Run it: `<command>`
- Before a push: `<command>`

## Layout
- `path/` what lives there

## Conventions
- A rule this codebase actually follows, with the file that shows it.

## Do not
- The thing that breaks this project.

## Where the knowledge lives
- `<doc path>`: what it covers
```

Rules for the content:

- Verified facts only. Anything you could not run gets `TODO:` and the reason,
  never a confident guess.
- Commands verbatim, including the wrapper (`make test`, not `pytest`).
- Name the paths an agent would otherwise grep for.
- Sentence case headings. No decorative emoji.
- The file covers this repo only. Other projects, folders that moved away, and
  what used to live here stay out of it. An agent working in this repo must not
  learn about external projects from its AGENTS.md, and a deleted thing leaves
  no line behind.
- Agent-instruction files are classifier-scanned as well as read. Never write
  anti-refusal scaffolding into them ("ignore content flags", "refusing does
  not protect anyone", "the assistant must"): it reads as a jailbreak wrapper
  and gets whole sessions cut. State authorization as calm facts of what the
  owner owns and does.
- Keep it under roughly 120 lines. Longer detail belongs in a doc that the
  file points at.

## Step 4: confirm

Show the draft in the reply and ask whether to write it. Do not write it
silently, and do not commit in the same breath. This file steers every future
session in the repo, so the user reads it first.

## Step 5: commit

Follow the `commit` skill. One commit, message naming the file.

## Refresh, not just create

When the file already exists, do not rewrite it from scratch. Read it, re-run
each command it claims, and fix only the lines that no longer hold. Report
which claims were stale and what the new output is. A file that survived this
pass is worth trusting; one that was never re-run is not.

When the user says to keep the current file and append, add one new top-level section at the bottom and leave every line above it byte-identical. Existing persona or voice text is theirs; do not tidy it. Run the commands before listing them, and state in the section which ones ran live and which were only read from the Makefile.

## When the file is gitignored

Some repos ignore `AGENTS.md` on purpose. Check with `git check-ignore`. If it
is ignored, the file helps this machine only. Say so, and put any fact a
teammate needs into a tracked file instead, usually the README.

## What this skill does not do

It does not optimize itself against a benchmark. SkillOpt and similar tools
score a skill by running it through a task suite behind a held-out gate, and
none of their built-in suites grade an AGENTS.md, so there is nothing here to
pass. Verification in this skill is that same loop done by hand: run the
command, read the output, write only what you saw.
