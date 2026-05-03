---
description: Plan decomposition for one or many hotspots. Accepts path, row N from /arch-hotspot, range A-B, list A,B,C, or ALL. Emits one of three verdicts per target — act / defer / no-op. Refuses to spawn decomposers if cleanup debt is high or DEC budget is exhausted.
---

Takes one argument. Forms:

- `/arch-decompose <path>` — a file or module directory.
- `/arch-decompose <N>` — row N from the latest `/arch-hotspot` state file.
- `/arch-decompose <A>-<B>` — inclusive range of rows (`1-5`).
- `/arch-decompose <A>,<B>,<C>` — comma-separated rows.
- `/arch-decompose ALL` (or `all`) — plan top-3 from the latest hotspot scan (capped). Use `--force-all` to override the cap.

Optional flags:

- `--force-all` — bypass the top-3 cap on `ALL`.
- `--skip-cleanup-gate` — bypass the cleanup-first gate.
- `--budget-override <reason>` — bypass the active-DEC budget cap.

## Pre-flight gates (run in order, fail-stop)

### Gate 1 — Cleanup-first

Read `${TMPDIR:-/tmp}/architecture-first/<md5(CLAUDE_PROJECT_DIR)>-hotspot.json`. If the latest scan recorded `cleanup_debt_count >= 10` (L1/L2 findings) AND no `/arch-clean` run is recorded for the current repo in the last 7 days, refuse:

```
The cleaner found <N> safely-removable items (L1/L2). Decomposition before cleanup tends to produce DECs that just delete dead code wrapped in ceremony. Recommended: run `/arch-clean` first.

To override: re-run with `--skip-cleanup-gate`.
```

### Gate 2 — DEC budget cap

Count active DECs:

```bash
ls docs/decomposition/DEC-*.md 2>/dev/null \
  | xargs -I{} sh -c 'grep -lE "^- \*\*Status\*\*:\s*(proposed|in progress)" "{}"' \
  | wc -l
```

If the count is `>= 3`, refuse:

```
You have <N> active DECs (`proposed` or `in progress`) already:
  - <DEC-XXX>: <target>
  - <DEC-YYY>: <target>
  - <DEC-ZZZ>: <target>

Close at least one before opening another. Update its `Status:` to `done | abandoned | no-op`, or run `/arch-session-close` to review.

To override: re-run with `--budget-override "<reason>"`. The override + reason will appear in the session-close ledger.
```

### Gate 3 — Trigger check (only on first invocation per session)

If this is the first `/arch-*` command in the session AND no `${TMPDIR}/architecture-first/<repo-hash>-trigger.txt` exists, ask once:

```
What triggered this architecture work?
  (a) a specific feature or incident is blocked or painful by current shape
  (b) proactive cleanup pass — repo feels heavy, no specific feature pushing
  (c) curiosity / metrics / tidying

Reply with one letter.
```

- (a) → record `trigger=feature` and proceed normally.
- (b) → record `trigger=cleanup` and **restrict to L1/L2 cleaner + tier-S decompositions only**. Refuse `ALL`, refuse multi-PR DECs.
- (c) → record `trigger=curiosity` and refuse decomposer entirely. Suggest `/arch-clean` or `/arch-hotspot` (read-only) and stop.

## Steps (when gates pass)

1. **Resolve targets:**
   - If the argument looks like a path (contains `/` or `.`) → single target.
   - Otherwise read `${TMPDIR:-/tmp}/architecture-first/<md5(CLAUDE_PROJECT_DIR)>-hotspot.json`.
     - If the file is missing: prompt the user to run `/arch-hotspot` first, stop.
     - Parse the argument: `ALL`/`all` → top 3 rows by rank (capped) unless `--force-all` is set; `N` → single row; `A-B` → inclusive range; `A,B,C` → list.
     - Map each row number to its `path`.
   - If the resolved target list has > 3 entries AND `--force-all` is NOT set, show the ranked list and ask which 3 to plan. Stop and wait for response.

2. **Dispatch:**
   - If 1 target: invoke `hotspot-decomposer` sub-agent once.
   - If ≥ 2 targets: dispatch **all hotspot-decomposer sub-agents in ONE assistant message** as parallel `Agent` tool calls.
     - In Cursor (no parallel agents): process sequentially but tell the user upfront it will take ~N × single-run time.

3. Each sub-agent receives: resolved path, `.arch-profile.yaml` (if present), detected stack profile, and is told **all three verdicts (act / defer / no-op) are valid first-class outcomes** — emitting `no-op` is success.

4. Each sub-agent writes the matching artifact:
   - Verdict `act` → `docs/decomposition/DEC-<next>-<slug>.md` via `templates/decomposition-plan.md.tmpl`.
   - Verdict `defer` → same path, but truncated form (Section 1 + Section 9 only).
   - Verdict `no-op` → `docs/decomposition/DEC-<next>-<slug>-noop.md` via `templates/decomposition-plan-no-op.md.tmpl`.

5. After all agents return, produce a summary table. **Every Target and DEC-file cell must be a clickable markdown link**:

   ```markdown
   | Target                                                                                | DEC file                                                            | Verdict   | Pattern                             | Effort | Recommendation                   |
   | ------------------------------------------------------------------------------------- | ------------------------------------------------------------------- | --------- | ----------------------------------- | ------ | -------------------------------- |
   | [`portfolios.service.ts`](src/portfolios/portfolios.service.ts)                       | [DEC-001](docs/decomposition/DEC-001-portfolios-service.md)         | act       | Extract Port + Query Object         | 3 PRs  | Act now                          |
   | [`v4.transports-service.ts`](src/v4/v4.transports-service.ts)                         | [DEC-002](docs/decomposition/DEC-002-v4-transports-service-noop.md) | **no-op** | thin transport (H1)                 | —      | **Це норм. Не чіпай.**           |
   | [`copy-portfolio.operation.ts`](src/followers/operations/copy-portfolio.operation.ts) | [DEC-003](docs/decomposition/DEC-003-copy-portfolio-operation.md)   | defer     | Branch by Abstraction (sunset half) | 2 PRs  | Re-open after DEC-016 PR-3 ships |
   ```

6. **End with one line per verdict bucket:**
   - "Click any `act` DEC to open the plan. Run `/arch-execute <N>` to implement PR-1."
   - "`no-op` DECs are closed — they explain why each file is fine."
   - "`defer` DECs include re-open conditions; revisit when those conditions become true."

   If all verdicts came back as `no-op`: end with **"Це норм. Усе гаразд. Архітектурно чіпати нічого."** (mirror user's language).

## Important

- The decomposer's **bias is toward `no-op`**. A scan that returns 3 `no-op`s is a successful scan, not a failed one — it means the codebase is healthier than the metrics suggested.
- `no-op` DECs go into `docs/decomposition/` with a `-noop` suffix so they're visually distinct in `ls`.
- Active-DEC count never includes `no-op` DECs (they're closed at birth).
