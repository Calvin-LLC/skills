---
name: arch-export
description: Use when exporting a sanitized architecture brief for an outside model with no repo access.
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [architecture, review, sanitization]
    related_skills: [arch-import]
---

# Arch export

Runs locally. Produces a sanitized, measurement-backed brief an outside model
can review with no repo access. The brief carries evidence (profile numbers,
complexity, data shapes), not just a description — without evidence the
reviewer can only guess. The reply comes back through `arch-import`.

## When to Use

- The user asks for `/arch-export`, a sanitized brief, or "something I can paste
  into Claude/Perplexity/ChatGPT for an architecture review".
- A finished artifact (corpus, pipeline output, generated dataset) needs a
  reviewable summary that states its own limits.
- You are about to hand architecture to an outside model and need the alias map
  and leak check done first.

## Rules

- Output contains NO source code, identifiers, paths, URLs, string literals,
  schema field names, or business logic. Pseudocode only. Structural bounds
  (buffer sizes, entry caps, record widths) and measured sizes are required
  evidence, not leaks — the banned literals are tree constants: magic values,
  offsets, signatures, hardcoded addresses.
- **Roles instead of names.** Replace every identifier with a role:
  `OrderService` becomes `Component A (write-heavy aggregator)`. Keep the alias
  map in `.arch/aliases.json` locally so you can translate the reply back.
  Never emit the map. Write map values as the translation key — the real
  file/symbol names a reply needs back-translated — and phrase the brief's
  role lines differently: a value echoing the draft's own prose fails the
  alias-value sweep against your own text.
- **Numbers carry the weight.** Include the top 5 hotspots with percent of
  time, call counts, p50/p95/p99, allocations, query counts and plan shapes,
  all anonymized. Every claim needs a measurement or is labeled "hypothesis".
  Measure before writing. Never estimate a number.
- **Declare the boundary.** State what is claimed versus what is not: which
  numbers are measured, which labels are inference, what was retried and what
  survived, and what the validation does *not* prove. Without that section the
  reviewer treats every number as ground truth and reviews the wrong thing.
- **Data shape instead of data.** For each structure give cardinality, growth,
  key distribution (uniform or skewed), value sizes, read/write ratio, and
  ordering or locality. This is what lets the reviewer pick the right
  algorithm.
- **State constraints and non-goals.** Give the latency budget, memory
  ceiling, consistency needs, hardware, and "don't add infra unless measured."

## Steps

When the run is scoped to one subsystem ("for the X system"), the brief covers
that slice: roles, structures, algorithms and measurements for it; other
components get one context line each. Mine prior agent work on the target
before measuring — session-history search plus the repo's docs, findings files,
and leftover untracked probe scripts. A prior audit's numbers are the strongest
evidence a brief can carry; an ask that glitched or never landed is open work
to name under Pain. Prior numbers whose suites or artifacts are archived or
absent from the current tree are history, not coverage — cite them labeled
unauditable and make the absence itself a Pain item.

1. **Stack:** detect languages, frameworks, datastores, runtime, deployment
   shape (versions included).
2. **Topology:** components, roles, sync/async edges, data flow, concurrency
   model, failure handling.
3. **Data structures:** for each hot structure give cardinality, growth, key
   distribution, value size, R/W ratio, access pattern, locality.
4. **Algorithms:** for each hot path give steps in pseudocode, big-O, input
   size N, measured cost.
5. **Evidence:** top 5 hotspots (% time, call counts, p50/p95/p99,
   allocs/query counts/plan shapes), anonymized. When the subject has no
   runtime profile (an offline corpus, a static-analysis product, a generated
   artifact), the same slot takes coverage, cardinalities, defect counts, retry
   yield and a failure taxonomy — see `references/analysis-artifact-briefs.md`.
   Pull the numbers from the machine-readable summary the pipeline wrote, then
   recompute every derived percentage so the arithmetic in the brief agrees.
6. **Constraints:** latency/memory budget, hardware, consistency, non-goals.
7. **Pain:** what is slow, flaky, or hard to change, with symptoms.
8. **Honest boundary:** one section carrying coverage and failures (counts per
   failure class, what retry recovered, what survived), non-entities that sit in
   the same index as real ones, provenance tiers (fact / inference /
   placeholder), scope limits, and what the validation proves versus what it
   only assumes. Each item ends with the conclusion a consumer must not draw.
   Structure and wording: `references/analysis-artifact-briefs.md`.
