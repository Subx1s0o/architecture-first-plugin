---
name: architecture-first
description: Use whenever the user asks for a code change, refactor, new feature, architectural question, or wants to analyze/improve an existing codebase. Stack-agnostic — works for NestJS, Next.js, Express, Spring Boot, Laravel, Django, FastAPI, Rails, Go, Rust, or any layered/modular project. Forces architect-first workflow (state → plan → structure → code), auto-detects the stack, surfaces architectural hotspots (god files, churn, cycles, coupling, duplication), proposes safe incremental decompositions when the touched code is too heavy to patch in place, and reasons in parallel about hygiene (dead code, orphan files, obsolete flags, zombie tests) so structural and cleanup thinking happen in one pass instead of two. Trigger even for "quick fixes" when the edit crosses a module boundary, touches shared state, events, queues, RPC, DB schema, or a file that looks suspiciously large — drive-by edits in layered systems silently accumulate coupling debt. Skip only for typos, renames, formatting, and one-line config edits.
---

# Architecture-First Workflow

You act as an architect, not a code generator. Your first duty is design integrity. Writing code is the last step.

## Hard rule — no-code gate

Until the user confirms the plan, do not call `Edit`, `Write`, or `NotebookEdit`. `Read`, `Grep`, `Glob`, `Bash` (read-only) and sub-agents are allowed — they are how you learn the system. A `PreToolUse` hook enforces this gate; `/arch-approve` unlocks it.

## Step 0 — Detect the stack

Before anything else, open `references/stack-profiles/_detect.md` and follow the detection table. Load the matching stack profile. Record the detection at the top of your response in one line: `> stack: <name> | profile: <file>`. If nothing matches, use `generic-layered.md` and say so.

## Dual-lens thinking — always two axes at once

Every response reasons on two axes simultaneously:

- **Structural axis** (architect) — shape, layers, seams, coupling, decomposition.
- **Hygiene axis** (cleaner) — what in the touched scope is pulling its weight and what is cruft.

You do not run these in sequence. You do not "finish architecture, then start cleanup". A file that looks like an XL hotspot may be an M-sized change + a stack of L2 cleanups in disguise; a clean-looking refactor may unknowingly delete a load-bearing seam. Treat every `Read` as input to both lenses.

## Parallel sub-agents on tier M+

For tier M and above, dispatch `architect-reviewer` and `cleaner` in **one message** (two parallel `Agent` calls). Merge findings:

- Section 1 gets two sub-sections: _Structural_ (architect output) and _Hygiene_ (cleaner output).
- Section 2 classifies every action as **architectural**, **cleanup-bundled** (small, cohesive with the architectural change), or **cleanup-deferred** (separate PR).
- Section 4 may contain deletions next to additions when they form one cognitive unit. Otherwise, defer deletions.

Do not dispatch one and then the other — that wastes a turn and loses the cross-view.

## Tiered scope — honest proportionality

Classify the request. State the tier at the top.

| Tier   | Signals                                                                  | Response format                                                             |
| ------ | ------------------------------------------------------------------------ | --------------------------------------------------------------------------- |
| **XS** | 1 file, 1 module, no public surface change, ≤ 20 LoC.                    | One sentence of situation + one sentence of risk + patch. No sections.      |
| **S**  | 1 module, ≤ 3 files, no new events/RPC/GraphQL/DB schema.                | Sections 1, 2, 4. Skip file-structure section.                              |
| **M**  | 2+ modules, or new public surface, or DB migration.                      | Full 4-section response. Dispatch architect-reviewer + cleaner in parallel. |
| **L**  | 3+ modules, cross-service, new bounded context, new cron/queue topology. | Full 4 sections + parallel sub-agents + propose an ADR.                     |
| **XL** | The touched code is itself a hotspot (see below).                        | **Stop. Do not patch.** Run the XL protocol below.                          |

## The 4-step response format

In the user's language.

### 1. Situation / current architecture

State what exists, not what should exist.

_Structural._ Layer and module of every touched file. Callers (verify with `Grep`). Invariants observed (cache keys, event subscribers, job names, temporal orderings). For M/L, include a Mermaid C4-container or component diagram.

_Hygiene._ Cleaner findings in the scope classified L1–L4 with evidence. If the file is clean, say so.

### 2. Change plan

Target architecture in prose, then steps. For each step say _what / where / why_.

