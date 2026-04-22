# Cleanup playbook

Principles and patterns for safe deletion. Companion to decomposition-playbook.

## Principles

1. **Git remembers, code forgets.** Delete commented blocks without ceremony (L1).
2. **Reachability ≠ imports.** DI, decorators, reflection, convention-scanning all route around static imports. Rule them out first (see `references/framework-magic.md`).
3. **One axis per batch.** A cleanup PR is orphan code OR deps OR formatting — never mixed.
4. **Delete before refactor.** Dead code removed first often reveals the remaining shape doesn't need a refactor.
5. **Tests unchanged.** If deletion forces a test change, code wasn't dead — it was under-covered. Escalate.

## Patterns

- **Delete commented block** — ≥ 3 lines, git blame age > 30d, non-WIP commit message → L1.
- **Remove orphan module** — 0 grep importers, no conventional-path match, no string registration → L2. Batch by directory.
- **Retire obsolete flag** — config hard-pinned > 90d. Inline winning branch, delete losing + declaration + branch-specific tests. One PR per flag.
- **Collapse speculative abstraction** — single-impl interface with no plausible second → inline (L3, architect review).
- **Deduplicate utility** — ≥ 2 near-identical functions (`formatMoney` / `priceFormat` / `toMoneyString`) → pick best-named, migrate callers, delete rest. Watch edge cases (rounding, locale).
- **Purge unused dep** — `depcheck` / `npm-check` / `pip-autoremove` / `go mod tidy` + grep confirms. Watch types-only (`@types/*`), peer deps, CI-only tools.
- **Prune zombie tests** — test exists for deleted code, or all `.skip` → delete.

## Anti-patterns

- Sweeping deletions with no evidence column.
- Multi-hundred-line "cleanup" PRs.
- Deleting the only test of a function before deleting the function.
- Mixing formatter-only with logic changes.
- "Just one more" delete mid-review.

## Pitfalls

- "Used by another repo" — grep the org first. External consumers → L3 minimum.
- "Someone might restore" — git remembers. Delete.
- "Used dynamically" — prove with grep on the string name. No evidence → L3, don't skip.