9. **Leak check:** grep the draft for every repo identifier, path, domain,
   literal, and alias value. Classify every hit before acting: substring matching produces expected noise — a short alias token hits inside ordinary prose words ("nan" in "maintenance") and prose slashes read path-shaped — so name each hit real leak or noise, fail and re-sanitize on any real hit, and never clear a real hit because noise exists. One pass with
   `rg`: dump sorted unique tokens of the repo and `rg -F -f` them against the
   draft, then a separate pass for path/URL-shaped strings and long
   high-entropy tokens. Every `.arch/aliases.json` value must be absent from
   the draft — sweep JSON **values** only: the keys are the role names, which
   must appear in the draft, so a walker that counts keys reports every role
   as a phantom leak. Pseudocode names must be generic and underscore-free: the token
   pass matches by substring, so an invented snake_case identifier collides
   with real repo tokens, and a schema field name in pseudocode is a hard fail
   regardless of intent. After any edit to the draft, re-run the sweep and
   diff the hit list against the previous one (`comm -13 old new`) so each
   re-check classifies only NEW tokens — save every hit list to a file before
   editing, or the diff has no left side; one edit can swap a token for
   another and leave the count identical. A zero-hit sweep is a broken
   command, not a clean draft (empty or unreadable pattern file, wrong path
   flavor, suppressed stderr): check the pattern file is non-empty and that a
   common word like `the` hits before trusting any result. A path pattern
   whose character class contains a backslash (`[/\]`) fails to parse in rg's
   Rust regex under git-bash and exits quietly with no matches — write the
   separators as `\x5C`/`\x2F` escapes or run one pattern per pass, each with
   its own control. Routine conditions trip the hex-code
   pattern — a resolution like 1920x1080 reads as `0x1080` — classify as
   condition, not leak.
   For a live-machine brief the token source is the raw probe outputs (process, service and task names, vendor
   and product names, hardware model, username, install paths) plus every alias value; put vendors, products and
   the host identity in the alias map even when they read as prose. The same bar applies to owner hardware in
   any brief: by capability (year class, capacity, compute capability, "USB capture device"), never vendor or model.
   **Your own artifacts leak too.** A sibling brief named by filename, the `.arch/`
   path, or the alias-map filename are real hits: write "a companion brief covers
   the rest" and "the alias map is kept separately", never the names. Build the
   token file from a curated domain vocabulary (product, project, symbol, path,
   constant, observer-side names), coined product phrases (hyphenated doc
   vocabulary leaks as prose even when every identifier is scrubbed — reword
   such a phrase on hit, and record deliberate retentions in the alias map),
   plus the alias values — dumping every identifier
   from the source tree returns mostly comment prose — and recheck short tokens on
   **word boundaries**: a case-insensitive substring pass flags a three-letter
   acronym inside ordinary words and a four-letter term inside "translate", so
   classify by boundary match instead of eyeballing a 150-hit list.
   Add each identifier **whole**. Do not expand a token list by splitting names on
   underscores or camelCase into their parts: `CredentialRepo` contributes
   `Credential`, `ConfigVersion` contributes `Config`, and the parts are ordinary
   English that appear legitimately in every paragraph. The result is a hit list of
   dozens of generic words and zero information, and the one real leak hides in it.
   Keep a boundary-match pass only for tokens you deliberately shortened (a
   distinctive acronym, a product name under five characters); everything else goes
   in at full length, where substring matching is already exact.
