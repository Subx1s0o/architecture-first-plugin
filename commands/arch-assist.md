---
description: Interactive refactor assistant. You describe a feature / file / module and I walk you through an architectural review, propose 2-3 refactor options with tradeoffs, discuss, and only then (on your explicit ask) write a plan or execute. If you say "just refactor it", I skip the plan and do it. Manual trigger only — not invoked automatically on routine edits.
---

Args: free-form scope (feature description / path / module name).

## Four phases, user-driven

### 1. Review (read-only)

Resolve scope (path / feature grep / module dir — ask once if ambiguous). Load stack profile + `.arch-profile.yaml`. Read fully. Produce CONDENSED read (not 4-section):

- **What's there** — layers, key components, 2-line purpose each.
- **Growing pain** — 3-5 bullets backed by `wc -l`, fan-in grep, 90-day churn.
- **Dependencies** — callers, callees, event/RPC edges.

End: `options | more: <aspect> | cancel`.

### 2. Options (read-only)

On `options`: 2-3 refactor directions narrowed to the actual pain (NOT the full 10 patterns). Per option: Name (matched to `references/decomposition-playbook.md` pattern), What you gain (2 bullets), What it costs (2), When it's right (trigger).

End: `pick <N> | combine A+B | tweak N: <change> | what about <alt> | more options | cancel`.

### 3. Discussion (loops, read-only)

User drives. Respond to tweaks / combinations / alternatives. Terminal keywords: `plan it now`, `just refactor it` / `do it` / `execute`, `cancel`.

### 4. Decision

Direction locked → ask once:

```
plan              — write docs/decomposition/DEC-<N>-<slug>.md, stop
plan + execute    — write DEC + /arch-execute --auto
execute           — skip plan, refactor directly
cancel            — stop
```

**Respect literally.** `execute` alone means NO plan.

### 5. Plan (only on `plan` / `plan + execute`)

Delegate to `hotspot-decomposer` with scope + chosen option + accumulated tweaks. Write `docs/decomposition/DEC-<N>-<slug>.md` per `templates/decomposition-plan.md.tmpl`. All strict rules from `/arch-decompose` apply.

If `plan + execute`, continue to phase 6 automatically.

### 6. Execute

**6a. After plan** → hand off to `/arch-execute <DEC-N> --auto`.

**6b. No plan** (`execute` / `just refactor it`) → ask `worktree | inplace`. Worktree: `<repo>.worktrees/assist-<slug>-<ts>/` on branch `refactor/assist-<slug>-<ts>`. Inplace: require clean tree, warn if on main/master. Either: touch approval marker, implement, run `commands.test` + `commands.build`, commit `refactor(<scope>): <option name>`. Worktree: push + remove unless `--keep`. Inplace: leave push to user.

No DEC file in 6b. After non-trivial changes (≥ 200 LoC touched, new modules, new events) offer: "retroactively write an ADR?" On yes → `docs/adr/ADR-<N>-<slug>.md` from the conversation.

## Rules

- **Manual only** — never auto-triggered.
- **Phases 1–4 read-only** — no file writes, no code changes.
- **No DEC unless user said `plan`.** No code unless user said `execute` / `do it` / `just refactor it` / `plan + execute`.
- **Listen to shortcuts** — let user jump Phase 1 → Phase 6.
- **Language mirrors user** (see SKILL.md). Accept localized keywords (`варіанти`, `обрати`, `план`, `виконати`).
- **One question at a time.**
