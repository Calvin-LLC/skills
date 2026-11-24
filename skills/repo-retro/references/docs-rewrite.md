# Rewriting AGENTS.md or a docs map after a retro

- Read the current file in full. Rewrite only the repo-facts section; leave persona and voice sections alone.
- Take every fact from the tree, not from memory or the old text: re-count each number the doc states, and build tables (routes, services, commands) from the code's own registry or config.
- Run every command the doc names once, from the shell the agents use, and read the output, not only the exit code.
- Extract every backticked path from the edited docs and assert each exists. Re-grep every `file:line` you cite after the edit; a dirty tree shifts lines.
- Fill a rules-and-enforcers table honestly: a rule with no check gets "Nothing yet" plus the proposed check.
- If AGENTS.md is gitignored, un-ignore it so the pointers reach other checkouts, and report that.
- Fix doc-versus-UI label mismatches, and name any other doc that still carries the old label instead of editing out-of-scope files.
- A file that holds only persona and voice text: append one `## Repo map and working facts` section and leave every existing byte alone. Copy the file aside, append, then byte-compare the copy against the same-length prefix of the result. Match the file's existing line endings (count `\r\n` in its bytes).
- Record uncommitted owner edits that affect behavior (a forced define, a hard-coded input) with the date, so a later agent neither reverts nor commits them.
- Write a long section to a scratch file and append it with a small script; confirm the line count changed.
- Bloat the user wants gone: move it to a sibling `_archive/<repo>/` outside the repo unless told to delete. First check tracked versus ignored (`git ls-files <dir>`, `git check-ignore -v <dir>`), grep scripts and docs for the path, compare file count and size after the move, then repoint the docs. A directory wired into the repo's scripts, an evidence or receipts directory, or a scratch directory written within the hour is not bloat: leave it and name the deferred command.
