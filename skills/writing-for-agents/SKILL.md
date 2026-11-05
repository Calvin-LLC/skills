---
name: writing-for-agents
description: "Write or prune any document an agent reads: skills, AGENTS.md, SOUL.md, briefs. Use when creating or editing a skill or agent instruction file, or when asked to slim one down."
---

# Writing for agents

The same levers make a skill, an `AGENTS.md`, a brief and a doc behind a pointer predictable: the agent takes the same process on every run.

## Context pointers

A pointer is a line in the agent's context that names out-of-context material and encodes when to reach it. A skill description is one; a line in `AGENTS.md` naming a doc is the same thing. The wording of the pointer, not the target, decides when and how reliably the agent reaches it. If a must-have target sits behind a weak pointer, sharpen the wording first and inline the material only if sharpening fails.

- Front-load the leading word.
- One trigger per branch. Synonyms that rename one branch are one branch written twice.
- Cut identity the body already carries.

## The two loads

- **Context load**: always-loaded material (an `AGENTS.md` line, a skill description) costs tokens and attention every turn whether or not it fires.
- **Cognitive load**: what the human must remember exists. Spend it where human judgement matters.

Material reached only through a pointer escapes context load at the price of that pointer's line.

## Information hierarchy

Every piece sits on a ladder by how immediately the agent needs it: in-file step, in-file reference, disclosed reference in a separate file behind a pointer. Inline what every branch needs; push behind a pointer what only some branches reach. Keep a concept's definition, rules and caveats under one heading. A document that is simply too long thins attention across every line, so cure sprawl by disclosure and by splitting per branch.

## Completion criteria

Every step ends on a condition that tells the agent it is done.

- **Clear**: done is distinguishable from not done. "Understanding reached" invites ending early; "every modified model accounted for" does not.
- **Demanding**: it requires the thorough version. The strongest criteria are checkable and exhaustive.

Sharpen the bound first. Split the sequence only when the bound is irreducibly fuzzy and you have seen the rush, and only across a real context boundary such as a subagent dispatch.

## Leading words

A leading word is a compact concept already in the model's pretraining (tracer bullet, idempotent, deep module). Repeat it as a token, never as a sentence, and it anchors a region of behaviour in few tokens. Replace "fast, deterministic, low-overhead" with "tight". Prefer an existing word to a coined one, since a coined word recruits no priors.

Steer by the target behaviour, not by prohibition: a ban drags the forbidden thing into context. Keep a prohibition only as a hard guardrail, paired with the positive target.

## Pruning

- One source of truth per meaning. Duplication costs tokens and inflates a meaning's prominence.
- The environment is a source of truth too (scripts, configs, `--help`). Restating it is a cache; keep only what the agent cannot find by looking: the unwritten convention, the reason behind a choice, the gotcha.
- Drop lines that no longer bear on what the document does.
- No-op test, sentence by sentence: does this change behaviour against the model's default? If not, delete the whole sentence. The test is model-relative, so settle disagreements by running the document.
