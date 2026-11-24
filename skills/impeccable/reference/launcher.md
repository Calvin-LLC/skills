# Launcher

`<base>` is the directory containing SKILL.md (the skill folder, not a plugin root above it). Fall back to this skill's directory only when the runtime reports no base directory. Keep cwd at the user's project.

Invoke every verb (`context`, `detect`, `doctor`, `hooks`, `pin`, and the rest, not only `context`) in the form that matches the shell:

```
POSIX (Linux, macOS, Git Bash):  sh <base>/scripts/impeccable <verb>
Windows (PowerShell or cmd):     <base>\scripts\impeccable.cmd <verb>
```

Other reference files write `<launcher>` for whichever form applies.

- **Timeout.** Run every launcher verb with a 60-second limit: the shell tool's own timeout, or on POSIX `timeout 60 sh <base>/scripts/impeccable <verb>`. A hang or timeout is not "launcher unavailable". Retry once, then fall back only if the retry also fails.
- **Line endings.** The POSIX launcher needs LF line endings; the repo's `.gitattributes` pins them. If `sh` prints `$'\r': command not found`, the checkout converted it to CRLF: on Windows use the `.cmd` form instead.
- A `.cmd` call that prints no findings is not a clean pass; treat it as unrun and check the launcher.
- Using `sh` also covers `Permission denied` (the file can lack its executable bit): that is a working launcher, not the launcher-unavailable case.
- The launcher runs a self-contained binary that ships next to it or is downloaded once on first run; no Node or other runtime is needed.
- Pass a named source file or route as `--target <path>`.

**Pin / Unpin:** `<launcher> pin <pin|unpin> <command>` creates or removes a standalone `/<command>` shortcut. Report the script's result concisely; relay stderr verbatim on error.
