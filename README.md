# architecture-first

> Plugin for **Claude Code** and **Cursor IDE**. Turns the model into an architect on demand: ranks hotspots, plans decompositions, ships PRs in isolated git worktrees, cleans dead code with safety levels. Stays out of your way on routine work. Stack-agnostic — NestJS, Next.js, Express, Spring Boot, Django, FastAPI, Laravel, Rails, Go, Rust, and generic layered projects.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

## What it does

- **Non-intrusive by default.** The skill and hook stay silent on routine edits. They activate only when you ask — explicitly ("review architecture", "find hotspots", etc.) or via a `/arch-*` slash command.
- **Bias toward leaving healthy code alone.** Every hotspot gets one of three verdicts — `act` / `defer` / `no-op`. The `no-op` verdict is first-class: when the metrics are misleading, the plugin says **"Це норм. Не чіпай."** / **"Leave it alone."** and stops. No PR plan, no risk table, no ceremony.
- **Anti-pattern heuristics baked in** (`references/known-antipatterns.md`): thin transport adapters, format-churn hotspots, leaf-of-tree fan-in, single-cluster small files, façade-narrowing without cycle proof, speculative reuse. The decomposer runs these before writing any plan and refuses on first match.
- **Hotspot ranking** across the repo (size × **decay-adjusted** churn × cycles × fan-in modules) with a ranked table whose rows you reference by number. Each row carries a likely verdict so you know what `/arch-decompose <N>` will return before you run it.
- **Cleanup-first gate.** When the cleaner finds ≥ 10 L1/L2 items, decomposition is gated behind `/arch-clean`. Dead-code removal often makes several DECs unnecessary.
- **DEC budget cap.** ≤ 3 active DECs (`Status: proposed | in progress`) per repo at a time. New DEC creation blocks until one closes. `no-op` DECs don't count against the budget.
- **Session trigger gate.** First `/arch-*` per session asks: feature-pushed / proactive-cleanup / curiosity. The third option refuses decomposers entirely.
- **Decomposition planning** for one or many hotspots in parallel. Produces `docs/decomposition/DEC-*.md` files with PR sequences, Mermaid target diagrams, rollout safety. `no-op` DECs use a `-noop` suffix and need no further action.
- **PR execution in a sibling git worktree** — your main checkout stays untouched. Full auto-flow by default: implement → test → build → commit → push → remove worktree. Failure-safe (push fails? worktree stays for retry).
- **Rich preview before implementing.** Before any code, you see Mermaid before/after, file tree, affected callers, tests, risks, alternatives. Four options: `yes | no | show more | tweak: <what to change>` (tweak loops until you're happy).
- **Cleanup manifests** with safety levels L1–L4 — framework-magic aware (DI, decorators, reflection, convention-scanning). Nothing is deleted blindly.
- **Honest session-close ledger** via `/arch-session-close` — DECs by status, LOC delta, cycle delta, worth-it-vs-ceremony ratio. Output goes to you, never to the repo.
- **Language mirroring.** Responds in whatever language you're writing in. Keeps identifiers (slash commands, file paths, DEC-IDs, tier names) English.
- **Per-repo calibration** via `.arch-profile.yaml`.

---

## Install

### Claude Code — marketplace (recommended)

```text
/plugin marketplace add Subx1s0o/architecture-first-plugin
/plugin install architecture-first@architecture-first-marketplace
```

Requires Python 3.8+ on `PATH`. Hook auto-registers via `hooks/hooks.json` (no manual `settings.json` editing).

### Cursor IDE — `/add-plugin`

```text
/add-plugin github.com/Subx1s0o/architecture-first-plugin
```

Cursor reads `.cursor-plugin/plugin.json` and wires the rule at `cursor/rules/architecture-first.mdc` plus 10 prompt snippets. See [CURSOR.md](CURSOR.md) for Cursor-specific limitations.

### Fallback — manual script

```bash
git clone https://github.com/Subx1s0o/architecture-first-plugin.git
cd architecture-first-plugin && ./install.sh           # Claude Code
./cursor/install.sh /path/to/your-project              # Cursor, per project
```

### Supported OS

macOS, Linux — native. Windows — via WSL or Git Bash (Python 3.8+ required).

---

## The workflow — how to actually use this

The plugin is built around a **quarterly (or pre-sprint) refactor rhythm**. Do it every few weeks, not every day.

### Step 1 — one-time setup per repo

```text
/arch-profile-init
```

Detects your stack, writes `.arch-profile.yaml`. Open it and fill in three things:

```yaml
default-branch: main # base for /arch-execute worktrees
hot-modules: [billing, auth] # modules where any change forces tier M+ (strict mode)
commands:
  test: npm test # used by /arch-execute to verify before commit
  build: npm run build # same
```

Commit the file. Done.

### Step 2 — see what's rotting

```text
/arch-hotspot
```

You get a ranked table of the top 30 hotspots (size × 90-day churn × cycles × fan-in). Each row has a number. The command also writes a state file to `$TMPDIR/architecture-first/` so later commands can reference rows by number.

### Step 3 — plan refactors for the worst offenders

```text
/arch-decompose 1-3         # top 3 hotspots in parallel
/arch-decompose ALL         # top 3 by rank (capped). --force-all to override.
/arch-decompose 1,3,7       # specific rows
/arch-decompose src/foo.ts  # or just a path
```

**Pre-flight gates run in this order:**

1. **Trigger check** (first `/arch-*` of the session) — asks: feature-pushed (a) / proactive-cleanup (b) / curiosity (c). (c) refuses the decomposer; suggests `/arch-clean` instead.
2. **Cleanup-first gate** — if `cleanup_debt_count >= 10` from the latest `/arch-hotspot` scan and no `/arch-clean` was run in the last 7 days, the command refuses and recommends running `/arch-clean` first. Override: `--skip-cleanup-gate`.
3. **DEC budget cap** — ≤ 3 active DECs per repo. New DEC creation blocks until one closes. Override: `--budget-override "<reason>"` (logged in the session-close ledger).

When the gates pass, each target gets one of three verdicts:

- **`act`** — real hotspot, domain decomposition exists → full DEC at `docs/decomposition/DEC-NNN-<slug>.md`.
- **`defer`** — real hotspot but cost > value right now → 1-section stub with explicit re-open condition.
- **`no-op`** — file is healthy, the metrics are misleading → no-op DEC at `docs/decomposition/DEC-NNN-<slug>-noop.md`. **No PR plan. Plan ends.** The `-noop` suffix makes these visually distinct in `ls`.

The decomposer's bias is toward `no-op`. A scan that returns 3 `no-op`s is a successful scan — it means the codebase is healthier than the metrics suggested. The summary table has a Verdict column; if all rows came back as `no-op`, the command ends with **"Це норм. Усе гаразд. Архітектурно чіпати нічого."** (mirrored to your language).

> **Cost warning.** `ALL` dispatches up to 3 parallel sub-agents = 3× tokens by default. Use `--force-all` to plan every hotspot from the latest scan.

### Step 4 — ship refactors

Three ways, pick by how much you want to babysit:

#### A. One PR at a time (most control)

```text
/arch-execute 4
```

Picks the first unexecuted PR of DEC-004, shows a **rich preview**, waits for you:

- Mermaid before/after diagram with LoC on each node
- Files-touched table with clickable links
- What moves, callers that continue to work, tests, risks, alternatives
- Destination (worktree path, branch name, base branch)

Reply:

```
yes                         — implement this PR only
yes-all                     — escalate to --auto for the whole DEC (see B)
no                          — abort
show more                   — dump the full PR section from the DEC
tweak: <what to change>     — adjust the plan, I'll re-preview
```

On `yes`: worktree → implement → tests → commit → push → remove worktree. You get a GitHub compare URL. Continue with `/arch-execute 4 PR-2` when ready.

#### B. Whole DEC in one shot (recommended for clear plans)

```text
/arch-execute 4 --auto
```

One preview up front showing every PR in DEC-004. On `yes-all`:

```
1. create ONE worktree at <repo>.worktrees/DEC-004-<slug>/
2. create ONE branch refactor/DEC-004-<slug>
3. for each PR 1..N:
     implement → tests + build → commit
4. git push -u origin refactor/DEC-004-<slug>
5. remove worktree
```

N commits on one branch, one PR on GitHub spanning the whole decomposition. Push the button, get coffee.

#### C. Every DEC in the repo (quarterly tech-debt sprint)

```text
/arch-execute ALL --auto
```

Walks every `docs/decomposition/DEC-*.md` with unexecuted PRs. Each DEC gets its own worktree + branch. Single `yes-all-decs` confirmation at the top, then the plugin marches through the whole queue. Stops on the first failure (whichever DEC/PR breaks) with a report of what shipped and what remains.

#### Failure handling (all three modes)

- **Test or build fails** → auto-run halts at that PR; worktree stays on disk with prior commits; report shows which PR failed + first 40 lines of output. Fix manually, resume with `/arch-execute <N> PR-<failed> --inplace` from inside the worktree.
- **Push fails** (auth / protected branch / non-ff) → worktree stays, commits preserved, retry manually.
- **Execution log is updated per-PR**, so partial progress survives any abort.

### Step 5 — sweep crust, every few weeks

```text
/arch-clean
```

Cleanup manifest in `docs/cleanup/CLN-NNN.md`, organized by safety level:

- **L1** (trivially safe) — debug logs, old commented code, local unused vars. Merge alone.
- **L2** (likely safe) — orphan files, unused deps, obsolete flags > 90 days. One-axis batches.
- **L3** (investigate) — may be reachable via DI / decorators / reflection / conventions. Consult architect.
- **L4** (architect decides) — dormant handlers, feature-flagged code. Requires an ADR.

Execute a specific batch:

```text
/arch-clean-approve CLN-001-batch-B
```

Claude lists every file to delete with evidence, asks `yes`, deletes, runs tests+build, appends the manifest. Fails-safe with `git restore` on any test failure.

---

## Commands

| Command                                  | What it does                                                                                              |
| ---------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `/arch-profile-init`                     | One-time per repo: detect stack, generate `.arch-profile.yaml`                                            |
| `/arch-hotspot`                          | Rank hotspots (decay-adjusted churn); also tallies cleanup debt; saves row state for later commands       |
| `/arch-decompose <path\|N\|A-B\|ALL>`    | Plan decomposition(s); emits `act` / `defer` / `no-op` verdict per target; gated on cleanup + DEC budget  |
| `/arch-session-close [<N>d]`             | Honest session ledger — DECs by status, LOC/cycle delta, worth-it-vs-ceremony ratio. Conversational only. |
| `/arch-execute <DEC-N> [PR-M]` `[flags]` | One PR: worktree → test → commit → push → remove                                                          |
| `/arch-execute <DEC-N> --auto`           | Whole DEC on one branch, N commits, no prompts between PRs                                                |
| `/arch-execute ALL --auto`               | Every DEC with unexecuted PRs, each in its own branch                                                     |
| `/arch-clean [scope]`                    | Cleanup manifest (L1–L4), no deletions                                                                    |
| `/arch-clean-approve <batch>`            | Execute one cleanup batch                                                                                 |
| `/arch-review`                           | Fast diff-only architectural review                                                                       |
| `/arch-describe [scope]`                 | C4 architectural description (Mermaid)                                                                    |
| `/arch-plan`                             | Freeze current plan as ADR (only on real X-vs-Y forks; never preemptive Phase-0 spec)                     |
| `/arch-approve [--adr] [--trivial "…"]`  | Unlock edits in strict mode (rarely needed outside strict)                                                |

### `/arch-decompose` flags

| Flag                           | Effect                                                                         |
| ------------------------------ | ------------------------------------------------------------------------------ |
| _(none)_                       | Run all pre-flight gates; emit verdict per target                              |
| `--force-all`                  | Bypass the top-3 cap on `ALL`                                                  |
| `--skip-cleanup-gate`          | Bypass the cleanup-first gate (when `cleanup_debt_count ≥ 10`)                 |
| `--budget-override "<reason>"` | Bypass the active-DEC budget cap; reason is logged in the session-close ledger |

### `/arch-execute` flags

| Flag              | Effect                                                              |
| ----------------- | ------------------------------------------------------------------- |
| _(none)_          | Full auto: commit + push + remove worktree                          |
| `--no-push`       | Commit only, keep worktree, push manually later                     |
| `--keep`          | Push, but keep worktree for manual review                           |
| `--inplace`       | No worktree — mutate current checkout; no push either               |
| `--base <branch>` | Base the refactor branch off `<branch>` instead of the repo default |

---

## Configuration — `.arch-profile.yaml`

Generated by `/arch-profile-init`. Full example:

```yaml
default-branch: main

# Opt into hard hook gate — blocks every significant edit until /arch-approve.
# Off by default; leave false unless you want strict discipline.
strict-gate: false

# Modules where any change forces tier M+ (only in strict mode).
hot-modules: [billing, auth, payments]

# Allowed direct-import edges (only in strict mode).
allowed-module-edges:
  orders: [billing, inventory]

# Thresholds override stack-profile defaults.
thresholds:
  file-loc: { warn: 400, xl: 600 }
  fn-loc: { warn: 60, xl: 100 }
  fan-in: { warn: 15, xl: 25 }
  churn-20: { warn: 4, xl: 7 }

# Used by /arch-execute and /arch-clean-approve to verify before commit.
commands:
  test: npm test
  build: npm run build
  lint: npm run lint
```

---

## What gets written where

| Path                               | When                  | Purpose                                                                                           |
| ---------------------------------- | --------------------- | ------------------------------------------------------------------------------------------------- |
| `.arch-profile.yaml`               | `/arch-profile-init`  | Per-repo calibration. Commit it.                                                                  |
| `docs/decomposition/DEC-*.md`      | `/arch-decompose`     | `act` / `defer` decomposition plans. Commit them.                                                 |
| `docs/decomposition/DEC-*-noop.md` | `/arch-decompose`     | `no-op` verdicts — explanation of why a file is healthy. Commit them so the next scan knows.      |
| `docs/cleanup/CLN-*.md`            | `/arch-clean`         | Cleanup manifests. Commit them.                                                                   |
| `docs/adr/ADR-*.md`                | `/arch-plan`, `--adr` | ADRs — only on real X-vs-Y forks. Commit them.                                                    |
| `$TMPDIR/architecture-first/…`     | hook + state files    | Ephemeral markers (hotspot state, trigger answer, active-DEC index, 24h TTL). Never in your repo. |
| `<repo>.worktrees/DEC-*-pr-*-…`    | `/arch-execute`       | Temporary per-PR worktree; auto-removed after push.                                               |

---

## Default mode vs. strict mode

|                                                                      | Default (non-intrusive)              | Strict (`strict-gate: true` in profile) |
| -------------------------------------------------------------------- | ------------------------------------ | --------------------------------------- |
| Skill auto-trigger on routine edits                                  | no                                   | no                                      |
| Hook blocks `Edit`/`Write` on architectural changes                  | no — only mass deletions ≥ 200 lines | yes — unless `/arch-approve`            |
| Hook blocks mass deletions ≥ 200 lines without `/arch-clean-approve` | **yes**                              | **yes**                                 |
| `/arch-*` commands                                                   | all available                        | all available                           |

Most users should stay on default. Turn strict on only if you want hard discipline for a team.

---

## Claude Code vs. Cursor

|                                        | Claude Code          | Cursor                             |
| -------------------------------------- | -------------------- | ---------------------------------- |
| Skill triggers on explicit ask         | ✅                   | ✅ (rule with `alwaysApply: true`) |
| `PreToolUse` hook (mass-deletion gate) | ✅                   | ❌ — not supported                 |
| Parallel sub-agents                    | ✅ (real parallel)   | ❌ (sequential)                    |
| Slash commands                         | ✅ native            | 🟡 Notepads or paste-from-snippet  |
| Global install                         | ✅ (once, all repos) | per-project                        |

Cursor users: enable Notepads in Settings → Features to get `/arch-*`-like invocation via `@arch-hotspot`, `@arch-execute`, etc.

---

## Storage footprint

Markers live under the OS temp dir (`$TMPDIR` / `%TEMP%`), **never in your repo**. They auto-expire after 24h. Each marker is ~0 bytes. No daemons, no logs, no background processes.

---

## Troubleshooting

- **`BLOCKED: mass deletion`** — you're trying to remove ≥ 200 lines. Either it's intentional (run `/arch-clean` → `/arch-clean-approve <batch>`) or the model is doing something unplanned (abort).
- **`BLOCKED: no approved plan` (strict mode only)** — produce the 4-step response, then `/arch-approve`.
- **Hook not firing** — re-run `./install.sh` (idempotent).
- **Skill doesn't trigger** — ask explicitly: "review the architecture of …", "find hotspots", "decompose …". Or use a `/arch-*` command directly.
- **`/arch-execute` push failed** — worktree stays on disk. Fix the push issue (auth, upstream, protected branch), then `cd <worktree> && git push -u origin <branch>` manually. Commit is recorded either way.
- **Leftover worktree** — `git worktree remove <path>` (or `--force` if needed).

---

## Update

```bash
cd architecture-first-plugin && git pull && ./install.sh
```

## Uninstall

```bash
./uninstall.sh
```

## Contributing

PRs welcome — especially new stack profiles. Copy `skills/architecture-first/references/stack-profiles/generic-layered.md`, fill in layer names, thresholds, and anti-patterns. Add a detection row to `_detect.md`.

## Updating the plugin

When a new version is released:

### Claude Code — marketplace install

```text
/plugin marketplace update architecture-first-marketplace
/plugin install architecture-first@architecture-first-marketplace --update
```

### Claude Code — manual install (via `./install.sh`)

```bash
cd /path/to/architecture-first-plugin
git pull origin main
./install.sh          # idempotent — refreshes files, de-dupes hook entry
```

### Cursor IDE

Cursor picks up `.cursor/rules/*.mdc` and `.cursor-plugin/plugin.json` on restart. To refresh prompt snippets in a project:

```bash
cd /path/to/architecture-first-plugin
git pull origin main
./cursor/install.sh /path/to/your-project
```

After restart, Cursor reloads the rule. Notepads you saved from snippets won't auto-update — re-import from the new `.cursor/prompts-architecture-first/*.md` if you use them.

### Optional: pre-commit LoC gate

Zero-LLM Python script in `hooks/arch-precommit-check.py` that warns when a staged source file approaches / crosses the hotspot threshold from `.arch-profile.yaml`.

Install once per repo (Husky-style example):

```bash
ln -sf ~/.claude/plugins/architecture-first/hooks/arch-precommit-check.py .husky/arch-check
echo './.husky/arch-check' >> .husky/pre-commit
```

Add `precommit: warn-only` to `.arch-profile.yaml` if you want warnings without blocking commits past the XL threshold.

## License

Apache 2.0 — see [LICENSE](LICENSE) and [NOTICE](NOTICE).
