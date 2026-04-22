---
description: Repo-wide health dashboard per module. Classifies each module green / yellow / red by size, churn, cycles. Writes docs/arch-health.md.
---

Read-only. Produces a one-page snapshot.

Steps:

1. Load stack profile + `.arch-profile.yaml`.
2. Enumerate top-level modules (typically `src/<module>/`).
3. Per module, compute cheaply:
   - **LoC total**: `wc -l $(find <module> -type f -name '*.<ext>')`.
   - **90-day churn**: `git log --since=90.days --name-only --pretty=format: -- <module>/ | sort -u | wc -l`.
   - **Cycles**: if `madge` / `pydeps` available, report any detected.
   - **Worst file**: largest single file under the module.
4. Classify each module per `.arch-profile.yaml` thresholds (or stack defaults):
   - **🟢 green**: all metrics within warn bounds.
   - **🟡 yellow**: one metric past warn, none past xl.
   - **🔴 red**: two+ past warn, or any past xl.
5. Write `docs/arch-health.md`:

```
# Architecture health — <YYYY-MM-DD>

| Module | LoC | Files | Churn 90d | Cycles | Worst file | Status |
|---|---|---|---|---|---|---|
| billing | 4200 | 42 | 12 commits | — | [`invoice.service.ts`](src/billing/invoice.service.ts) — 640 LoC | 🟡 |

## Headline
- N modules green, M yellow, K red.
- Top risk: <module> — <one-line reason>.

## Recommended next moves
1. `/arch-hotspot` on <worst module> → `/arch-decompose`.
2. `/arch-clean src/<module>` — surface orphan code.
3. (N more only if actually warranted)
```

6. End with: "Re-run monthly. Trend emerges after 3 snapshots — Obsidian vault keeps them at `changelog/`."

No source edits. No sub-agent.
