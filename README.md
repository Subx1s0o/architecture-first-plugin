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

### Claude Code

```bash
git clone https://github.com/Subx1s0o/architecture-first-plugin.git
cd architecture-first-plugin && ./install.sh
```

Requires Python 3.8+, bash, git. Works on macOS, Linux, and Windows (WSL/Git Bash).

### Cursor IDE (per project)

```bash
cd /path/to/your-project
/path/to/architecture-first-plugin/cursor/install.sh
```

Commit `.cursor/` so your team gets the same guardrail. For details on Cursor limitations (no hook, no parallel agents) see [CURSOR.md](CURSOR.md).

### Uninstall

```bash
./uninstall.sh
```

## Commands

| Command                         | What it does                                                 |
| ------------------------------- | ------------------------------------------------------------ |
| `/arch-profile-init`            | One-time per repo: detect stack, create `.arch-profile.yaml` |
| `/arch-hotspot`                 | Rank architectural hotspots                                  |
| `/arch-decompose <path>`        | Plan a safe decomposition for one hotspot                    |
| `/arch-clean [scope]`           | Produce a cleanup manifest (L1–L4)                           |
| `/arch-clean-approve <batch>`   | Execute a cleanup batch                                      |
| `/arch-review`                  | Quick diff review                                            |
| `/arch-describe [scope]`        | C4 architectural description                                 |
| `/arch-plan`                    | Freeze the current plan as an ADR                            |
| `/arch-approve [--trivial "…"]` | Unlock edits after the plan is agreed                        |

## Workflow

1. You describe what you want.
2. The skill produces a 4-section response. The last section (Code) is empty — edits are blocked.
3. You read the plan. If it's good: `/arch-approve`.
4. Claude writes the code. Surgical — no unrequested refactors.

For trivial edits: `/arch-approve --trivial "typo fix"`.

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

- **`BLOCKED: no approved plan`** — run `/arch-approve` after the plan looks right. For real trivia: `/arch-approve --trivial "<reason>"`.
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
