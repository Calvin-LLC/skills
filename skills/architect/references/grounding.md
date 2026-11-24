# Grounding branches

Phase A cases that only some requests hit. Read the section that matches.

## The request changes product direction

Separate the user's wanted behavior from inherited roadmap gates before sketching. For every inherited gate, verify whether code or finite resources enforce it or it is only documented, and whether the new direction keeps, deletes, or defers it. A documented target is not a design constraint until that check is done.

When the agreed design replaces a documented direction, mold the doc tree to the new model in the same change: delete superseded docs and sweep old-model mentions (the **code-dedup** skill's repo-hygiene pass, if installed), not just add the new doc beside the old ones.

## Direction sources conflict, or the direction doc holds no architecture

- Check what the named direction file actually contains before treating it as binding. A repo's agent-instructions file is often a voice-and-conduct card with no product architecture in it; then the binding direction is the plan docs, the README, or the executable path, and the grounding artifact says which one you used.
- A decision list inside a plan does not reopen a fork the binding docs already settle. Adopt the option that implements the binding doc, log it as a standing decision, and reserve human gates for choices the docs leave open or irreversible writes they do not authorize.
- Never hand runners a premise one source contests and another forbids. A "losing" candidate that matches the user's actual model means Phase A, not the runner, was wrong.

## Two code paths compete for "the product path"

Settle which one is live before sketching: grep the artifacts that have actually run (payloads, fixtures, proven configs) for each candidate's contract markers — the metadata it requires, the exports it looks up, the flags it reads. A path whose required contract no artifact in the tree satisfies is dead, not an alternative, and a name that echoes the binding doc's vocabulary is not evidence it implements the doc.

Attribute defects to the exact flow, too. A banned behavior often lives in a separate verb beside the flow, not inside it; blaming the flow for the verb's sins recommends the wrong survivor.

## The design unifies duplicates into one shared library

Ground it as a merge, not a pick.

- Diff the declared surfaces both ways, and hash every copy of the shared definitions to find which ones actually diverged. Each copy holds functions the others lack; that two-way drift is the requirements list.
- Census call sites per function in every consumer, so the unified surface is the union actually called, not the declared surface alone.
- Build the chosen base against the current shared contract before offering it as a candidate. A base that references a contract since deleted is unbuildable, not a candidate.
- Port first under the old public names and signatures so each consumer move collapses to a path edit. Rename later in its own unit, and do not restyle ported bodies during the move.
- The library never names its host's globals or owns its host's sinks: the host passes values and callbacks in at the entry point.
- When the unified layer loses a distinction the old one made, record it as an accepted gap with a named closing unit instead of inventing a channel to recover it.

## The ask is an audit or a clean state before other work

Phase A *is* the audit, run the same way.

1. Write a quality-bar artifact first: numbered checks a reviewer can grade against, derived from the user's named bar plus the binding docs. When several same-named bar files exist, resolve which one is active before dispatching and record that resolution; a stale copy found first is itself a finding, never the bar.
2. Explorers stay read-only. Each writes its full report to a named file with `path:line` citations per check; chat summaries are rollups only.
3. While explorers run, run the gates you can read directly yourself instead of delegating the verdict.
4. Verify each report file exists on disk and spot-check its load-bearing citations before synthesis. A summary without its file is a claim, not a finding.
5. Report "builds on X" and "documented build blocked because Y" as separate lines: a pass on a different toolset does not clear a pinned baseline.

## A new constraint arrives after runners are dispatched

Scope growing mid-flight is normal. Ground only the newly named subsystem, append it to the grounding artifact as a numbered constraint, and keep the running design pass; steer any runner whose premise the new constraint contradicts instead of letting it finish on the old one. Do not re-run Phase A whole or cancel dispatched runners: the artifact on disk is what makes the append cheap.
