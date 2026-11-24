# Choosing and running the reviewer

Companion to "Hand-off" in SKILL.md. Read when the user has not named a
reviewer, wants two compared, asks for a headless run, or a reviewer refuses.

- **Deep-reasoning chat session** (e.g. Claude Max): best for the algorithm and
  architecture table. It handles a long brief, so include the full data-shape
  detail.
- **Search-capable session** (e.g. Perplexity): use when the question is
  "what's the current best-known approach for X". It can search current papers,
  libraries and benchmarks. Add the research addendum from SKILL.md.
- **Both:** run the same brief through each and diff the answers. Agreement
  between two different-family models is a strong signal; where they disagree,
  bake off both candidates by hand.
- **Named session.** The user names the reviewer: a consumer web session they
  paste the brief into by hand. The deliverable is the brief file path stated
  plainly; never try to deliver or post it yourself.
- **Retention.** Retention settings on the receiving account are not a gate. The
  leak check is what makes the brief safe for an ordinary consumer account, so
  say it passed and that it names no identifiers. Do not ask the user to verify
  settings or to hold a zero-retention plan before pasting.
- **Refusal.** A reviewer that refuses on content policy has not found a leak.
  Do not re-sanitize identifiers. Restate the question as the general systems
  problem without operational framing, or use another reviewer, and say which
  you did. The same applies when the user cannot use the named reviewer.

## Headless Opus run

Only when the user says "to an opus session" (or otherwise asks you to run the
review). Run it from the leak-checked brief:

```
POSIX:
cat .arch/brief-<topic>.md | claude -p "Review the architecture brief on stdin and answer its Ask section. Work only from the brief." --model opus --effort high --tools "" --max-turns 1 --no-session-persistence --output-format json > out.json

Windows (PowerShell):
Get-Content -Raw .arch\brief-<topic>.md | claude -p "Review the architecture brief on stdin and answer its Ask section. Work only from the brief." --model opus --effort high --tools '""' --max-turns 1 --no-session-persistence --output-format json | Set-Content -Encoding utf8 out.json
```

In Windows PowerShell 5 an empty `--tools ""` argument is dropped, hence the
`'""'` form; PowerShell 7 takes plain `--tools ""`. Prefer `| Set-Content` to
`>`, which writes UTF-16 in PowerShell 5.

Extract `.result` to `.arch/<reviewer>-reply.md` and read the reply in full
before summarizing. Report the model id from `modelUsage` and the cost. Relay
the reviewer's stated assumptions as unverified items, and recheck its
arithmetic against the brief's own numbers. Nothing from the reply is applied
until the user picks items; the **arch-import** skill turns it into work.
