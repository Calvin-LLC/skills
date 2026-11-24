---
description: Edit the file in place instead of writing a renamed copy
condition: '[\s\S]'
scope: "tool:write(*_v[0-9]*.*), tool:write(*_final.*), tool:write(*_fixed.*), tool:write(*_copy.*)"
interruptMode: tool-only
repeatMode: always
---

This file name marks a throwaway copy (`_v2`, `_final`, `_fixed`, `_copy`). Edit the original file in place; git keeps the old version. Scratch output goes in the OS temp directory, outside the repository. Follow `skill://tidy`.
