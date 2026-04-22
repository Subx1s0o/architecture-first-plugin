# architecture-first

> Plugin for **Claude Code** and **Cursor IDE**. Makes the model think like an architect and a code janitor in the same pass — before writing code. Works with NestJS, Next.js, Express, Spring, Laravel, Django, FastAPI, Rails, Go, Rust, and generic layered projects.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

## What it does

- Forces a 4-step response: **Situation → Plan → File Structure → Code**. Code is blocked until you approve the plan.
- Reasons about **architecture** and **hygiene** (dead code, orphans, unused deps) in one go.
- Ranks repo **hotspots** (size × churn × cycles × fan-in) and plans safe decompositions.
- Produces **cleanup manifests** with safety levels L1–L4 — never deletes blindly.
- Per-repo calibration via `.arch-profile.yaml`.

## Install

### Claude Code — via marketplace (recommended)

In Claude Code, run:

```text
/plugin marketplace add Subx1s0o/architecture-first-plugin
/plugin install architecture-first@architecture-first-marketplace
```

The hook auto-registers via `hooks/hooks.json` using `${CLAUDE_PLUGIN_ROOT}` — no manual `settings.json` editing. Requires Python 3.8+ on `PATH`.

### Cursor IDE — via `/add-plugin` (recommended)

In Cursor, run:

```text
/add-plugin github.com/Subx1s0o/architecture-first-plugin
```

Cursor reads `.cursor-plugin/plugin.json` and wires up the rule at `cursor/rules/architecture-first.mdc` plus the 9 prompt snippets under `cursor/prompts/`.

For Cursor's limitations (no hard hook, no parallel sub-agents) see [CURSOR.md](CURSOR.md).

### Fallback — manual install via script

If you don't use marketplaces, clone and run the installer:

```bash
git clone https://github.com/Subx1s0o/architecture-first-plugin.git
cd architecture-first-plugin && ./install.sh                 # Claude Code
./cursor/install.sh /path/to/your-project                     # Cursor per project
```

### Uninstall

Claude Code: `/plugin uninstall architecture-first` (or `./uninstall.sh` if installed manually).
Cursor: remove `.cursor/rules/architecture-first.mdc` and `.cursor/prompts-architecture-first/` from the project.

## Commands

| Command                       | What it does                                                           |
| ----------------------------- | ---------------------------------------------------------------------- |
| `/arch-profile-init`          | One-time per repo: detect stack, create `.arch-profile.yaml`           |
| `/arch-hotspot`               | Rank architectural hotspots                                            |
| `/arch-decompose <path>`      | Plan a safe decomposition for one hotspot                              |
| `/arch-clean [scope]`         | Produce a cleanup manifest (L1–L4)                                     |
| `/arch-clean-approve <batch>` | Execute a cleanup batch                                                |
| `/arch-review`                | Quick diff review                                                      |
| `/arch-describe [scope]`      | C4 architectural description                                           |
| `/arch-plan`                  | Freeze the current plan as an ADR                                      |
| `/arch-approve`               | Unlock edits for this session (optional: `--adr` to also write an ADR) |

### How each command works

<details>
<summary><code>/arch-profile-init</code> — detect the stack, generate <code>.arch-profile.yaml</code> (one-time)</summary>

1. Reads project root: `package.json`, `pyproject.toml`, `go.mod`, `Gemfile`, `composer.json`, `pom.xml`, `Cargo.toml`, etc.
2. Matches the first signature against `_detect.md` → picks a profile (NestJS, Next.js, Spring Boot, Django, FastAPI, Laravel, Rails, Go, Rust, or generic-layered).
3. Copies `arch-profile.yaml.tmpl` to `<repo>/.arch-profile.yaml`.
4. Pre-fills `layers` (canonical names for the stack), `modules` (top-level dirs under `src/`), `thresholds` (stack defaults).
5. Leaves `hot-modules`, `allowed-module-edges`, `commands.test/build`, and `glossary` empty with hints — you fill them in.
6. Refuses to overwrite if the file already exists; prints a diff instead.

</details>

<details>
<summary><code>/arch-hotspot</code> — rank architectural hotspots across the repo</summary>

1. Loads the stack profile and `.arch-profile.yaml` thresholds (falls back to defaults).
2. **Tier 0** — top 30 files by LoC (`wc -l`); top 30 by 90-day churn (`git log`).
3. **Tier 1** — fan-in via grep on top-20 exports; cycles via `madge --circular` (JS/TS) or `pydeps --show-cycles` (Python) if available. Skips silently if the tool is missing.
4. Cross-references: files in both top-size **and** top-churn = **primary** hotspots. Churn only = secondary. Size only = tertiary.
5. For each primary, reads the file and counts distinct verb-object clusters in public exports (responsibility heterogeneity).
6. Produces one ranked table: `Rank | Path | Size | Churn | Cycle? | Smell | Suggested pattern`.
7. Writes nothing. Suggests `/arch-decompose <path>` for any row you want to dig into.

