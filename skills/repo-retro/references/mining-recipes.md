# Batch-mining recipes (reading `calls.jsonl`)

The miner writes one row per deduped tool call. Analyse it with a script file
(see the SKILL.md heredoc pitfall), not as a shell heredoc.

## Row schema

`call_id`, `session` (owning id, root or child), `root` (top-level session id),
`child` (`'True'`/`'False'` strings — compare as strings), `name`, `args`
(dict), `flags` (dict, `{}` on fire-and-forget calls), `head` (first bytes of
the result text), `ts` (epoch string). There are **no prompt rows**: user text
is not in `calls.jsonl` — pull it per session with `session export
--format jsonl --only user-prompts --session-id <id>`.

## Outcomes without parsing output bodies

- `flags.total_count == 0` on a `search_files` row = empty search (the
  zero-search metric). Count every machine-readable row in the denominator
  (`{}`-flag rows included), not just the rows matching your preferred shape.
- `terminal` with `flags.exit_code` in (1, 2, 124, None) = failed call;
  `flags.cause` carries the traceback head when a tool call raised. Group the
  failed command heads after normalising whitespace so reruns cluster.
- `head` is non-empty on most rows: classify hot spots from it — command
  prefixes for `terminal`, path/target for `read_file`, error tails for
  failures — instead of inferring from `args` alone.

## Recurring junction-workspace counters

- **Alias-duplicate reads** (thin workspace over an umbrella through
  junctions): group `read_file` rows per root by basename AND path form
  (thin-workspace path vs umbrella path); a basename seen through both forms
  in the same session is one churn unit. Report basenames, not read calls.
  Before publishing, verify the two forms are physically the same file —
  file-id compare (`os.stat(...).st_ino` on Windows NTFS junctions, or the
  repo's own `check_paths.py --verify-junctions` when present).
- Normalise the path key before grouping: backslash to forward slash,
  then basename (`p.replace('\\','/').rsplit('/',1)[-1].lower()`), and
  classify the form by which workspace-root substring the path carries
  (`auto-work-env` vs the thin-workspace name) — the transcripts mix both
  spellings for the same file, and an unnormalised key splits one alias
  pair into two "/wrong-form" buckets. Write the counter in a scratch
  script file, never in a heredoc: a one-line replace with a backslash
  literal dies in the heredoc before the counter runs.
- **Terminal boilerplate prefix**: count `terminal` rows whose command
  starts with the literal `cd <dir> &&` prefix. The prefix share of terminal
  calls sizes the missing launcher; the segment after the first `&&`
  classifies what work the prefix wrapped (VM verb, build, heredoc
  analysis, dump walk).
- **Monolith re-read shape**: split the read-file count into full-file reads
  vs windowed reads (`args.offset`/`args.limit` set). Windowed reads against
  a maintained code map are sanctioned navigation; full reads of a
  multi-thousand-line file are the cost signal.
- **Sanity-check your own recompute** of orientation/edit indexes against
  the miner's printed table; agreement within ±1 means your row keying
  matches its field names. A wide divergence means you mistyped a field
  (`ts` is a string; sort on `float(ts)`).
