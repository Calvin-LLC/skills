---
name: grill-me
description: Grilling, three ways. Challenge a fork (one plain question with a recommended pick when a product or preference call would change the work), grill a plan with a design-tree interview that surfaces every hidden decision, or run a multi-model review of a contested design or diff. Use for grill me, interrogate, which approach, challenge this, stress-test this plan. Do not ask if the answer is already clear, reversible, or observable.
---

# Grill me

Three jobs, one skill: ask a fork, grill a plan, or stress-test the work. Default for all is proceed. Do not invent a fork.

Do not use for how it works (`how`) or why it exists (`why`). `how` critique mode already covers architecture of existing code.

## Ask

Default: do not ask. Infer, run, or ship.

Ask only when all of these hold, or they said grill me:

1. Two or more concrete outcomes, and they would change what you build, keep, or drop
2. Context does not already pick one
3. You cannot run, measure, or read the answer
4. The call is product, preference, or irreversible. Not "should I do this reversible thing?"

If any of those fail, proceed. Do not block on the human. Show the result.

Before asking, look for an option that removes the fork instead of choosing a side. When every option keeps a hand-edited switch, flag, or convention that someone must remember, the real answer is usually to derive it from something that already exists (the build configuration, a registry) or make the wrong state impossible. Make that the recommended option, or just build it if it is reversible. A question whose options all preserve the fragile mechanism gets rejected for a better design the user then has to spell out.

Read the code each option touches BEFORE asking, so the answer can be applied without another read pass. Once the user answers, the very next tool call is the edit or write that applies and records the decision; reading more files first looks like stalling, and the user will interrupt to ask why it is not fixed yet. When the invocation text already says to get it all done, ask only the one-way door and decide every reversible fork yourself.

Use `ask_user_question` (in Hermes the tool is `clarify`, called as `questions=[{question, choices}]`; keep each call short and complete, since a truncated JSON argument fails the call). One question per turn. Two to four options.

**The question text carries no domain vocabulary.** Write it like `/bro`: short sentences, no jargon, a 6th grader could pick. This is the part that gets skipped — the options get written plainly and the sentence above them is left in the project's own words. A question holding a constant name, a mode name, a multiplier, or an internal noun ("the calibration base", "the AI path", "3.2x further") is a question the user cannot answer; they will stop and tell you to restate it in plain English, which costs the round trip you were trying to save. Describe the observable instead: what moves, what changes for them, what breaks. Keep the identifier in the chat sentence just before the question, where it can be explained once. If a term is genuinely load-bearing, say what it does in the same breath.

Each option:

- Label: 1-5 everyday words. Put your pick first and add `(Recommended)`
- Description: what happens if they choose it, in one or two sentences
- Preview when the choice is a layout, copy, or config they need to see

The recommended pick is your guess. Wrong and clear beats vague and safe. Wait for the answer before the next question.

A good question names a real fork.

Bad: "How should we handle auth?"
Good: "When the login site is down, keep trying, fail now, or save the cart as unpaid?"

If you cannot name two concrete outcomes, you do not have a question. Look again, then proceed. Do not ask what the code already shows. If the design and the code disagree, ask which one wins, and quote both.

When the answer is a question back ("elaborate", "wtf is the difference", "why is this relevant"), the question was jargon or not a real fork for them. Drop it, gather the facts with commands (counts, file sizes, which code path runs today), then re-ask in the user's own picture of the system with the concrete numbers. A user who says "I thought it was all saved in one place" has just stated the target: offer that as the recommended option. A scope answer ("that's for later") ends every question that depended on the deferred work; cut them rather than re-asking in another shape.

**An answer can void the premise instead of picking an option.** "That path is deprecated, don't worry about it" is not one of the choices and must not be logged as one: the fork (hold versus tap) ceases to exist and the real decision is the retirement. Log the retirement as its own row, matched option `none`, and correct everything that still tells the next reader the work is open — the board column, the issue text, the doc line that says to fix it — in the same pass. A retired item left sitting in a "to do" column is worse than never having asked, because it now reads as scheduled work. Conversely, when an answer says a subsystem is retired, its keys and payload slots usually stay for backward compatibility: write that constraint down too, or a later session prunes them and breaks old clients.

Finish one decision before opening another. Restate the pick in one line, then move. Stop when you can predict the next three answers, or leftover forks are low-risk.

## Grill a plan (design-tree interview)

Use this when they want to stress-test a plan, design, or idea — not a single fork, but the hidden decisions under it. Interview relentlessly until every branch is settled.

