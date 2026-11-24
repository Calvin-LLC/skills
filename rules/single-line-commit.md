---
description: A commit message is one subject line with no body
condition:
  - '\bgit\s+commit\b(?:(?!",")[^\n])*\s-[a-zA-Z]*m\s(?:(?!",")[^\n])*\s-[a-zA-Z]*m\s'
  - '\bgit\s+commit\b[^\n]*\s(?:-F|--file)(?:\s|=)'
  - '\bgit\s+commit\b[^\n]*\s-[a-zA-Z]*m\s+\\?["''][^"'']*(?:\n|\\n)'
  - '\bgit\s+commit\b[^\n]*\s-[a-zA-Z]*m\s+\\?["'']?\$\('
scope: "tool:bash"
interruptMode: tool-only
repeatMode: always
---

A commit message is a single imperative subject line of 72 characters or fewer, passed with one `-m`. Write no body, second `-m`, message file or heredoc unless the operator asked for a body in so many words. Follow `skill://commit`.
