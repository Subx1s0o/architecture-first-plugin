# architecture-first

> A plugin for **Claude Code** and **Cursor IDE** that makes the model think like a **software architect and a code janitor at the same time** — not sequentially. Stack-agnostic. Works for NestJS, Next.js, Express, Spring Boot, Django, FastAPI, Laravel, Rails, Go, Rust, and any layered project.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

---

## What it does

- **Forces a 4-step response** on any code change: `Situation → Plan → File Structure → Code`. No code is written until you explicitly approve the plan.
- **Dual-lens thinking.** Every response reasons in parallel about the _structural axis_ (layers, seams, coupling, decomposition) and the _hygiene axis_ (dead code, orphan files, obsolete flags, zombie tests). One pass, both lenses.
- **Hotspot detection** — ranks the repo by size × churn × cycles × fan-in. Points at the 5 files that will cause 80% of your future bugs.
- **Decomposition playbook** — 10 canonical patterns with a decision tree. Strangler Fig, Branch by Abstraction, Extract Port, Event-Carried State Transfer, Saga, Anti-Corruption Layer, and more. Picks the right refactor by _trigger_, not by taste.
- **Cleanup manifests with safety levels L1–L4.** Nothing is deleted blindly. The cleaner is framework-magic aware (DI, decorators, reflection, convention-scanning) and demotes findings that might be reachable through non-obvious paths.
- **Hard gates in Claude Code.** A `PreToolUse` hook physically blocks `Edit` and `Write` until the plan is approved, and blocks mass deletions without an explicit cleanup-batch authorization.
- **Per-repo calibration** via `.arch-profile.yaml`: layer names, allowed module edges, hot modules, thresholds, domain glossary.

---

## See it in action

You ask:

> Add a `copy_mode` enum (ONE_WAY / TWO_WAY) to `SubscriptionService` and wire it into the order-placement flow.

The plugin responds (abridged):

```text
> stack: nestjs | profile: nestjs.md
> tier: M

## 1. Situation

**Structural.** Subscription model lives in [subscription.model.ts:14](src/subscriptions/models/subscription.model.ts#L14),
mutated via [update-subscription.operation.ts:28](src/subscriptions/operations/update-subscription.operation.ts#L28).
The order flow in [place-order.operation.ts:41](src/orders/operations/place-order.operation.ts#L41) does not
branch on direction today. Three subscribers listen to `SubscriptionUpdated`: risk-watchdog,
fee-allocator, portfolio-sync. The GraphQL type `Subscription` is consumed by the web frontend.

**Hygiene.** The file is 186 LoC — not a hotspot. The cleaner found:
- L1: 12 `console.log` calls in [order.processor.ts:*](src/orders/processors/order.processor.ts) — leftover debug.
- L1: commented block 2023-08 in [subscription.model.ts:14](src/subscriptions/models/subscription.model.ts#L14), git blame: "WIP revert".
- L2: [legacy-subscription.service.ts](src/subscriptions/services/legacy-subscription.service.ts) (84 LoC) — 0 importers,
  no decorators, not in public barrel. Safe to delete.

## 2. Plan

**Architectural.**
- New `CopyMode` enum in `domain/copy-mode.enum.ts` (ONE_WAY | TWO_WAY).
- New port `CopyDirectionPolicy` in `domain/` with two adapters in `services/policies/`.
- `place-order.operation.ts` consumes the port via DI — direction logic leaves the operation.
- GraphQL field nullable with default ONE_WAY for frontend backward compat.
- DB migration: `ADD COLUMN copy_mode VARCHAR(16) NOT NULL DEFAULT 'ONE_WAY'`.
- Risk: fee-allocator caches subscription. Invalidate `sub:<id>` key on update.

**Cleanup-bundled in this PR.**
- L1 — remove commented block in subscription.model.ts:14.

**Cleanup-deferred to separate PRs.**
- L2 Batch B — delete `legacy-subscription.service.ts`. Evidence: 0 grep hits, no decorators, not barrelled.
  Run `/arch-clean-approve CLN-007-batch-B` when ready.
- L1 Batch A — replace 12 `console.log` with the logger in order.processor.ts.

**L3/L4.** None detected.

## 3. File structure
src/
  orders/
    operations/place-order.operation.ts     # modified (injects port)
  subscriptions/
    domain/
+     copy-mode.enum.ts
+     copy-direction-policy.port.ts
    services/policies/
+     one-way-direction.policy.ts
+     two-way-direction.policy.ts
  database/migrations/
+   20260421-add-copy-mode.ts

## 4. Code
(empty — awaiting your /arch-approve)
```

