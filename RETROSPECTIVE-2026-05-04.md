# Architecture-First Plugin — Retrospective (3-day session, copy_trading_service)

**Date:** 2026-05-04
**Repo:** `copy_trading_service` (NestJS + TS + PG + Redis + Bull + GraphQL)
**Session:** 3 days, ~24 DEC IDs touched, 447 files changed, net **−1 614 LOC**, 9 listeners introduced, 1 cycle broken (9 → 8).

---

## TL;DR

The plugin's worst trait is that **it cannot say "no, leave it alone"**. Every signal (size, churn, fan-in, exports count) gets converted into a PR plan. There is no honest output mode for "this code is healthy, the metric is misleading, do nothing".

This produced ~40% wasted work in this session: DECs written for healthy files, façades that didn't break cycles, ADRs deleted at session end, and one PR (#53) that the user had to close as over-engineering.

The single most impactful change to the plugin: **make "no-op" a first-class verdict** with as much weight and as clear an output as "act". A user must be able to run `/arch-decompose` and get back, in plain words: **"Це норм. Не чіпай."**

---

## 1. DEC-by-DEC honest verdict

Each DEC we touched, with: what the plugin recommended, what we did, what the right answer **should have been**, and whether the file/module was **already fine and we should have left it alone**.

| DEC           | Target                                                 | Plugin said                                | We did                                                                                                    | Right call                                                                                                                                            | Verdict                                                                                                               |
| ------------- | ------------------------------------------------------ | ------------------------------------------ | --------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| 016           | `CopyPortfolioOperation` (282 LOC)                     | act, 3 PRs                                 | PR-1 (watch-list), PR-2 (bus emit), PR-3 ("LoC 283<400, no extraction needed")                            | PR-2 (bus emit) yes; PR-1 + PR-3 unnecessary — file was healthy, the "no extraction needed" verdict from PR-3 should have been **the answer in PR-1** | **Mixed.** 1 PR of value out of 3.                                                                                    |
| 017           | `StopFollowPortfolioOperation`                         | act, 4 PRs                                 | All 4 done, listeners adopted                                                                             | Yes — real god-method split                                                                                                                           | **Worth it.**                                                                                                         |
| 018           | margin event handlers                                  | act, 3 PRs                                 | All 3 done                                                                                                | Yes — handlers were genuinely tangled                                                                                                                 | **Worth it.**                                                                                                         |
| 019           | bootstrap `CopyEventsBus` + `common/ports/`            | act, 7 PRs                                 | Done                                                                                                      | Yes — enabled DEC-016/017 listener pattern                                                                                                            | **Worth it.**                                                                                                         |
| 020           | DB self-cycle                                          | act, 2 PRs                                 | Done                                                                                                      | Yes — broke 1 cycle for real (madge proven)                                                                                                           | **Worth it.**                                                                                                         |
| 021           | `PortfoliosService` decomp                             | act, 5 PRs                                 | PR-1 + PR-2 extracted `PortfolioPublicLinksService`, `PortfolioUserProfileService`                        | PR-1 yes (real cohesive extract). PR-2 borderline. PR-3..5 not done — and that was correct. **The DEC was right to stop.**                            | **Partial.** Should have been 2 PRs total, not 5 in the plan.                                                         |
| 022           | `SpotPropagateOrderOperation`                          | act, 6 PRs                                 | PR-1..3 extracted `ExecutionLogBuilder`, `SpotOrderPrepareStep`, `SpotSellRatioStep`                      | PR-1 (shared `ExecutionLogBuilder`) yes. PR-2/3 (extract steps) yes. Remaining 3 PRs not done — correct.                                              | **Partial.** Real value in PR-1..3.                                                                                   |
| 023           | `V4TransportService` (PR #53)                          | act, multi-PR                              | PR opened, **user closed it**                                                                             | **NO-OP.** File was a thin JSON-RPC envelope adapter; fan-in was structural, not a smell. Plugin should have said "це норм, не чіпай" from the start. | **Pure waste.**                                                                                                       |
| 024           | `FollowersResolver` god-class                          | act, 4 PRs                                 | Split into 4 resolvers                                                                                    | Yes — file was 800+ LOC, 4 distinct concerns                                                                                                          | **Worth it.**                                                                                                         |
| 025           | shared `Propagator` (margin+spot reuse)                | act, multi-PR                              | **Not executed**                                                                                          | Probably worth it (real reuse). Lifted to "future" because session ran out of pressure                                                                | **Deferred (correct).**                                                                                               |
| 026           | `WalletsService` god-class                             | act, 4 PRs                                 | Split into repos + allocation service; façade deleted                                                     | Yes — read/write concerns genuinely tangled                                                                                                           | **Worth it.**                                                                                                         |
| 027           | copy-portfolio dual-path soak                          | "defer" recommendation buried in 5-PR plan | Not executed (DEC-034 partially closed it)                                                                | **NO-OP.** File was healthy; the "defer" recommendation was right. Plan body was theatre.                                                             | **Should have been 1-line no-op verdict.**                                                                            |
| 028           | `FollowerMarginClosedPositions`                        | act, multi-PR                              | **Not executed**                                                                                          | **NO-OP.** File was working, no fan-in pain, no cycle, no churn. Plugin recommended decomposition based on size alone.                                | **Should have been no-op from the start.**                                                                            |
| 029           | `BatchCancelOperation`                                 | act, multi-PR                              | **Not executed**                                                                                          | **NO-OP.** Similar shape — file is fine.                                                                                                              | **Should have been no-op from the start.**                                                                            |
| 030           | followers `exports:` 18→7                              | act, 4 PRs                                 | Façades introduced, exports narrowed                                                                      | **Cosmetic.** Cycles unchanged. The façades did not solve any caller pain.                                                                            | **Mostly waste.** 1 of 4 PRs (drop zero-callers) was honest cleanup; the other 3 were narrowing for narrowing's sake. |
| 031           | portfolios `exports:` 25→10                            | act, 2 PRs                                 | Same shape                                                                                                | **Cosmetic.**                                                                                                                                         | **Mostly waste.**                                                                                                     |
| 032           | jobs `exports:` 11→3                                   | act, 2 PRs                                 | Same shape                                                                                                | **Cosmetic.**                                                                                                                                         | **Mostly waste.**                                                                                                     |
| 033           | margin `exports:` 15→5                                 | act, 1 PR                                  | Honest deletion of zero-callers, no façade introduced (DEC-023 lesson applied)                            | The "no façade" instinct was correct here. The PR boiled down to deletes.                                                                             | **Partial.** PR was OK because it dropped the façade idea mid-flight.                                                 |
| 034           | notifications consolidation                            | act, 5 PRs                                 | All 5 done; `internal-events` alias killed; emits moved to listeners                                      | Yes — single canonical emit path is genuinely enforceable now                                                                                         | **Worth it.**                                                                                                         |
| 035           | move 3 margin files to `margin/`                       | act, 1 PR                                  | Mechanical move                                                                                           | Yes — one-shot domain locality fix                                                                                                                    | **Worth it.**                                                                                                         |
| Phase 0 spec  | preemptive ADRs + system overview + glossary (9 files) | "write spec for global design"             | 9 markdown files written → **all deleted at session end**                                                 | **NO-OP.** ADRs are post-decision artifacts. We had no real X-vs-Y forks at the time.                                                                 | **Pure waste.**                                                                                                       |
| Final cleanup | 25 L1/L2 findings                                      | "scan for safely-removable dead code"      | 11 source files deleted, 8 deprecated methods/fns/imports purged, all 22 doc files removed, **−1.6k LOC** | Yes — and **this should have run first**, not last                                                                                                    | **Highest ROI of the entire session.**                                                                                |

### Summary by category

- **Worth doing again:** DEC-017, DEC-018, DEC-019, DEC-020, DEC-024, DEC-026, DEC-034, DEC-035, **final cleanup**.
- **Worth doing partially (less PRs than the plan claimed):** DEC-016, DEC-021, DEC-022, DEC-033.
- **Should have been NO-OP from the start:** **DEC-023, DEC-027, DEC-028, DEC-029, DEC-030, DEC-031, DEC-032 (mostly), Phase 0 spec.**
- **Total NO-OP that became work:** ~7 DECs + 1 phase = **~40% of the session**.

---

## 2. The big problem: plugin can't say "це норм, не чіпай"

Every other failure mode below ultimately roots in this. The plugin's prompts and templates structurally assume the answer is "decompose / refactor / extract". A healthy file gets the same shape of report as a pathological one.

### What "це норм" output should look like

Today, when a hotspot is healthy, the plugin still emits a 9-section DEC plan with PRs and risks. That plan **is itself pressure to execute** — once it exists, it begs to be done.

The plugin needs a parallel output template, equally weighty:

```markdown
# DEC-NNN: NO-OP — `<target>` is healthy

- **Status:** no-op
- **Verdict:** Це норм. Не чіпай.

## Why it looked like a hotspot

| Signal    | Value      | Threshold | Why it's misleading                                                 |
| --------- | ---------- | --------- | ------------------------------------------------------------------- |
| Churn 90d | 17 commits | warn 7    | 16 of 17 are arch-bot/format/lint commits; product-driven churn = 1 |
| Fan-in    | 12         | warn 15   | All 12 are leaf consumers in a single resolver tree                 |
| LoC       | 282        | warn 400  | Below threshold                                                     |

## What "act" would cost

- 3 new files (façade, listener, port).
- 30+ caller imports renamed.
- Zero cycles broken (verified: `madge --circular` before/after identical).
- No existing pain reported (no failing tests, no PR comments, no incident).

## When to revisit

If any of these become true, reopen:

- LoC > 400, **and** churn > 7 product commits in 90d.
- A specific feature requires touching > 5 files in this module.
- Cycle count rises above current N.

Until then: **don't write a PR for this.**
```

This output ends the conversation. No PR list, no risk table, no execution path. The DEC closes itself.

### Trigger conditions for `no-op` verdict

The decomposer agent must produce a `no-op` DEC when **any one** of:

1. All Tier 0/1 signals are below their thresholds.
2. Tier 0 churn is above threshold but **product-decay-adjusted churn** (excluding format / lint / bot / merge commits) is ≤ 1.
3. The file is a **thin transport adapter** (RPC envelope wrapping, > 50% lines are `await client.call(...)` shapes, no validation/branching).
4. The proposed structural change (façade / extract / split) does not break any cycle AND no caller-pain evidence is provided.
5. The file is < 300 LOC AND has only one responsibility cluster.

Multiple of these together → **strong** no-op (decomposer should refuse to write a plan even if user re-asks).

---

## 3. What was bad, in detail

### B1. Plugin treats every signal as actionable

`/arch-hotspot` ranks 30 files. `/arch-decompose ALL` spawns 8 agents in parallel. Each agent assumes its assigned target needs a plan.

- **What happened:** out of 8 hotspot rows, 3 were genuinely actionable (DEC-016/017/018-equivalent files), 3 were thin transport / leaf-of-tree (false positives), 2 were healthy and just hit churn threshold from arch-bot's own commits.
- **What should have happened:** before spawning a decomposer agent, plugin should run a 30-second filter: thin-transport check, decay-adjusted churn check, single-cluster check. Files that pass any one of these never get an agent.

### B2. Decomposer always writes a multi-PR plan

Once an agent is spawned, it has no exit. The template forces sections 1–8 (Evidence, Pattern, Target, PRs, Rollout, Sunset, Risks, Success criteria). Even DEC-027, where the agent **literally recommended option 2 (defer)**, still emitted a 5-section plan body.

- **What should happen:** template branches on verdict. `verdict: act` → full plan. `verdict: defer` → 1-section trigger condition. `verdict: no-op` → 1-section "why this is fine + when to revisit".

### B3. Façade pattern offered as default cycle-breaker — it isn't

DEC-030..033 introduced façade classes (`FollowersService`, `JobsExecutor`, etc.) under the implicit promise that narrowing module `exports:` would reduce cycles. **It didn't.** Cycles are formed by `forwardRef(() => OtherModule)` in `imports:`, not by symbol-level usage. After 4 façade DECs, cycle count stayed at 8.

- **What should happen:** plugin must classify cycle vs no-cycle work explicitly:
  - **Cycle work:** must rewire `imports:` (port inversion, event-bus inversion, or operation relocation between modules). Any DEC that doesn't touch `imports:` cannot claim cycle reduction.
  - **Non-cycle work:** clarity / public-surface work is fine, but the DEC must justify itself by caller pain (failing tests, PR comments, onboarding confusion) — never by `exports:` count alone.

### B4. Phase 0 spec was preemptive ADR generation — pure waste

User asked for "global design" guidance. Plugin interpreted that as "write 5 ADRs + system overview + glossary upfront". **All 9 files were deleted by user at session end.**

- **Why it was wrong:** ADRs are "we considered X vs Y, picked Y because Z" artifacts. We had **no real fork** to record. The docs were guesses dressed as decisions.
- **What should happen:** ADRs only generate on:
  - A DEC where two patterns are actually on the table and one must be picked (decomposer outputs `decision-required: true`).
  - A user-initiated `/arch-decide X-vs-Y` with both options described.
  - **Never** as a "Phase 0 / global design" exercise. There is no Phase 0. There are decisions, made one at a time, recorded after they're made.

### B5. Cleanup was an afterthought — it should have run first

The single highest-ROI activity of the session was the L1/L2 cleaner pass at the end: 25 findings, 11 source files deleted, ~1 600 LOC purged. Several DECs would have been **moot** if cleanup had run first:

- `WalletsService` façade was deleted as DEC-026 PR-4 — could have been a single L2 cleanup item instead.
- 7 deprecated repo methods marked `@deprecated 0 callers — pending deletion (DEC-026 PR-4)` were carried for ~3 days and then deleted. They could have been deleted on day 1.
- The `internal-events.ts` alias (1-line re-export) survived through DEC-034 PR-1 — could have been a 30-second L1 deletion.
- **What should happen:** `/arch-hotspot` should be paired with **mandatory** prior `/arch-clean` scan. If ≥ N safe deletions exist, plugin recommends running cleanup first and refuses to spawn decomposers until either cleanup runs or user explicitly skips.

### B6. No DEC budget — work compounds infinitely

13 DEC files written this session. 5 genuinely shipped, 1 abandoned (PR #53), 7 deferred / no-op. Each DEC carries reading + writing + state-tracking cost.

- **What should happen:** hard cap of **3 active DECs** (`Status: proposed | in-progress`) per repo at any time. New DEC creation blocks until one closes (`executed | abandoned | no-op`). Override flag for genuine emergencies.

### B7. No early-exit between PR-steps of one DEC

DEC-030 had 4 PRs; we executed all 4. By PR-3, the cycle hadn't moved and nothing was easier for any caller. There was no plugin-driven "stop, this isn't paying off" check.

- **What should happen:** between PRs in a multi-PR DEC, plugin emits a check:
  > "DEC-NNN PR-N/M shipped. Re-run signals:
  >
  > - Did the metric this DEC targeted move? (re-run hotspot → fail check)
  > - Has any caller stopped using a removed seam? (grep test → 0 callers means PR-N+1 isn't needed)
  > - If both 'no', recommend `defer` or `no-op` for remaining PRs."

### B8. Thin transport adapter trap (PR #53)

Decomposer recommended splitting `V4TransportService` based on fan-in alone. The file was 600 LOC of `await client.invoke(...)` calls — structurally thin, no business logic to untangle. PR opened, user closed.

- The lesson is now in user memory (`feedback_thin_transport_adapters.md`), but **the plugin doesn't know it** until the user re-teaches it on the next repo.
- **What should happen:** decomposer runs a transport-shape heuristic before recommending decomposition: ratio of `await client.<method>(...)` lines to total non-trivial lines > 0.5 + zero validation/branching → flag as thin transport, default verdict = `no-op`.

### B9. Repo polluted with deletable docs

22 markdown files written into `docs/architecture/` + `docs/decomposition/`. Every one deleted at session end. They were never read by anyone except me, never reviewed, never load-bearing.

- **What should happen:** distinguish **ephemeral session notes** from **durable artifacts**:
  - DECs default to `${TMPDIR}/architecture-first/<repo-hash>/dec-NNN.md`. Promoted to `docs/decomposition/` only via explicit `/arch-publish-dec NNN` once user confirms it's reviewable and decision-load-bearing.
  - ADRs go to `docs/architecture/adr/` only after the corresponding DEC is `executed` AND the decision was a real X-vs-Y fork.
- This stops the "I wrote 13 files, deleted 13 files" cycle.

### B10. False cycle-breaking claims

Several DECs in this session claimed they would "reduce cycles". None of the narrowing DECs (030–033) did. There was no automated check.

- **What should happen:** every DEC mentioning "reduces cycles" must include:
  1. `madge --circular` output **before**, in evidence.
  2. Predicted output **after**, in success criteria.
  3. Mandatory verification at end of execution: re-run madge; **fail** if prediction wrong; mark DEC as `partial-failure`.
- DECs that don't break a cycle must say so explicitly: `Cycles affected: 0`. Today the plugin omits this line, and the omission itself implies value that isn't there.

### B11. No "what triggered this work?" gate

Architecture work without product pressure is yoga — and that's exactly what 40% of this session was. The plugin never asked "what feature or incident triggered this?"

- **What should happen:** at session start, plugin asks once:
  > Was this triggered by:
  > **(a)** a specific feature/incident that's blocked or painful → proceed to full architecture-first flow.
  > **(b)** a proactive cleanup pass → restrict to L1/L2 cleaner + tier-S decompositions only.
  > **(c)** curiosity / metrics / tidying → suggest `/arch-clean` only, **no DECs allowed**.
- Answer (c) → plugin never spawns the decomposer agent. Period.

### B12. Honest session-close ledger missing

Session ended with the user asking "як змінилася наш сервіс 3 дні тому VS зараз" and "тобто твій фідбек - класс і це все двйсно вартувало того". Plugin had no built-in answer.

- **What should happen:** new command `/arch-session-close` that produces:
  - DECs touched, status of each (executed / abandoned / deferred / no-op).
  - LOC delta net, cycle delta, listeners/façades net.
  - Ratio: % time on shipped value vs % time on docs-that-were-deleted.
- Output to user only, never to repo. Calibrates expectation for next session.

---

## 4. Concrete plugin improvements (with file targets)

Each item: problem → fix → file in `architecture-first-plugin/` to touch.

### P1. **No-op verdict, first-class** ← most important

**Problem:** decomposer can't say "це норм, не чіпай" (B1, B2).
**Fix:** add `verdict: no-op` as a fourth output of `agents/hotspot-decomposer.md`. Output template branches:

- `act` → full 9-section DEC plan.
- `defer` → 1-section trigger-condition stub.
- `no-op` → "Це норм. Не чіпай." + signals-explanation table + revisit conditions. **No PR plan. No risk table. Plan ends.**

Trigger heuristics: see §2 above (5 conditions; one suffices).
**Touch:** `agents/hotspot-decomposer.md`, `templates/decomposition-plan.md.tmpl` (split into `-act.tmpl`, `-defer.tmpl`, `-no-op.tmpl`).

### P2. Pre-decomposer filter: thin-transport + decay-adjusted churn

**Problem:** false positives reach decomposer (B1, B8).
**Fix:** before spawning a `hotspot-decomposer` agent for any row, plugin runs a 30-second filter pass:

- Thin-transport detector (regex on `await ... client.<method>` ratio).
- Decay-adjusted churn (exclude commits matching `arch-bot`, `chore(format)`, `chore: strip`, merge-commits).
- Single-responsibility-cluster check (count distinct verb-object groups in file).
  Files that fail any one → automatic `no-op` verdict, no agent spawned.
  **Touch:** `skills/arch-hotspot/SKILL.md` or `commands/arch-hotspot.md` (filter before state file is written).

### P3. DEC budget cap (≤ 3 active per repo)

**Problem:** unlimited DEC creation (B6).
**Fix:** plugin tracks active DECs in `${TMPDIR}/architecture-first/<repo-hash>-active-decs.json`. New DEC blocks if ≥ 3 active. Override: `/arch-budget-override <reason>`.
**Touch:** `skills/arch-decompose/`, new state file.

### P4. Cleanup runs FIRST, gate decomposer on it

**Problem:** highest-ROI activity ran last (B5).
**Fix:** `/arch-hotspot` and `/arch-decompose` both check for prior `/arch-clean` run. If no cleanup run in last 7 days OR ≥ 10 unfixed L1/L2 findings exist, plugin **refuses** to spawn decomposers until user runs `/arch-clean` or explicitly passes `--skip-cleanup`.
**Touch:** `skills/architecture-first/SKILL.md`, `skills/arch-hotspot/`, `skills/arch-decompose/`.

### P5. Cycle proof mandatory

**Problem:** false cycle-breaking claims (B3, B10).
**Fix:** any DEC mentioning "cycles" must include explicit cycle-evidence section with `madge --circular` before/after. Plugin verifies at execution end. DECs that don't touch cycles must state `Cycles affected: 0`.
**Touch:** `templates/decomposition-plan.md.tmpl`, `agents/hotspot-decomposer.md`, post-execution hook.

### P6. ADRs only post-decision, never preemptive

**Problem:** Phase 0 spec deleted (B4).
**Fix:** remove all "Phase 0", "global design", "system spec" prompts from `skills/architecture-first/SKILL.md`. ADRs trigger only on:

- DEC marked `decision-required: true` (real X-vs-Y fork).
- User-initiated `/arch-decide X-vs-Y`.
  **Touch:** `skills/architecture-first/SKILL.md`.

### P7. Ephemeral vs durable doc split

**Problem:** repo pollution (B9).
**Fix:** DECs default to `${TMPDIR}/architecture-first/<repo-hash>/dec-NNN.md`. New `/arch-publish-dec NNN` command promotes to repo. ADRs same model.
**Touch:** `skills/arch-decompose/`, new `commands/arch-publish-dec.md`.

### P8. Mid-DEC reality check

**Problem:** no checkpoint between PRs (B7).
**Fix:** between PR-N and PR-(N+1), plugin re-runs target signals. If metric unmoved AND no caller migrated to new seam, recommend `defer`/`no-op` for remaining PRs.
**Touch:** `commands/arch-execute.md`.

### P9. Session-trigger gate

**Problem:** no demand-side check (B11).
**Fix:** at session start, plugin asks the (a/b/c) question. Answer (c) → decomposer disabled, only `/arch-clean` available.
**Touch:** `skills/architecture-first/SKILL.md` first step.

### P10. Session-close ledger

**Problem:** no honest summary (B12).
**Fix:** new `/arch-session-close` command. Lists DECs by status, LOC/cycle delta, value-vs-ceremony ratio. Output to user only.
**Touch:** new `commands/arch-session-close.md`.

### P11. "Це норм" UX polish

**Problem:** even when no-op verdict exists (P1), it can read like a defeat.
**Fix:** make the no-op output **affirmative and confident**, in the user's language. Default templates:

- 🇺🇦: "**Це норм. Не чіпай.** Файл здоровий, метрики оманливі тому що X. Повертайся, коли Y."
- 🇬🇧: "**Leave it alone.** File is healthy. Signals X are misleading because Y. Revisit if Z."
  This frames the no-op as a real engineering choice, not a fallback.
  **Touch:** `templates/decomposition-plan-no-op.tmpl`.

### P12. "Already learned" lessons portable across repos

**Problem:** thin-transport lesson lived in `feedback_thin_transport_adapters.md` (per-user memory) — invisible to plugin (B8).
**Fix:** plugin ships with a `references/known-antipatterns.md` (transport adapters, leaf-of-tree fan-in, format-churn-hotspots, etc.). Decomposer agent checks every target against this list before producing a verdict.
**Touch:** new `references/known-antipatterns.md`, referenced from `agents/hotspot-decomposer.md`.

---

## 5. Priorities

If only one change can be made → **P1 (no-op verdict).** Without it, every other improvement still gets routed into "write a plan to do something". P1 ends that automatic pressure.

If two changes → **P1 + P4 (cleanup-first).** P4 alone would have removed ~11 files at session start and made several DECs unnecessary. Together they catch most of the ~40% wasted work.

If three → **P1 + P4 + P3 (DEC budget cap).** Caps the failure mode the user explicitly named: _"ця ситуація з деками до безкінечності може продовжуватися"_.

The remaining items (P2, P5–P12) are progressive refinements once the top three are in place.

---

## 6. What to keep — these worked

- `cleaner` agent's L1/L2 framing. The level granularity was exactly right; we trusted L1 deletions, verified L2, never escalated to L3/L4 — and the result was the highest-ROI part of the session.
- `architect-reviewer` agent for genuine multi-module / public-surface changes (DEC-016, DEC-018, DEC-024 reviews held up).
- Tier system (XS/S/M/L/XL) — useful as a _ceiling_ on ceremony. Harmful when it auto-spawns subagents on M+ regardless of demand.
- Stack-profile detection (NestJS profile worked, no manual config needed).
- Mermaid-over-ASCII for C4 diagrams.

## 7. One-liner takeaway

> **Plugin should default-prefer deletion over creation, no-op over PR plan, ephemeral notes over committed docs.** The plugin's most useful new capability is the ability to look at code and say plainly, in the user's language: **"Це норм. Не чіпай."** — and stop there.

The user's verbatim observation is the canonical failure mode to design against:

> _"ця ситуація з деками до безкінечності може продовжуватися"_ — every architectural metric becomes a DEC, every DEC becomes a PR plan, every PR plan begs to be executed. Cut this loop at the verdict stage.
