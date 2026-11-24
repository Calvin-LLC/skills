# Agent notes for this repository

Skills live in `skills/<name>/SKILL.md`, with optional `references/` and `scripts/`. Six harnesses load them, so skill text stays harness-neutral.

## Commands

- `python scripts/check.py` runs every `scripts/check_*.py` and prints PASS, FAIL, ERROR or SKIP for each. `python scripts/check.py skills` runs one. The pre-commit hook and CI run the same command.
- `powershell -ExecutionPolicy Bypass -File install.ps1 -Source .` (POSIX: `sh install.sh --source .`) fast-forwards the installed clone from this checkout and relinks every harness. The post-commit hook runs it on `main`.
- `python scripts/skill_eval.py` replays the prompts in `tests/fixtures/skill_eval/cases.json` through OMP with no window, on the models named by `--models`. Per model it prints whether `SOUL.md` reaches a main session and a subagent, which skill each prompt loads next to the one it should, and whether a commit and a bug fix in a throwaway repo follow the rules. It spends model usage, so it is not part of `check.py`; run it after changing a description or `SOUL.md`. `--no-rules` shows the result without `SOUL.md`.

## How a change reaches agents

Agents do not load this checkout. Every harness but OMP loads `~/.agents/calvin-skills`, a clone that moves only by the installer. Edit here, commit on `main`, and the post-commit hook syncs the clone. Never edit or copy files into the clone. When `check.py install` fails, run the command its FAIL line names; `-Stash` sets a dirty clone aside in a git stash and deletes nothing.

OMP loads skills from its plugin, a copy of the pushed `main`: `omp plugin install github:Calvin-LLC/skills` once, then `omp plugin upgrade @calvin-llc/skills` after each push. A commit that is not pushed has not reached OMP's skills.

`SOUL.md` reaches a harness only under the file name that harness loads. OMP loads `~/.omp/agent/RULES.md`, in main sessions and subagents, and drops any `AGENTS.md` for subagents. Muse Code loads `AGENTS.md` in its config folder. The installer links `SOUL.md` to both.

Hooks are enabled per checkout by `git config core.hooksPath scripts/hooks`, which the installer sets when given a source.

## Rules and what enforces them

"judgment" means nothing fails when the rule is skipped.

| Rule | Enforcer |
|---|---|
| Skill text names no single harness's tool, CLI or path. A cited file exists. | `scripts/check_skills.py` |
| A reference file names only sections, steps and phases its own `SKILL.md` has. | `scripts/check_skills.py` |
| Guidance in a skill or `SOUL.md` states the action to take, in words that fit any harness, tool and browser. | judgment |
| No version number in a skill's frontmatter, its `VENDORED.md`, or the README. A copied skill is identified by the upstream commit in its `VENDORED.md`, written once. | `scripts/check_skills.py` (frontmatter and `VENDORED.md`); the README is judgment |
| The installed clone equals this checkout's `main` and is clean; every harness resolves into it and holds no skill the clone dropped. | `scripts/check_install.py`, `scripts/hooks/post-commit` |
| `SOUL.md` reaches every agent, subagents included. | `scripts/check_install.py` (each link exists and matches); `scripts/skill_eval.py --parts reach` (the agent reports seeing it) |
| A check that exists is a check that runs. | `scripts/check.py` enumerates the directory; `scripts/hooks/pre-commit`; `.github/workflows/checks.yml` |
| The arch-export leak sweep runs through the shipped script, and a broken sweep is ERROR, never a pass. | `skills/arch-export/scripts/leak_check.py`, `tests/test_leak_check.py` |
| Scratch folders, throwaway names, version piles and report notes do not enter a repo. | In this repo: `scripts/check_sprawl.py` (runs `skills/tidy/scripts/sprawl.py` against `.sprawl-baseline.json`), `tests/test_sprawl.py`. In another repo: only after the `tidy` skill installs the gate there; otherwise judgment (`SOUL.md`) |
| A tracked shell script keeps its executable bit (a commit made on Windows can drop it). | `scripts/check_modes.py` |
| No check or test reads a commit hook's git variables: a test that runs `git init` under them rewrites this repository. | `scripts/check.py` strips them for every check; `tests/test_checks.py` |
| A pasted reviewer reply loads arch-import. One prompt carries one `/skill:` token; OMP expands only the first. | judgment (arch-import description; no extension, by the operator's decision) |
| arch-export writes the brief and does not fix the subject. | judgment (skill text) |
| The arch-export hand-off does not gate on retention settings; a reviewer refusal is not a leak. | judgment (skill text) |
| architect auto-loads only for a change to types, signatures or module boundaries. | judgment (description) |
| Operator prompts, briefs, alias maps and reviewer replies never enter a tracked file. Fixtures are synthetic. | judgment (`.arch/` is gitignored) |
| Push only when the operator asks for that push. | judgment (commit skill) |
| A commit is one subject line with no body, unless the operator asks for a body. | `scripts/skill_eval.py` (`check_commit_rules`, when run); otherwise judgment (commit skill) |
| Comment rules live in the `no-comments` skill; `SOUL.md` and other skills point to it. | judgment |
| An architecture, ownership or state diagram is a fenced `mermaid` block of a type and size a terminal can draw. | judgment (`skills/architect/references/diagrams.md`) |

When you add a rule, add its row. When a check makes a rule impossible to break, replace "judgment" with the check. Drop a row once its mistake cannot happen.
