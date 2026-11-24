# Calvin-LLC agent skills

These are the skills I've made or picked up as I've gotten more familiar with LLMs and agentic development, all tuned with [skillopt](https://github.com/microsoft/SkillOpt). I pieced them together to fit my own workflow and standards.

They work with most harnesses. I've tested them on Pi, Hermes, OMP, Claude Code, and Muse Code, and they also support Codex. The skill text names what to do (spawn a subagent, ask the user, read session history) instead of one harness's tool names, so the same files work in each of them. Where a command differs between Linux/macOS and Windows, the skill gives both, and helper scripts ship in both forms (`.sh` plus `.ps1` or `.cmd`). Built on the [Open Agent Skills](https://agentskills.io) standard.

## Install

```bash
# Claude Code, Pi, Hermes, and any other agent the skills CLI detects
npx -y skills add Calvin-LLC/skills -g -y

# OMP
omp plugin install github:Calvin-LLC/skills

# Muse Code (install as plugin or import from Claude)
muse plugins install .
# or import installed Claude skills:
muse skills import --from claude
# enable a skill (one skill per call):
muse skills enable <skill-name> --scope user

# Codex, plus every harness above (the script is in this repo)
sh install.sh        # Windows: powershell -File install.ps1
```

`install.sh` and `install.ps1` clone this repository to `~/.agents/calvin-skills`, or update the copy there with `git pull --ff-only`. They link every skill into `~/.agents/skills`, `~/.claude/skills`, `~/.pi/agent/skills`, `~/.omp/agent/skills`, `~/.hermes/skills`, `~/.config/muse/skills`, and `~/.codex/skills`. When the `muse` CLI is on `PATH`, they also enable each skill in Muse Code. `install.sh` honors `CLAUDE_CONFIG_DIR`, `MUSE_CONFIG_DIR`, and `CODEX_HOME`. `install.ps1` uses the default paths.

The installer replaces files without asking. Back up your own copies first.

- Both scripts link this repository's `SOUL.md` into each harness under the name that harness loads: `~/.omp/agent/RULES.md` (OMP reads it in main sessions and subagents), `~/.config/muse/AGENTS.md` (Muse Code), and `SOUL.md` in `~/.pi/agent`, `~/.hermes` and `~/.agents`. A file already at one of those paths is replaced.
- Both scripts delete any folder that has a skill's name in the skill directories before they link the new one. A Muse Code folder that Muse manages is updated through `muse skills update` and `muse skills install`, never deleted.
- A skill removed from this repository leaves every harness on the next install: both scripts delete its link, and ask Muse Code to uninstall the copy it made from this repository.

From a checkout, `install.ps1 -Source .` (`sh install.sh --source .`) updates the installed copy from that checkout's `main` and enables the repository's git hooks. After that, each commit on `main` syncs the installed copy. The installer refuses to update a copy with uncommitted changes; `-Stash` (`--stash`) sets them aside in a git stash first.

## Use

| Harness | Invocation |
|---|---|
| Claude Code, Hermes, Muse Code | `/<skill>` |
| OMP, Pi | `/skill:<skill>` |
| Codex | `$<skill>` |

## Included skills

The repository holds 40 skills.

### Custom skills

| Skill | Description |
|---|---|
| `harden` | Report-only audit of a whole repository: security (OWASP Top 10:2025, plus the OWASP LLM and agentic Top 10 when the repository uses them), supply chain, reliability, and tests. Every finding quotes the code with a file:line citation. Built upon [cloudflare/security-audit-skill](https://github.com/cloudflare/security-audit-skill). |
| `wcag` | Web accessibility audit (WCAG 2.2 A/AA). Runs nine checks on the rendered page in five browser passes and reports violations with selectors, snippets, and recommended fixes. Inspired by Derek Featherstone's course, with initial work credited to [ECC's accessibility skill](https://github.com/affaan-m/ECC/blob/main/skills/accessibility/SKILL.md). |
| `deslop` | Code hygiene audit against numeric ceilings: CCN < 15, nesting depth < 4, fewer than 5 parameters, file length < 500 LOC, no duplicate clusters, no dead code, no type escapes, and at least 60% line coverage. |
| `gemini-vision` | Send a UI screenshot, mockup, diagram, or wireframe to a vision model for a review of layout, hierarchy, readability, and visual bugs. Despite the name it works with any vision model behind an OpenAI-compatible endpoint: OpenAI, Gemini, a gateway, or a local model. Ships `wcag.mjs`, which computes the contrast ratio of a hex color pair. |
| `reference-mining` | Check whether a reference project already solves a problem, or mine one for mechanisms when improving a target repository. The reference is evidence, and the skill never copies its code. |
| `arch-export` | Write a sanitized architecture brief that an outside model with no repository access can review. |
| `arch-import` | Check the outside reviewer's reply against the real code, run the bakeoff locally, apply the cheap safe wins, and end with a decision ledger and build order. |
| `readme-clean` | Rewrite a README plain and concise, check every claim against the repository, and prove no technical fact was dropped. |
| `writing-plans` | Write an implementation plan from a specification before touching code. |
| `commit` | Git commit rules: one major feature per commit on `main`, a 1-2 line message, and no push until the change is proven locally. |
| `init` | Build or refresh a repository's `AGENTS.md`, running each candidate command before writing it down. |
| `tidy` | Clean up file sprawl and keep it out: an inventory script for scratch folders, throwaway names, version piles, duplicates and stray reports, a cleanup that waits for approval, and a baseline gate that fails only on new sprawl. |

### Retrospective and architecture skills

Adapted from [mattpocock/skills](https://github.com/mattpocock/skills).

| Skill | Description |
|---|---|
| `repo-retro` | Review recent agent sessions, from every harness that worked in the repo, for wasted navigation, failed searches, stale docs, and command loops. It proposes fixes and edits nothing until you approve. |
| `correct` | Find the mistakes agents repeat in a repository and make each one impossible: by architecture first, then types, a lint, a test, and docs last. |
| `writing-for-agents` | Write or prune agent instruction documents: skills, `AGENTS.md`, `SOUL.md`, and briefs. |
| `to-questionnaire` | Turn a decision you cannot resolve alone into a questionnaire for the person who holds the answer: a lead, a client, or a reviewer. |

### Execution and discipline skills

Adapted from [cursor/plugins/pstack](https://github.com/cursor/plugins/tree/main/pstack) by Lauren Tan.

| Skill | Description |
|---|---|
| `plain` | Restate the last message in plain language, with no jargon or codenames. |
| `architect` | Sketch types, signatures, and module boundaries before code, then implement against the agreed sketch. With no change named yet, it first ranks what to restructure from a git-history scan of the most-changed files and the files that change together. |
| `blast-radius` | Find what a change could break outside the diff, and prove the one fact that makes it safe by running real code. |
| `benchmark-checklist` | Vet a benchmark's method, limits, repeatability, and error margins before reporting a speedup or regression. |
| `diagnosing-bugs` | Diagnose a defect or performance regression by first building one command that reproduces the exact symptom. |
| `poteto-mode` | A working style: tasks routed through playbooks, deliberate subagent delegation, verified work, simple code, and concise replies. |
| `babysit` | Drive an existing pull request or Graphite stack to merge-ready, or watch a push to `main` through CI and the deploy until it is live. It monitors CI and triages review comments. It reports merge conflicts instead of resolving them. |
| `recall` | Reconstruct working context from agent session history and repository state. Ships `scripts/sessions.py`, which reads OMP, Pi, Muse Code, Claude Code, Codex, and Hermes session stores in one format. |
| `sharpen` | Before a vague or over-specified task, work out the expert approach, what the user is really after, and the right level of specification. |
| `show-me-your-work` | Keep a TSV decision log during multi-phase or unattended runs, one row per decision: `ts`, `phase`, `decision`, `why`, `evidence`, `result`. |
| `create-verification-skill` | Generate a repository-local verification skill that drives the app the way a user does and captures evidence. |
| `maintain-verification-skill` | Audit a repository's verification skill and feature map against the current app, and correct what drifted. |
| `grill-me` | Ask one fork question, grill the hidden decisions in a plan, or run a multi-model review of a contested design. |
| `how` | Explain how a subsystem, feature, or flow works, where it lives, and what owns it. It can also say whether the thing is implemented yet, or critique its architecture. |
| `why` | Explain why code exists or why a choice was made, citing git history and GitHub. |
| `figure-it-out` | Design an auditable playbook for a large migration, or for any task no narrower playbook fits. |
| `in-your-own-words` | Restate the user's goals and the problem they are solving, to confirm alignment before work begins. |
| `no-comments` | Delete unproven, narrating, and stale code comments from a diff or file set. |
| `technical-writing` | Write or review docs, RFCs, and commit messages with Diátaxis modes, Google developer style, STE, and Global English. |
| `unslop` | Edit text to cut AI tells (puffery, filler, em dashes, jargon) and add a human voice. |

### Prose editing

Vendored from [oaustegard/claude-skills](https://github.com/oaustegard/claude-skills), minus its Stop hook. See `skills/declauding/VENDORED.md`.

| Skill | Description |
|---|---|
| `declauding` | Rewrite model-written prose (PRs, commit messages, READMEs, docs, essays) to read like a human technical writer: removes staged reveals, verdict headers, aphoristic closers, forced triads, and flat-certainty adverbs, with a lint scan and a diff check that no facts were lost or invented. |

### Orca workspaces and workers

Vendored unchanged from [stablyai/orca](https://github.com/stablyai/orca) (MIT; bundled skills). Both are stubs that load the matching guide from the installed `orca` CLI, so they need Orca. See `skills/orca-cli/VENDORED.md`.

| Skill | Description |
|---|---|
| `orca-cli` | Operate Orca-managed worktrees, terminals, repos, automations, and Orca's embedded browser through the `orca` CLI; hand work off to another agent or worktree. |
| `orchestration` | Start worker agents in Orca workspaces (any installed agent and model), message them, and get their results back. |

Orca bundles more skills than these two: computer use, iOS and Android emulators, Jira, Linear, per-workspace environments, and plugin authoring. This repository does not copy them. `orca skills list` shows them, and `orca skills install --skill <name>` installs one.

### Frontend craft and UI auditing

Adapted from [pbakaus/impeccable](https://github.com/pbakaus/impeccable) by Paul Bakaus (Apache 2.0). See `skills/impeccable/VENDORED.md` for the local changes.

| Skill | Description |
|---|---|
| `impeccable` | Design, critique, and audit web and native UI: layout hierarchy, typography, color, motion, UX copy, accessibility, responsive behavior, and design systems. |

## Editing a skill

Run `python scripts/check.py` after you change a skill. It runs every `scripts/check_*.py`: skill text (broken frontmatter, a version number in frontmatter or a `VENDORED.md`, a cited path that does not exist, a dead cross-reference, wording tied to one harness, a warning when a `SKILL.md` is over 8,000 bytes), the tests, new file sprawl, a shell script that lost its executable bit, and whether the installed copy matches this checkout. The pre-commit hook and CI run the same command. `AGENTS.md` lists each rule and what enforces it.

`python scripts/skill_eval.py` tests the part `check.py` cannot: what a model does. It replays fixed prompts through OMP with no window and prints, per model, whether `SOUL.md` reaches the agent, which skill each prompt loads, and whether a commit and a bug fix in a throwaway repo follow the rules. It spends model usage, so run it by hand after changing a description or `SOUL.md`.

## License

MIT © Calvin-LLC. See `LICENSE`.

Bundled work keeps its upstream license. `impeccable` is Apache 2.0, with the license text in `skills/impeccable/LICENSE` and upstream's notices in `skills/impeccable/NOTICE.md`. The axe-core rule engine in `skills/wcag/scripts/vendor/` is MPL-2.0. `declauding` and the two Orca skills are MIT.
