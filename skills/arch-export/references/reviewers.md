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
review). Run it in `bash` from the leak-checked brief:

```
omp -p --model <model> --thinking high --no-tools --no-session --mode json --no-skills --no-rules --no-context-files "Review the attached architecture brief and answer its Ask section. Work only from the brief." @.arch/brief-<topic>.md > .arch/<reviewer>-out.jsonl
```

`<model>` is `opus` for "an opus session", otherwise the model the user names.
`@<brief-file>` attaches the brief to the prompt. `--no-tools` holds the
reviewer to the brief, and `--no-skills --no-rules --no-context-files` keep
this repo's instructions out of its context.

`--mode json` prints one JSON event per line. The last `message_end` event
whose `message.role` is `assistant` carries the reply in the `text` blocks of
`message.content`, the model id in `message.model` and the cost in
`message.usage.cost.total`. Write the reply text to
`.arch/<reviewer>-reply.md` and read it in full before
summarizing. Report the model id and the cost. Relay the reviewer's stated
assumptions as unverified items, and recheck its arithmetic against the brief's
own numbers. Nothing from the reply is applied until the user picks items; the
**arch-import** skill turns it into work.