</details>

<details>
<summary><code>/arch-decompose &lt;path&gt;</code> — safe decomposition plan for one hotspot</summary>

1. Resolves the path (file, directory, or module name).
2. Dispatches the `hotspot-decomposer` sub-agent with the path + stack profile + `.arch-profile.yaml`.
3. Sub-agent confirms hotspot via the detection pyramid (evidence table with reproducible commands).
4. Picks a pattern from the playbook via the decision tree — production-running code prefers Strangler Fig or Branch by Abstraction.
5. Produces: evidence table, chosen pattern + why, target Mermaid diagram, PR sequence (≤ 5 PRs), rollout safety (flags, canary, parity), sunset date, risks.
6. Writes `docs/decomposition/DEC-<N>-<slug>.md`.
7. Ends with three options: **proceed** / **defer (ticket it)** / **patch-in-place (accept the debt, log an ADR)**.

</details>

<details>
<summary><code>/arch-clean [scope]</code> — cleanup manifest, no deletions</summary>

1. Loads the stack profile and thresholds.
2. Resolves scope — path argument or the whole repo.
3. Dispatches the `cleaner` sub-agent. It scans for dead code, orphan files, obsolete flags, unused deps, zombie tests, stale TODOs, speculative abstractions, duplicate utilities.
4. Before declaring anything "unreferenced", rules out framework-magic reach paths (DI, decorators, reflection, convention-scanning, string-name dispatch, public library index). Raises safety level on any uncertainty.
5. Classifies every finding **L1** (trivially safe), **L2** (likely safe), **L3** (investigate — needs architect), **L4** (architect-only, requires ADR).
6. Groups into batches — one axis per batch (formatting vs orphan code vs deps vs flags).
7. Writes `docs/cleanup/CLN-<N>-<slug>.md` with 4 tables + proposed batches. Every row has a reproducible evidence command.

</details>

<details>
<summary><code>/arch-clean-approve &lt;batch-id&gt;</code> — execute one cleanup batch</summary>

1. Locates the manifest under `docs/cleanup/`; reads the named batch.
2. Refuses if the batch contains any L3/L4 finding — those need `/arch-review` first.
3. Lists every file and line-range the batch will delete with per-row evidence; asks for explicit "yes".
4. Writes an ephemeral cleanup marker under `$TMPDIR/architecture-first/` so the hook allows the mass deletion for this batch only.
5. Executes the deletions: L1 edits / `git rm` for L2 orphans / manifest edits + lockfile regen for L2 deps.
6. Runs `commands.test` and `commands.build` from `.arch-profile.yaml`. On failure: `git restore` and report.
7. Appends the manifest with `Status: executed on <date>, commit <sha>` and the test/build result.

</details>

<details>
<summary><code>/arch-review</code> — quick diff-only review (no sub-agent)</summary>

1. Runs `git diff --stat` and `git diff` (staged + unstaged).
2. For each changed source file: identifies module and layer via `.arch-profile.yaml` or the stack profile.
3. Flags: imports from another module's internals (not its barrel), new event emits without a subscriber, new queue jobs without a processor, duplicated external calls, files past the LoC threshold, new cycles introduced by the diff.
4. Produces a table: `Severity | Location | Finding | Suggested seam`.
5. Writes nothing. Suggests `architect-reviewer` sub-agent if findings are deep enough to warrant it.

</details>

<details>
<summary><code>/arch-describe [scope]</code> — C4 architectural description</summary>

1. Loads the stack profile and `.arch-profile.yaml` if present.
2. Stops at the smallest useful C4 level — Context (external systems), Containers (cross-container), Components (module-level), Code (single unit).
3. Uses Mermaid for levels 2–3.
4. For module scope, ends with an "Intent vs. Reality" section if `.arch-profile.yaml`'s `allowed-module-edges` disagrees with what grep actually shows.

</details>

<details>
<summary><code>/arch-plan</code> — freeze the current plan as an ADR</summary>

