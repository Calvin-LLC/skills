# Doc sets: directories, file lists, "all docs"

## Directory mode

Every `README.md` under the directory gets one pass, in the Workflow order from `SKILL.md`. Shared facts that repeat across files (install, usage) get inventoried once and checked per file. Report one row per file: files changed, lines before/after, facts preserved/dropped.

## Tiers when the scope is every doc

Tier the set by reader and intent before rewriting:

- Reader-facing topical docs (README, `docs/*.md`, package READMEs): the full workflow.
- Dated plans, evidence logs, and working briefs: one tell sweep only. Em dashes become commas or periods, curly quotes become straight, and every number survives untouched. These are records. Their register is facts with timestamps, and polish beyond the tells is scope creep.
- Agent identity cards, scratch reports under dot-directories, and data tables: out of scope. A data table is not prose and a persona card's voice is deliberate.

State the tiers and the per-tier treatment in the final report, so the user can hand back the parts treated lighter.

## Scripted tell sweeps

Tell sweeps across many files are scripted, not hand-edited. Rules that keep the script safe:

- Read and write bytes (`open(f,'rb').read().decode('utf-8')`) so CRLF files keep their endings, then confirm `git diff --stat` shows equal insertions and deletions.
- Toggle on lines starting with three backticks and skip everything inside fences. Code and shell comments keep their punctuation.
- Replace in order: a lone em dash in a table cell becomes a hyphen, an em dash at end of line becomes a comma, one before a capital becomes a period, the rest become commas.
- Headings need their own pass (` — ` becomes `: `) because the sentence rules read wrong in a title. List heading hits separately before editing.
- Re-scan afterwards outside fences and print any survivor with file and line.
