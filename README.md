# architecture-first

> Plugin for **Claude Code** and **Cursor IDE**. Turns the model into an architect on demand: ranks hotspots, plans decompositions, ships PRs in isolated git worktrees, cleans dead code with safety levels. Stays out of your way on routine work. Stack-agnostic — NestJS, Next.js, Express, Spring Boot, Django, FastAPI, Laravel, Rails, Go, Rust, and generic layered projects.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

## What it does

- **Non-intrusive by default.** The skill and hook stay silent on routine edits. They activate only when you ask — explicitly ("review architecture", "find hotspots", etc.) or via a `/arch-*` slash command.
- **Hotspot ranking** across the repo (size × churn × cycles × fan-in) with a ranked table whose rows you reference by number.
- **Decomposition planning** for one or many hotspots in parallel. Produces `docs/decomposition/DEC-*.md` files with PR sequences, Mermaid target diagrams, rollout safety.
- **PR execution in a sibling git worktree** — your main checkout stays untouched. Full auto-flow by default: implement → test → build → commit → push → remove worktree. Failure-safe (push fails? worktree stays for retry).
- **Rich preview before implementing.** Before any code, you see Mermaid before/after, file tree, affected callers, tests, risks, alternatives. Four options: `yes | no | show more | tweak: <what to change>` (tweak loops until you're happy).
- **Cleanup manifests** with safety levels L1–L4 — framework-magic aware (DI, decorators, reflection, convention-scanning). Nothing is deleted blindly.
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
/arch-decompose 1-5       # top 5 hotspots in parallel
/arch-decompose ALL       # every row in parallel (quarterly review)
/arch-decompose 1,3,7     # specific rows
/arch-decompose src/foo.ts  # or just a path
```

Each target gets its own `docs/decomposition/DEC-NNN-<slug>.md` — PR sequence, target Mermaid, rollout safety, risks. The summary table at the end has clickable links: Target → opens the source file, DEC file → opens the plan.

> **Cost warning.** `ALL` dispatches N parallel sub-agents = N× tokens. For a normal week, start with `1-3`.

### Step 4 — ship PR-1 of the most urgent plan

```text
/arch-execute 4
```

`/arch-execute` reads `DEC-004`, picks the first unexecuted PR, and shows you a **rich preview**:

- Mermaid before/after diagram with LoC on each node
- Files-touched table with clickable links
- What moves (symbols being relocated)
- Callers that continue to work (backward compat explanation)
- Existing test pins + new tests this PR adds + coverage gaps
- Risks + mitigation
- Alternatives considered (chosen vs rejected, from the DEC)
- Destination (worktree path, branch name, base branch)

Respond with one of four options:

```
yes                         — proceed as shown
no                          — abort, no changes
show more                   — dump the full PR section from the DEC
tweak: <what to change>     — adjust the plan, I'll re-preview
```

On `tweak: <…>`, the preview re-renders with the adjustment applied. Loop until you say `yes`.

### Step 5 — the default auto-flow

On `yes`, the plugin does the whole dance automatically:

```
  1. creates sibling worktree at <repo>.worktrees/DEC-NNN-pr-M-slug/
  2. implements the PR per the plan
  3. runs commands.test + commands.build
  4. commits: refactor(<scope>): <PR title> [DEC-NNN PR-M/total]
  5. git push -u origin refactor/DEC-NNN-pr-M-slug
  6. git worktree remove <path>
```

End result: your main checkout is untouched, the refactor branch sits on `origin` ready for a PR. You get a GitHub compare URL in the report — one click to open the PR.

You keep working on your feature branch the whole time. No merge conflicts, no stashing.

### Step 6 — the next PR

```text
/arch-execute 4 PR-2
/arch-execute 4 next       # explicit "next unexecuted"
```

The plugin tracks which PRs have been executed (in the DEC's Execution log) and picks the next one.

### Step 7 — sweep crust, every few weeks

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

| Command                                  | What it does                                                                    |
| ---------------------------------------- | ------------------------------------------------------------------------------- |
| `/arch-profile-init`                     | One-time per repo: detect stack, generate `.arch-profile.yaml`                  |
| `/arch-hotspot`                          | Rank hotspots; save row state so later commands can use row numbers             |
| `/arch-decompose <path\|N\|A-B\|ALL>`    | Plan decomposition(s); parallel sub-agents when ≥ 2 targets                     |
| `/arch-execute <DEC-N> [PR-M]` `[flags]` | Implement one PR — worktree → test → commit → push → remove (default auto-flow) |
| `/arch-clean [scope]`                    | Cleanup manifest (L1–L4), no deletions                                          |
| `/arch-clean-approve <batch>`            | Execute one cleanup batch                                                       |
| `/arch-review`                           | Fast diff-only architectural review                                             |
| `/arch-describe [scope]`                 | C4 architectural description (Mermaid)                                          |
| `/arch-plan`                             | Freeze current plan as ADR                                                      |
| `/arch-approve [--adr] [--trivial "…"]`  | Unlock edits in strict mode (rarely needed outside strict)                      |

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

| Path                            | When                  | Purpose                                             |
| ------------------------------- | --------------------- | --------------------------------------------------- |
| `.arch-profile.yaml`            | `/arch-profile-init`  | Per-repo calibration. Commit it.                    |
| `docs/decomposition/DEC-*.md`   | `/arch-decompose`     | Decomposition plans. Commit them.                   |
| `docs/cleanup/CLN-*.md`         | `/arch-clean`         | Cleanup manifests. Commit them.                     |
| `docs/adr/ADR-*.md`             | `/arch-plan`, `--adr` | Architectural Decision Records. Commit them.        |
| `$TMPDIR/architecture-first/…`  | hook + state files    | Ephemeral markers, 24h TTL. Never in your repo.     |
| `<repo>.worktrees/DEC-*-pr-*-…` | `/arch-execute`       | Temporary per-PR worktree; auto-removed after push. |

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

## License

Apache 2.0 — see [LICENSE](LICENSE) and [NOTICE](NOTICE).
