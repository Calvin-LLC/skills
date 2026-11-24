# Vendored copy of impeccable

- Source: [pbakaus/impeccable](https://github.com/pbakaus/impeccable) by Paul Bakaus, at commit `b49177d`: the build under upstream's `.omp/skills/impeccable/` with the script path written as `.agents/skills/impeccable/`. That commit is the only record of which upstream this is. The launcher reads the engine it downloads from `scripts/VERSION` and `scripts/engine-checksums.txt`; both come from upstream and are never edited by hand.
- License: Apache License 2.0. `LICENSE` and `NOTICE.md` are copied unchanged from the root of the upstream repository at that commit. The two files `NOTICE.md` calls `skill/reference/ios.md` and `skill/reference/android.md` are `reference/ios.md` and `reference/android.md` here.
- Re-vendored by a three-way merge of the old and new upstream commits with the local changes below on top.
- Not copied: the five files in upstream's `agents/` directory (four `.toml` agent definitions and `openai.yaml`).
- To upgrade: fetch upstream's newest skill release, diff its `.agents/skills/impeccable/` at the commit above against the new one, apply that with the local changes below kept, re-copy `LICENSE` and `NOTICE.md`, and write the new commit above.

## Local modifications

Changed by Calvin-LLC so the skill reads the same in every harness and on Windows:

- `SKILL.md`: shorter description, launcher instructions for POSIX and Windows, and the command table and launcher details moved into the two added files below.
- `reference/craft-floor.md`: gained the loaded-symbols ban that was in `SKILL.md`.
- `reference/doctor.md`, `reference/hooks.md`, `reference/foundations.md`: commands written as `<launcher> <verb>` with the POSIX and Windows forms. `reference/hooks.md` also drops the Hermes plugin path.
- `reference/new-work.md`: gained the paragraph on working from screenshot fixtures when the app cannot run.

Command path only. These match upstream's `.omp/skills/impeccable/` build with the script path written as `.agents/skills/impeccable/`:

- `reference/audit.md`, `reference/critique.md`, `reference/degraded/asset-producer.md`, `reference/generate.md`, `reference/layout.md`, `reference/routing.md`, `reference/typeset.md`

Live-mode element removal ships upstream, so `reference/live.md`, `reference/degraded/manual-edit-applier.md` and `scripts/live-browser.js` match upstream.

Added here, not from upstream:

- `reference/commands.md`, `reference/launcher.md`, and this file.
