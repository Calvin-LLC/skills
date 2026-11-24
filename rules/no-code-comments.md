---
description: Code ships without comments unless one is a verified exception
condition: '(?m)^[ \t]*(?:#[ \t]+|//|/\*)(?![^\n]*(?:noqa|eslint-disable|@ts-|type:|prettier-ignore|clang-format|go:|SPDX|Copyright|License))'
scope: "tool:edit(*.{py,ts,tsx,js,jsx,rs,go,c,cpp,h}), tool:write(*.{py,ts,tsx,js,jsx,rs,go,c,cpp,h})"
interruptMode: tool-only
repeatMode: after-gap
---

This change adds a code comment. Read `skill://no-comments` and keep a comment only when it is one of the verified exceptions there: a license header, a tooling directive, or a checked note on a constraint the code cannot show. Remove narrating and unproven comments before writing the file.
