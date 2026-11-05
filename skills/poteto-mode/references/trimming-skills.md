# Trimming skill tokens

For "reduce tokens in the skills" and for removing a behavior from a skill.

- Remove a behavior by deleting the sentence that asks for it. Do not add a "never X" line or a
  reason in its place: the negation costs tokens and plants the idea.
- Measure bytes and words (`wc -c`, `wc -w`) over the touched files before and after. Report both.
- Cut what the model already does without the text: intro paragraphs that restate the title,
  restated rules, generic search steps, evidence checklists, return-format blocks, rationale and
  history. Keep steps, gates, and output shapes.
- Prove each cut on one real task before and after. Revert a cut that changes behavior.
- Skip punctuation swaps (semicolons, dashes): a period plus a capital tokenizes longer.
- Keep descriptions short. They load every session. Drop words that contradict
  `disable-model-invocation`.
- A local skill that diverges from its upstream import is not re-imported wholesale. Port the cut
  by hand.
