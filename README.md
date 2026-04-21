# architecture-first

A Claude Code + Cursor plugin that makes the model think like an **architect and a code janitor at the same time** — not sequentially. Stack-agnostic. Works for NestJS, Next.js, Express, Spring Boot, Django, FastAPI, Laravel, Rails, Go, Rust, and generic layered projects.

## What it does

- **Forces a 4-step response format** on any code change: Situation → Plan → File Structure → Code. No code is written until you confirm the plan.
- **Dual-lens thinking**: every response reasons about both the structural axis (layers, seams, coupling) and the hygiene axis (dead code, orphans, obsolete flags) in one pass.
- **Hotspot detection** across the repo: size × churn × cycles × fan-in, ranked.
- **Decomposition playbook** (10 canonical patterns) with a decision tree — chooses the right refactor by trigger, not by taste. Production-safe rollouts (Strangler Fig, Branch by Abstraction).
- **Cleanup manifest** with safety levels L1–L4: what to delete, with evidence, never blindly. Framework-magic aware (DI, decorators, reflection, convention-scanning).
- **Hard gates in Claude Code**: a `PreToolUse` hook blocks `Edit`/`Write` until the plan is approved, and blocks mass deletions without an approved cleanup batch.
- **Per-repo calibration** via `.arch-profile.yaml`: layers, allowed module edges, hot modules, thresholds, glossary.

---

## Install — Claude Code

Prerequisites: macOS or Linux, Python 3, `jq` (optional — installer falls back without it).

```bash
git clone https://github.com/Subx1s0o/architecture-first-plugin.git
cd architecture-first-plugin
./install.sh
```

The installer is idempotent. It copies the skill to `~/.claude/skills/architecture-first/`, the three sub-agents to `~/.claude/agents/arch-*.md`, the nine slash commands to `~/.claude/commands/arch-*.md`, and registers the `PreToolUse` hook in `~/.claude/settings.json`. Re-running refreshes files and de-duplicates the hook entry.

To verify:

```bash
ls ~/.claude/skills/architecture-first/
ls ~/.claude/agents/arch-*.md
ls ~/.claude/commands/arch-*.md
```

To uninstall:

```bash
./uninstall.sh
```

---

## Install — Cursor IDE

```bash
cd /path/to/your-project
/path/to/architecture-first-plugin/cursor/install.sh
# or from inside a cloned plugin: ./cursor/install.sh /path/to/your-project
```

This creates `.cursor/rules/architecture-first.mdc` and `.cursor/prompts-architecture-first/arch-*.md` in the target project. Commit `.cursor/` so the whole team gets the same guardrail. See [`CURSOR.md`](CURSOR.md) for usage details and limitations (no hook, no parallel sub-agents, no slash commands — the rule is always-on and commands become prompt snippets / Notepads / a Custom Mode).

---

## Quick start (once installed)

In any repo:

```
/arch-profile-init     # one-time per repo: detect stack, generate .arch-profile.yaml
/arch-hotspot          # rank the repo's architectural hotspots
/arch-clean            # produce a cleanup manifest (L1–L4), nothing deleted
```

During normal coding, just describe what you want. The skill auto-triggers, produces a 4-section response, and the pre-edit hook blocks edits until you approve:

```
/arch-approve                          # after the plan looks right
/arch-approve --trivial "rename only"  # for genuine typos/formatting
```

---

## Commands

| Command | Writes files? | Lifts the hook? | When to use |
|---|---|---|---|
| `/arch-profile-init` | `.arch-profile.yaml` | no | one-time per repo |
| `/arch-hotspot` | no | no | weekly health check, or before a sprint |
| `/arch-decompose <path>` | `docs/decomposition/DEC-*.md` | no | deep plan for one hotspot |
| `/arch-clean [scope]` | `docs/cleanup/CLN-*.md` | no | before cleaning |
| `/arch-clean-approve <batch-id>` | **yes — deletes code** | raises the mass-delete gate | execute a batch |
| `/arch-review` | no | no | quick pass over `git diff` before a PR |
| `/arch-describe [scope]` | no | no | onboarding, ADR drafting |
| `/arch-plan` | `docs/adr/ADR-*.md` | no | freeze the current plan as an ADR |
| `/arch-approve [--trivial "reason"]` | touches a marker, maybe writes ADR | **yes** | after the plan is agreed |

---

## Daily workflow

