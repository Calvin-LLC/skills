---
name: readme-clean
description: Rewrite a README to be plain, clear, and concise without losing technical facts. Kills AI slop (puffery, passive voice, em dashes, rule-of-three), enforces active voice and sentence case, verifies every fact survives the diff. Use when asked to clean up, optimize, rewrite, or de-slop a README.
---

# README clean

Rewrite a README so a tired engineer understands it in one pass. The deliverable is prose a human wrote on purpose, not a template. Preserve every technical fact. Kill every AI tell.

## Load first

Read the `unslop` skill before editing. Its pattern list is the checklist. This skill adds README-specific workflow on top of it; it does not restate the patterns.

## Scope

This is not README-only. The same workflow covers any text the user wants plain and factual for a technical reader: an HTML caption page, a demo walkthrough, a standup page, a status dashboard, a run log digest. The caller names the file, directory, or explicit file list. Otherwise `README.md` in the cwd. If none exists, stop and report. Do not invent one for an empty repo.

Page and site text has its own register. It is read at a glance, not read through, so each step gets one line of what is happening plus one line of the state it is in. Cut anything the heading already carries (the order number, the timestamp, the step name) and anything the reader cannot act on (raw API response bodies, JSON blobs). Keep every number, identifier, and code reference, phrased plainly. The target line reads like "Cookies cleared. The account is logged out. DB now: no session. Profile blob 0 bytes."

Step titles use the everyday word, never the internal or technical term. A reader scanning the page should recognise the step without knowing the domain. "Interstitial" becomes "Loading", "Device-approval wall" becomes "Approval asked", "Two-factor method" becomes "Where to send the code", "Captcha wall: where the re-run stopped" becomes "Waiting for a person". If a title names a state machine value or a field name, rewrite it as what a person sees.

Delete text you cannot make truthful. A caption that describes a state the artifact does not actually show is worse than no caption: the reader trusts the page and is wrong. If a claim cannot be checked against the artifact right now, cut the sentence or the whole step rather than hedging it. The user's standing preference is that a wrong line gets removed, not softened, and that a page which says only true things beats a fuller page that overclaims.

Strip provenance prose that only the author cares about. Run ids, capture timestamps, frame numbers, script filenames, and phrases like "captured at" belong in the evidence manifest, not in the words a reader scans. Keep the number when it is the fact (a byte count, a duration, a state name); drop the machinery that produced it.

Directory mode: every `README.md` under the directory, one pass each in the Workflow order below. Shared facts that repeat across files (install, usage) get inventoried once and checked per file. Report one row per file: files changed, lines before/after, facts preserved/dropped.