You read it. It looks right. You type:

```text
/arch-approve
```

The gate lifts, Claude writes the code.

---

## Install — Claude Code

**Prerequisites:** macOS or Linux, Python 3, `git`. (`jq` is used if available.)

```bash
git clone https://github.com/Subx1s0o/architecture-first-plugin.git
cd architecture-first-plugin
./install.sh
```

What the installer does:

1. Copies the skill to `~/.claude/skills/architecture-first/`.
2. Copies three sub-agents to `~/.claude/agents/arch-{architect-reviewer,hotspot-decomposer,cleaner}.md`.
3. Copies nine slash commands to `~/.claude/commands/arch-*.md`.
4. Registers a `PreToolUse` hook in `~/.claude/settings.json` (idempotent — re-running won't duplicate the entry).

**Verify:**

```bash
ls ~/.claude/skills/architecture-first/
ls ~/.claude/agents/arch-*.md
ls ~/.claude/commands/arch-*.md
```

In a Claude Code chat you should see the skill `architecture-first` in the skills list and the 9 `arch-*` slash commands in autocomplete.

**Uninstall:**

```bash
./uninstall.sh
```

**Update** (pull and reinstall — hook entry is de-duplicated):

```bash
cd architecture-first-plugin && git pull && ./install.sh
```

---

## Install — Cursor IDE

Cursor doesn't have hooks, slash commands, or sub-agents. The plugin adapts by shipping **rules** + **prompt snippets**.

```bash
cd /path/to/your-project
/path/to/architecture-first-plugin/cursor/install.sh
```

This creates inside the project:

- `.cursor/rules/architecture-first.mdc` — a rule with `alwaysApply: true`. The model reads it on every request.
- `.cursor/prompts-architecture-first/arch-*.md` — 9 ready-to-paste prompt snippets (one per command).

**Commit `.cursor/`** so everyone on the team gets the same guardrail.

**Three ways to trigger "commands" in Cursor**

1. **Copy-paste.** Open `.cursor/prompts-architecture-first/arch-hotspot.md`, paste into chat, replace `<PATH>` / `<SCOPE>`.
2. **Notepads** (recommended). Cursor Settings → Features → Notepads → enable. Create one Notepad per snippet. In chat, call with `@arch-hotspot`, `@arch-clean`, etc.
3. **Custom Mode "Architect"** (strongest). Settings → Models → Custom Modes → New. Paste the body of `architecture-first.mdc` (without YAML front-matter) as the system prompt. Switch this mode on for non-trivial work; switch off for quick edits.

**Honest trade-offs vs Claude Code**

|                     | Claude Code                       | Cursor                             |
| ------------------- | --------------------------------- | ---------------------------------- |
| Skill auto-triggers | ✅                                | ✅ (via `alwaysApply: true` rule)  |
| Hard `Edit` gate    | ✅ (`PreToolUse` hook)            | ❌ — soft, lives in rule text only |
| Mass-deletion gate  | ✅                                | ❌                                 |
| Parallel sub-agents | ✅ (architect-reviewer ∥ cleaner) | ❌ — sequential                    |
| Slash commands      | ✅ native                         | 🟡 snippets or Notepads            |
| Global install      | ✅ (once, for all repos)          | Per-project                        |

For Cursor, the reliable workflow is: **Custom Mode "Architect"** for meaningful changes + **Notepads** for the 9 commands.

See [`CURSOR.md`](CURSOR.md) for the full Cursor reference.

---

## First run (5-minute tour)

In a fresh repo:

**Step 1** — detect the stack and calibrate:

```text
/arch-profile-init
```

Creates `.arch-profile.yaml` in the project root. Open it, fill in three things:

```yaml
hot-modules: [billing, auth, payments] # forces tier M+ on any change here
allowed-module-edges:
  orders: [billing, inventory] # direct imports; everything else via events/ports
commands:
  test: npm test
  build: npm run build
```

Commit the file. Done once per repo.

**Step 2** — look at the repo:

```text
/arch-hotspot
```

You get a ranked table like:

| Rank | Path                                   | Size | Churn | Cycle?               | Smell                         | Suggested pattern     |
| ---- | -------------------------------------- | ---- | ----- | -------------------- | ----------------------------- | --------------------- |
| 1    | `src/orders/operations/place-order.ts` | 834  | 14/20 | —                    | 3 responsibilities, fan-in 27 | Extract Port + split  |
| 2    | `src/billing/invoice.service.ts`       | 612  | 9/20  | madge: cycle w/ subs | god dependency                | Break cycle via event |
| …    |                                        |      |       |                      |                               |                       |

Pick any row and dig in:

```text
/arch-decompose src/orders/operations/place-order.ts
```

You get a `docs/decomposition/DEC-001-place-order.md` file with evidence table, chosen pattern, target Mermaid diagram, and a PR sequence.

**Step 3** — look at the cruft:

```text
/arch-clean
```

You get a `docs/cleanup/CLN-001-repo-scan.md` with findings classified L1 (safe) → L4 (architect-only). Review Batch B (orphan code), then:

```text
/arch-clean-approve CLN-001-batch-B
```

Claude lists every file to delete, asks "yes?", executes, runs `npm test && npm run build`, appends the manifest with the commit SHA. If anything fails — `git restore` and report.

**Step 4** — code normally. The skill triggers, produces the 4-step response, the hook blocks edits until you `/arch-approve`.

---

## Commands

| Command                              | Writes files?                     | Lifts the hook?         | Typical use                            |
| ------------------------------------ | --------------------------------- | ----------------------- | -------------------------------------- |
| `/arch-profile-init`                 | `.arch-profile.yaml`              | no                      | one-time per repo                      |
| `/arch-hotspot`                      | no                                | no                      | weekly health check                    |
| `/arch-decompose <path>`             | `docs/decomposition/DEC-*.md`     | no                      | deep plan for one hotspot              |
| `/arch-clean [scope]`                | `docs/cleanup/CLN-*.md`           | no                      | audit before cleanup                   |
| `/arch-clean-approve <batch-id>`     | **yes — deletes code**            | raises mass-delete gate | execute one batch                      |
| `/arch-review`                       | no                                | no                      | quick pass over `git diff` before a PR |
| `/arch-describe [scope]`             | no                                | no                      | onboarding, ADR drafting               |
| `/arch-plan`                         | `docs/adr/ADR-*.md`               | no                      | freeze the current plan as an ADR      |
| `/arch-approve [--trivial "reason"]` | touches a marker (+ optional ADR) | **yes**                 | after the plan is approved             |

### Example invocations

```bash
# Scan only one subsystem:
/arch-hotspot src/billing

# Hotspot deep-dive with a specific hint:
/arch-decompose src/orders/operations/place-order.ts

# Cleanup scoped to one module:
/arch-clean src/legacy

# Execute a specific cleanup batch from the manifest:
/arch-clean-approve CLN-003-batch-C

# Skip the plan gate for a genuine typo:
/arch-approve --trivial "rename variable"

# Freeze a decision as an ADR without touching code:
/arch-plan
```

---

## Workflows

### Daily workflow — feature work

1. You describe what you want.
2. Skill detects stack, loads `.arch-profile.yaml`, classifies the tier (XS / S / M / L / XL).
3. For **tier M+**, it dispatches `architect-reviewer` and `cleaner` **in parallel** (one turn, two concurrent sub-agents).
4. You see the 4-section response. Code section is empty — the hook is blocking.
5. You agree (or push back on) the plan. When agreed: `/arch-approve`.
6. Claude writes code. Surgical — no refactors beyond what's in the plan.
7. Run your tests. Open a PR. Optionally `/arch-review` to sanity-check the diff.

### Periodic repo health — weekly or pre-sprint

```text
/arch-hotspot                               # ranked table
/arch-decompose <top-hotspot>               # plan for the worst one
/arch-clean                                 # cleanup manifest
```

Manifest lives in `docs/cleanup/CLN-*.md`. Triage into:

- **Do now** (L1 + small L2 batches).
- **Ticket for next sprint** (larger L2 batches, L3 after investigation).
- **Bring to team** (L4 needs ADR).

### Cleanup execution

```text
/arch-clean-approve CLN-007-batch-A   # formatting & logs
/arch-clean-approve CLN-007-batch-B   # orphan files
/arch-clean-approve CLN-007-batch-C   # unused deps
```

Each batch:

1. Claude enumerates every file/line to remove with evidence from the manifest.
2. Asks "yes?" — you type `yes`.
3. Executes deletions.
4. Runs `commands.test` and `commands.build` from the profile.
5. On failure: `git restore`, report the failure, append the manifest with the error.
6. On success: append `Status: executed on <date>, commit <sha>`.

---

## Configuration — `.arch-profile.yaml`

Generated by `/arch-profile-init`. Example (filled in for a fictional e-commerce app):

```yaml
repo: my-app
stack: [typescript, nestjs, postgres, redis, graphql]

layers:
  operations: use-cases, orchestration
  services: DB + cache glue
  models: ORM-coupled persistence
  domain: pure business logic, framework-free
  events: event subscribers
  graphql: resolvers + DTOs

modules:
  orders: [operations, services, models, domain, events, graphql]
  billing: [operations, services, models, domain, events]
  inventory: [operations, services, models, domain]
  users: [operations, services, models, graphql]

allowed-module-edges:
  orders: [billing, inventory]
  billing: [] # billing is a leaf, only talks back via events
  users: []

hot-modules: [billing, users] # any change here forces tier M+

thresholds:
  file-loc: { warn: 400, xl: 600 }
  fn-loc: { warn: 60, xl: 100 }
  fan-in: { warn: 15, xl: 25 }
  churn-20: { warn: 4, xl: 7 }

commands:
  test: npm run test
  build: npm run build
  lint: npm run lint

glossary:
  order: a customer-initiated purchase request
  invoice: a billing record tied to a fulfilled order
```

When the skill encounters code in `billing/`, it knows it's a hot module → tier M minimum → architect-reviewer runs. When `cleaner` proposes deletion, it runs `commands.test` before accepting. When Claude describes modules, it uses your glossary so `order` always means the same thing.

---

## Safety levels — cleanup classification

| Level  | What it is                                                                                                                                                                                                                | Where it ends up                                                                                                             |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| **L1** | Trivially safe: debug `console.log`, trailing whitespace, commented code > 30 days old, local unused vars                                                                                                                 | Bundled with any PR without fanfare                                                                                          |
| **L2** | Likely safe: file-private exports with 0 importers, orphan files (after reach-checks), unused deps, obsolete flags (> 90 days pinned), TODOs > 180 days old                                                               | Explicit bullet in section 2; user approves by confirming the plan; one-axis batches (orphan OR deps OR flags — never mixed) |
| **L3** | Investigate: public exports with 0 repo-local importers (may be consumed externally), symbols registered by string (routes, queue jobs, CLI names), decorator-registered classes, interfaces with a single implementation | Never in an architecture PR without investigation; surfaced in section 2, proposed as follow-up                              |
| **L4** | Architect decides: dormant handlers, dormant ports, features behind default-off flags, legacy kept for compliance                                                                                                         | Requires an ADR; `/arch-clean-approve` refuses to execute batches containing L4                                              |

The cleaner always runs framework-magic rule-outs first (DI, decorators, reflection, convention paths) and raises safety level when any applies.

---

## What's enforced vs. what's guided

Honest summary of _how_ the plugin changes behavior:

| Mechanism                      | Claude Code                                                    | Cursor                                |
| ------------------------------ | -------------------------------------------------------------- | ------------------------------------- |
| 4-step response format         | Skill description + body instructions                          | Rule (`alwaysApply: true`)            |
| No-code gate                   | **Enforced** — `PreToolUse` hook blocks `Edit`/`Write`         | Guided — text instruction in the rule |
| Mass-deletion gate (≥ 200 LoC) | **Enforced** — same hook                                       | Guided                                |
| Parallel sub-agents on tier M+ | **Built-in** — architect-reviewer and cleaner run concurrently | Simulated sequentially by one model   |
| Per-repo calibration           | `.arch-profile.yaml` read by skill                             | Same file, read by the rule           |
| Per-stack defaults             | 11 stack profiles loaded on detection                          | Same                                  |

Cursor is strictly weaker on enforcement (no hooks). Use the "Architect" Custom Mode when you want stricter behavior.

---

## What's inside

```
architecture-first-plugin/
├── install.sh / uninstall.sh
├── hooks/pre-edit-gate.sh                   # PreToolUse gate (Claude Code)
├── skills/architecture-first/
│   ├── SKILL.md                             # the workflow
│   ├── references/
│   │   ├── hotspot-detection.md             # signal pyramid (Tier 0–4)
│   │   ├── decomposition-playbook.md        # 10 patterns + decision tree
│   │   ├── cleanup-playbook.md              # L1–L4 safety discipline
│   │   ├── c4-model.md, mermaid-cheatsheet.md
│   │   └── stack-profiles/                  # nestjs, nextjs, express, spring-boot,
│   │                                        # django, fastapi, laravel, rails, go-stdlib,
│   │                                        # rust-axum, generic-layered
│   └── templates/
│       ├── arch-profile.yaml.tmpl
│       ├── ADR.md.tmpl
│       ├── decomposition-plan.md.tmpl
│       └── cleanup-batch.md.tmpl
├── agents/                                  # architect-reviewer, hotspot-decomposer, cleaner
├── commands/                                # 9 × arch-*.md slash commands
└── cursor/                                  # Cursor IDE adaptation
    ├── install.sh
    ├── rules/architecture-first.mdc         # alwaysApply rule
    └── prompts/arch-*.md                    # 9 pasteable snippets / Notepads
```

---

## FAQ / Troubleshooting

**Q. The hook blocks every edit — is it broken?**
That's the point. Produce the 4-step response, then run `/arch-approve`. For real trivia (typos, formatting): `/arch-approve --trivial "<one-line reason>"`.

**Q. Hook isn't firing at all.**
Re-run `./install.sh`. The installer is idempotent and restores the `settings.json` entry.

**Q. The skill doesn't auto-trigger.**
The request was too trivial ("rename X"). Add context: "…in the `orders` module" or "I want an architectural review".

**Q. I ran `/arch-clean-approve` and the test suite failed.**
The plugin does `git restore` automatically and reports the failure. Nothing is lost. Check the manifest — it now has a `Status: failed — <reason>` line.

**Q. Stale `.claude/.arch-approved-*` files in my repo.**
Harmless markers. `rm <repo>/.claude/.arch-approved-*` whenever you like.

**Q. I want to tune the thresholds — 400 LoC is too strict for my legacy Rails app.**
Edit `.arch-profile.yaml` → `thresholds:`. Stack defaults are only used when you don't override.

**Q. Adding a new stack profile?**
Copy `skills/architecture-first/references/stack-profiles/generic-layered.md`, fill in the canonical layer names, thresholds, anti-patterns, preferred decomposition patterns, and `commands.test/build/lint`. Add a detection row to `_detect.md`. PRs welcome.

**Q. Does this work with ChatGPT / Gemini / Copilot?**
Not directly. The Claude Code install wires hooks that only Claude Code runs. The Cursor install is a generic MDC rule — Cursor always uses your configured model (which may be Claude or not). For other platforms, copy the content of `SKILL.md` into a custom system prompt manually.

---

## Roadmap

- **v0.4 — Continuous cleanup telemetry.** `.claude/arch-telemetry.jsonl` logs every L2+ finding and its resolution. `/arch-telemetry --report` renders a weekly trend chart: findings created vs. fixed per module, mean time to resolve. Added once there are 2–4 weeks of real usage driving a concrete question.
- **v0.5 — CI validator.** GitHub Action that runs `./install.sh --dry-run` on Linux + macOS and lints all stack profiles against a schema.
- **v0.6 — Community marketplace.** Submit to `anthropics/claude-plugins-official` as a community plugin.

---

## Contributing

Issues and PRs welcome. Most valuable contributions today:

- **New stack profiles** — Scala/Play, Elixir/Phoenix, ASP.NET Core, Kotlin/Ktor. Use `generic-layered.md` as the skeleton.
- **Stack-specific anti-pattern lists** — rough edges unique to a framework that the cleaner or architect-reviewer should flag.
- **Decomposition patterns** — if you know a pattern that's not in the 10 already listed and it has a clear trigger + rollout story, open an issue.

By submitting a contribution you agree to license it under Apache-2.0 (see `LICENSE`). Please keep the copyright notice in `NOTICE` intact in any fork.

---

## License

Apache License 2.0 — see [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).

Copyright © 2026 Subx1s0o (`nazarsabardin@gmail.com`). All original work. Forks and derivatives must retain the copyright notice, the NOTICE file, and indicate modifications per section 4 of the license.
