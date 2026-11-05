---
name: to-questionnaire
description: Turn a decision you can't resolve alone into a questionnaire someone else fills in. Use when blocked on knowledge another person holds (a lead, a client, a reviewer) and you need it pulled out of them async. Do not use for questions you can answer by running or reading something.
---

# To questionnaire

Turn something the user can't answer alone into a **questionnaire**: a Markdown document they hand to one person to fill in async, or work through together in a meeting. The recipient holds knowledge the user lacks; the questionnaire pulls it out of them.

**Grill the send, not the subject.** Interview the user only about the *send*, which they can always answer: who it goes to, and what they need back. The questions in the document then target the **gap** between what the recipient knows and what the user needs.

## Steps

1. **Who is it going to?** In one `clarify` exchange, get the recipient's role, expertise, and relationship to the user. This fixes the tone and how much context the document must carry. Done when you know who the recipient is and what they know that the user doesn't.

2. **What do you need back?** In one `clarify` exchange, get the specific decisions or facts the user can't resolve alone and needs from this person. Done when you have a concrete list of what the user must walk away able to do or decide.

3. **Write the questionnaire.** Draft questions aimed at the gap from steps 1–2, following the document structure below. Write it to `to-questionnaire-<slug>.md` in the current directory (slug from the topic) and report the path. Done when the file exists and every item the user named in step 2 is covered by a question.

## Document structure

Frame the document as a **discovery questionnaire**: the user lacks context, the recipient holds it. Order questions most-important-first, since async means you may only get one pass. Group them under `##` headings by theme once there are more than a handful.

```
# <Questionnaire title>

**Purpose:** why this questionnaire exists and the decision riding on it.

**From:** <the user>, **To:** <the recipient>, **How your answers will be used:** <where they go>

## Context

One paragraph orienting a recipient who wasn't in the user's head. Enough to answer well, not a page.

## How to answer

Deadline and rough effort. Partial answers and "I don't know" are useful: flag anything you're unsure of rather than skipping it.

## <Theme heading>

### <One question, one idea>

_Why this matters: <one line, only where the question could be misread or invite a throwaway answer.>_

>

## Anything else?

A closing catch-all: anything we didn't ask that we should know?
```

Every question is one idea, never compound, with an answer stub (`>`) directly beneath. A question whose answer you could get by running code or reading a file does not belong here — that is your job, not the recipient's.