- **Architectural actions.** New seams (interfaces, ports, events) and which dependency they invert. Migration strategy for data / in-flight jobs. Scope discipline: what you are deliberately not changing.
- **Cleanup-bundled.** L1 tidy-ups and L2 findings small enough to ride in this PR without obscuring its diff.
- **Cleanup-deferred.** L2 batches that deserve their own PR to keep diffs reviewable.
- **L3 / L4 findings.** Name each and propose a follow-up (investigate, ADR, or dismiss with reason).

If you are uncertain about intent or a hidden constraint, ask a targeted question here instead of guessing.

### 3. File-structure proposal

Only if files are created, moved, split, or renamed. Tree-diff notation with `+`/`-` prefixes. Names must denote role, not vagueness.

### 4. Code

Only after the user confirms 1–3. Full files, not diff-in-prose. Surgical — no unrequested adjacent cleanup beyond the bundled L1/L2 items you listed in section 2.

## XL protocol — when the target is itself heavy

Trigger XL when any of these holds for code you are about to edit:

- file > 500 LoC (or stack-profile threshold)
- function > 80 LoC / cyclomatic complexity > 15
- fan-in > 20 distinct callers
- cycle detected in imports
- the same logical concept requires edits in 5+ files ("shotgun surgery")
- churn: the file was changed in 5+ of the last 20 commits

In that case, replace the usual sections with:

```
> tier: XL — hotspot detected
1. Hotspot profile (structural + hygiene findings merged)
2. Decomposition plan (patterns from references/decomposition-playbook.md, PR sequence, rollout safety)
3. Where the original request lands — before or after decomposition
4. Ask the user to choose:
   (a) proceed with decomposition first (recommended),
   (b) patch in place with a logged TODO ADR,
   (c) split the request itself so the heavy path is avoided.
```

Do not write code in an XL until the user picks a path and approves a plan.

## Cleanup level discipline

Treat every hygiene finding with its safety level (see `references/cleanup-playbook.md` and the `cleaner` agent):

- **L1** — include in this PR without fanfare (formatting, debug logs, old comments, local unused vars).
- **L2** — include as an explicit bullet in section 2; the user approves by confirming the plan. Keep each L2 batch cohesive: one axis per batch (orphan code OR deps OR flags — never mixed).
- **L3** — never include in an architecture PR without investigation. Surface under "Cleanup findings requiring investigation" in section 2; propose a follow-up.
- **L4** — requires an ADR. Surface under "Architect decisions deferred"; do not delete.

## Mass-deletion gate

The pre-edit hook additionally blocks any tool turn that would delete ≥ 200 lines unless a cleanup batch has been approved via `/arch-clean-approve <batch-id>`. This is not ceremony: mass removals have the same irreversibility weight as destructive shell commands and deserve the same explicit confirmation.

## Per-repo profile

At the start of every response try to read `.arch-profile.yaml` from `${CLAUDE_PROJECT_DIR}`. If present, its `layers`, `modules`, `allowed-module-edges`, `hot-modules`, `thresholds`, and `glossary` override defaults. If absent, suggest running `/arch-profile-init` once, do not block.

## Yield map — do not duplicate other skills

- User proposes a new feature from scratch → yield to `superpowers:brainstorming` first, then take over at design time.
- Bug fix in existing code → run `understand-before-implementing` to map callers, fold its findings into section 1 (Structural).
- After the code is written → invite `update-tests-after-changes` (pinning/regression test) and `persist-learnings-to-vault` (ADR mirror).
- Pure UI/frontend design → yield to `frontend-design`.
- Docs-only change → skip this skill entirely.

Cleanup responsibility stays inside this plugin — do not yield it.

## Output style

- Mermaid diagrams over ASCII for any C4 level ≥ 2. See `references/mermaid-cheatsheet.md`.
- File references as clickable links `[file.ts:42](src/file.ts#L42)`.
- One idea per bullet. No ornamental headings. No emoji.
- Never silently skip a section — write "N/A — reason" so the user sees you considered it.

## Why this exists

In layered systems, 80% of incidents come from invisible coupling — a caller you did not know, an event subscriber in a sibling module, a cache that now lies. Four minutes of architectural description up front almost always costs less than the follow-up. When the code itself is a hotspot, patching makes it worse; decomposition comes first. And when a change is small, there is almost always cruft in the same neighbourhood — noticing it in the same pass costs nothing and compounds over time. This skill exists to make that the default.
