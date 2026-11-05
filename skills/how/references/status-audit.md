# Status audit: implemented, parked, or reference-only

Companion to Status Audit Mode in SKILL.md. Use when the ask is "does this exist yet?" disguised as "how does it work?".

## Search order (each step can end the audit)

```bash
# 1. Mechanism symbols in live source, excluding vendored and build trees
rg -n --glob '!ext/**' --glob '!build*/**' --glob '!references/**' \
   'NtUserGetDC|NtGdiPatBlt|<the syscall/API the mechanism needs>' <product tree>

# 2. Is there a target that builds it?
rg -n 'add_library|add_executable' <product>/CMakeLists.txt | rg -i '<module name>'
rg -n '<module name>' <product>/*.vcxproj

# 3. Docs: is the term described, or only indexed?
rg -n -i '<feature term>' docs

# 4. Retired docs still in history
cd <owning repo> && git log --all --oneline -S '<feature term>' -- docs
cd <owning repo> && git show <commit>:<path-from-log>

# 5. Reference implementations
rg -l -i '<mechanism API>' <umbrella>/references
```

## Traps

- **A junction workspace can span several git repos.** Run `git -C <dir> rev-parse --show-toplevel` before any history query. `git log -- <path>` from the umbrella prints nothing for a path owned by a nested repo, which reads as "never existed" and is wrong.
- **`find <junction>` does not descend it.** Without a trailing slash or `-L`, `find` returns the link itself. `ls -la <junction>` also shows the link, not its contents. Use `find <junction>/ ...`.
- **Stale vendored copies answer "yes" to an implementation question.** A second copy of the library under another project's `ext/` will match your grep while the canonical tree has nothing. Restrict to the canonical tree, then check copies separately and say which one the build actually uses.
- **Deleted is not gone.** The live docs tree can be a post-mold slice where the design docs were removed from disk but survive in history. `git log -S` on the term, then `git show <commit>:<path>`, recovers the status line and the acceptance criteria. Cite that form (commit + path), never a path that no longer exists.
- **Count the mentions before calling something documented.** A single reference in a split/index document that files the item under "archive" or "visual theater" is the whole live footprint; treat it as a pointer and go to history for the substance.

## Report shape

1. Verdict sentence first ("reference-only, nothing in the SDK or the hypervisor").
2. How the mechanism works, with `file:line` in the reference clone.
3. What the project planned, quoting the retired doc's own status line.
4. What the product actually has instead, with the target/file that proves it.
5. Leftovers found during the audit (orphan headers, declared functions with no definition, targets absent from the build) as a short separate list.
6. Next step: the smallest honest first move, or recommend leaving it parked.
