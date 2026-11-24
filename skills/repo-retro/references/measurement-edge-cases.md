# Measurement edge cases

- Sessions that are mostly shell automation (browser, mail, documents) barely move the orientation and empty-search counts. Measure repeated boilerplate prefixes, one-off scripts versus calls into the repo's reusable tools, and re-reads of the same state files. Before proposing a new wrapper, look for an existing launcher it should call.
- A steering doc can describe code that no longer exists, and no session shows friction because agents ignore it. Extract its backticked paths, test each against the tree, hand-check the misses, and report it as its own row.
- A gitignored directory (`git check-ignore -v <dir>`) cannot carry a committed fix or CI gate, and a gitignored AGENTS.md reaches only this checkout. Say so in the proposal.
- The same filename can exist in two repos of one workspace. `git ls-files --error-unmatch <path>` from each candidate, edit the tracked copy, and say which you touched.
