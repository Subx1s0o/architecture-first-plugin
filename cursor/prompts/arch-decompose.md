Plan a decomposition for one or more targets. Argument forms: <PATH>, <N> (row from last /arch-hotspot), <A>-<B> (range), <A>,<B>,<C> (list), or ALL. Optional flags: `--force-all` (bypass top-3 cap on ALL), `--skip-cleanup-gate`, `--budget-override <reason>`.

**Pre-flight gates — run in order, fail-stop:**

1. **Cleanup-first gate.** Read `${TMPDIR:-/tmp}/architecture-first/<md5(project_dir)>-hotspot.json`. If `cleanup_debt_count >= 10` AND no `/arch-clean` run in last 7 days, refuse and recommend running `/arch-clean` first. Override: `--skip-cleanup-gate`.

2. **DEC budget cap.** Count active DECs (`grep -lE "^- \*\*Status\*\*:\s*(proposed|in progress)" docs/decomposition/DEC-*.md`). If ≥ 3, refuse with the list of active DECs and ask user to close one. Override: `--budget-override "<reason>"`.

3. **Trigger check (first /arch-\* per session only).** If no `${TMPDIR}/architecture-first/<repo-hash>-trigger.txt`, ask: "What triggered this? (a) feature/incident pushing / (b) proactive cleanup / (c) curiosity". (a) → proceed. (b) → restrict to L1/L2 cleaner + tier-S only. (c) → refuse decomposer; suggest `/arch-clean` or `/arch-hotspot`.

**Resolve:** path → single target. Otherwise map row numbers from state file. `ALL` → **top 3 by rank** (capped) unless `--force-all`. If > 3 resolved AND no `--force-all`, ask user to pick 3.

For each resolved target, the decomposer emits **one of three verdicts**, all equal weight:

- **`act`** — real hotspot, domain decomposition exists → full DEC plan in `docs/decomposition/DEC-<N>-<slug>.md`.
- **`defer`** — real hotspot, cost > value now → truncated DEC with explicit re-open condition.
- **`no-op`** — file is healthy, metrics are misleading → `docs/decomposition/DEC-<N>-<slug>-noop.md` using the no-op template. **No PR plan. Plan ends.** Default to no-op when in doubt — bias toward leaving healthy code alone.

Pre-checks the decomposer must run before writing any plan: H1 thin transport, H2 format-churn, H3 leaf-of-tree fan-in, H4 single-cluster small file, H5 already-decomposed soak window, H6 test-only file, H7 façade-narrowing without cycle proof, H8 speculative reuse. First heuristic that fires with no-op wins.

End with a summary table where Target + DEC-file cells are clickable markdown links, with a Verdict column. Sample:

| Target                                                          | DEC file                                                            | Verdict   | Pattern             | Effort | Recommendation         |
| --------------------------------------------------------------- | ------------------------------------------------------------------- | --------- | ------------------- | ------ | ---------------------- |
| [`portfolios.service.ts`](src/portfolios/portfolios.service.ts) | [DEC-001](docs/decomposition/DEC-001-portfolios-service.md)         | act       | Extract Port        | 3 PRs  | Act now                |
| [`v4.transports-service.ts`](src/v4/v4.transports-service.ts)   | [DEC-002](docs/decomposition/DEC-002-v4-transports-service-noop.md) | **no-op** | thin transport (H1) | —      | **Це норм. Не чіпай.** |

If all verdicts came back as `no-op`: end with one line in user's language — "Це норм. Усе гаразд. Архітектурно чіпати нічого."

In Cursor, decomposers run sequentially. Warn the user upfront when there are multiple targets. No code writes.
