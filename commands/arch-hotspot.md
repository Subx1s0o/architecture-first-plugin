---
description: Rank architectural hotspots (size × decay-adjusted churn × cycles × fan-in). Also tallies cleanup debt so /arch-decompose can gate on it. Saves state file. Read-only.
---

1. Detect the stack via `skills/architecture-first/references/stack-profiles/_detect.md`. Load thresholds from the matching profile; override with `.arch-profile.yaml` `thresholds:` if present.

2. Run Tier 0 signals:
   - Top 30 files by LoC: adapt extensions to the detected stack.
   - Top 30 files by **decay-adjusted** 90-day churn:

     ```bash
     # Raw churn
     git log --since=90.days --name-only --pretty=format: \
       | grep '\.<ext>$' | sort | uniq -c | sort -rn | head -30

     # Decay-adjusted: exclude bot / format / lint / merge commits
     git log --since=90.days --name-only \
       --pretty='format:%h %s' \
       | grep -vE 'arch-bot|chore\(format\)|chore: strip|chore: prettier|chore: lint|^[0-9a-f]+ Merge ' \
       | grep '\.<ext>$' | sort | uniq -c | sort -rn | head -30
     ```

   Report **decay-adjusted churn** as the primary signal in the table; show raw only if it diverges by ≥ 3×.

3. Run Tier 1 signals where tools are available:
   - Cycles: `npx --yes madge --circular src 2>/dev/null` (JS/TS) or `python -m pydeps --show-cycles . 2>/dev/null` (Python).
   - Fan-in on top-20 exported symbols: grep across the repo. Also compute **distinct top-level module fan-in**: number of distinct `src/<module>/` subtrees that import the symbol. If = 1, the fan-in is structural (leaf-of-tree per H3 in `references/known-antipatterns.md`) and should be flagged in the smell column.

4. Cross-reference: files in BOTH top-size AND top-(decay-adjusted)-churn = **primary**. Top-churn only = secondary. Top-size only = tertiary.

5. For each primary hotspot read the file and count distinct responsibility clusters (verb-object groups). If exactly 1 cluster AND LoC < 300, mark as **likely no-op** in the table — the file is small and cohesive, the metrics are misleading.

6. **Cleanup debt scan.** Dispatch the `cleaner` sub-agent for an L1/L2 scan in parallel with the hotspot ranking. The cleaner returns a count (`cleanup_debt_count`) and the top 10 findings. This count is later used by `/arch-decompose` to gate decomposition behind cleanup-first.

7. Produce the ranked table:

   ```
   | Rank | Path | Size | Churn (adj/raw) | Cycle? | Fan-in (mods) | Smell | Likely verdict |
   ```

   The "Likely verdict" column previews what `/arch-decompose <N>` will likely return:
   - `act` — clear pattern, signals all real.
   - `no-op` — anti-pattern heuristic likely fires (H1–H8) or signals are stale.
   - `defer` — real but blocked.

8. **Write the state file** so `/arch-decompose` can reference rows by number AND gate on cleanup debt:
   - Path: `${TMPDIR:-/tmp}/architecture-first/<md5(CLAUDE_PROJECT_DIR)>-hotspot.json`
   - Shape:
     ```json
     {
       "timestamp": "<iso>",
       "project": "<abs path>",
       "cleanup_debt_count": 25,
       "cleanup_top_findings": [
         { "path": "src/x.ts:17", "level": "L1", "what": "unused import" }
       ],
       "rows": [
         {
           "rank": 1,
           "path": "src/x.ts",
           "size": 834,
           "churn_adjusted": 14,
           "churn_raw": 20,
           "cycle": false,
           "fan_in_modules": 3,
           "smell": "…",
           "likely_verdict": "act",
           "pattern": "Extract Port"
         }
       ]
     }
     ```
   - Create the parent dir if missing. Overwrite on every run.

9. **Surface cleanup debt in the conversation.** If `cleanup_debt_count >= 10`, prepend a banner to the output:

   ```
   ⚠ Cleaner found <N> safely-removable items (L1/L2). Recommended: run `/arch-clean` first — this often makes several DECs unnecessary.
   ```

10. End with:
    - If `cleanup_debt_count >= 10`: "**Recommend `/arch-clean` first**, then revisit hotspots. Or pass `--skip-cleanup-gate` to `/arch-decompose`."
    - If all primary hotspots have `likely_verdict: no-op`: "**Це норм. Усе гаразд.** Метрики не показують реальної проблеми. Файли здорові, нічого не треба декомпозити." (mirror user's language).
    - Otherwise: "Run `/arch-decompose <N>` for row N, `/arch-decompose 1-3` for top 3, `/arch-decompose ALL` (capped at 3 by default; `--force-all` to bypass)."

Do not edit code.
