# Hotspot detection — pyramid of signals

Investigate from cheap to expensive. Escalate only when a cheaper signal has already fired.

## Tier 0 — free signals (always run)

Run these on any file you plan to edit.

- **Size.** `wc -l <file>`. Flag if > stack threshold (typically 400–600 LoC). Functions/methods > 80 LoC — read the file and spot-check.
- **Churn.** `git log --since=90.days --name-only --pretty=format: -- <file> | sort -u | wc -l` and `git log --oneline --since=90.days -- <file> | wc -l`. Files changed in ~5+ of the last 20 commits are bug magnets.
- **Age × churn.** Young file with high churn = still stabilizing, not necessarily a smell. Old file with high churn = entropic hotspot.

## Tier 1 — cheap structural signals

- **Fan-in.** `Grep` for imports of the file/symbol across the repo. > 20 importers = god dependency; edit risk scales worse than linearly with fan-in.
- **Fan-out.** Read the file's import block. > 15 distinct modules imported = god client; probably doing too much.
- **Cycle.** TS/JS: `npx madge --circular src`. Python: `pydeps --show-cycles`. Go: manual via `go list -deps`. Rust: `cargo-modules`. A cycle at module level is almost always a missing port.
- **Duplication.** `npx jscpd` / `pmd-cpd` / manual grep for signature fragments. 3+ near-duplicate blocks argue for an abstraction.

## Tier 2 — semantic signals (read the code)

- **Responsibility heterogeneity.** List public methods / exports. If you can group them into ≥ 2 unrelated clusters by verb-object, the unit has ≥ 2 responsibilities.
- **Long parameter lists.** > 4 parameters → data clump; those params usually belong in a value object.
- **Primitive obsession.** `string userId`, `string accountId` all as raw strings → opaque / branded types.
- **Temporal coupling.** Comments like "call `init()` before `run()`", or invariants enforced by call ordering alone. Resolve via constructor injection, factory, or state machine.
- **Feature envy.** Method of class A accesses 3+ fields of class B but only 0–1 of its own. Move the method to B.
- **Switch / if-chain on type code.** `switch (kind) { case … }` repeated in 2+ places → strategy or polymorphism.
- **Nested depth.** > 3 levels of `if`/`try`/loop. Extract clauses; consider a state machine.

## Tier 3 — cross-cutting signals (multi-file reads)

- **Shotgun surgery.** Planned change requires edits in 5+ files that don't share an obvious module. Symptom of a leaked concern. Introduce a cohesive unit and funnel the change through it.
- **Divergent change.** One file is changed for 3+ unrelated reasons across recent PRs.
- **Speculative generality.** Abstract classes/interfaces with one implementation and no plausible second. Collapse.
- **Dead code.** Exports with 0 importers outside tests. Delete, do not refactor.

## Tier 4 — external / runtime signals

- **Coverage holes.** Hotspots with low test coverage — highest decomposition priority.
- **Incident density.** `git log --grep='fix'` on the file. Files mentioned in many fix-commits are decomposition candidates regardless of size.
- **Ownership breadth.** `git shortlog -sn -- <file>`. Files touched by > 8 distinct authors tend to lack an owner.

## How to report a hotspot

| Signal tier | Evidence                                   | Severity | Implication                               |
| ----------- | ------------------------------------------ | -------- | ----------------------------------------- |
| 0           | `wc -l src/x.ts` → 840                     | high     | XL — decompose before editing             |
| 1           | 27 importers of `UserService`              | high     | god dependency; extract interface + split |
| 2           | `sendEmail` + `calculateTax` in same class | med      | responsibility split                      |

Severity:

- **high** — blocks this PR (trigger XL) or materially raises incident risk.
- **med** — should be ticketed; not necessarily this PR.
- **low** — stylistic, mention under "observed tech debt".
