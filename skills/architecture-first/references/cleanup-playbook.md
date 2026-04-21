# Cleanup playbook

Principles, patterns, and pitfalls of safe code removal. Complements the decomposition playbook.

## Principles

1. **Git remembers, code forgets.** Commented code is noise; if someone needs it, they read history. Delete commented blocks without ceremony (L1).
2. **Reachability is not the same as imports.** DI, decorators, reflection, dynamic strings and convention-based loading all route around static imports. Before declaring unreferenced, rule these out.
3. **One axis per batch.** A cleanup PR should be "delete orphan code" OR "remove unused deps" OR "reformat", not all three. Reviewable diffs get reviewed; big mixed diffs get rubber-stamped.
4. **Delete before refactor.** Removing dead code first often reveals that the remaining shape does not need a refactor at all. Cheap win, earned clarity.
5. **Cleanup PRs ship tests unchanged.** If deleting code forces a test change, the code was not dead — it was under-covered. Escalate to architect.

## Patterns

### Delete commented code block

- **Trigger.** `/*…*/` or `//…` block ≥ 3 lines old enough for context to be lost.
- **Safety.** `git blame` the block; if the commit message is WIP-style or `TODO`, raise to L2 and ask. Otherwise L1.
- **Pitfall.** Deleting a block that documents a workaround with no replacement reference. Check nearby code for the workaround's purpose first.

### Remove orphan module

- **Trigger.** `Grep` finds 0 importers of any export of the file across repo, tests included.
- **Safety.** Rule out: convention paths (Next.js `page.tsx`, Rails `app/`), framework scanning, dynamic require, public library index, string-based registration.
- **Batch.** Group by directory; one PR per top-level module touched.

### Retire obsolete feature flag

- **Trigger.** Config shows the flag is hard-pinned to one value for > 90 days, and code still branches on it.
- **Procedure.** Inline the winning branch, delete the losing branch, delete the flag declaration, delete tests that exercised the losing branch. One PR per flag.
- **Pitfall.** A flag that looks pinned in one environment but diverges in others. Check every environment's config.

### Collapse speculative abstraction

- **Trigger.** Interface / abstract class with exactly one implementation and no plausible second (no other implementation in git history, no open ticket for one).
- **Procedure.** Inline the interface into the concrete. If the interface was used for testing (mock target), replace with a test-only fake or move the seam to the real boundary.
- **Safety level.** L3 — always consult architect. This touches structure.

### Deduplicate utility function

- **Trigger.** Structural grep finds ≥ 2 near-identical functions (`formatMoney`, `priceFormat`, `toMoneyString`).
- **Procedure.** Pick the best-named one in the most appropriate layer. Migrate callers one module at a time. Delete the rest.
- **Pitfall.** Functions that _look_ the same but diverge in edge cases (rounding, locale). Compare test coverage before consolidating; if neither has tests, write one first.

### Purge unused dependency

- **Trigger.** `depcheck` / `npm-check` / `pip-autoremove` / `go mod tidy` flags a package AND grep confirms zero direct usage.
- **Procedure.** Remove from manifest, regenerate lockfile, run full test suite + a build of each deployable.
- **Pitfall.** Types-only deps (`@types/*`), peer deps of other deps, tools invoked only by CI scripts, transitive deps surfaced in tsconfig paths. Check these before removing.

### Prune zombie tests

- **Trigger.** Test file exists but the production code it exercises was deleted, OR all tests are `.skip`.
- **Procedure.** Delete the test file. Do not resurrect skipped tests "for later" — if they mattered, they would not be skipped.

## Pitfalls catalog

- **"It might be used by another repo."** If that repo is in this org, `grep` it. If it is external, it is a published API — L3 at minimum.
- **"Someone might restore this later."** Git remembers. Delete.
- **"It's only a few lines."** A few lines × many files × years = tech debt iceberg.
- **"It's used dynamically."** Maybe. Prove it: grep the string name, check registrations. If no evidence, demote to L3 — do not skip.
- **"Let's also refactor while we're here."** No. One axis per batch.

## Anti-patterns of cleanup itself

- Sweeping deletions with no evidence column.
- Multi-hundred-line diff PRs labelled "cleanup".
- Deleting the only test of a function before deleting the function.
- Mixing formatter-only changes with logic-touching changes.
- Adding "just one more" delete to a batch after review has started.
