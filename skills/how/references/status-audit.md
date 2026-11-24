# Status audit: implemented, parked, or reference-only

Companion to Status audit in SKILL.md. Use when the ask is "does this exist yet?" disguised as "how does it work?".

## Audit order

Audit in this order, and stop when one verdict fits every fact:

1. **Live source, build manifest included.** Grep the candidate trees for the mechanism's own symbols (the kernel/OS calls it must make, not the feature name). A header, API table, or helper proves an interface, never an implementation: check `CMakeLists.txt` / `*.vcxproj` (or the stack's build manifest) for a target that builds it, then grep for callers of the declared entry points. Declared-but-unreferenced is a leftover, and say so.
2. **Live docs.** Grep the docs tree for the feature name and for the mechanism. One hit in an index or split-document table that files the item under "archive" is a pointer, not a description.
3. **Git history for retired docs.** `git log --all --oneline -S '<term>' -- <docs path>` finds the commit that carried the doc; `git show <commit>:<path>` still reads it after it left the disk. Retired plans usually carry their own status line ("PARKED", "superseded by") and the acceptance criteria nobody met.
4. **Reference clones.** Third-party trees under `references/` are evidence for the technique, not for the product. Cite `file:line` there to explain how the mechanism works, and state plainly that they are not ported.

## Commands

```
# 1. Mechanism symbols in live source, excluding vendored and build trees
rg -n --glob '!ext/**' --glob '!build*/**' --glob '!references/**' '<the syscall/API the mechanism needs>' <product tree>

# 2. Is there a target that builds it?
rg -n -i '<module name>' <product>/CMakeLists.txt
rg -n '<module name>' --glob '*.vcxproj' <product>

# 3. Docs: is the term described, or only indexed?
rg -n -i '<feature term>' docs

# 4. Retired docs still in history
git -C <owning repo> log --all --oneline -S '<feature term>' -- docs
git -C <owning repo> show <commit>:<path-from-log>

# 5. Reference implementations
rg -l -i '<mechanism API>' <umbrella>/references
```

These are one-liners that run unchanged in POSIX shells and PowerShell; do not rely on shell globs or `\` line continuations.

## Traps

- **A junction workspace can span several git repos.** Run `git -C <dir> rev-parse --show-toplevel` before any history query. `git log -- <path>` from the umbrella prints nothing for a path owned by a nested repo, which reads as "never existed" and is wrong.
- **Listing or searching a junction may return the link, not its contents.** Pass the path with a trailing separator or tell the tool to follow links (POSIX `find -L <junction>` or `find <junction>/`; PowerShell `Get-ChildItem <junction>\ -Recurse`), and check that the result lists files inside it.
- **Stale vendored copies answer "yes" to an implementation question.** A second copy of the library under another project's `ext/` will match your grep while the canonical tree has nothing. Restrict to the canonical tree, then check copies separately and say which one the build actually uses.
- **Deleted is not gone.** Design docs removed from disk survive in history. `git log -S` on the term, then `git show <commit>:<path>`, recovers the status line and the acceptance criteria. Cite that form (commit + path), never a path that no longer exists.
- **Count the mentions before calling something documented.** A single reference in a split/index document that files the item under "archive" is the whole live footprint; treat it as a pointer and go to history for the substance.

## Report shape

1. Verdict sentence first ("reference-only, nothing in the product tree").
2. How the mechanism works, with `file:line` in the reference clone.
3. What the project planned, quoting the retired doc's own status line.
4. What the product actually has instead, with the target/file that proves it.
5. Leftovers found during the audit (orphan headers, declared functions with no definition, targets absent from the build) as a short separate list.
6. Next step: the smallest honest first move, or recommend leaving it parked.
