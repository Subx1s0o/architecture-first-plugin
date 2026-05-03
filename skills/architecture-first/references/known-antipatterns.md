# Known anti-patterns — checks before recommending decomposition

Heuristics carried across repositories. The decomposer agent runs these **before** writing a plan. If any heuristic fires with `no-op`, the agent emits the no-op template and stops — it does not "see if there's still something worth extracting".

These exist because the same false-positive shapes appear in every codebase. Bake the lessons in once; don't relearn per repo.

---

## H1. Thin transport adapter

**Shape.** A class/file whose body is mostly `await client.<method>(args)` calls — JSON-RPC envelope wrapping, HTTP-client method, message-bus publish, gRPC stub. Typically 300–700 LOC of nearly-uniform shape.

**Why decomposer false-positives on it.** Fan-in is high (every module that talks to the external system imports it), LoC may be high. The heuristic-only signals scream "god dependency". But the file has no business logic to untangle — it's a pure passthrough.

**Detection.**

```bash
# Ratio of lines matching the transport-call shape to total non-trivial lines
TOTAL=$(grep -cvE '^\s*(\*|//|$|import|export\s+\{|\})' <file>)
TRANSPORT=$(grep -cE 'await\s+this\.\w+\.(invoke|call|emit|send|publish|request|query|mutate|fetch|get|post)\(' <file>)
RATIO=$(echo "scale=2; $TRANSPORT / $TOTAL" | bc)
```

If `RATIO > 0.4` AND no validation/branching is visible in a quick scan (no `if (` outside the transport-call ladder, no `switch`, no `throw new <Domain>Exception`), default to **no-op**.

**Override conditions.** A transport adapter is decomposable if and only if:

- Multiple distinct external services are bundled into one file (split by service, not by method).
- The adapter performs domain-level orchestration on top of transport (e.g. retry policy + circuit breaker + business-level fallback) — and that logic itself has multiple concerns.

**Example refusals.**

- `V4TransportService` (600 LOC of `await this.client.invoke(...)`).
- `MarginRpcClient`, `WalletsRpcClient` style adapters.
- Generated SDK clients (never touch).

---

## H2. Format-churn hotspot

**Shape.** A file with high raw 90-day churn whose commit history is dominated by formatter / linter / arch-bot / merge commits, not product changes.

**Why decomposer false-positives on it.** Raw `git log --oneline | wc -l` blindly counts every commit, including pure-format passes that touch every file in a directory.

**Detection — decay-adjusted churn.**

```bash
RAW=$(git log --since=90.days --oneline -- <file> | wc -l)
PRODUCT=$(git log --since=90.days --oneline -- <file> \
  | grep -vE 'arch-bot|chore\(format\)|chore: strip|chore: prettier|chore: lint|^[0-9a-f]+ Merge ' \
  | wc -l)
```

If `RAW > 7` (warn threshold) but `PRODUCT ≤ 1`, the churn is artifact — default to **no-op** unless other tier-0/1 signals also fire.

**Override conditions.** None — if product-driven churn is below 2, the file is stable in the way that matters.

---

## H3. Leaf-of-tree fan-in

**Shape.** A file with many importers, but every importer lives within a single module subtree (e.g. all importers are under `src/portfolios/`).

**Why decomposer false-positives on it.** Fan-in is counted globally by grep; the heuristic doesn't ask whether the importers are domain-local.

**Detection.**

```bash
# Top-level dirs that import the file
git grep -l "<symbol>\|from\s+['\"].*<file-stem>['\"]" \
  | awk -F/ '{ print $1"/"$2 }' | sort -u | wc -l
```

If the answer is **1** (all importers are inside a single module subtree), the high fan-in is structural — the file is the module's well-named internal hub. Default to **no-op**.

**Override conditions.** Fan-in becomes a real smell when ≥ 3 distinct top-level modules import the file. Then it's a god dependency that crosses bounded contexts.

---

## H4. Single-cluster small file

**Shape.** File < 300 LOC with exactly one responsibility cluster (one verb-object group at the public surface).

**Why decomposer false-positives on it.** Even short files can hit churn or fan-in thresholds. The decomposer agent has no "this is fine, just small and busy" verdict by default.

**Detection.** Open the file, list public methods/exports, group by verb-object. If **all** public surface fits one cluster (e.g. all methods are about "validate followers" or "format display name"), and LoC < 300, this file is doing one thing well.

Default to **no-op** unless:

- Cycle exists.
- ≥ 3 distinct module-level subtrees import it (H3 inverted).

---

## H5. Already-decomposed file

**Shape.** File whose recent history shows a successful prior decomposition (`refactor(...)` or `[DEC-NNN PR-X/Y]` in commit messages within last 30 days) and whose current shape is the post-decomposition steady state.

**Why decomposer false-positives on it.** Post-decomposition, signals can briefly stay elevated as callers migrate, before settling.

**Detection.**

```bash
git log --since=30.days --oneline -- <file> \
  | grep -cE 'refactor\(|DEC-[0-9]+'
```

If the answer is **≥ 2** and the file's structure matches the playbook pattern claimed in those commits, default to **no-op** with note: "soak window — re-evaluate after 30 days post last refactor".

---

## H6. Test-only / dev-only file

**Shape.** File under `tests/`, `__tests__/`, `*.spec.*`, `*.test.*`, `examples/`, `scripts/`, `tools/`. Or a top-level `*-example.*`, `*-mock.*`, `*-fixture.*`.

**Why decomposer false-positives on it.** Hotspot scanners may not exclude these by default.

**Default to no-op.** Test files don't get decomposition DECs. They get refactored organically when the production code they cover changes.

---

## H7. Façade-narrowing-without-cycle-evidence

**Shape.** A proposed DEC whose pattern is "narrow module exports" / "introduce façade" / "wrap operations in a service" — and whose claimed benefit is "module exports go from N → M".

**Why this is an anti-pattern.** Module-level cycles in NestJS / Spring / Angular / Nx are formed by `forwardRef(() => OtherModule)` or analogous in `imports:` arrays. They cannot be broken by symbol-level export narrowing. If a façade DEC doesn't rewire `imports:`, it cannot reduce cycle count.

**Refusal rule.** Any DEC whose pattern involves "narrowing exports" or "façade" must declare:

- **Cycles affected: N** (verified by `madge --circular` before/after).
- **OR** specific named caller pain (failing tests, PR comments, onboarding confusion) — never `exports:` count alone.

If neither evidence is present, the DEC must be `no-op` with note: "façade-narrowing without cycle proof or caller pain is cosmetic".

---

## H8. Speculative reuse

**Shape.** A proposed DEC whose pattern is "extract shared utility" / "pull common base" — but the supposed second consumer doesn't exist yet.

**Why this is an anti-pattern.** Collapsing two similar files into one shared abstraction by speculation locks in the wrong shape; the real second use case usually wants something different.

**Refusal rule.** Don't propose extraction unless ≥ 2 actual implementations exist today. Three similar lines is better than a premature abstraction.

---

## How the decomposer uses this file

Before writing any DEC plan, run through H1–H8 in order. The first heuristic that fires with `no-op` wins; emit the no-op template and stop.

Multiple heuristics firing → strong no-op (decomposer should refuse to write a plan even if user re-asks within the same session). User can override via `/arch-decompose <path> --force`, but the `--force` flag is logged and surfaces in the session-close ledger.

**The bias is toward no-op.** False-positive decompositions cost more than missed real ones — the missed ones get re-flagged on next scan, the false ones ship code and have to be reverted (PR #53 in the copy_trading_service retrospective).
