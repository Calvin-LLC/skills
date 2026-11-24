# Local proof traps

Read when the proof for a commit rests on a build log, prebuilt test binaries, or changed PowerShell scripts. The MSBuild and PowerShell specifics below apply to Windows/MSBuild projects; the fresh-binaries principle is general.

Proof means fresh binaries, not available ones. Test suites that are standalone executables run whether or not the current code compiles, so a suite run right after a failed or clipped build reports green over an uncompilable commit. Capture the build output and require an explicit success line (MSBuild: `0 Error(s)` or the `-> <target>` line) before running any test, in the same chain, from binaries that build just produced.

- Never trust a clipped build view (`tail -3`, `Select-Object -Last 3`, truncation) as proof: failure lines live where the clip cut. Search the captured output for `error` and read the matches; then confirm the success line.
- A match-count command that exits 1 on zero matches (POSIX `grep -c`) makes `count && run-tests` skip the tests exactly when the build is clean. Structure the chain so a clean build is the success path (an exit-code check on the build itself, or run the steps unconditionally and inspect).
- In a regex, `|` is alternation (`grep -E 'A|B'`). For a receipt token that contains a literal `|`, escape it or match it as a fixed string (POSIX `grep -F`; PowerShell `Select-String -SimpleMatch`); otherwise one broad pattern matches everything and the count means nothing.
- When the build graph is already up to date nothing rebuilds, and a green control build over an unchanged tree proves nothing fresh. Read the target line and the artifact mtime, and force a real build whenever the claim is "this tree builds": MSBuild `/t:Rebuild`; elsewhere the build tool's force or clean flag (`make -B`, `cargo clean -p <crate>`) or delete the target's intermediate output.
- PowerShell edits need a parse check before commit: `[System.Management.Automation.Language.Parser]::ParseFile` per changed `.ps1`, one invocation per file. An array `-Files` argument arrives as one mangled string and a shell loop's path substitution corrupts Windows paths, so drive the per-file calls from Python `subprocess`.
