# Subagent models and steering

Read before choosing worker or judge models, getting a second opinion, or changing a running worker's scope.

- **Default and tiering.** Workers inherit the user's default model unless a playbook names one. Code delegates tier by difficulty: judgment-heavy work to a strong judgment model, a precisely specified sequence to a strong instruction-following model, trivial mechanical edits to a fast model.
- **Diversity.** Routed workflow skills (**how**, **why**, **grill-me**) still pick diverse models when they fan out; don't flatten every worker onto one model. A bakeoff judge runs on a different model family from the runners. Pick the model per subagent when the tool allows it; otherwise run the harness's headless one-shot CLI on that model; if neither is possible, say model diversity was unavailable.
- **Second opinion.** The same prompt against a different model. Agreement is high-signal.
- **Mid-run changes.** For a wording or scope change that arrives mid-run, message the owning subagent if the harness can steer a running subagent; otherwise wait for it to finish and dispatch the change as a follow-up. Interrupt-chained resumes silently drop directives, so fire a fresh subagent with consolidated scope rather than trusting a "done" summary.
- **Fresh by default.** A fix round, retry, follow-up or next queue item goes to a fresh subagent with the original brief, every later directive, and the prior agent's report. Resume one only when it holds state that is costly to move: its checkout, uncommitted changes, or a process it still runs.
- **A "done" report is a claim**, most of all from a worker that hit its iteration cap: re-run its suites, compile or lint its files, and read its diff before telling the user anything.
- **"Use sub agents then review"** means you write no implementation: ground, write the contract, dispatch, then review the diff and measure on the real surface.
