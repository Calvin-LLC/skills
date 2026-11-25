# Agent notes for this repository

Skills live in `skills/<name>/SKILL.md`, with optional `references/` and `scripts/`. This repository is OMP-first: skill text names OMP's core tools (`read`, `write`, `edit`, `ast_edit`, `grep`, `glob`, `bash`, `eval`, `lsp`, `debug`, `task`, `wait`, `todo`, `ask`, `web_search`, and `browser` inside `eval`) and its internal URLs (`skill://`, `pr://`, `issue://`, `agent://`, `conflict://`) directly, and `rules/` and native Mermaid are first-class. The other five harnesses load the same files, so `SOUL.md` stays in words any of them can act on.

## Commands

- `python scripts/check.py` runs every `scripts/check_*.py` and prints PASS, FAIL, ERROR or SKIP for each. `python scripts/check.py skills` runs one. The pre-commit hook and CI run the same command.
- `powershell -ExecutionPolicy Bypass -File install.ps1 -Source .` (POSIX: `sh install.sh --source .`) fast-forwards the installed clone from this checkout and relinks every harness. The post-commit hook runs it on `main`.
- `python scripts/skill_eval.py` replays the prompts in `tests/fixtures/skill_eval/cases.json` through OMP with no window, on the models named by `--models`. Per model it prints whether `SOUL.md` reaches a main session and a subagent, which skill each prompt reads first next to the one it should, and whether a commit and a bug fix in a throwaway repo follow the rules. A `loads` run passes only when the first skill read is an expected one, and each miss names the skill that was read in its place. It spends model usage, so it is not part of `check.py`; run it after changing a description or `SOUL.md`. `--no-rules` shows the result without `SOUL.md`. `--no-skills` runs `reach` and `behaves` with no skill loaded, which shows what `SOUL.md` does alone. Skills come from this checkout's working tree only, so an edit is tested before the commit: the installed plugin, the linked copies in `~/.agents`, the Pi, Claude and Codex user folders and `skills.customDirectories` are switched off for each run. `SOUL.md` still comes from the installed clone, the last commit on `main`. So does a rule that already exists: OMP reads the installed copy in `~/.omp/agent/rules/` (priority 100) ahead of this checkout's copy, which `-e` offers at priority 90. Only a new rule file in `rules/` that is not committed yet loads from the checkout.

## How a change reaches agents

Agents do not load this checkout. Every harness but OMP loads `~/.agents/calvin-skills`, a clone that moves only by the installer. Edit here, commit on `main`, and the post-commit hook syncs the clone. Never edit or copy files into the clone. When `check.py install` fails, run the command its FAIL line names; `-Stash` sets a dirty clone aside in a git stash and deletes nothing.

OMP loads skills from its plugin, a copy of the pushed `main`: `omp plugin install github:Calvin-LLC/skills` once, then `omp plugin upgrade @calvin-llc/skills` after each push. A commit that is not pushed has not reached OMP's skills.

The installer links skills into `~/.agents/skills` for the harnesses that read that folder, Pi among them, and OMP reads it too unless told otherwise. Keep `skills.enableAgentsUser` and `skills.enablePiUser` set to `false` in OMP (`omp config set <key> false`), and leave `claude` and `codex` out of `enabledProviders`. Otherwise a skill committed but not pushed differs from the plugin's copy and OMP lists it twice, the second time under a namespaced name.

A harness gets one copy of each skill. Pi and OMP get no link folder of their own, and the installer removes the links an earlier version made in `~/.pi/agent/skills` and `~/.omp/agent/skills`. Muse Code keeps its own copies under `~/.config/muse/skills` and skips the `~/.agents/skills` ones as shadowed. The installer has `muse` copy each skill from the clone, reinstalls a copy that `muse` tracks from any other folder, and enables every skill. Muse has no state that keeps a skill out of the model's routing yet lets the model load it when the user asks: `user-only` refuses the load (`disabled-skill`). So a skill with `disable-model-invocation: true` is on in Muse, and its description starts "Manual only." so the model loads it only when the user names it.