When the caller extends scope to every doc, tier the set by reader and intent before rewriting:
- Reader-facing topical docs (README, docs/*.md, package READMEs): the full workflow below.
- Dated plans, evidence logs, and working briefs: one tell sweep only. Em dashes become commas or periods, curly quotes straight, and every number survives untouched. These are records, not marketing; their register is facts with timestamps, and polish beyond the tells is scope creep.
- Agent identity cards, scratch reports under dot-directories, and data tables: out of scope. A data table is not prose and a persona card's voice is deliberate.
State the tiers and the per-tier treatment in the final report, so the user can hand back the parts treated lighter.

Tell sweeps across many files are scripted, not hand-edited. Rules that keep the script safe:
- Read and write bytes (`open(f,'rb').read().decode('utf-8')`) so CRLF files keep their endings, then confirm `git diff --stat` shows equal insertions and deletions.
- Toggle on lines starting with three backticks and skip everything inside fences. Code and shell comments keep their punctuation.
- Replace in order: a lone em dash in a table cell becomes a hyphen, an em dash at end of line becomes a comma, one before a capital becomes a period, the rest become commas.
- Headings need their own pass (` — ` becomes `: `) because the sentence rules read wrong in a title. List heading hits separately before editing.
- Re-scan afterwards outside fences and print any survivor with file and line.
- The user's "all docs and the README" request still does not cover persona files (`AGENTS.md`) or a to-do list.
- Do not commit unless asked. Offer one commit line at the end.

## Workflow

1. **Inventory facts.** Read the README and list every technical fact: names, versions, commands, flags, paths, URLs, limits, defaults. This list is the contract for the rewrite. Nothing on it may vanish. If the doc tree already carries uncommitted edits from a prior or sibling pass, read that diff first: it may already fix half the stale claims, so build on the working tree and never re-fix what a pending edit already fixes.
2. **Read the code or skill files the README describes.** A README that documents behavior the artifact does not have is wrong in a way prose polish cannot fix. Verify claims against the real artifact where cheap (does the command exist, does the file exist). Correct what fails. Report what you could not verify as unverified, per claim.

   Verify in bulk, before any edit, so the corrections land in one pass:
   - Existence-check every referenced path, command file, and script in one shell loop. A referenced file deleted from the tree is the most common stale claim.
   - Re-count every number from the source it describes instead of trusting the prose: migration and program counts from directory listings and conf files, suite file counts from the runner script or package manifest, coverage flags from the test config, poll intervals and TTLs from the module constants that read them. Prose numbers drift silently; a doc that is otherwise reliable still lies about its counts.
   - Measure size and line-count claims (cloc for code lines, wc -c for bytes); raw wc -l overstates code lines, so a stale count in a debt table needs remeasurement, not re-copying.
   - Grep env defaults, ports, and timeouts in the file that reads them, not the file that installs them.
   - When the doc describes a live system, measure the system, not the repo. Run version, disk, container and listener commands over ssh and diff the output against the doc. Services documented but gone, disk percentages, kernel and OS versions, and runner counts drifted in a runbook that read as current. Fix the doc and record the audit date inside it.
   - Check each backtick path in the README and CLAUDE.md with `os.path.exists`, and check each script name in a command example separately. Commands that name a script the repo never had (`verify-all.sh` when the real one is `check.sh`) are the stale claim readers hit first.
   - Look for a duplicated or truncated tail left by an earlier bad edit (a closing section pasted twice, a fragment starting mid-word) before rewriting.
   - A path you cannot find a replacement for stays in the doc with a plain note that it is missing and where it used to live. Do not delete the pointer and do not invent a new one.
   - When the user asks you to "save a credential in the docs as an env", put it in a gitignored env file (check `git check-ignore -v <file>` first; `.env.*` patterns usually cover it) plus a tracked `*.env.example` with the key and no value, and document only the variable name and the script that reads it. Tracked docs are pushed. Then grep tracked and untracked-nonignored files for the value, and `git log -S` for history; report any hit with the value masked.
3. **Check structure.** A README needs, in roughly this order: what it is (one paragraph), install, usage with real examples, and anything the reader must not do. Sections beyond that earn their place by being read by someone. Delete empty boilerplate sections (fake badges rows with no badges, "Contributing" with no process, "Roadmap" with one done item). Do not add sections the project does not need.
4. **Rewrite.** Apply the unslop checklist. In order of impact:
   - Active voice. Name the actor. "Findings are quoted" becomes "every finding comes with a quote".
   - Say the mechanism, not the feeling. "Evidence-driven" means nothing; "audits X and reports findings" means something.
   - One idea per sentence. Split dense sentences.
   - Sentence case headings.
   - No em dashes, no colon-as-connector, no bold-label bullets that restate themselves.
   - Describe every file in a layout block. A bare filename in a tree tells the reader nothing.
   - Code examples stay untouched unless they reference something that does not exist.
5. **Fact audit.** Diff old against new. For each item in the inventory from step 1, confirm it appears in the rewrite (possibly reworded). Report any that dropped and why. A dropped fact is a bug in the rewrite, not a style choice.
6. **Self-audit.** Ask: "What makes this obviously AI generated?" Fix remaining tells. Then ask: "Could this paragraph appear unchanged in another project's README?" If yes, it says nothing about this project. Cut or make it specific.

## Report

- Files changed, lines before/after (bytes is fine when the artifact is generated).
- Facts preserved (count) and any dropped, with reason.
- Claims checked against the artifact and their result (verified, unverified, corrected).
- Sections deleted, if any.
