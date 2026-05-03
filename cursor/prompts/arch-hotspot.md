Scan the whole repo for architectural hotspots.

Tier 0: top 30 files by LoC (`wc -l` adapted to detected stack); top 30 by **decay-adjusted** 90-day churn — `git log --since=90.days --pretty='format:%h %s' | grep -vE 'arch-bot|chore\(format\)|chore: strip|chore: prettier|chore: lint|^[0-9a-f]+ Merge '`. Report decay-adjusted as the primary number; only show raw if it diverges ≥ 3×.

Tier 1: fan-in via grep on top-20 exports; **distinct top-level module fan-in** (number of distinct `src/<module>/` subtrees that import the symbol — if 1, fan-in is structural per H3); cycles via `madge --circular` (JS/TS) or `pydeps --show-cycles` (Python).

For each primary hotspot read the file and count responsibility clusters. If exactly 1 cluster AND LoC < 300, mark **likely no-op** — small + cohesive, metrics misleading.

Cross-reference: BOTH top-size AND top-(adjusted)-churn = primary. Run cleaner sub-agent in parallel for L1/L2 cleanup-debt count.

Produce ranked table: `Rank | Path | Size | Churn (adj/raw) | Cycle? | Fan-in (mods) | Smell | Likely verdict`. Likely verdict ∈ {act, no-op, defer}.

Write state file at `${TMPDIR:-/tmp}/architecture-first/<md5(project_dir)>-hotspot.json` with shape including `cleanup_debt_count`, `cleanup_top_findings`, and per-row `churn_adjusted`, `fan_in_modules`, `likely_verdict`. Overwrite each run.

If `cleanup_debt_count >= 10`, prepend banner "⚠ Cleaner found N safely-removable items — recommend `/arch-clean` first".

End with one of:

- All hotspots `likely_verdict: no-op` → "**Це норм. Усе гаразд.** Метрики не показують реальної проблеми. Файли здорові."
- High cleanup debt → "Recommend `/arch-clean` first; or pass `--skip-cleanup-gate` to `/arch-decompose`."
- Otherwise → "Run /arch-decompose <N>, 1-3, or ALL (capped at top-3 by default; --force-all to bypass)."

No code writes.