1. You describe what you want to build or fix.
2. Claude detects the stack, loads `.arch-profile.yaml`, and produces the 4-section response: Situation (structural + hygiene) → Plan (architectural + cleanup-bundled + cleanup-deferred) → Structure → Code (empty — waiting on you).
3. You read the plan. If it looks right: `/arch-approve`.
4. Claude writes the code. The code stays surgical — no refactors you didn't ask for.
5. Optional after-flow: `/arch-review` on the diff, `/arch-plan` to persist the decision as an ADR.

## Periodic repo health

```
/arch-hotspot                  # ranked table
/arch-decompose <hot-path>     # for any row that matters — produces a PR sequence
/arch-clean                    # cleanup manifest
/arch-clean-approve CLN-NN-batch-B   # after you review the batch
```

---

## Per-repo profile (`.arch-profile.yaml`)

Generated by `/arch-profile-init`. Fill three things:

- **`hot-modules`** — modules where any change forces tier M minimum and invokes the architect-reviewer (e.g. `[billing, auth, risk]`).
- **`allowed-module-edges`** — which modules can import which, directly. Everything else must go through events or a port.
- **`commands.test` / `commands.build`** — used by `/arch-clean-approve` to verify cleanup batches don't break anything.

The plugin ships with sensible defaults per stack profile (NestJS, Next.js, Spring Boot, Django, etc.). The profile only overrides what you explicitly set.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `BLOCKED: no approved plan` on every edit | Normal — produce the 4-step response, then `/arch-approve`. Or `/arch-approve --trivial "reason"` for real trivia. |
| `BLOCKED: mass deletion (≥200 lines)` | Use `/arch-clean-approve <batch>`. If the deletion is not intentional, abort — the model is doing something unplanned. |
| Hook doesn't fire at all | Re-run `./install.sh`. It restores the `settings.json` entry idempotently. |
| Skill doesn't trigger on a request | The description was too trivial. Add context: "…in module X" or say "architectural review needed". |
| Stale `.claude/.arch-approved-*` files piling up in repo | Harmless but ugly. `rm <repo>/.claude/.arch-approved-*` when you want. |

---

## Update

```bash
cd /path/to/architecture-first-plugin
git pull
./install.sh      # Claude Code
./cursor/install.sh /path/to/project   # Cursor, per project
```

---

## What's inside

```
architecture-first-plugin/
├── install.sh / uninstall.sh
├── hooks/pre-edit-gate.sh              # PreToolUse gate (Claude Code)
├── skills/architecture-first/
│   ├── SKILL.md                        # the workflow
│   ├── references/
│   │   ├── hotspot-detection.md        # pyramid of signals
│   │   ├── decomposition-playbook.md   # 10 patterns + decision tree
│   │   ├── cleanup-playbook.md         # L1–L4 safety levels
│   │   ├── c4-model.md, mermaid-cheatsheet.md
│   │   └── stack-profiles/             # nestjs, nextjs, express, spring-boot,
│   │                                   # django, fastapi, laravel, rails, go, rust, generic
│   └── templates/                      # arch-profile.yaml, ADR, decomposition-plan, cleanup-batch
├── agents/                             # architect-reviewer, hotspot-decomposer, cleaner
├── commands/                           # 9 × arch-*.md slash commands
└── cursor/                             # Cursor IDE adaptation
    ├── install.sh
    ├── rules/architecture-first.mdc    # alwaysApply rule
    └── prompts/arch-*.md               # 9 pasteable snippets / Notepads
```

---

## Roadmap

- **v0.4 — Continuous cleanup telemetry.** `.claude/arch-telemetry.jsonl` records every L2+ finding and its resolution. `/arch-telemetry --report` renders a weekly trend: findings created vs. fixed per module, mean time to resolve, net debt velocity. Gated behind real usage — will be added once the plugin has been used in production for 2–4 weeks and there's a concrete question it needs to answer.
- **v0.5 — CI validator.** GitHub Action that runs `./install.sh --dry-run` on Linux + macOS and lints all stack profiles.
- **v0.6 — Submit to `claude-plugins-official`** as a community plugin.

---

## License

MIT.

## Contributing

Issues and PRs welcome. Adding a new stack profile: copy `skills/architecture-first/references/stack-profiles/generic-layered.md`, fill in canonical layers, thresholds, anti-patterns, preferred decomposition patterns, and test/build commands. Add a detection row to `_detect.md`.
