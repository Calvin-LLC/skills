# Vendored copy of declauding

- Source: https://github.com/oaustegard/claude-skills, `declauding/` at repo commit b9eb735, taken from the repository tree, not the release zip. That commit is the only record of which upstream this is; no file here carries a version number.
- Left out of the tree copy: `hooks/`, `tests/`, `README.md`, `CHANGELOG.md`. The scripts use only the standard library, apart from the two below.
- Removed on purpose: `hooks/hooks.json` (a Stop hook that runs `fresh_eyes.py` and writes to `~/.claude`). Do not re-add it.
- Local edits to `SKILL.md`: the hard-coded `/mnt/skills/user/declauding/` script prefix is replaced with "this skill's directory", plus a `python`/`python3` note; the `metadata` block with upstream's version is deleted from the frontmatter. Re-apply after an upgrade.
- Further local edits, re-apply after an upgrade: (1) `SKILL.md` gains a "UI and product copy (local)" section (UI copy in scope; cutting detail for a brief or non-technical reader is allowed and reported as a content cut) and one line in File mode (when the user wants to review first, return a before / after / why table and write nothing until approved). (2) `references/corpus.md` "Reproducing it": the `python3 - <<'EOF'` heredoc became a saved `lead_rate.py` script with a Windows `python` note.
- Not used by default: `scripts/declaude_review.py` (sends text to the Gemini or Anthropic API) and `scripts/declaude_rank.py` (needs torch). `scripts/fresh_eyes.py` only runs if called by hand.
- To upgrade: fetch upstream, diff `declauding/` between the commit above and the new one, apply that diff to this folder (skip the frontmatter version line), re-read the scripts for network or exec calls, and write the new commit above.
