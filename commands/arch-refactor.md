---
description: Review ONE file for cleanup + refactor. Produces 1-3 concrete suggestions (hotspot smells, L1-L2 cleanup, possible extract). No DEC written. Narrower alternative to /arch-assist.
---

Args: `<file-path>`.

Read-only. Returns a response, no files written.

Steps:

1. Size + structure: `wc -l`, count public exports, scan for responsibility clusters (verb-object groups).
2. Cheap hotspot signals (just this file): LoC, fan-in via grep, 90-day churn.
3. L1-L2 findings inside the file (debug logs, commented code > 30d, unused locals, obvious dupe methods).
4. Pick 1-3 suggestions. Each:
   - **Name** — matched to a decomposition-playbook pattern where applicable.
   - **Why** — one sentence.
   - **First move** — concrete (extract method X into file Y, delete commented block Z, etc.).
   - **Cost** — rough LoC impact + risk.

Output:

```
# <file> — refactor review

LoC <n> · churn <x>/20 · fan-in <k> · responsibility clusters: <list>

## Cleanup findings
- L1: <n> debug logs, <n> commented blocks — safe to delete inline.
- L2: <n> orphan private helpers — single PR.

## Suggestions
1. **<pattern>** — <why>.
   First move: <concrete action>. Cost: ~<n> LoC.
2. …

## Next step
- Light-touch fix: `/arch-clean <file>` → `/arch-clean-approve`.
- Full decomposition: `/arch-decompose <file>` → writes DEC + PR sequence.
```

Stop there. User picks the depth.
