# Calvin-LLC Agent Skills
Here are all the skills i've either made or picked up as I become more familiar with LLMs and agentic development, all tuned via [skillopt](https://github.com/microsoft/SkillOpt). This was pieced together to meet my workflow & standards. Can be used with most harnesses, tested personally on Pi, Hermes, and OMP. Built on the [Open Agent Skills](https://agentskills.io) standard.

## Installation


```bash
# Claude Code, Pi, and Hermes
npx -y skills add Calvin-LLC/skills -g -y

# OMP
omp plugin install github:Calvin-LLC/skills
```

## Included skills

### Custom skills

| Skill | Description |
|---|---|
| `harden` | Security posture audit covering OWASP Top 10:2025, OWASP LLM/Agentic Top 10, supply chain, reliability, and tests with quoted code and file:line citations. Built upon [cloudflare/security-audit-skill](https://github.com/cloudflare/security-audit-skill). |
| `wcag` | Web accessibility audit (WCAG 2.2 A/AA). Measures rendered pages across five browser passes and reports violations with selectors, snippets, and recommended fixes. Inspired by Derek Featherstone's course, with initial work credited to ECC's ["https://github.com/affaan-m/ECC/blob/main/skills/accessibility/SKILL.md"](https://github.com/affaan-m/ECC/blob/main/skills/accessibility/SKILL.md). |
| `deslop` | Programmatic scan of code quality metrics (CCN < 15, nesting depth < 4, file length < 500 LOC, duplication, and dead code). Audits codebase health against numeric thresholds. |
| `gemini-vision` | Visual review of UI screenshots, mockups, diagrams, and wireframes. Labels UI components, checks layout hierarchy and alignment, verifies readability, and identifies visual contrast bugs. |
| `reference-mining` | Search reference projects for prior art, architectural mechanisms, or implementation patterns when improving a target repository. |
| `arch-export` | Export a sanitized architecture brief for an external model without direct repository access. |
| `arch-import` | Convert an external model's architecture review response into a local bakeoff plan. |
| `readme-clean` | Rewrite documentation to be plain, clear, and factual for a technical reader while preserving technical details. |
| `writing-plans` | Create an implementation plan from a specification before modifying code. |
| `commit` | Git commit guidelines: one logical feature per commit on `main`, concise summary, and local verification before pushing. |
| `init` | Generate or refresh a repository's `AGENTS.md` by verifying active commands directly against the project environment. |

### Retrospective and architecture skills
Adapted from [mattpocock/skills](https://github.com/mattpocock/skills).

| Skill | Description |
|---|---|
| `repo-retro` | Review recent agent sessions for redundant navigation, failed searches, stale documentation, and execution loops. |
| `correct` | Identify recurring agent errors in a repository and enforce prevention via architecture checks, types, lints, tests, or documentation. |
| `writing-for-agents` | Create or edit agent instruction documents, including skills, `AGENTS.md`, and briefs. |
| `improve-codebase-architecture` | Scan a codebase for structural improvements, render an interactive HTML report, and review selected paths. |
| `to-questionnaire` | Convert ambiguous or blocked decisions into an asynchronous questionnaire for team leads, clients, or reviewers. |

### Execution and discipline skills
Adapted from [cursor/plugins/pstack](https://github.com/cursor/plugins/tree/main/pstack) by Lauren Tan.

| Skill | Description |
|---|---|
| `plain` | Restate complex technical explanations in plain, jargon-free language. |
| `architect` | Draft type signatures, interfaces, and module boundaries before implementation. |
| `blast-radius` | Identify code paths affected by a proposed change and verify safety margins using executable code. |
| `benchmark-checklist` | Verify benchmark methodology, environment limits, repeatability, and error margins before reporting performance metrics. |
| `diagnosing-bugs` | Isolate defects or performance regressions by writing a deterministic reproduction command first. |
| `poteto-mode` | Engineering discipline focusing on concise responses, deliberate subagent delegation, clean code, and empirical verification. |
| `babysit` | Drive an existing pull request or Graphite stack to merge-ready status. Monitors CI, resolves conflicts, triages review comments, and reports stack status. |
| `recall` | Reconstruct working context from agent session history, transcripts, and repository state. |
| `sharpen` | Clarify task scope, technical intent, and specification detail before execution. |
| `show-me-your-work` | Maintain an auditable TSV decision log (decision, rationale, evidence, outcome) during multi-phase runs. |
| `create-verification-skill` | Generate a repository-local verification skill that exercises application behavior end-to-end. |
| `maintain-verification-skill` | Audit and update a repository verification skill to prevent drift against application changes. |
| `grill-me` | Challenge design decisions, conduct design-tree interviews, or run multi-model reviews on contested proposals. |
| `how` | Explain subsystem mechanics, ownership boundaries, and file organization. |
| `why` | Trace the historical context, rationale, and past regressions behind existing code. |
| `figure-it-out` | Design an auditable execution playbook for large migrations, open-ended tasks, or complex refactors. |
| `in-your-own-words` | Summarize user goals and operational constraints to confirm alignment before work begins. |
| `no-comments` | Audit and remove stale, redundant, or misleading source code comments. |
| `technical-writing` | Structure documentation using Diátaxis principles, active voice, and concise technical grammar. |
| `unslop` | Edit text to eliminate repetitive AI clichés, passive voice, and artificial prose tells. |

### Frontend craft and UI auditing
Adapted from [pbakaus/impeccable](https://github.com/pbakaus/impeccable) by Paul Bakaus.

| Skill | Description |
|---|---|
| `impeccable` | Design review, UX analysis, layout hierarchy, typography, accessibility, responsive behavior, and design system governance for web and mobile interfaces. |

## License

MIT © Calvin-LLC
