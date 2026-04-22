---
description: Interactive refactor assistant. You describe a feature / file / module and I walk you through an architectural review, propose 2-3 refactor options with tradeoffs, discuss, and only then (on your explicit ask) write a plan or execute. If you say "just refactor it", I skip the plan and do it. Manual trigger only — not invoked automatically on routine edits.
---

Takes a free-form scope argument: a feature description, a file path, or a module name.

Examples:

- `/arch-assist refactor the billing checkout flow`
- `/arch-assist src/followers/followers.service.ts`
- `/arch-assist the margin event processing pipeline`

## The flow

Four phases. Early phases are read-only. You move between phases with plain-English keywords, no special syntax.

### Phase 1 — Architectural review (read-only)

1. Resolve the scope: a path, a feature name grepped across the repo, or a module directory. If ambiguous, list candidates and ask which one (one question only, no interrogation loop).
2. Load the stack profile + `.arch-profile.yaml`.
3. Read the scope fully. Do not modify anything.
4. Produce a condensed architectural read — NOT the full 4-section format. Just:
   - **What's there** — layers, key components, 2-line purpose of each.
   - **Growing pain** — 3-5 bullets on what's accumulating (size, responsibilities, coupling, duplication, missing seams). Use cheap hotspot signals (`wc -l`, fan-in grep, 90-day churn) to back the bullets.
   - **Dependencies you should know about** — who calls this, who it calls, any hidden event/RPC edges.

End the review with a transition prompt:

```
What do you want to explore? Say:
  options                — show 2-3 refactor options with tradeoffs
  more: <aspect>         — dig deeper into one aspect of the review
  cancel                 — stop here
```

### Phase 2 — Options (read-only)

On `options`: propose **2-3 refactor directions**, not more. Each option:

- **Name** — one-line what it is (matched to a pattern from `references/decomposition-playbook.md` when possible).
- **What you gain** — 2 bullets.
- **What it costs** — 2 bullets (effort, rollout risk, reviewer burden).
- **When it's right** — the trigger that makes this the best choice.

Do **not** just list all 10 patterns from the playbook — narrow to the 2-3 that fit the scope's actual pain.

End with:

```
What next?
  pick <name|1|2|3>                      — proceed with that option
  combine <A>+<B>                        — merge two options, I'll show the hybrid
  tweak <N>: <change>                    — adjust an option, I'll re-state it
  what about <your-alternative>          — I'll evaluate your idea alongside
  more options                           — I'll propose a different 2-3
  cancel                                 — stop here
```

### Phase 3 — Discussion (loops until a terminal keyword)

User drives. You listen. Possible moves:

- `pick 2` → lock option 2 as the choice. Move to Phase 4.
- `combine 1+3` → produce a hybrid option, ask for confirmation.
- `tweak 2: use a port instead of a service` → re-state option 2 with that adjustment.
- `what about splitting by persistence layer instead` → add this as a 4th option, show tradeoffs, ask which.
- `plan it now` → Phase 5 (write DEC), skip remaining discussion.
- `just refactor it` / `do it` / `just do it` / `execute` / `go` → Phase 6 (implement immediately), skip the plan entirely.
- `cancel` → stop.

Discussion stays read-only. No code writes, no DEC file writes, no worktree creation.

### Phase 4 — Decision fork

Once the user has picked one option (explicitly or implicitly by saying `plan it` or `just refactor`), ask **once**:

```
Direction locked: <option name>.

How do you want to proceed?
  plan              — I'll write docs/decomposition/DEC-<N>-<slug>.md and stop there
  plan + execute    — write DEC, then /arch-execute it in --auto mode
  execute           — skip the plan, refactor directly (either in a worktree or inplace)
  cancel            — stop
```

**Respect the user's choice literally.** If they say `execute` alone, do **NOT** quietly write a plan first. Going direct is a valid choice — "Якщо я не хочу плана а просто одразу все рефакторити то ти маєш мене послухати".

### Phase 5 — Plan (only on `plan` or `plan + execute`)

Delegate to the `hotspot-decomposer` sub-agent with:

- The scope path(s).
- The chosen option (as the pattern hint).
- The user's tweaks accumulated during discussion.

The agent writes `docs/decomposition/DEC-<next-number>-<slug>.md` using `templates/decomposition-plan.md.tmpl`. All strict rules from `/arch-decompose` apply (Mermaid syntax, per-PR scope with callers/tests/risks so `/arch-execute` can render cleanly later).

Report the DEC path + a one-paragraph summary. If the user chose `plan + execute`, continue to Phase 6 automatically.

### Phase 6 — Execute (only on `execute` or `plan + execute` or `just refactor it`)

Two sub-modes:

#### 6a. Execute after a plan (`plan + execute`)
Hand off to `/arch-execute <DEC-N> --auto`. The `--auto` path applies (one worktree per DEC, one branch, N commits, tests between, push + remove at the end).

#### 6b. Execute without a plan (`execute` / `just refactor it`)

No DEC file is created. The user chose to go direct. Ask one short question:

```
Where should I do this?
  worktree          — sibling worktree on a new branch (recommended)
  inplace           — your current checkout, current branch
```

On `worktree`:
- Create `<repo>.worktrees/assist-<slug>-<timestamp>/` and branch `refactor/assist-<slug>-<timestamp>`.
- Touch the session approval marker.
- Implement the chosen option end-to-end in the worktree.
- Run `commands.test` + `commands.build` from `.arch-profile.yaml`.
- On green: commit as `refactor(<scope>): <one-line option name>`, push, remove worktree.
- On failure: keep worktree for inspection, report.

On `inplace`:
- Sanity check: clean tree? On main/master? Warn and ask for one `yes` before touching anything.
- Touch the session approval marker.
- Implement, run tests + build.
- On green: commit (same message format), leave push to the user.
- On failure: `git restore .` and report.

No DEC file is written in this path. The commit message is the only record of what was done. If the refactor is non-trivial (≥ 200 LoC touched, new modules created, events added), offer **after** the commit: "This was a non-trivial change — want me to retroactively write an ADR capturing what we did? [yes/no]". On `yes`, write `docs/adr/ADR-<N>-<slug>.md` from the conversation.

## Rules

- **Manual only.** This command is invoked by the user typing `/arch-assist ...`. Never auto-trigger on file opens, general questions, or keyword matches in other conversations.
- **Read-only until the user opts in.** Phases 1–4 do not write any files and do not modify code. Even exploratory Bash must be read-only (`git log`, `wc`, `grep`).
- **No DEC file unless the user says `plan`.** No code changes unless the user says `execute` / `do it` / `just refactor it` / `plan + execute`.
- **Listen to shortcuts.** If the user wants to skip straight from Phase 1 to Phase 6, let them. Do not insist on going through options or writing a plan when they've made it clear they don't want to.
- **Language mirrors the user's.** Ukrainian request → Ukrainian prose. English request → English prose. Keywords like `options`, `pick`, `plan`, `execute` work in both — translate them naturally (`варіанти`, `обрати`, `план`, `виконати`) but accept both forms.
- **One question at a time.** Don't ask a three-part question at any transition. Give the user a menu with labeled responses and wait.
