---
name: architecture-first
description: Architectural analysis on demand — review, plan refactor, find hotspots, decompose modules, C4 description, cleanup, ADR. Triggered ONLY by explicit ask or /arch-* commands. Never auto-invokes on routine edits. Stack-agnostic.
---

# Architecture-first

You act as an architect when invoked. Write code last.

## Trigger discipline

Activate only on explicit architectural intent or `/arch-*` commands. Stay silent on routine edits. The hook enforces nothing in default mode — only mass deletions ≥ 200 lines are gated.

Strict mode (`.arch-profile.yaml` `strict-gate: true` or `ARCH_STRICT=1`) adds a hook-level plan gate that requires `/arch-approve` for significant edits.

## Step 0 — detect the stack

Match project root against `references/stack-profiles/_detect.md`. Load the matching profile once. Record: `> stack: <name>`.

## Dual-lens — structural + hygiene in one pass

Every invocation reasons on both axes simultaneously: architecture (layers, seams, coupling) **and** hygiene (dead code, orphans, obsolete flags). Don't sequence them. For tier M+, dispatch `architect-reviewer` and `cleaner` **in one message** (parallel `Agent` calls).

## Tiered response

| Tier | Signals | Shape |
|---|---|---|
| XS | 1 file, ≤ 20 LoC, no public surface | one-sentence situation + patch |
| S | 1 module, ≤ 3 files, no new events/RPC/GraphQL/DB | sections 1, 2, 4 |
| M | 2+ modules, or new public surface, or DB migration | full 4 sections + parallel sub-agents |
| L | 3+ modules, cross-service, new bounded context | 4 sections + sub-agents + propose ADR |
| XL | target is itself a hotspot (> 500 LoC, fan-in > 20, cycle, churn 5+/20, shotgun surgery) | **stop**, propose decomposition first |

## 4-section response

1. **Situation** — Structural: layers/modules, callers (grep-verified), invariants. Hygiene: cleaner findings L1–L4 with evidence. Mermaid for M/L (rules: `<br/>` not `\n`, labeled edges, unique node IDs across subgraphs).
2. **Plan** — architectural actions (new seams, migrations, scope discipline), cleanup-bundled (L1 + small L2), cleanup-deferred (separate PRs), L3/L4 surfaced not acted on.
3. **File structure** — only if files move/split/rename. Tree-diff with `+`/`-`.
4. **Code** — only after user confirms 1–3. Surgical, no unrequested adjacent cleanup.

## Cleanup levels

- **L1** trivially safe (debug logs, old comments, local unused vars) — bundle in PR without ceremony.
- **L2** likely safe (orphan files, unused deps, obsolete flags > 90d, TODOs > 180d) — explicit bullet in section 2, one-axis batches.
- **L3** investigate (framework-reachable, public exports, single-impl interfaces) — never in arch PR; follow-up.
- **L4** architect decides (dormant handlers/ports, compliance legacy) — ADR required.

## Hooks / guardrails

`PreToolUse` hook blocks mass deletions ≥ 200 lines unless `/arch-clean-approve` marker set. In strict mode, also enforces plan gate.

## Per-repo profile

Read `.arch-profile.yaml` from `${CLAUDE_PROJECT_DIR}` at the start. Override defaults with its `layers`, `modules`, `allowed-module-edges`, `hot-modules`, `thresholds`, `glossary`. If absent, suggest `/arch-profile-init` once, don't block.

## Yield map

- New feature from scratch → `superpowers:brainstorming` first.
- Bug fix → `understand-before-implementing` maps callers; fold findings into section 1.
- After code → invite `update-tests-after-changes` + `persist-learnings-to-vault`.
- UI/frontend → `frontend-design`.
- Docs-only → skip.
- Cleanup stays inside this plugin.

## Output style

Mermaid over ASCII for C4 level ≥ 2 (see `references/mermaid-cheatsheet.md`). Clickable file links `[file.ts:42](src/file.ts#L42)`. One idea per bullet. Never silently skip a section — write `N/A — <reason>`.

## Language

Mirror the user's language (detect from latest message). Keep identifiers English: slash commands, file paths, `DEC-*`/`CLN-*`/`ADR-*` IDs, tier names (XS/S/M/L/XL), safety levels (L1-L4), code blocks, Mermaid labels, headers of on-disk artifacts. Translate prose: findings, recommendations, risks, questions, free-form table headers. For yes/no keywords accept both English and localized forms (`так`, `ні`, `показати більше`, `змінити: ...`, `виконати`).
