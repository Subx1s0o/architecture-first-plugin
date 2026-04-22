---
description: Git blame + grep-driven — who last touched a symbol, who depends on it, who to tag as reviewer. Pure git, no LLM reasoning beyond formatting.
---

Args: `<symbol>` or `<file-path>` or `<file-path>:<line>`.

Read-only. No sub-agent. Uses only `git`, `rg`.

Steps:

1. Resolve target:
   - Pure symbol: `rg -n '<symbol>' --type <lang>` to find definitions.
   - File path: analyze whole file.
   - `file:line`: narrow to that line.
2. `git log --follow --oneline -10 -- <file>` — last 10 touches.
3. `git shortlog -sn --no-merges -- <file>` — top authors by commit count.
4. Grep callers: `rg -l '<symbol>'` excluding the defining file. Show up to 10 with clickable links.
5. Suggested reviewer = author of the latest non-trivial touch AND heaviest net-line-contributor. If two different people, list both.

Output:

```
# <symbol> — ownership + dependencies

Defined in: [`<file.ts:line>`](path#Lline)

**Last touches** (git log)
- <sha> <date> <author> — <subject>

**Top authors** (git shortlog)
- <n> commits — <author1>
- <n> commits — <author2>

**Callers** (<N> files)
- [`<file.ts>`](path) — <line preview>

**Suggested reviewer(s):** @<author1> (last non-trivial touch) [, @<author2> (most commits)]
```

No recommendation beyond ownership. For "should this be refactored" → `/arch-refactor`.
