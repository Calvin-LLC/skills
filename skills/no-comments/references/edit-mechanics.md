# Edit mechanics

## Resolve scope per repo

A workspace can be a thin tree of junctions or symlinks over other repos. `git status` at its root may say "not a git repository". The real history lives in each linked repo, and each has its own base branch.

- Find every repo the scope touches (`git -C <dir> rev-parse --show-toplevel`).
- Per repo, diff against its base branch, including the working tree.
- Unpushed commits put the comments in both `origin/main..HEAD` and the working tree. `git diff <base>..HEAD` shows committed history only. It cannot prove a deletion landed. Prove it with `git diff <base>` (working tree).
- An untracked-only working tree (fresh repo, empty initial commit, everything new) is invisible to `git diff` and appears only as untracked paths in `git status`. Back the files up to a scratch dir before editing, then verify with `diff -u <backup>/<file> <file>` and confirm every added `+` line is a comment you meant to keep.

## The swallowed-opener bug

Deleting a comment block with a search-and-replace edit eats live code when the match covers the comment plus the first line of the construct below it, and the replacement drops that line's opener (`try {`, `{`, `if`, a decorator, a guard).

- End the match at the last comment line. Never include the line below.
- A comment directly above an opener: replace only the comment lines. Keep the opener.
- A bad edit: restore the opener alone. Do not re-add the comment.
- Re-read the edited region after every edit. A missing `{` is invisible in a diff summary.
- Run the parser or build after each file.

## Verification commands

```bash
# no added comment survives in the working tree (adjust the comment syntax per language)
git diff <base> | grep -nE '^\+.*(//|/\*|\*/)'            # C-family
git diff <base> -- <path> | grep -nE '^\+.*(#|//)'        # shell, PowerShell, Python

# every non-comment line in the diff is expected code, not collateral damage
git diff <base> | grep -E '^[+-]' | grep -vE '^(\+\+\+|---)' | grep -vE '^[+-]\s*(//|/\*|\*|#)'
```

The second command should print nothing for a pure comment pass.

## Proving only comments changed

- Python: compare `ast.dump` of `git show HEAD:<path>` and the working file with docstring `Expr` nodes stripped from both; equal for every file.
- C/C++: run one lexer-aware stripper over both versions (`//` and `/* */` removed, string, char and raw-string literals copied verbatim), delete all whitespace, compare the strings per file. This proves the code is token-identical without a build, and it catches a swallowed opener that a diff summary hides.
- A firmware image is not a valid byte-hash proof. Deleting comment lines shifts the debug line table, so the image keeps its size and section usage but differs by a few dozen bytes (the embedded ELF digests). Use the token comparison plus an unchanged size report, and state that the hash moved.
- Shell: `bash -n`, and shellcheck finding counts equal before (`git show HEAD:<path> | shellcheck -`) and after. Config files: parse both versions (configparser, yaml) and compare the dicts. A file that feeds a generated artifact (a partition table, a linker script) is proven by generating the artifact from the old and new text and comparing hashes (`gen_esp32part.py` on `partitions.csv`), not by reading the diff.

PowerShell parse check (initialize `$errs` first or the `[ref]` binding fails):

```powershell
$errs=$null
[System.Management.Automation.Language.Parser]::ParseFile($path,[ref]$null,[ref]$errs) > $null
if($errs){$errs|%{$_.Message}}else{'PARSE_OK'}
```

## Large passes

For a codebase-wide pass, work in batches.

- Hash data and resource files before and after every batch. Any change fails the batch.
- Run the full test matrix against the baseline counts on a consistent tree. Never report results from a half-edited tree.
- If the project keeps an audit ledger or receipts file, append the batch entry (batch id, files, deletion count, test tallies, data files untouched) before you commit.

## Batch mechanics

When a scripted pass deletes and trims hundreds of comments across files, the mechanics decide whether it corrupts code:

- **Derive diff-scoped spans via zero-context hunks.** For passes limited to diff additions, running `git diff -U0 <base> -- <file>` gives exact 0-indexed line intervals (`@@ -old,count +new,count @@`) of introduced lines in the working tree. This prevents accidental deletion of pre-existing comments or collateral non-comment lines. Untracked files treat all lines as in-scope.
- **Anchor by text, never by worklist line numbers.** A worklist captured before the first edit is stale after it; every batch shifts line numbers. Locate each block by a unique first-line substring and re-derive the span at edit time.
- **Consume the comment span dynamically.** Comment blocks vary in length (2–7 lines), and a fixed N-line replacement overreaches into live code as soon as one block differs. Walk consecutive comment lines from the anchor, assert every consumed line is a comment, and stop at the first code line. An assertion failure at the span edge is the guard working — shrink the span, never weaken the guard.
- **Comment-pattern regexes lie in markup and CSS.** CSS id selectors (`#top_bar {`) match `#`-comment patterns inside `<style>` blocks; shape-guard (`#`-line ending in `{` or `,` is a selector). In standalone CSS files, universal selectors (`* {`) or attribute selectors mimic comment syntax (`/*`, `* `). Always require full delimiters (`/* ... */`). Do NOT apply selector shape guards to `.py`/`.js` comment prose.
- **Embedded documentation in string literals.** Scripts that generate files or sanitize trees often embed markdown docs (`## Heading`) inside multiline string literals or docstrings. Naive line-prefix checks treat these as `#` comments. Verify tokens are outside string constants before stripping.
- **Replicated blocks need multi-hit trims.** The same comment copied at every handler call site must be trimmed identically at every copy; a single-hit assert fails halfway and strands the rest. Replace-all, bottom-up, then report the site count.
- **Parse immediately after every file.** A trimmed span that swallowed an opener or delimiter shows up as a syntax error, not in the diff summary. Run per-language checks immediately (`ast.parse(code, filename=path)` for Python, `node --check <file>` for JS, `bash -n <file>` for Shell).
