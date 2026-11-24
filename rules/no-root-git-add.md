---
description: Stage explicit paths, never the whole tree
condition: '\bgit\s+add\s+(?:-A|--all|\.)(?!\s+--\s)(?=\s|$|[\\"'';&|)])'
scope: "tool:bash"
interruptMode: tool-only
repeatMode: always
---

Stage only the paths that belong to this commit, each named explicitly: `git add -- <path> <path>`. `git add -A -- <explicit paths>` is fine; `git add -A`, `git add --all` and `git add .` sweep in other sessions' work. Follow `skill://commit`.