The installer treats a harness as installed when its config folder exists (`~/.claude`, `~/.hermes`, `~/.config/muse`, `~/.codex`, `~/.pi/agent`, `~/.omp/agent`). It links skills, `SOUL.md` and rules only into those, and creates no folder for a harness that is absent. `~/.agents/skills` is always linked.

`SOUL.md` reaches a harness only under the file name that harness loads. OMP loads `~/.omp/agent/RULES.md`, in main sessions and subagents, and drops any `AGENTS.md` for subagents. Muse Code loads `AGENTS.md` in its config folder. The installer links `SOUL.md` to both.

`rules/*.md` are OMP stream rules: each one watches a tool call or the reply for a pattern and interrupts with its body as a reminder. The installer links every rule in the clone into `~/.omp/agent/rules/`, so a rule is live in OMP after a commit on `main`. A Windows account that cannot create symlinks gets hard links, which keep no pointer back to the clone, so `install.ps1` also writes the names of the rules it hard-linked to `~/.agents/calvin-skills-omp-rules.txt`; the installer and `check_install.py` read that list to find a rule the clone dropped. Each rule has must-trigger and must-not-trigger cases in `tests/fixtures/rules/cases.json`.

The plugin carries its own copy of `rules/`. The linked rule wins while both exist. A rule deleted or renamed here loses its link at the commit, and OMP then falls back to the plugin's old copy until the push and `omp plugin upgrade @calvin-llc/skills`. Finish a rule removal with both.

Hooks are enabled per checkout by `git config core.hooksPath scripts/hooks`, which the installer sets when given a source.

## Rules and what enforces them

"judgment" means nothing fails when the rule is skipped.

