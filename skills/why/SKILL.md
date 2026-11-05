---
name: why
description: Use for why code exists, why we picked Y, regressions, or postmortems. Cite git and gh. Use how for how it works.
---

# Why

Explain why something was done. Read the history. Quote it. If the record is silent, say so.

`how` is runtime and structure. This skill is motivation. Do not infer intent from code shape.

```bash
git blame -L <start>,<end> <file>
git log --follow -p -- <file>
git log --oneline -20 -- <file>
gh pr view <number> --json title,body,author,comments,reviews
```

Default to git and `gh`. Open a ticket, doc, chat, metric, or error tool only when it is already in the session and git is not enough.

Answer with:

- **Question.** What we are explaining.
- **Evidence.** Commit, PR, or message, quoted, with a citation.
- **Inference.** Labeled as inference. Never mixed into evidence.
- **Gaps.** What we looked for and did not find.
