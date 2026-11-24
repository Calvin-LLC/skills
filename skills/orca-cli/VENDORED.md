# Vendored copy of Orca's bundled skills

Covers `skills/orca-cli/` and `skills/orchestration/`.

- Source: [stablyai/orca](https://github.com/stablyai/orca) (MIT), the two stubs under `skills/` at commit 4ca2cae, copied here unchanged. `orca skills install --skill orca-cli --skill orchestration --local --agent universal` writes the same files.
- Each `SKILL.md` is a discovery stub. The usage guide is printed by the installed binary (`orca skills get orca-cli`, `orca skills get orchestration`), so it always matches the Orca version that runs the commands. Do not paste that guide into these files.
- Needs the `orca` CLI on `PATH` and the Orca app running. Without Orca the skills do nothing.
- To upgrade: run `orca skills install --skill orca-cli --skill orchestration --local` in a scratch project, diff the result against these two files, and replace them. `orca skills update` only touches copies Orca installed itself, not these.
