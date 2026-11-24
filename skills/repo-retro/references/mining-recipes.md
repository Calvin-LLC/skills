# One-pass mining of `sessions.py calls` output

Save `sessions.py calls --session <id> --children --clip 0` per session to a scratch file (the OS temp directory) and analyse with a script file. Do not clip the dump: a cut call-argument JSON fails to parse and identical long commands split into different groups. Clip only what you print.

## Rows

One JSON object per line: `harness`, `session`, `parent` (root session id of a subagent; empty for a root), `cwd`, `child`, `kind` (`call` or `result`), `tool`, `id` (the harness tool-call id; a call and its result share it), `ts` (UTC ISO time), `text` (call arguments as JSON, or the result), `error`. Before counting:

- Dedupe replayed history by `id` (keep the first row per `kind` + `id`): a forked or resumed session replays an older session's calls.
- Order by `ts`, not file order.
- Group subagents under their root by `parent`; an empty `parent` is a root session.
- Pair a `result` with its `call` by `id`; where `id` is empty, a `result` follows the `call` it answers, and parallel calls are followed by their results in the same order.

Tool names differ per harness, so classify by what the call does:

- **read**: the tool name contains `read`, or a shell call whose command starts with `cat`, `head`, `tail`, `sed -n`, `Get-Content`
- **search**: name contains `grep`, `search`, `glob`, `find`, or a shell `rg`/`grep`/`find`/`ls`/`dir`/`Select-String`/`Get-ChildItem`
- **mutate**: name contains `edit`, `write`, `patch`, or a shell redirect into a repo file. Not repo mutations: a redirect into the scratch directory, and a `>` inside a search pattern (`rg 'a>b'`, `=>`)
- **shell**: `bash`, `powershell`, `terminal`, `shell`, `exec`

## Counters

- **Orientation before first edit**: every non-mutating call (read, search, listing, web, build, probe) before the first mutate call. Report beside it the reads-and-searches-only count (read, search and web calls only).
- **Empty search**: a search call whose result is empty or says no matches. Print the denominator (all search calls) beside it.
- **Failed command**: `error` is true, or the result reports a non-zero exit code. Group the failing command heads after normalising whitespace so reruns cluster.
- **Re-reads**: group read calls per session by normalised path (backslashes to forward slashes, lower-cased). Split full-file reads from windowed reads (an offset, limit or line range in the arguments): windowed reads are navigation; repeated full reads of a large file are the cost.
- **Alias reads**: the same file reached through two path forms (a junction or symlinked workspace). Confirm the two are one file before reporting, and count basenames, not calls.
- **Boilerplate prefix**: shell commands that begin with the same `cd <dir> &&` or connect/bootstrap line. Its share of shell calls sizes the missing launcher; the remainder of the command says what the prefix wrapped.

Recompute one session by hand before publishing a counter.
