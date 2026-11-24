### Authoring or modifying a skill

**You own the skill's voice.** Agent-facing prose has a higher bar than human prose. Unhelpful sentences become instructions.

1. Write or edit the `SKILL.md` in this repo. Frontmatter needs `name` and `description`. Follow **unslop**.
2. Validate: referenced files exist, cross-skill links resolve, no second skill restates this one.
3. Test cases if structural. Skip if subjective.
4. Run **Committing on main**.

**Description is a router.** Trigger phrase plus, for auto-invoke skills, one anti-trigger. Body holds the rest. A description over ~200 characters is doing the skill's job in the catalog.

**One idea, one skill.** If two files teach the same improvement, delete it from one of them. Point at the owner by path. Do not paraphrase.

Auto-invoke skills (no `disable-model-invocation`) must not share a trigger. Manual skills still must not duplicate an idea. "Do not use" lines are for auto-invoke collisions, not a wall of negatives on a skill the user named.

Rank every sentence:

1. **Systematic.** Encodes a recurring miss, not one task.
2. **Complementary.** Fills a gap. If a sibling or a `references/` file already says it, delete the copy.
3. **General.** No hardcoded gold answers, machine paths, model names, or entity lists. `firecrawl --help` beats a command encyclopedia.
4. **Actionable.** `When X, do Y.` Direct. No posture essays.
5. **Short.** Length is a quality metric. Prefer deletion. A skill that grew past a few KB is repeating itself.

When in doubt, delete. Prose earns its keep by changing a decision. Tell it to do the thing and skip the reason. Explain only when the rule is confusing without one. Point at structural sources (types, READMEs, config) instead of restating them, since hardcoded details go stale. A workflow you keep hitting that is not captured → propose a new skill.

**Reply:** summary of the skill, key design decisions, validation notes.
