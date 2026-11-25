---
name: grill-me
description: Use for grill me, interrogate, which approach, challenge this, stress-test this plan, steer. Asks one non-jargon fork question, grills a plan's hidden decisions, or runs a multi-model design review. Not for rewording or explaining.
---

# Grill me

Three jobs: ask a fork, grill a plan, or review the work. Default for all is proceed. Do not invent a fork.

Do not use for how it works (the **how** skill, whose critique mode covers architecture of existing code) or why it exists (the **why** skill). If the invocation asks to explain or go deeper, answer directly or load **how**.

## Ask

Ask only when all of these hold, or they said grill me:

1. Two or more concrete outcomes, and they would change what you build, keep, or drop
2. Context does not already pick one
3. You cannot run, measure, or read the answer
4. The call is product, preference, or irreversible. Not "should I do this reversible thing?"

If any fail, proceed and show the result. If you cannot name two concrete outcomes, you do not have a question. When the invocation already says to get it all done, ask only the one-way door and decide every reversible fork yourself.

Before asking:

- Look for an option that removes the fork instead of choosing a side. When every option keeps a hand-edited switch, flag, or convention someone must remember, derive it from something that already exists (the build configuration, a registry) or make the wrong state impossible. Recommend that, or just build it if it is reversible.
- Read the code each option touches, so the answer can be applied without another read pass. Once the user answers, the very next tool call is the edit that applies and records the decision.

Ask through `ask`. One question per turn, two to four options, then wait. Keep the call short and complete, since a truncated argument fails it.

**The question text carries no domain vocabulary**, and the sentence above the options is where this gets skipped. Write it like the **plain** skill: short sentences, no jargon, a 6th grader could pick. No constant name, mode name, multiplier, or internal noun. Describe the observable instead: what moves, what changes for them, what breaks. Explain an identifier once inside the `ask` form, above the options.

Each option:

- Label: 1-5 everyday words. Put your pick first and add `(Recommended)`
- Description: what happens if they choose it, in one or two sentences
- Preview when the choice is a layout, copy, or config they need to see

The recommended pick is your guess. Wrong and clear beats vague and safe.

Bad: "How should we handle auth?"
Good: "When the login site is down, keep trying, fail now, or save the cart as unpaid?"

Do not ask what the code already shows. If the design and the code disagree, ask which one wins, and quote both.

Reading the answer:

- **A question back** ("elaborate", "what's the difference", "why is this relevant") means the question was jargon or not a real fork for them. Drop it, gather the facts with commands (counts, file sizes, which code path runs today), then re-ask in the user's own picture of the system with the concrete numbers. When they say how they thought it worked, offer that as the recommended option.
- **A scope answer** ("that's for later") ends every question that depended on the deferred work. Cut them; do not re-ask in another shape.
- **An answer that voids the premise** ("that path is deprecated, don't worry about it") picks no option. Log the retirement as its own row, matched option `none`, and in the same pass correct everything that still says the work is open (board, issue, doc line), noting that retired keys and payload slots stay for backward compatibility.

Finish one decision before opening another. Restate the pick in one line, then move. Stop when you can predict the next three answers, or leftover forks are low-risk.

## Grill a plan (design-tree interview)

Use when they want a plan, design, or idea stress-tested: not one fork, but the hidden decisions under it. When they say steer or course-correct, they want a direction audit: first restate their original ask and targets in one line, list what the work so far covers and skips, and ask about the gaps; start no new work.

Map the decision space as a **design tree**: every decision branches into the decisions that hang off it. Work it in rounds. The **frontier** is every decision whose prerequisites are already settled. Ask the whole frontier each round in one `ask` call (cap ~3): number each, give your recommended answer, and word it so "yes" accepts that answer. Then wait.

- **Facts are your job, decisions are the user's.** When a question needs a fact from the environment (a path, a count, a version, which code runs today), spawn a `scout` with `task` or run the command yourself. A running lookup blocks only the questions downstream of it; ask the rest of the frontier now.
- **Each round reshapes the tree.** Recompute the frontier from the answers. A question that depends on one still open this round belongs to a later round.
- **Done when the frontier is empty**: every branch visited, nothing silently assumed. Do not act on the plan until the user confirms shared understanding.
- **On convergence, record it** per the next section. Write an ADR in `docs/adr/NNNN-slug.md` (context, choice, reason in 1-3 sentences) only for decisions that are hard to reverse, surprising without context, or a real trade-off.

## Record the answers

An answer that lives only in the chat is lost at the next compaction, and the next agent never sees it. The very next tool call after the answers arrive is the decision-log write: no lookups, edits, or other work first. The final reply states how many rows were added.

1. **Find the repo's decision record and append to it.** Look for `DECISIONS.md`, `docs/decisions*`, `docs/adr/`, `docs/plans/`, a `Decision log` section in a status page, then whatever the README or doc map points to. Match its format exactly: for a table or TSV, add a row with the same columns, the chosen option in the decision field and the user's own words in the reason field. A decision that changes what is built also updates the status and open-work rows that stated the old behavior, in the same edit.
2. **No record exists: create `docs/decisions.md`** with a `Decision log` table: date, question, options offered, answer verbatim, which option it matched (or "none"), what it changes.
3. **A rule that governs future work goes in the repo's agent-instruction file (`AGENTS.md` or equivalent) too**, one line under the section it belongs to. Run `git check-ignore` on it first. If it is ignored, say so and put the line in the README or the decision record instead.
4. **A spec being written** keeps its own `Decision log`, and earlier wording that was your assumption is corrected in the spec body in the same edit.
5. **Ship it with the work.** The record change goes in the same commit as the change it shaped.

- Free-text answers often reject the offered options. Log them as given, mark which option if any they matched, and fix prior text that rested on your guess.
- A question answered with a question stays an open item in the record until the fact is gathered. Never log it as a closed decision.
- A round lost to compaction is recovered through the **recall** skill, if installed.

## Review

When they say interrogate, the design is contested, or you are about to ship a change that still has a real fork in it, read `references/review.md` and run its five steps: scope, intent, spawn read-only reviewers on different models with `task`, synthesize, judge. Do not auto-apply anything.

After Ask, Grill, or Review, ship. If they asked for a plan, the **writing-plans** skill. If a decision is blocked on knowledge only someone else holds, the **to-questionnaire** skill. Otherwise, if the **poteto-mode** skill is installed, match one of its playbooks.