| Rule | Enforcer |
|---|---|
| Skill text names OMP's core tools and internal URLs (`skill://`, `pr://`, `issue://`, `agent://`, `conflict://`) and no other harness's tool, CLI, config key or path: no Hermes name, no `ask_user_question`, no `/tmp/`, no machine-specific path. A cited file exists. | `scripts/check_skills.py`, `tests/test_checks.py` (the other harnesses' names; an OMP tool name that does not exist is judgment) |
| A skill reaches another skill's file through `skill://<name>/<path>`, never `../<name>/`: OMP's `skill://` resolver rejects `..`. Every `skill://` URI and every "the **name** skill" names a skill or a file under `skills/`, unless the same sentence says "if installed". | `scripts/check_skills.py`, `tests/test_checks.py` |
| An OMP feature that a setting gates and that is off by default (`ast_grep`, `computer`, and the `task` item fields `outputSchema`, `isolated` and `model`) is named with its setting and, in the same clause, the path that works at defaults. No other off-by-default tool is named (`github`, `security_scan`, `generate_image`, `tts`, `checkpoint`, `rewind`, the memory tools). | judgment |
| A reference file names only sections, steps and phases its own `SKILL.md` has. | `scripts/check_skills.py` |
| Guidance in `SOUL.md` states the action to take, in words that fit any harness, tool and browser. | judgment |
| No version number in a skill's frontmatter, its `VENDORED.md`, or the README. A copied skill is identified by the upstream commit in its `VENDORED.md`, written once. | `scripts/check_skills.py` (frontmatter and `VENDORED.md`); the README is judgment |
| The installed clone equals this checkout's `main` and is clean; every harness resolves into it and holds no skill the clone dropped. Every rule in the clone is linked into `~/.omp/agent/rules/`, with no link to a rule the clone dropped. | `scripts/check_install.py`, `scripts/hooks/post-commit` |
| A harness loads each skill once: no link into the clone sits in `~/.pi/agent/skills` or `~/.omp/agent/skills`. | `scripts/check_install.py`, `tests/test_install.py`. OMP's own settings (`skills.enableAgentsUser`, `skills.enablePiUser`) are judgment |
| A skill with `disable-model-invocation: true` is never auto-invoked and stays loadable when the user names it: hidden in OMP, on in Muse Code with a description that starts "Manual only." | `scripts/check_skills.py` (the description), `tests/test_checks.py`; `install.ps1` and `install.sh` enable it in Muse on every run, proven by `tests/test_install.py`. Whether a model obeys "Manual only." is judgment |
| The installer creates no folder for a harness that is not installed. | `tests/test_install.py` |
| A rule in `rules/` has a body, an explicit `scope` on a regex trigger, valid `interruptMode` and `repeatMode`, no version number, and fires on its must-trigger cases and stays quiet on its must-not-trigger cases. | `scripts/check_rules.py` (runs `omp ttsr test`; SKIP for the trigger cases where `omp` is absent), `tests/test_rules.py` |
| `SOUL.md` reaches every agent, subagents included. | `scripts/check_install.py` (each link exists and matches); `scripts/skill_eval.py --parts reach` (the agent reports seeing it) |
| A check that exists is a check that runs. | `scripts/check.py` enumerates the directory; `scripts/hooks/pre-commit`; `.github/workflows/checks.yml` |
| The arch-export leak sweep runs through the shipped script, and a broken sweep is ERROR, never a pass. | `skills/arch-export/scripts/leak_check.py`, `tests/test_leak_check.py` |
| Scratch folders, throwaway names, version piles and report notes do not enter a repo. | In OMP: `rules/no-sprawl-files.md` interrupts a write to a `_v2`, `_final`, `_fixed` or `_copy` file name, proven by `scripts/check_rules.py`. In this repo: `scripts/check_sprawl.py` (runs `skills/tidy/scripts/sprawl.py` against `.sprawl-baseline.json`), `tests/test_sprawl.py`. In another repo: only after the `tidy` skill installs the gate there; otherwise judgment (`SOUL.md`) |
| A tracked shell script keeps its executable bit (a commit made on Windows can drop it). | `scripts/check_modes.py` |
| No check or test reads a commit hook's git variables: a test that runs `git init` under them rewrites this repository. | `scripts/check.py` strips them for every check; `tests/test_checks.py` |
| A pasted reviewer reply loads arch-import. One prompt carries one `/skill:` token; OMP expands only the first. | judgment (arch-import description; no extension, by the operator's decision) |
| arch-export writes the brief and does not fix the subject. | judgment (skill text) |
| The arch-export hand-off does not gate on retention settings; a reviewer refusal is not a leak. | judgment (skill text) |
| architect auto-loads only for a change to types, signatures or module boundaries. | judgment (description) |
| Operator prompts, briefs, alias maps and reviewer replies never enter a tracked file. Fixtures are synthetic. | judgment (`.arch/` is gitignored) |
| Push only when the operator asks for that push. | In OMP: `rules/no-unapproved-push.md` interrupts every push command once so the agent confirms the approval, proven by `scripts/check_rules.py`. Elsewhere judgment (commit skill) |
| A commit is one subject line with no body, unless the operator asks for a body. | In OMP: `rules/single-line-commit.md` interrupts a second `-m`, a message file or a multi-line message, proven by `scripts/check_rules.py`. `scripts/skill_eval.py` (`check_commit_rules`, when run). Elsewhere judgment (commit skill) |
| A commit stages explicit paths, never the whole tree. | In OMP: `rules/no-root-git-add.md`, proven by `scripts/check_rules.py`. Elsewhere judgment (commit skill) |
| Comment rules live in the `no-comments` skill; `SOUL.md` and other skills point to it. | judgment |
| Code ships without narrating or unproven comments. | In OMP: `rules/no-code-comments.md` interrupts an edit or write that adds a comment line to a code file, proven by `scripts/check_rules.py`. It reads line starts only, so a trailing comment is judgment (`no-comments` skill) |
| Prose in a reply uses no em dashes. | In OMP main sessions: `rules/no-em-dash.md`, proven by `scripts/check_rules.py`. Elsewhere judgment (`unslop` skill) |
| An architecture, ownership or state diagram is a fenced `mermaid` block of a type and size a terminal can draw. | judgment (`skills/architect/references/diagrams.md`) |

When you add a rule, add its row. When a check makes a rule impossible to break, replace "judgment" with the check. Drop a row once its mistake cannot happen.
