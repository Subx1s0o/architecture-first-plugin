# Cleanup playbook

Principles and patterns for safe code polish + deletion. Companion to decomposition-playbook.

## Principles

1. **No quota.** Zero findings on a clean module is success. Inventing marginal findings to fill a PR is the bigger sin than missing real ones — humans push back on noise, and noise destroys trust in the bot.
2. **Idempotency over breadth.** A module polished today should stay silent tomorrow unless its content changes. Use a ledger (e.g. `.arch-polish.json` keyed by git blob SHA) so the bot doesn't re-scan stable code.
3. **Git remembers, code forgets.** Delete commented blocks without ceremony (L1).
4. **Reachability ≠ imports.** DI, decorators, reflection, convention-scanning all route around static imports. Rule them out first (see `references/framework-magic.md`).
5. **One axis per batch.** A polish PR is visibility OR unused exports OR deletions — never mixed. Single axis = single mental model for the reviewer.
6. **Delete before refactor.** Dead code removed first often reveals the remaining shape doesn't need a refactor.
7. **Tests unchanged.** If a polish forces a test change, the code wasn't dead/private — it was under-covered or genuinely public. Escalate, don't paper over.
8. **Mechanical only.** Every polish action must be applicable without judgment. If "this might be cleaner" needs a taste call, it's not for the cleaner — it's for `/arch-decompose`.

## Patterns

### Mechanical refactors (M-class)

- **M1 Tighten visibility** — `public` member with 0 external callers → `private`. Skip framework-decorator-bound methods (see `framework-magic.md`).
- **M2 Drop unused export** — `export X` with 0 importers → strip the `export` keyword.
- **M3 Dead branch** — `if (false)`, code after `return`, empty `catch {}` swallowing → remove.
- **M4 Inline single-use private** — private helper ≤ 10 LOC with exactly 1 caller in same file → inline at call site.
- **M5 Hoist repeated literal** — same literal ≥ 3 times in a file → extract to const.
- **M6 `let` → `const`** — never reassigned `let` → `const`.

### Deletions (L-class)

- **L1 Delete commented block** — ≥ 3 lines, git blame age > 30d, non-WIP commit message.
- **L1 Delete dead import line** — full `import` line where no imported name is referenced.
- **L1 Delete zombie test** — `.skip`'d test for a function that no longer exists.
- **L2 Remove orphan module** — 0 grep importers, no conventional-path match, no string registration. Batch by directory.
- **L2 Retire obsolete flag** — config hard-pinned > 90d. Inline winning branch, delete losing + declaration + branch-specific tests. One PR per flag.
- **L3 Collapse speculative abstraction** — single-impl interface with no plausible second → inline (architect review).
- **L2 Deduplicate utility** — ≥ 2 near-identical functions → pick best-named, migrate callers, delete rest.
- **L2 Purge unused dep** — `depcheck` / `npm-check` / `pip-autoremove` / `go mod tidy` + grep confirms. Watch types-only, peer deps, CI-only tools.

## Anti-patterns

- **Cosmetic noise as L1.** Trailing whitespace, parameter renames `_data`, formatting drift — these are formatter/linter jobs. NEVER ship as cleanup.
- **Quota-filling.** "I have to find at least 3 things." No, you don't. Empty manifest is a valid outcome.
- Sweeping deletions with no evidence column.
- Multi-hundred-line "cleanup" PRs.
- Deleting the only test of a function before deleting the function.
- Mixing formatter-only with logic changes.
- Mixing M-classes within one PR (visibility + unused-export in same diff).
- "Just one more" delete mid-review.
- Re-scanning stable modules every cron run (use the ledger).

## Pitfalls

- "Used by another repo" — grep the org first. External consumers → L3 minimum.
- "Someone might restore" — git remembers. Delete.
- "Used dynamically" — prove with grep on the string name. No evidence → L3, don't skip.
- "It might be needed for testing" — if the test would break, the code isn't dead. Don't M2/M1 it.
- "Could be private" but the class implements an interface — interface members can't be private. Skip.
