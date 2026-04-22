---
description: Rank architectural hotspots (size × churn × cycles × fan-in). Saves state file so /arch-decompose can reference rows by number. Read-only.
---

1. Detect the stack via `skills/architecture-first/references/stack-profiles/_detect.md`. Load thresholds from the matching profile; override with `.arch-profile.yaml` `thresholds:` if present.

2. Run Tier 0 signals:
   - Top 30 files by LoC: adapt extensions to the detected stack.
   - Top 30 files by 90-day churn: `git log --since=90.days --name-only --pretty=format: | grep '\.<ext>$' | sort | uniq -c | sort -rn | head -30`.

3. Run Tier 1 signals where tools are available:
   - Cycles: `npx --yes madge --circular src 2>/dev/null` (JS/TS) or `python -m pydeps --show-cycles . 2>/dev/null` (Python). Skip quietly if missing.
   - Fan-in on top-20 exported symbols: grep across the repo.

4. Cross-reference: files in BOTH top-size AND top-churn = **primary**. Top-churn only = secondary. Top-size only = tertiary.

5. For each primary hotspot read the file and count distinct responsibility clusters (verb-object groups).

6. Produce the ranked table: `Rank | Path | Size | Churn | Cycle? | Smell | Suggested pattern`.

7. **Write the state file** so `/arch-decompose` can reference rows by number:
   - Path: `${TMPDIR:-/tmp}/architecture-first/<md5(CLAUDE_PROJECT_DIR)>-hotspot.json`
   - Shape:
     ```json
     {
       "timestamp": "<iso>",
       "project": "<abs path>",
       "rows": [
         { "rank": 1, "path": "src/x.ts", "size": 834, "churn": "14/20", "cycle": false, "smell": "…", "pattern": "Extract Port" }
       ]
     }
     ```
   - Create the parent dir if missing. Overwrite on every run.

8. End with: "Run `/arch-decompose <N>` for row N, `/arch-decompose 1-5` for a range, `/arch-decompose 1,3,5` for a list, or `/arch-decompose ALL` to plan decomposition for every row in parallel."

Do not edit code.
