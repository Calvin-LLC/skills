---
name: recall
description: "Reconstruct your recent working context from agent session history, legacy pi transcripts, and live git state, then hand back a tight current-state brief. Use for 'recall my work on X', 'catch me up', 'what have I been working on', 'where did I leave off', before starting or resuming work."
disable-model-invocation: true
---

# Recall

**Before you start or resume work, you rebuild the user's recent working context and hand back a tight capsule of where things stand now and what to do next.**

Keep it tight and on-topic. Read only what the in-scope threads need, then stop.

Your context lives in two records. Your own chat history holds what you did and decided. The repo's history holds everything that happened around the same code under other names: fixes that shipped and got reverted, commits that touched the same files, PR discussion. The **why** skill searches that second record with git and `gh`. A feature with a long bug tail keeps most of its story there, so don't reconstruct it from transcripts alone.

## Where the transcripts are

- **agent sessions** (current harness), in a SQLite store. List with `hermes sessions list --workspace <repo-basename> --limit 50`. Export the user's own words with `session export --format jsonl --only user-prompts --newer-than 7d --cwd <absolute-repo-path> --yes <export-path>`; under `--only user-prompts` each line is one prompt, `{session_id, index, created_at, role, text, message_id}`. A full export (no `--only`) is one line per **session**: a session object (`id`, `title`, `cwd`, `model`, `message_count`) whose `messages` array holds the turns, so parse `.messages` and never assume a per-message row. `--format md` writes one file per session into a directory instead. Narrow with `--session-id`, `--title`, `--after`, `--min-messages`; `--session-id` works on a session still open in this chat, which is how you read the current one back. The `session_search` tool searches the same store by keyword; passing `session_id` narrows it to that one session, so drop it when the question is "did we research this anywhere" — a scoped zero result reads as "no prior work" when the answer is sitting in an older session. When keyword search comes back thin, go at the store directly: `sqlite3 <hermes-home>/state.db` with a `LIKE` over `messages.content` joined to `sessions` (filter `m.role='user'` to find the user's own statements), which reaches every session at once including ones whose title never mentions the topic.

Run `--dry-run` first to see how many sessions match. `--cwd` takes an absolute path and matches sessions whose working directory is under it (a basename like `pi-dotfiles` matches nothing, and `~` is expanded by the shell). `hermes sessions list --workspace` is the one that takes a substring or basename. A repo worked on only through another cwd returns 0, so check `hermes sessions list` before concluding there is no history.
- **Legacy pi sessions** (before the move to Hermes), at `~/.pi/agent/sessions/--<slug>--/<timestamp>_<uuid>.jsonl`, where `<slug>` is the workspace path with the leading slash dropped and each `/` turned into `-` (so `~/proj` becomes `home-user-proj`). Rows have `type`; user turns are `type == "message"` with `message.role == "user"` and `message.content` an array of `{type: "text", text}`. Extract them with `jq -r 'select(.type=="message" and .message.role=="user") | .message.content | map(.text // empty) | join(" ")' <file>`. These files hold the pre-Hermes record, so include them when the window reaches back that far.

Write exports under the scratch directory (`C:/Users/<user>/AppData/Local/hermes/cache/scratch/recall/` on Windows), never into the repo — and hand `hermes` a **native** path. It is a native binary: an MSYS-style translate-path target raises `FileNotFoundError` after the export has already counted the prompts, and `$TMPDIR` in git-bash resolves to the MSYS root.

## Procedure

1. Classify, then route. One specific prior chat to resume is the `session-pickup` playbook of the **poteto-mode** skill, not this. Turning habits into a durable skill is a different task. A human-readable summary of your work is a different task. Recall loads working context across recent chats before you act. If the user already gave you a full state capsule (paths, branch, the change), use it and skip the mining.
2. Lock the scope before searching. Pin the window ("recent" is a real range, default the last 7 days), the topic if named, and the workspace (default the active one; never read another project's sessions without being asked). State the scope back. Never quietly turn "all" into "recent N".
3. Count before reading. Export with `--dry-run` or the user-prompts export and count sessions and prompts. Under about 150 prompts, read them directly: user prompts are the cheap signal for goals, decisions, and corrections. Check the one message you actually need was stored intact first: a long paste can be elided at ingest and persisted as `[[ head.. [N lines] .. tail ]]`, and no re-export recovers the body. When that happens, say so in one line and rebuild the state from live repo/VM state plus the prior session instead of asking for a re-paste — the task is usually recoverable without it.
4. Fan out only when the corpus is too big. Use `task` with one `tasks` entry per slice of sessions (a call takes at most 3 `tasks`, so batch more slices across calls and run each batch to completion). Give each child the exact export command, the topic to grep first, and the instruction to read only matching sessions and only their relevant regions. Skip the current session and obvious noise (cron, subagent, eval, and test sessions; `--source` and `--title` filters separate them). Each child returns the same schema, one block per session: topic, the user's goal, decisions, open threads, struggles and corrections, artifacts (PRs, branches, commits), each citing the session id. Children start with no context, so pass the scope and schema in `context`. The raw transcripts stay with the children; the main thread gets only their findings. For one or two sessions, skip the fan-out and read directly.
5. Sweep the repo record whenever the topic names a feature, file, subsystem, or bug. Run the **why** skill's git and `gh` queries on the named target and ask "what's the current state, what's been tried and didn't hold": `git log --oneline -20 -- <path>`, `git log --all --grep=<topic>`, reverts, and `gh pr list --search <topic> --state all`. Check the scratch directory for prior artifacts before fanning out: audit and report markdowns written under `hermes/cache/scratch/` are the cheapest evidence available, they are already distilled, and a previous audit of the same subsystem usually answers "we already looked into this" outright.

Skip this step only for pure activity recall with no named target ("what did I do this week"), where session history and live state are the whole answer.
6. Verify against live state. A transcript is history, not current truth. Take the PRs, branches, and commits that the mining and the sweep surfaced and check them with `git` and `gh`. When the answer hinges on what an agent actually did (the tools it ran, files it read, errors it hit), read the full transcript, not just the user prompts.
7. Write the brief to the contract below. Group by thread. Stay on the named topic.

## Output contract

Lead with the capsule, then the thread status, then the problems, then the next move. Deeper detail goes below or gets cut.

- **Capsule.** At most 5 bullets. What this work is and where it stands overall.
- **Threads.** One line each, prefixed with exactly one status tag: `[merged #N]`, `[open PR #N]`, `[in flight <branch>]`, `[verified, uncommitted]`, `[reverted #N]`, or `[planned, not started]`. A thread with no tag is not done yet, so tag it.
- **Problems.** At most 5, the recurring ones. Include any fix that shipped and was reverted, so the next attempt starts where the last one failed.
- **Next move.** The single most useful next action, concrete.

An adjacent feature stays out unless it blocks this one. When the capsule and thread lines outgrow a screen, cut detail before you cut threads. Write the brief through the **unslop** skill, cite session findings by session id and repo findings by commit SHA or PR number, and sanitize private context before any public output.

**Reply:** the brief, to the contract above.
