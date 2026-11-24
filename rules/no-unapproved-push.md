---
description: A push waits for the operator's approval of that specific push
condition: '\bgit\s+push\b'
scope: "tool:bash"
interruptMode: tool-only
repeatMode: always
---

Stop before this push. Push only when the operator has approved this specific push in this conversation; an approval of an earlier push, or an instruction to commit, merge or revert, does not cover it. With no such approval, show the commits that are ready and ask. Follow `skill://commit`.
