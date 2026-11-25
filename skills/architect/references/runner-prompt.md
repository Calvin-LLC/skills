# Architect runner prompt

The parent spawns every Phase B runner through one `task` call and points each `tasks[]` item at this file. The shared `context` carries the scope, the constraints and the path of the Phase A grounding artifact; each item's `task` carries that runner's lens. Runners edit nothing in the repo. Scratch files go in a per-runner subdirectory of the sketch dir, never a git worktree or feature branch.

You are producing one candidate design in architect's parallel exploration. Read `skill://architect` in full first; that's the workflow you're inside. Read the grounding artifact next. Shape the rationale per [`rationale-template.md`](rationale-template.md), which sits beside this file.

## Reply shape

Reply with one JSON object and nothing around it: no prose and no code fence, or the parent cannot read a field through `agent://<id>/<key>`.

```json
{
  "lens": "the structural lens you were assigned",
  "usage": "README-style usage plus two or three real call sites",
  "type_sketch": "the core types, as source text in the repo's language",
  "signatures": ["one function or method signature per entry, bodies `not implemented`"],
  "module_map": [{"path": "module or file", "owns": "what it owns and what it hides"}],
  "rationale": "markdown that fills every heading of the rationale template"
}
```

When `task.structured` is on, the parent passes this shape as each item's `outputSchema` and the reply is validated against it.

## Design discipline

Apply the following discipline. The parent compares candidates on these axes to pick a base.

- Caller's usage first. Write the README-style usage and two or three real call sites before the types, then derive the type sketch from them. The usage is the spec; the two must agree, so reconcile the sketch to the usage, not the reverse.
- Data structures first. Get the core types right and the code becomes obvious. Trace each dominant access pattern through the proposed structure; if the answer is "we'll add a map / index / cache later," the structure is wrong.
- Interface depth. Compare the capability hidden behind the public surface relative to the size of that surface. Prefer a simple interface that pulls complexity into the callee, even when the implementation becomes less simple. Do not put transport or wire types on the public surface; parse into domain types behind the interface.
- Shared state: if two actors might both write, ask "what happens?" If the answer isn't "nothing," default to per-actor state with a merge at the read boundary.
- Make boundaries visible. `not implemented` errors for bodies, `// TODO` pseudocode for tricky logic, doc comments stating intent and invariants. A reader should trace data from input to output by reading types and signatures alone. The pseudocode and doc comments are sketch scaffolding for Phase B only: Phase D fill-in removes them per the **no-comments** skill, and none ship.
- Encode invariants in types: hard-to-misuse types > runtime checks > prose comments.
- Validate at boundaries, trust types inside, per the rest of this bullet list. Business logic as pure functions; the shell stays thin.
- Single source of truth per invariant. Derive instead of sync.
- Idempotent state transitions where applicable. Ask what happens if the operation runs twice or crashes halfway.
- Short call chains. If tracing the flow needs more than three files, flatten the hierarchy.

You are one of several runners, each assigned a different structural lens. Produce the best design your lens can make; don't hedge toward the others. Differences between candidates are the signal used to pick a base and graft. Converging on a safe-looking middle defeats the exploration.
