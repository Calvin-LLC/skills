# Leak check: token file and triage

Companion to step 9 in SKILL.md. `scripts/leak_check.py` runs the sweep. Read
this to build the token file and to classify what the sweep reports.

## Building the token file

- **Curate, don't dump.** Use a domain vocabulary (product, project, symbol,
  path, constant, observer-side names) plus the alias values. Dumping every
  identifier from the source tree returns mostly comment prose.
- **Coined product phrases leak as prose.** Hyphenated doc vocabulary leaks even
  when every identifier is scrubbed. Reword such a phrase on hit, and record
  deliberate retentions in the alias map.
- **Add each identifier whole.** Do not split names on underscores or camelCase:
  `CredentialRepo` contributes `Credential`, `ConfigVersion` contributes
  `Config`, and the parts are ordinary English that appears legitimately in
  every paragraph. The hit list becomes dozens of generic words and the one real
  leak hides in it. At full length, substring matching is already exact.
- **Boundary-match only what you deliberately shortened** (a distinctive
  acronym, a product name under five characters). A case-insensitive substring
  pass flags a three-letter acronym inside ordinary words and a four-letter term
  inside "translate"; classify by the script's word-boundary count instead of
  eyeballing a 150-hit list.
- **Live-machine brief.** The token source is the raw probe outputs (process,
  service and task names, vendor and product names, hardware model, username,
  install paths) plus every alias value. Put vendors, products and the host
  identity in the alias map even when they read as prose.

## Triage

- Substring matching is loud: a short alias token hits inside ordinary prose
  words ("nan" in "maintenance"), English words collide with identifier
  fragments, and prose slashes read path-shaped. Name each hit real leak or
  noise. Whole-token artifact names: reword the draft. Overlap noise: leave the
  prose alone and record it in the noise file with its reason. Never clear a
  real hit because noise exists.
- **Pseudocode names.** An invented snake_case identifier collides with real
  repo tokens. Keep names generic and underscore-free. A schema field name in
  pseudocode is a hard fail regardless of intent.
- Your own artifacts are real hits: a sibling brief named by filename, the
  `.arch/` path, the alias-map filename. The noise file cannot clear them.
- One edit can swap a token for another and leave the count identical. Re-run
  with the previous hits file as the baseline so each pass classifies only new
  hits.
