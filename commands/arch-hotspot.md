---
description: Scan the repo for architectural hotspots and rank them. Uses cheap signals first, then semantic ones. No writes.
---

1. Detect the stack via `skills/architecture-first/references/stack-profiles/_detect.md`. Load the matching profile's thresholds. If `.arch-profile.yaml` exists, override with its `thresholds`.

2. Run Tier 0 signals (cheap, universal):
   - Top 30 files by LoC. Example for JS/TS: `find . -type f \( -name '*.ts' -o -name '*.tsx' -o -name '*.js' \) -not -path '*/node_modules/*' -not -path '*/.git/*' | xargs wc -l | sort -rn | head -30`. Adapt the extensions to the detected stack.
   - Top 30 files by 90-day churn: `git log --since=90.days --name-only --pretty=format: | grep -E '\.(ts|tsx|js|py|go|rs|java|rb|php)$' | sort | uniq -c | sort -rn | head -30`.

3. Run Tier 1 signals where tools are available:
   - Cycles: for TS/JS `npx --yes madge --circular src 2>/dev/null || true`; for Python `python -m pydeps --show-cycles . 2>/dev/null || true`; skip quietly if the tool is missing.
   - Fan-in on the top-20-by-size exported symbols: grep for import of each symbol across the repo.

4. Cross-reference. A file that appears in BOTH top-size AND top-churn lists is a **primary** hotspot. Top-churn only is **secondary**. Top-size only is **tertiary**.

5. For each primary hotspot read the file and classify responsibilities (count distinct verb-object clusters among public exports, note obvious smells from `references/hotspot-detection.md` Tier 2).

6. Produce one ranked table:

| Rank | Path | Size | Churn (90d) | Cycle? | Smell summary | Suggested pattern |
| ---- | ---- | ---- | ----------- | ------ | ------------- | ----------------- |

7. End with: "Run `/arch-decompose <path>` to get a detailed plan for any row."

Do not edit code. Do not auto-invoke `hotspot-decomposer` — the user picks which row warrants a deep dive.