Map the decision space as a **design tree**: every decision branches into the decisions that hang off it. Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled — the questions you can ask now without guessing at answers you haven't heard yet. Ask the whole frontier each round in one `clarify` call (cap ~3 per round so it stays readable): number each, give your recommended answer, and word it so "yes" accepts that answer. Then wait before the next round.

- **Facts are your job, decisions are the user's.** Never ask the user for something you can look up. When a frontier question needs a fact from the environment (a path, a count, which code runs today, a version), dispatch a read-only `task` or run the command yourself. Don't block the whole round on it: a running lookup is just an unsettled prerequisite, so only the questions downstream of it wait — ask the rest of the frontier now.
- **Each round reshapes the tree.** Answers settle decisions and push the frontier outward, unblocking what hung off them. Recompute the frontier and ask the next round. A question whose answer depends on another question still open this round belongs to a later round, not this one.
- **Done when the frontier is empty** — every branch visited, nothing silently assumed. Do not act on the plan until the user confirms you've reached shared understanding.
- **On convergence, record it.** Use the Record section below; write the settled design as an ADR in `docs/adr/NNNN-slug.md` (context, choice, reason in 1–3 sentences) only for decisions that are hard to reverse, surprising without context, or a real trade-off.

## Record the answers

An answer that lives only in the chat is lost at the next compaction, and a teammate or the next agent never sees it. After each round, before any other work, write it into the repo.

1. **Find the repo's decision record and append to it.** Look for `docs/decisions*`, `docs/adr/`, `docs/plans/`, a `Decision log` section in a status page such as `docs/mission.md`, then the page `docs/MAP.md` or the README points to. A record file that no longer exists is not a record: use the status page's log and say where it went. A decision that changes what is built or not built also updates the status and open-work rows that stated the old behavior, in the same edit. Match its format exactly: if it is a table or TSV, add a row with the same columns, the chosen option in the decision field and the user's own words in the reason field.
2. **No record exists: create `docs/decisions.md`** with a `Decision log` table: date, question, options offered, answer verbatim, which option it matched (or "none"), what it changes.
3. **A rule that governs future work goes in `AGENTS.md` too**, one line under the section it belongs to, not the whole discussion. Run `git check-ignore AGENTS.md` first. If it is ignored the line helps this machine only: say so and put it in the README or the decision record instead.
4. **A spec being written** keeps its own `Decision log` and any earlier wording that was your assumption is corrected in the spec body in the same edit.
5. **Ship it with the work.** The record change goes in the same commit as the change it shaped, never as a separate doc commit that can be dropped.

Recording rules:

- Free-text answers often reject the offered options ("we want to consolidate all of these features cleanly in the desk ui"). Log them as given, mark which option if any they matched, and fix prior text that rested on your guess.
- A question answered with a question ("what even caused it to hang?") stays an open item in the record until the fact is gathered. Never log it as a closed decision.
- When a round is lost to compaction, the stored messages are readable from `~/.hermes/state.db`, table `messages`, tool results containing `user_response`; the in-session search skips the session you are in.

## Review

Use this when they name interrogate, the design is contested, or you are about to ship a change that still has a real fork in it. Do not auto-apply anything.

1. Scope. The files or diff they pointed at. On `main`, `git diff` / `git log`. Package that plus the context the reviewers need.
2. Intent. One paragraph: what this change is trying to do. From the user, the commits, and the code. Reviewers challenge the execution, not the goal. If you cannot state the intent, that is an Ask, not a Review.
3. Spawn. One reviewer per configured review model via `task` (up to 3 `tasks` per call; batch larger lists). `task` has no per-call model field, so reviewer models come from `delegation.model`; for a genuinely different model, run `subagent chat -q -m <model>` per reviewer. Same filled prompt to every reviewer. Fill `references/reviewer-prompt.md` with the intent, the diff, `references/rubric.md`, and `references/code-quality-review.md`. Read-only. Do not flatten onto one model.
4. Synthesize. Consensus (2+ models) is high signal. Lone findings still get read. Merge duplicates. Note disagreements.
5. Judge. You are the lead, not an aggregator. Filter with `references/lead-judgment.md`. Bucket every finding: Act on / Consider / Noted / Dismissed. Include which models raised it and one line why you bucketed it that way. Cap Act on at a handful. Show Dismissed so they can override you.

Output: Intent, Reviewers, the four buckets, then where the models agreed or split.

After Ask, Grill, or Review, ship. If they asked for a plan, `writing-plans`. If a decision is blocked on knowledge only someone else holds, `to-questionnaire`. Otherwise match a poteto-mode playbook.
