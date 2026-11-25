# Driving the debugger

Companion to Phase 4. `debug` holds one DAP session at a time, and each action below is one `debug` call.

## Before the first launch

- **Python.** The adapter is `python -m debugpy.adapter`, run with the `python` OMP finds on `PATH`. `adapter 'debugpy' is not available` means that interpreter has no `debugpy`: install it there with `python -m pip install debugpy`.
- **C, C++, Rust, Zig, Swift.** The adapter is `lldb-dap`. `DAP adapter exited unexpectedly` means the adapter binary cannot start, not that the target is broken: run `lldb-dap --version` in `bash` and fix what it reports. On Windows the usual cause is that the Python DLL this LLVM build links against is not on `PATH`. Build the target with debug info and no optimization: `-g -O0` for clang or gcc, the `Debug` configuration for an MSVC build (`cmake --build build --config Debug`). `lldb-dap` reads the MSVC PDB and shows `std::string` values.
- **Go.** The adapter is `dlv` (`go install github.com/go-delve/delve/cmd/dlv@latest`). Pass the package directory as `program`; `dlv` builds it.
- **A different interpreter or adapter build.** A `.omp/dap.json` in the project replaces an adapter by id. This one debugs with the project's virtualenv:

```json
{
  "adapters": {
    "debugpy": {
      "command": "<absolute path to the venv's python>",
      "args": ["-m", "debugpy.adapter"],
      "fileTypes": [".py"],
      "launchDefaults": { "request": "launch", "justMyCode": false, "stopOnEntry": true }
    }
  }
}
```

## The sequence

1. `launch` with an absolute `program` and `cwd`, plus `args`. A good reply says `Status: stopped` and `Stop reason: entry`.
2. `set_breakpoint` with `file` and `line`, or with `function`. The reply lists the breakpoint as `verified`. Add `condition`, an expression in the target's language such as `discount > 0`, when only one input fails.
3. `continue`. The reply says `Stop reason: breakpoint` with the frame and its `file:line`.
4. `stack_trace` lists the callers. `scopes` gives a `ref` for Locals, and `variables` with that `variable_ref` lists each local with its type.
5. `evaluate` an expression in the stopped frame. This is where the hypothesis's prediction is checked.
6. `step_over`, `step_in` and `step_out` walk to the first line where the state is wrong.
7. `terminate` before the next `launch`.

## When it does not stop

- **`Status: running` after `launch`.** The first stop was missed, and a `continue` now only times out. `pause` first: the reply says `Stop reason: pause`, and from there breakpoints and `continue` work. An interpreter with a large site-packages and `.pth` hooks does this; a virtualenv interpreter stops at entry.
- **`The operation timed out`.** Raise `timeout` (seconds, up to 300) once. If `attach` times out again, start the target under `launch`, or fall back to the tagged logs in Phase 4.
- **A native target stops at entry inside the loader**, not in `main`. That is expected: set the breakpoint and `continue`.
