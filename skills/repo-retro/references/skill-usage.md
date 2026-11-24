# Counting skill use across all projects

`scripts/skill_usage.py <skills dir> --days 30` runs the session reader for every harness store and every working directory, with no `--cwd` filter. Pass `--skip-cwd <skills repo>` for the checkout that holds the skills. It prints one row per skill and lists skills with zero use last.

## Definitions

- **Typed:** a user prompt that starts with the harness's invocation token for a skill (`/name`, `/skill:name`, `$name`). Only tokens that match a skill folder count, so built-in commands drop out.
- **Self-load:** a read call whose only target is `<skill>/SKILL.md` or the skill's own address. Reading a reference file inside the skill is not a load.
- **Sessions:** root sessions with either signal. Subagents roll up to their root, and a session counts once per skill.
- Rows that replay a forked session's history count once.

## Rules

- A read of `SKILL.md` by a session working in the skills repo is authoring, not use. That is what `--skip-cwd` removes. Typed use in that repo still counts.
- Print the window, the root-session count and the harnesses beside the table. A harness that has no typed token or no skill address shows zeros; name it as uncovered.
- Zero use in 30 days does not mean dead. A skill for a rare event needs a longer window. A skill with zero self-loads and a description that opens with what it does, not when to use it, may have a broken router: read its description before proposing a delete.
- Propose only. This mode writes no log row.
