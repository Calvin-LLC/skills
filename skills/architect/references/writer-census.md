# Writer census: effects that leave the codebase

Before sketching anything that charges, grants, revokes, deletes, or sends, list
every code path that mutates the same authoritative state, quote each one's
predicate for doing so with `path:line`, and diff those predicates against each
other. The divergences are the design's real requirements, and collapsing them
into one owner is the sketch — not a follow-up cleanup task.

- A duplicated stack is visible because someone decides to unify it. A duplicated
  *effect* is invisible: each new caller looks like a fresh feature, so the fourth
  copy of "grant the subscription" gets written by someone who never saw the
  third. Reading the neighbourhood of the new code will not find it.
- Grep for the state, not the feature: the column name, the table, the external
  identifier. Every writer names the same thing, whatever it calls the verb.
- Record what each writer reads the *same* input to mean. Two paths that agree on
  "paid" but disagree on which units a money field holds, on a lifetime order, or
  on whether a partial payment counts are already broken against each other, and
  one has been silently winning.
- Name the reconciliation source: the external system that knows the truth, the
  field that keys back to it, and what a disagreement should look like. A design
  with no reconciliation step cannot tell success from silence.
- A safety path (cron, retry worker, backfill) that has never run is not a safety
  path. Check it executed at least once in production: a fatal error at the top of
  a cron turns it into a no-op that reports nothing forever, and its presence on
  disk reads as coverage.
- The owner can be the storage engine, not a module. When the census shows an
  invariant held by convention across many writers plus a helper that checks and
  repairs it on every request, the repair *is* the defect: two requests
  interleaving through its clear-then-set window put the duplicate back. Enforce
  it in the schema and every writer stays untouched, including one written next
  year that never learns the constraint exists. Recipe, DDL and the measurement
  to run before shipping: `enforced-invariants.md`.
