---
name: recall
description: "Reconstruct your recent working context from agent session history and live git state, then hand back a tight current-state brief. Use for 'recall my work on X', 'catch me up', 'what have I been working on', 'where did I leave off', before starting or resuming work."
---

# Recall

**Before you start or resume work, you rebuild the user's recent working context and hand back a tight capsule of where things stand now and what to do next.**

Keep it tight and on-topic. Read only what the in-scope threads need, then stop.

Your context lives in two records. Your own chat history holds what you did and decided. The repo's history holds everything that happened around the same code under other names: fixes that shipped and got reverted, commits that touched the same files, PR discussion. The **why** skill searches that second record with git and `gh`. A feature with a long bug tail keeps most of its story there, so don't reconstruct it from transcripts alone.

## Where the transcripts are

Run `python <this skill's directory>/scripts/sessions.py` (below, `sessions.py`). It reads every agent harness's session store on the machine (`--help` lists commands and filters; `sources` shows which stores exist). Work in the active repo may have happened in a different harness than the one you are running in, so leave `--harness` off unless the user names one.

- `list --cwd <absolute-repo-path> --days 7 --limit 0` counts and names the sessions (the default stops at 10). `--cwd` is a prefix match on the directory a session ran in, so a repo worked on only from another directory returns nothing: retry without `--cwd` before concluding there is no history.
- `prompts` prints what the user typed, one JSON line each. `transcript --session <id>` prints everything, including the session you are in. `--session <id>` lifts `--days` and `--limit`; add `--children` to also get that session's subagent rows (their `parent` is the root session id).
- To find a topic anywhere, save `prompts --days 90 --limit 0` to a scratch file and search it for the topic; a search scoped to one session reads as "no prior work" when the answer sits in an older one.

Redirect large `transcript` or `calls` output to a scratch file outside the repo (the harness's own scratch dir if it names one, else the OS temp dir); `list` and `prompts` stay on stdout.

## Procedure

1. Classify, then route. One specific prior chat to resume is the `session-pickup` playbook of the **poteto-mode** skill, not this. Turning habits into a durable skill is a different task. A human-readable summary of your work is a different task. Recall loads working context across recent chats before you act. If the user already gave you a full state capsule (paths, branch, the change), use it and skip the mining.
2. Lock the scope before searching. Pin the window ("recent" is a real range, default the last 7 days), the topic if named, and the workspace (default the active one; never read another project's sessions without being asked). State the scope back. Never quietly turn "all" into "recent N".
3. Count before reading. Run `list`, then `prompts` with `--limit 0` (both stop at 10 sessions by default), and count sessions and prompts. Under about 150 prompts, read them directly: user prompts are the cheap signal for goals, decisions, and corrections. `prompts` clips each message to 400 characters (shown as `…[+N chars]`): re-run with `--clip N` (`--clip 0` = no clipping) or use `transcript --session <id>` before treating a message as lost. When the message is truly unrecoverable, say so in one line and rebuild the state from the live repo and the prior session instead of asking for a re-paste.
4. Fan out only when the corpus is too big. Spawn one subagent per slice of sessions (respect the tool's per-call limit and batch the rest; with no subagent tool, read the slices yourself in sequence). Give each the exact `sessions.py` command, the topic to search first, and the instruction to read only matching sessions and only their relevant regions. Skip the current session and automated, subagent, eval, and test sessions. Each returns the same schema, one block per session: topic, the user's goal, decisions, open threads, struggles and corrections, artifacts (PRs, branches, commits), each citing the session id. Subagents start without your conversation, so pass the scope and schema in the brief. The raw transcripts stay with them; the main thread gets only their findings. For one or two sessions, read directly.
5. Sweep the repo record whenever the topic names a feature, file, subsystem, or bug. Run the **why** skill's git and `gh` queries on the named target and ask "what's the current state, what's been tried and didn't hold": `git log --oneline -20 -- <path>`, `git log --all --grep=<topic>`, reverts, and `gh pr list --search <topic> --state all`. Check the scratch directory and the repo's docs for earlier audit or report files first: they are already distilled, and a previous audit of the same subsystem usually answers "we already looked into this" outright.

Skip this step only for pure activity recall with no named target ("what did I do this week"), where session history and live state are the whole answer.
6. Verify against live state. A transcript is history, not current truth. Take the PRs, branches, and commits that the mining and the sweep surfaced and check them with `git` and `gh`. When the answer hinges on what an agent actually did (the tools it ran, files it read, errors it hit), run `calls --session <id>` (rows carry `id`, `ts` and `parent`; a forked or resumed session replays older calls, so dedupe by `id`) or read the full transcript, not just the user prompts.
7. Write the brief to the contract below. Group by thread. Stay on the named topic.

## Output contract

Lead with the capsule, then the thread status, then the problems, then the next move. Deeper detail goes below or gets cut.

- **Capsule.** At most 5 bullets. What this work is and where it stands overall.
- **Threads.** One line each, prefixed with exactly one status tag: `[merged #N]`, `[open PR #N]`, `[in flight <branch>]`, `[verified, uncommitted]`, `[reverted #N]`, `[blocked: <reason>]`, or `[planned, not started]`. A thread with no tag is not done yet, so tag it.
- **Problems.** At most 5, the recurring ones: recorded failures and reverted fixes, each cited by session id, SHA or PR, so the next attempt starts where the last one failed. Mark a cause you did not verify `[hypothesis]`. Fixes belong in Next move, not here.
- **Next move.** The single most useful next action, concrete.

An adjacent feature stays out unless it blocks this one. When the capsule and thread lines outgrow a screen, cut detail before you cut threads. Write the brief through the **unslop** skill, cite session findings by session id and repo findings by commit SHA or PR number, and sanitize private context before any public output.

**Reply:** the brief, to the contract above.
