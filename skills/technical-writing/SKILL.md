---
name: technical-writing
description: "Use for /technical-writing or when writing or reviewing docs, RFCs, readmes, PR descriptions, commit messages, or any prose the reader must understand on first read: Diátaxis modes, Google developer style, STE, Global English."
---

# Technical writing

Write so a tired engineer understands on the first read. Apply all four layers.

Above the layers:

- **Before you draft, read the brief, the sources, and any existing text on the topic.** Match the stated length, format, and citation rules. Don't guess what a file says.
- **A sample of the user's own prose outranks the layers.** Match its voice.
- **Docs describe what is, not the edit that produced it.** No change-log narration: "removed on <date>", "moved from X", "per the owner". A deleted thing leaves no line behind. Git is the record.
- **Prune.** Delete status reports, closure reports, and duplicate pages. Keep one page per job. Link instead of restating.
- **Cut every word that does no work, and use the short, everyday word.** "In order to" is "to". "Use", not "utilize". A long word has to buy its length with precision.
- **Write the real name.** The codebase is the word list: the real symbol, file, flag, or command, not a synonym or a description of it.
- **Don't invent jargon.** Use the words a developer would say out loud: "move", "delete", "a budget that only decreases", not "evacuate", "ratchet", or "endgame". A named pattern is fine when the doc says what it means the first time. Add new offenders to the **unslop** skill's abstract-metaphor rule with their replacement.
- **When a rule makes a sentence worse, fix the sentence another way or leave it alone.** A sentence that follows every rule and sounds machine-written has failed.

## Vary the rhythm

A doc can obey every layer and still read machine-written: every sentence clipped, no view, nothing specific.

- Mix sentence lengths on purpose. One thought per sentence does not mean one length per sentence: split the sentence that carries two thoughts, keep the long one that carries one.
- Have a view where the mode allows it. Explanation weighs trade-offs, so say what you make of them. Reference stays dry.

## Pick the mode first (Diátaxis)

One document, one mode. Skip this for single-purpose prose such as an essay or a message. Two questions pick it: does the content serve action or understanding, and learning or work? The same test works on one sentence.

- Action + learning: **tutorial**, learning by doing.
- Action + work: **how-to**, steps to a goal.
- Understanding + work: **reference**, facts for lookup.
- Understanding + learning: **explanation**, understanding and why.

Before you write or restructure a document, read its mode's rules in `references/modes.md`.

Don't mix modes: no reference tables inside a tutorial, no hand-holding inside reference, no arguing inside a how-to. Split and link instead.

## Write sentences to the reader (Google developer style)

- Talk to the reader as "you", in the present tense. "Will" only for things that happen later.
- Say who does what: "the compiler checks", not "is checked". Passive is fine only when the actor is unknown or beside the point.
- Write instructions as commands: "Click Submit." Never narration or "should be done".
- Put the condition or warning before the instruction it guards: "To delete the document, click Delete."
- Put the common case first. Exceptions after.
- Sound like a knowledgeable friend. No buzzwords.
- Don't pre-announce ("we will soon support...") and don't start consecutive sentences with the same phrase.
- Numbered lists for sequences, bullets for everything else. Introduce a list with a complete sentence. Keep items parallel.

Link text, heading style, UI bold, serial commas, "please", and "simply": read `references/style.md`.

## Make statements load one at a time (STE rules)

- One instruction per sentence. One thought per sentence everywhere else.
- Split instructions longer than about 20 words and other sentences longer than about 25.
- Keep "the" and "a": "Remove backup file" reads two ways. "Remove the backup file" reads one.
- Give each word one meaning and keep it. If "check" means inspect, don't also use it for restrain. Pick one word per action: "start", not "start" here and "initiate" there.
- Avoid "-ing" words where you can.

## Leave no sentence open to two readings (Global English)

- Keep "only" and "not" next to the word they change: "only fails on growth" and "fails only on growth" say different things.
- Break up long noun strings: "the cache size limit check script" becomes "the script that checks the cache size limit".
- Make every "it", "they", and "this" point at one obvious thing. Repeat the noun when in doubt. Never use "this" or "which" to point at a whole clause.
- Don't drop verbs: "Step 1 installs the CLI and step 2 the daemon" leaves step 2 without one.
- Keep the small words that show structure, such as "that" in "Ensure that the switch is off". Never trade clarity for word count.
- Repeat the article in a series when it prevents a misread: "the client and the host", not "the client and host", when they are two things.
- Say which parts "and" or "or" joins when a sentence can group two ways. "Both...and", "either...or", and "if...then" disambiguate for free.
- Use periods, not semicolons. Replace an em dash with a new sentence.
- Make text in parentheses a full grammatical unit or its own sentence. Never form plurals with "(s)".
- No slashes: write "a, b, or both" instead of "a/b" or "and/or".
- Call each thing by one name, everywhere. A doc that says "the gate", "the ratchet", and "the budget check" for one thing teaches three things. Don't reword an unchanged sentence between edits either.
- Skip idioms, colloquialisms, Latin abbreviations, and metaphors. Non-native readers, translators, and agents parse plain constructions best.

## Voice

- Apply the **unslop** skill to every doc this skill touches. That skill owns the slop-pattern catalog: AI vocabulary, filler, hedging, formatting tells.
- PR descriptions and commit messages are writing too. Every layer except Diátaxis applies to them. A PR body is a briefing a reviewer reads in under a minute. Link logs, SHA lists, and metric tables instead of pasting them.
- Product UI strings are not documentation. Use the product's copy guidelines for those.
- Match the repo's existing snippet indentation. Write real paths. Make every count or tree claim true at the commit that lands it, and include the command that regenerates it.

## Worked example

Before:

> Configuration of the lint warning budget script parameters is performed via warnings.json. Note that it's important to remember that running with --write, which updates the committed budget to reflect the current count, should only be done when lowering it. If exceeded, CI fails.

After:

> `check-warnings` reads the committed budget from `warnings.json` and counts the lint warnings. If the count exceeds the budget, CI fails. Run `check-warnings --write` only to lower the budget.

## Review checklist

Done when every item holds for the prose this skill covers. Item 1 applies only to document sets.

1. Each file is one Diátaxis mode, with links where modes meet.
2. Every instruction is a command, with its condition in front.
3. No sentence carries two instructions or two thoughts.
4. No word can be cut without losing meaning.
5. "Only" sits next to the word it changes. Every "it" points at one thing. Every clause keeps its verb.
6. Each thing has one name across the docs.
7. A developer would say every word out loud: no invented metaphors, no fancy synonyms, real symbol names.
8. All symbols, paths, and counts are real at this commit, with the commands that regenerate the counts.
9. No sentence narrates an edit instead of stating the world.
