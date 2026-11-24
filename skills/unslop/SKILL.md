---
name: unslop
description: "Use when writing or editing text a person will read (docs, READMEs, replies, commit messages, cover letters, messages to people, product and landing-page copy): cuts AI tells (puffery, filler, em dashes, jargon) and adds a human voice. Not for fiction or quoted text."
---

# Unslop

Edit text to remove AI patterns and add human voice.

## Process

1. Scan for the patterns below.
2. Rewrite. Preserve meaning, match intended tone.
3. Add soul (see next section).
4. Self-audit: "What makes this obviously AI generated?" Fix remaining tells.

Applies to anything you write: replies, docs, comments, commit messages. In a bulk sweep, list the hits and rewrite each sentence rather than substituting a character.

## Adding soul

Removing patterns is half the job. Sterile, voiceless writing is just as obvious.

- **Have opinions.** React to facts instead of neutrally listing pros and cons.
- **Vary rhythm.** Short sentences. Then longer ones that take their time.
- **Acknowledge complexity.** "Impressive but also kind of unsettling" beats "impressive."
- **Use "I" when it fits.** First person isn't unprofessional.
- **Let some mess in.** Perfect structure looks machine-made.
- **Be specific.** Not "this is concerning" but "there's something unsettling about agents churning away at 3am."

Voice comes from the source or the author. Never invent an opinion, anecdote, number, or mistake to sound human.

## Patterns to detect and fix

### Content

1. **Puffery.** "pivotal moment", "testament to", "evolving landscape", "setting the stage for", "indelible mark", "deeply rooted". State what happened.
2. **Name-dropping.** Listing media outlets without context. Pick one, say what was said.
3. **Superficial -ing phrases.** "highlighting...", "ensuring...", "reflecting...", "showcasing...", "fostering...". Delete or expand with real sources.
4. **Promotional language.** "nestled", "vibrant", "breathtaking", "groundbreaking", "renowned", "stunning", "must-visit". Use neutral descriptions.
5. **Vague attributions.** "Experts believe", "Industry reports suggest", "Some critics argue". Name the source or delete.
6. **Formulaic challenges.** "Despite challenges... continues to thrive." Replace with specific facts.

### Language

7. **AI vocabulary.** Additionally, crucial, delve, enduring, enhance, fostering, garner, interplay, intricate, landscape (abstract), pivotal, showcase, tapestry (abstract), testament, underscore, vibrant. Replace with plain words.
8. **Fancy ways to say "is".** "serves as", "stands as", "boasts", "features". Say "is" or "has".
9. **"Not just X, but Y."** State the point directly.
10. **Rule of three.** Forcing ideas into groups of three. Use the natural number.
11. **Synonym cycling.** Protagonist, main character, central figure, hero all in one paragraph. Pick one, repeat it.
12. **False ranges.** "from X to Y" where X and Y aren't on a meaningful scale. List topics directly.

### Style

13. **Em dashes.** Use none. End the sentence or use a comma. No parenthetical asides, en dashes, or hyphen-as-dash substitutes: those trade one tell for another. Parentheses for code (`fn()`), units, and ranges are fine.
14. **Colon overuse.** Colons are fine before a list or example, not as mid-sentence connectors. "If you're coming from traditional automation: instead of registering event handlers, you describe conditions" becomes "Describing when the scheduler should fire works best as plain English." Drop the comparison framing with the colon.
15. **Boldface overuse.** Don't bold every proper noun or acronym.
16. **Inline-header lists.** The tell is a bold label and colon that restates the line: "**Performance:** Performance improved...". Convert those to prose. A bold lead-in that ends in a period, names the item, and is followed by new detail ("**Retries.** Failed calls retry three times.") is fine.
17. **Title case headings.** Use sentence case.
18. **Decorative emoji.** Ban it in skills, agent-facing files, replies, commit messages, comments, and CLI chrome. A mark stays only if it carries information the words do not: site assets (SVG, PNG, favicon), UI icons, a tool's own status glyph, a feature-matrix check. Write `ok` / `fail` / `warn` instead of a decorative check, X, star, or warning face.
19. **Curly quotes.** Replace with straight quotes.

### Communication artifacts

20. **Chatbot phrases.** "I hope this helps!", "Let me know if...", "Of course!", "Certainly!", "Found the smoking gun!" Remove.
21. **Cutoff disclaimers.** "While specific details are limited..." Find sources or remove.
22. **Sycophantic tone.** "Great question! You're absolutely right!" Respond directly.

### Filler

23. **Filler phrases.** "In order to" becomes "To". "Due to the fact that" becomes "Because". "It is important to note that" gets deleted.
24. **Excessive hedging.** "could potentially possibly be argued that it might" becomes "may".
25. **Generic conclusions.** "The future looks bright." State specific plans or facts.

### Jargon

26. **Abstract metaphor nouns.** When used as metaphor: substrate, wedge, vector, locus, vantage, nexus, primitive, harness, surface (as in "API surface"), bedrock, scaffolding, modality, paradigm, gold-plating, ratchet, evacuate (for moving code), endgame, north star, flywheel. Literal technical uses are fine. Pick the concrete word: "substrate" becomes "base", "wedge in" becomes "add", "vector" becomes "way" or "method", "gold-plating" becomes "more than the job needs", "ratchet" becomes the mechanism's real name or "a limit that only tightens", "evacuate" becomes "move out", "endgame" becomes "the last phase".

### Plain speech

27. **Say what it does, not how it feels.** "the database stays close at hand", "SQL you can read", "types that follow your schema" name a feeling. Name the mechanism or a number: "`--dry-run` prints every file it would delete", "a column rename fails the build". If you can't restate a sentence as a concrete instruction, fact, or number, cut it. If it could appear unchanged in another project's docs, it says nothing about this one. Cut it.
28. **Shorten or split dense sentences.** If the reader has to backtrack to parse a sentence, break it in two or drop clauses. One idea per sentence.
29. **Active voice.** Catch "is/are/was/were + past participle" and name the actor: "queries are validated" becomes "the compiler validates queries". Passive is fine only when the actor is unknown or doesn't matter.
30. **Cut adverbs, or use a stronger verb.** "runs quickly" becomes "is fast" or the number. "significantly improves" becomes the measured delta.
31. **Prefer the plain word.** "utilize" and "leverage" become "use", "facilitate" becomes "help", "numerous" becomes "many", "in the event that" becomes "if".
32. **Pages someone scans.** On a page read at a glance (a dashboard, a walkthrough, a caption page), keep provenance out of the body: run ids, frame numbers, capture timestamps, and file paths belong in a log or behind a toggle. Rename internal state names to the word an outsider would use: "Interstitial" becomes "Loading", `AWAIT_REVIEW` becomes "Waiting for a person". Write each step as one line of what is happening plus one line of state.
33. **Change-log narration in docs.** "Removed on <date>...", "moved from X", "was deleted after the checks", "squashed into", "per the owner". Docs describe what is. A deleted thing leaves no line behind. Delete the sentence. Git is the record.
34. **Figurative verbs and personified code.** "the parser swallows errors", "the cache remembers", aphorisms. Use the literal phrase: what the code does.
35. **Dropped small words.** Write whole sentences with articles and verbs. Spell out arrows and abbreviations in prose.