10. **Emit:** write `.arch/brief.md` from the template below with the ask
   appended verbatim, and add `.arch/` to the repo's ignore file when missing —
   the alias map must never reach a remote, and the brief leaves by paste.
   `.arch/` at a thin workspace root is the workspace's own, not any
   junction's: add `.arch/` to the ignore file at whatever git roots can see
   it. `ls .arch/` first: a parallel seat in the same repo may already own `brief.md` and `aliases.json`. Read what is there,
   then write to topic-named files (`brief-<topic>.md`, `aliases-<topic>.json`) instead of overwriting, and say in the brief which
   companion brief covers the rest. Create the alias map with a no-clobber write; rename yours if it collides.
   For a hardware/placement question, the brief's "algorithm" is the placement or sizing problem (inputs, constraints, choice set)
   and the Ask gains a short list of hardware-specific questions.
   For a targeted "fix this" ask, same shape: a scope paragraph above the
   verbatim block naming the defects to fix and the option space to enumerate.
   For a mechanism/detection question, "hot algorithms" becomes **the mechanism
   under review**: the install sequence and the invoke sequence in pseudocode, then
   the observer's checks as their own numbered section carrying thresholds, then a
   ledger of mitigation options with cost and verdict. The Ask gains a short scope
   paragraph above the verbatim block naming the checks and the option space to
   enumerate. Record deliberate retentions in the alias map as a note (an ISA or
   OS family the reviewer's answer is wrong without) so a later sweep does not
   "fix" them.
   Reach-based briefs work like any audit-backed brief: state what the reply
   must preserve as a reach invariant, not as a count — "the go-to semantics
   must be unchanged" names what measurement would falsify a candidate, and
   tolerance stays too tight to carry a number.

## Before you export: is the target reachable?

A brief asking an outside model to hit a quality target is only worth writing
after you have measured whether that target is reachable **at all**. Exporting
to optimise an unreachable number sends the reviewer to work on a problem that
no algorithm solves, and you cannot separate its good advice from its bad,
because both arrive as ways to close a gap that is already closed.

So when the ask is "get to N nines / under X ms / below Y% error", enumerate the
floor first, over the whole input space rather than a sample:

1. **Count what survives the lossy stage.** Map every input through it and count
distinct outputs. If the input space is 16.7M and the stage yields 2.6M, nothing
downstream can distinguish the inputs that collapsed.
2. **Split the error into already-gone and recoverable.** For each input the
current logic accepts, classify whether its loss happened before the stage under
review could see it, or at that stage's own boundary. Only the second kind is
addressable by tuning, and it is usually a rounding error beside the first.
3. **Check the cheap knobs before designing.** A range setting, a bit depth, a
container flag: measure each against the floor. If full-range encoding moves
collisions from 99.92% to 99.87%, that lever is a non-event, and saying so
removes a whole class of advice from the reviewer's option space.
4. **Re-aim the metric when the floor blocks it.** A whole-space score caps near
the floor while the same logic on real captured data can score far higher,
because real data occupies a small clustered slice of the space. The
unreachable number is almost always the abstract one; name the metric that is
reachable and measured on real data.

When the floor rules the target out, the deliverable is the measurement and a
re-aimed metric — not a brief. Say the target is unreachable, show the number
that proves it, and propose the measurement that can succeed. Recipe and worked
arithmetic: `references/reachability-gate.md`.

## Brief template

```markdown
## Stack and runtime
## Topology (components by role, edges, concurrency)
## Hot data structures (table: role, cardinality, growth, distribution, R/W, access)
## Hot algorithms (role, pseudocode, complexity, N, measured cost)
## Measurements (anonymized)
## Honest boundary — what is claimed, and what is not
## Constraints and non-goals
## Pain points
## Ask (verbatim to the reviewer)
```

## The ask

Append verbatim to the bottom of every brief:

```markdown
You have no repo access. Work only from this brief.
1. For each hot algorithm/structure: list every known alternative (including approximate, amortized, batched, SIMD/bitset, and reductions to classic problems) with complexity, constants, cache behavior, and the input regimes where it wins or loses. Flag any assumption you're making about my data.
2. Rank by expected gain / effort. Cite the measurement each gain would address.
3. Architectural changes: only those justified by the measurements. Name what to measure first if the evidence is insufficient.
4. For each recommendation, give: pseudocode, the invariants to preserve, a differential test idea, and what benchmark would prove it.
5. Reply as a table (id, target role, change, expected gain, risk, test, benchmark), then notes.
Do not ask for code. Do not suggest new infrastructure without a measured reason.
```

Step 4 matters most. You get pseudocode plus test ideas, and your local cheap
model implements each one against the real code.

## Choosing the reviewer

- **Claude Max session:** deep reasoning on the algorithm and architecture
  table. It can handle a long brief, so include the full data-shape detail.
- **Perplexity session:** use when the question is "what's the current
  best-known approach for X". It can search current papers, libraries and
  benchmarks. For any search-capable reviewer (named consumer sessions
  included), add this research addendum to the ask verbatim: `(For this run: survey the current
  best-known tools/libraries/approaches per area — searches allowed; cite
  benchmarks or specs where they exist, and flag quality/latency tradeoffs.)`
- **Both:** run the same brief through each and diff the answers. Where two
  different-family models agree, treat it as a strong signal. Where they
  disagree, bake off both candidates by hand.
- **Opus on demand.** When the user says "to an opus session", run it headless from the leak-checked brief:
  `cat .arch/brief-<topic>.md | claude -p "Review the architecture brief on stdin and answer its Ask section. Work only from the brief." --model opus --effort high --tools "" --max-turns 1 --no-session-persistence --output-format json > out.json`,
  extract `.result` to `.arch/<reviewer>-reply.md`, and read the reply in full before summarizing. Report the model id from `modelUsage` and the cost.
  Relay the reviewer's stated assumptions as unverified items, and recheck its arithmetic against the brief's own numbers
  (it caught a VRAM budget that was too generous). Nothing from the reply is applied to the machine until the user picks items;
  `arch-import` is the path for turning it into work.
- **Named sessions.** The user names the reviewer ("to argon 4") — a consumer
  web session they paste the brief into by hand. The deliverable is the brief
  file path stated plainly; never try to deliver or post it yourself.

## Caveats

- **Sanitizing is lossy.** If the reviewer's advice doesn't fit, it's usually
  because the data shape was described wrong. Fix the brief rather than
  loosening the redaction.
- **Leak hits need triage.** Substring matching is loud: English words collide
  with short identifier fragments (`validat…` inside a longer token, `failures`
  as prose), and those hits are not leaks. Split hits into whole-token artifact
  names (reword the draft) and overlap noise (leave the prose alone). Keep
  address, path, URL and long-hex patterns in their own pass so a real hit
  cannot hide inside the noise.
- **Pseudocode can still leak.** A distinctive algorithm or domain rule is
  itself sensitive. If that matters, generalize it ("a scoring function over a
  sliding window") and keep only the complexity-relevant shape.
- **ZDR terms differ.** Claude Max and Perplexity consumer sessions aren't the
  same as the API-level zero-data-retention arrangements used for code, so
  check retention and training settings on each account before pasting. That's
  why the leak check runs first.
