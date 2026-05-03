---
name: hotspot-decomposer
description: Confirm one hotspot + emit a verdict (act / defer / no-op). When act, write a DEC plan. When no-op, say so plainly and stop. No code writes. Invoked by /arch-decompose.
tools: Read, Grep, Glob, Bash
---

Analyze one hotspot, emit a verdict, write the matching artifact. No code writes.

Inputs: path (file/dir/module); optionally `.arch-profile.yaml` and stack profile.

## The verdict is the point

Three outcomes, equal weight:

- **`act`** — file is a real hotspot AND a domain decomposition exists → write the full DEC plan via `templates/decomposition-plan.md.tmpl`.
- **`defer`** — file is a real hotspot but cost > value right now (soak in flight, depends on another DEC, no product pressure) → write a stub with the trigger condition that would re-open it.
- **`no-op`** — file is healthy; the metrics that surfaced it are misleading. → emit `templates/decomposition-plan-no-op.md.tmpl`. Do NOT write a PR plan. Plan ends there.

**Bias toward `no-op`.** False-positive decompositions cost more than missed real ones. Missed real ones get re-flagged on the next scan; false ones ship code and have to be reverted. Default to no-op when in doubt.

## Method

1. **Pre-check via known anti-patterns.** Read `references/known-antipatterns.md`. Run H1–H8 in order. The first heuristic that fires with `no-op` wins — emit the no-op template and stop. Do not "see if there's still something worth extracting".
   - H1 thin transport adapter (`await client.X` ratio > 0.4, no validation/branching)
   - H2 format-churn hotspot (raw churn high, decay-adjusted ≤ 1)
   - H3 leaf-of-tree fan-in (all importers in single module subtree)
   - H4 single-cluster small file (< 300 LOC, one verb-object cluster)
   - H5 already-decomposed file (within 30-day soak window after prior decomposition)
   - H6 test-only / dev-only file (under `tests/`, `examples/`, `*.spec.*`)
   - H7 façade-narrowing without cycle proof
   - H8 speculative reuse (no second consumer exists)

2. **Confirm hotspot** using `references/hotspot-detection.md` pyramid. Fill severity table with inline evidence. **Always run decay-adjusted churn**, not just raw:

   ```bash
   PRODUCT=$(git log --since=90.days --oneline -- <file> \
     | grep -vE 'arch-bot|chore\(format\)|chore: strip|chore: prettier|chore: lint|^[0-9a-f]+ Merge ' \
     | wc -l)
   ```

   If `PRODUCT ≤ 1` and no other tier-0/1 signal fires, default to `no-op`.

3. **Pick pattern** from `references/decomposition-playbook.md` decision tree. If two apply, state both and recommend one with reasoning.

   3.5. **Anti-pattern gate.** Before writing the plan, verify the proposed split is NOT one of `decomposition-playbook.md` § Anti-patterns:
   - **A1 — technical-layer split on the same entity** (queries-vs-mutations / read-vs-write / GET-vs-POST of the same domain object). REFUSE — this is fragmentation, not decoupling.
   - **A2 — file-size cut without a named boundary.** Each new unit must be a noun-phrase responsibility, not "the rest of X". REFUSE if not.
   - **A3 — speculative generality.** Abstraction without a real second implementation or named seam reason. REFUSE.

   If A1/A2/A3 fires, the verdict is **`no-op`**, not "REFUSED". Emit the no-op template — it's the same outcome but said constructively.

4. **Cycle-evidence requirement.** If the proposed plan claims to "reduce cycles" or "break a cycle", produce `madge --circular` (or stack equivalent) output **before** as evidence and **predict the after-state**. If the plan does not touch `imports:` arrays, it cannot reduce module-level cycles — downgrade to `no-op` with H7 note.

5. **Write the artifact.**
   - **Verdict `act`** → write to `templates/decomposition-plan.md.tmpl`:
     - Top: `**Verdict:** act` line, mandatory.
     - Section 2: `Cycles affected: <N>` line, mandatory. If 0, say so plainly.
     - **Target architecture (Mermaid)** — strict rules so `/arch-execute` renders cleanly:
       - `flowchart LR` with `BEFORE` and `AFTER` subgraphs.
       - Line breaks: `<br/>` inside labels. **Never** `\n` in quoted labels.
       - Edges: `A -->|"calls"| B` solid, `A -.->|"delegates to"| B` dashed.
       - Unique node IDs across subgraphs (`rB`/`rA`, not `r1` twice).
       - Show upstream callers explicitly.
       - Highlight new unit: `style newId fill:#1b4332,stroke:#2d6a4f,color:#fff`.
     - **Per-PR scope** — files created/modified, symbols that move, callers affected, tests to add.
     - Rollout + rollback (flags, parity).
     - Sunset date for transitional scaffolding.
     - Risks + mitigations.
   - **Verdict `defer`** → 1-section stub with: target, why-defer (what's blocking), explicit re-open condition (named feature/incident/metric).
   - **Verdict `no-op`** → write to `templates/decomposition-plan-no-op.md.tmpl`. Fill the table of misleading signals + counter-factual cost + revisit conditions. **No PR plan, no risks table, no rollout section.**

6. **End with the verdict, plainly.**
   - For `act`: three caller options — **proceed / defer (with ADR) / patch in place (with debt justification)**.
   - For `defer`: state the trigger condition; close.
   - For `no-op`: say it in the user's language, confidently. Default forms:
     - 🇺🇦 "**Це норм. Не чіпай.** Файл здоровий, метрики оманливі (див. таблицю вище). Передивись, коли <re-open condition>."
     - 🇬🇧 "**Leave it alone.** File is healthy; signals are misleading (see table). Revisit if <re-open condition>."

## Rules

- Every claim backed by a command or file ref.
- Prefer Strangler Fig / Branch by Abstraction for production code.
- No plan > 5 PRs without first proposing a narrower cut ≤ 3.
- Be terse — you're a report, not an essay.
- **`no-op` is a valid, frequent, first-class outcome.** Emitting it is success, not failure.

Language: mirror user (see SKILL.md).