1. Reads the latest architectural plan from the conversation (sections 1–3 of the 4-step response).
2. Populates `ADR.md.tmpl` with Context (from Situation), Decision (from Plan), Consequences, Alternatives Considered.
3. Writes `docs/adr/ADR-<N>-<slug>.md`.
4. Mirrors to an Obsidian vault if the `repo-vault-routing` skill is installed.
5. Does **not** unlock the hook — this persists intent, not authority. Use `/arch-approve` to proceed to code.

</details>

<details>
<summary><code>/arch-approve</code> — unlock edits for this session</summary>

Three forms, all touch an ephemeral marker under `$TMPDIR/architecture-first/`:

1. **`/arch-approve`** — bare. Touch the marker. Confirm `✓ Edit gate lifted.`
2. **`/arch-approve --adr`** — also write `docs/adr/ADR-<N>-<slug>.md` from the current plan.
3. **`/arch-approve --trivial "<reason>"`** — optional bypass reason, logged but not persisted as an ADR.

The marker expires after 24h and lives only in the OS temp dir — never in your project tree.

</details>

## Workflow

**The plugin stays out of your way by default.** It does not auto-invoke itself on routine edits — you ask for it when you want it.

1. For routine work (bug fixes, small features, typos) — just code normally. The skill is silent, the hook only protects against mass deletion (≥ 200 lines).
2. For architectural work — ask explicitly: "review the architecture of X", "plan a refactor of Y", "find hotspots", "decompose this file", "write an ADR", or run any `/arch-*` command.
3. The skill then produces the 4-section response (Situation → Plan → Structure → Code). Confirm the plan, Claude writes the code.

### Strict mode (opt-in)

If you want the old hard-gate behaviour — every significant change blocked until you approve the plan — add `strict-gate: true` to `.arch-profile.yaml`, or run one session with `ARCH_STRICT=1`. In strict mode `/arch-approve` unlocks the session for significant edits.

### What counts as "trivial" (auto-passes)

| Signal          | Threshold                                                                                           |
| --------------- | --------------------------------------------------------------------------------------------------- |
| Diff size       | ≤ 30 lines affected                                                                                 |
| File size       | ≤ 400 LoC                                                                                           |
| Docs / config   | any `.md`, `.txt`, `.json`, `.yaml`, `.toml`, `.env`                                                |
| Tests           | paths under `tests/`, `__tests__/`, or files ending in `.spec.ts`, `.test.py`, `_test.go`, etc.     |
| Build artefacts | anything under `dist/`, `build/`, `.next/`, `node_modules/`, `__pycache__/`, `coverage/`, `target/` |
| New file        | ≤ 50 lines (small utility / config)                                                                 |

### What counts as "significant" (requires `/arch-approve`)

- Any file ≥ 500 LoC (likely hotspot).
- Any diff > 30 lines.
- New files > 50 lines (likely new module/feature).
- Anything under `migrations/` or `schema/`.
- Mass deletion ≥ 200 lines — requires `/arch-clean-approve <batch>` regardless of plan approval.

Thresholds are tuned deliberately permissive — daily bug fixes and feature tweaks flow through. The gate only speaks up when the change has real architectural weight.

## Configuration

`/arch-profile-init` generates `.arch-profile.yaml`. Fill in:

```yaml
hot-modules: [billing, auth] # any change here forces tier M+
allowed-module-edges:
  orders: [billing, inventory] # direct imports allowed; rest via events
commands:
  test: npm test
  build: npm run build
```

Commit the file.

## How it behaves

|                         | Claude Code | Cursor                    |
| ----------------------- | ----------- | ------------------------- |
| Skill auto-triggers     | ✅          | ✅                        |
| Hard `Edit` gate (hook) | ✅          | ❌ (soft, rule text only) |
| Parallel sub-agents     | ✅          | ❌ (sequential)           |
| Slash commands          | ✅          | 🟡 snippets / Notepads    |

## Storage footprint

Session markers live under the OS temp dir (`$TMPDIR` / `%TEMP%`), **never in your repo**. They auto-expire after 24 hours. Each marker is ~0 bytes. No daemons, no logs, no background processes.

## Troubleshooting

- **`BLOCKED: no approved plan`** — run `/arch-approve` after the plan looks right. No args needed.
- **Hook not firing** — re-run `./install.sh` (idempotent).
- **Skill doesn't trigger** — the request was too short. Add context like "in module X".

## Update

```bash
cd architecture-first-plugin && git pull && ./install.sh
```

## Contributing

PRs welcome — especially new stack profiles. Copy `skills/architecture-first/references/stack-profiles/generic-layered.md`, fill in layer names, thresholds, and anti-patterns. Add a detection row to `_detect.md`.

## License

Apache 2.0 — see [LICENSE](LICENSE) and [NOTICE](NOTICE).
