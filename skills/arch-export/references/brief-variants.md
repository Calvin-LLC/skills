# Brief variants by kind of ask

Companion to step 10 in SKILL.md. The template stays; these change what a
section carries. In every variant the verbatim Ask block is still appended
unchanged, with any scope paragraph placed above it.

- **Targeted "fix this" ask.** Add a scope paragraph above the verbatim block
  naming the defects to fix and the option space to enumerate.
- **Hardware / placement question.** The brief's "algorithm" is the placement
  or sizing problem: inputs, constraints, choice set. The Ask gains a short list
  of hardware-specific questions. Describe owner hardware by capability (year
  class, capacity, compute capability, "USB capture device"), never vendor or
  model.
- **Mechanism / detection question.** "Hot algorithms" becomes **the mechanism
  under review**: the install sequence and the invoke sequence in pseudocode,
  then the observer's checks as their own numbered section carrying thresholds,
  then a ledger of mitigation options with cost and verdict. The scope
  paragraph names the checks and the option space to enumerate. Record
  deliberate retentions in the alias map as a note (an ISA or OS family the
  reviewer's answer is wrong without) so a later sweep does not "fix" them.
- **Reach-based brief** (backed by a reachability audit rather than a profile).
  State what the reply must preserve as a reach invariant, not as a count:
  "the go-to semantics must be unchanged" names what measurement would falsify
  a candidate, where a tolerance is too tight to carry a number.
- **Artifact with no runtime profile.** See `analysis-artifact-briefs.md`.
