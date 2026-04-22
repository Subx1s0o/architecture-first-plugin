---
description: Explain a file's role in the repo — purpose, callers, tests that pin it, reasons it can't be deleted. Onboarding + debugging tool.
---

Args: `<file-path>`.

Read-only. No sub-agent.

Steps:

1. Read the file. Extract: top-level exports, class/function names, decorators/registrations.
2. Grep callers: `rg -l '<exportName>'` across the repo, excluding the file itself. Show up to 10 with clickable links.
3. Grep tests: files matching `**/*.{spec,test}.*` that reference any export.
4. Framework reach-outs: if decorators / string-registered (routes, queue processors) / convention-path (Next `page.tsx`, Django `apps.py`) — note it.
5. Last-3 git log entries on the file: `git log -3 --oneline -- <file>`.

Output (Markdown):

```
# <file-path>

**Purpose.** <one paragraph — what the file does, in the user's language>

**Exports.** `<symbol1>`, `<symbol2>`, …

**Called by.** <N> places
- [`<file.ts:line>`](path#Lline) — one-line why this caller uses it

**Tests that pin it.** <N> specs
- [`<spec.ts>`](path) — what behaviour is locked

**Why it can't be trivially deleted.** Reachable via: <list mechanisms — decorator, route string, barrel export, etc.>

**Recent history.**
- <sha> <date> — <subject>

**If you're refactoring:** consider starting with `/arch-refactor <file>` for a concrete suggestion.
```

If the file truly is orphan (0 callers, no framework reach) → say so plainly and suggest `/arch-clean`.
