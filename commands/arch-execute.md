---
description: Execute one PR from a decomposition plan. Default flow: creates a sibling git worktree, implements the PR, runs tests + build, commits, pushes the branch to origin, and removes the worktree — leaving you with a clean checkout and a ready-to-PR branch on GitHub. Use --inplace, --no-push, --keep for finer control.
---

Takes: `<DEC-N|N>` optionally followed by `<PR-M|M|next>` and optional flags.

## Argument forms

- `/arch-execute 4` → PR-1 of DEC-004: worktree → implement → test → commit → **push** → remove worktree
- `/arch-execute DEC-004 PR-2` → PR-2 specifically, same full flow
- `/arch-execute 4 --no-push` → commit only; do not push, do not remove the worktree
- `/arch-execute 4 --keep` → push, but keep the worktree on disk for manual review
- `/arch-execute 4 --inplace` → mutate current checkout instead of a worktree; commits locally, does not push
- `/arch-execute 4 --base develop` → base the branch off `develop` instead of the repo default
- Flags combine: `/arch-execute 4 --base develop --keep`

## Steps

### 1. Resolve the DEC file and PR

- Normalize id: `4` → `DEC-004`, globbed at `docs/decomposition/DEC-<padded>-*.md`. If missing → stop and say "run `/arch-decompose` first".
- Parse: Target, chosen Pattern, full PR sequence, Execution log.
- If PR not given, pick the lowest PR not in the Execution log. If all done → stop and say so.

### 2. Provision isolated worktree (default)

**Skip this whole section if `--inplace` was passed.**

**Run every git operation directly via the `Bash` tool. Never write a temporary shell script in `/tmp` or anywhere else — no `create-wt.sh`, no `setup.sh`, no scaffolding files. One `Bash` call per git command, or chain with `&&` if they depend on each other. Scripts are unreviewable noise; inline commands show the user exactly what is happening.**

- Derive paths in a single `Bash` invocation (shell variables in one call):
  ```bash
  REPO_ROOT="$(git rev-parse --show-toplevel)"
  REPO_NAME="$(basename "$REPO_ROOT")"
  WORKTREES_DIR="$REPO_ROOT/../${REPO_NAME}.worktrees"
  WT_PATH="$WORKTREES_DIR/DEC-<padded>-pr-<M>-<slug>"
  BRANCH="refactor/DEC-<padded>-pr-<M>-<slug>"   # slug kebab-case, ≤ 40 chars
  ```
- Resolve the base branch: first of `--base <name>` / `.arch-profile.yaml` `default-branch:` / `origin/HEAD` / `main` / `master` that exists. Check with `git show-ref --verify --quiet refs/heads/<name>` chained via `||`.
- Create the sibling dir and the worktree in one shot:
  ```bash
  mkdir -p "$WORKTREES_DIR" && git worktree add -b "$BRANCH" "$WT_PATH" "$BASE"
  ```
- If `"$WT_PATH"` already exists: ask the user whether to reuse, blow away (`git worktree remove --force "$WT_PATH"`), or abort — then run the chosen command directly. Do NOT materialize a wrapper script for the choice.
- `.arch-profile.yaml` is tracked in git, so it's already in the worktree via the checkout. If by accident it's untracked in the main repo, `cp "$REPO_ROOT/.arch-profile.yaml" "$WT_PATH/"`.
- **The user's original checkout is never modified.**

### 3. Preflight (inplace mode only)

- `git status --porcelain` — if non-empty, stop and say: "Working tree has uncommitted changes. Either commit/stash them, drop `--inplace`, or pass `--inplace --force` (not recommended)."
- If on main/master, warn and suggest a named branch.

### 4. Display scope + confirm (rich preview)

**Critical — do NOT re-analyze the codebase here.** The DEC file is the plan of record. It was produced by `/arch-decompose` after a full hotspot analysis of the target. Reading the source again, grepping for callers, checking where symbols are registered, etc. — all of that work was already done and is captured in the DEC. Repeating it wastes a turn and risks diverging from the agreed plan.

**Render the preview purely from the DEC file's contents.** Extract:

- **Architecture before/after** — take the Mermaid from Section 3 of the DEC ("Target architecture"). If the DEC only has an after-diagram, infer the before-diagram from the DEC's Evidence table (current LoC, responsibility count) — no code reads.
- **Files touched** — from the DEC's PR-<M> entry in Section 4 (PR sequence). If the DEC lists file paths there, use them. If it's high-level ("extract avatar service"), derive file names by convention (`<module>/services/<new-name>.service.ts`) — still no code reads.
- **What moves** — from the DEC's Section 1 (Evidence → responsibility clusters) matched to this PR's scope.
- **Callers that continue to work** — from the DEC's backward-compat notes or the Pattern section (Strangler / Branch-by-Abstraction plans always list these). If the DEC did not record callers, write "callers: per DEC — delegation preserves the public API" rather than grepping.
- **Tests** — from the DEC's Section 8 (Success criteria) and any Tests subsection if present.
- **Risks + alternatives** — directly from Sections 2 and 7 of the DEC.

The **only** new work allowed at this step is rendering these into the preview format. If a field is genuinely missing from the DEC (rare — the decomposer should have captured it), state that explicitly in the preview: `(not captured in DEC — will re-check in Step 5)`. Do not silently go fill the gap by reading source.

Produce a fully-visualized preview **before** asking for confirmation. Sections in this order:

#### Header

> **DEC-<padded> · PR-<M>/<total> — <PR title>**
> Pattern: <pattern from DEC>
> Estimated diff: ~<N> LoC across <K> files

#### Architecture — before → after

Mermaid `flowchart LR` with two subgraphs showing the relevant slice of the module. The diagram must answer three questions at a glance:

1. **Who calls the unit** — upstream callers (GraphQL clients, HTTP handlers, other services)
2. **What the unit does and how big it is** — LoC and the bundled responsibilities
3. **What changes in this PR** — which piece gets extracted, which edges get redirected, where delegation flows

**Mermaid syntax that works** — strict rules, because the renderer is unforgiving:

- Line breaks inside a node label: use **`<br/>`**, never `\n` (literal `\n` will show up in the rendered box).
- Keep labels short — 3 lines max per node. Long labels wrap unpredictably.
- Every edge needs a label unless it is trivial:
  - solid labeled edge: `A -->|"calls"| B`
  - dashed labeled edge (delegation / extraction): `A -.->|"delegates to"| B`
  - bare arrow `-->` is only OK for "calls" where the direction is self-evident
- Node IDs (b1, a1, etc.) must be unique across both subgraphs. Reusing an id in BEFORE and AFTER merges them into one node.
- Put the extracted unit on the AFTER side only. Highlight it with `style` for clarity.

**Canonical template** — adapt labels, keep the structure:

```mermaid
flowchart LR
  subgraph B["BEFORE"]
    direction LR
    cB["GraphQL callers<br/>(N endpoints)"] -->|"uses"| rB["FollowersResolver<br/>1021 LoC<br/>lifecycle + margin + spot<br/>+ wallet + PnL"]
    rB -->|"wallets / PnL"| wsB["WalletsService"]
    rB -->|"copy balances"| cbB["FollowerCopyBalancesService"]
  end

  subgraph A["AFTER PR-1"]
    direction LR
    cA["GraphQL callers<br/>(wallet + PnL endpoints)"] -->|"uses"| newA["FollowerWalletResolver<br/>~180 LoC<br/>wallet + balances + PnL"]
    cA2["GraphQL callers<br/>(lifecycle + margin + spot + subs)"] -->|"uses"| rA["FollowersResolver<br/>~840 LoC<br/>lifecycle + margin + spot + subs"]
    newA -->|"wallets / PnL"| wsA["WalletsService"]
    newA -->|"copy balances"| cbA["FollowerCopyBalancesService"]
    rA -.->|"no longer needs"| wsA
    style newA fill:#1b4332,stroke:#2d6a4f,color:#fff
  end
```

Adapt:

- **Pattern = Extract Resolver / Module / Service**: two units on the AFTER side, callers routed to the new unit for the extracted concern, old unit loses those outbound edges.
- **Pattern = Extract Port**: old unit stays, AFTER shows new interface between old unit and the concrete adapter; delegation is dashed.
- **Pattern = Strangler Fig**: a router/facade node appears on AFTER, dashed edges to both old and new with percentages ("50% traffic").

If the DEC does not contain enough information to draw callers (rare — `/arch-decompose` should have captured them), draw a single generic `clients[...]` node and note `(callers not enumerated in DEC)` under the diagram rather than inventing them.

Keep it small — the slice of the repo this PR actually changes, not the whole system.

#### Files touched

Table with clickable repo-root-relative links:

| Action | File                                                                                 | Reason                  |
| ------ | ------------------------------------------------------------------------------------ | ----------------------- |
| CREATE | [`portfolio-avatar.service.ts`](src/portfolios/services/portfolio-avatar.service.ts) | new seam                |
| MODIFY | [`portfolios.service.ts`](src/portfolios/portfolios.service.ts)                      | delegate avatar methods |

#### What moves

Inline-code list of symbols / methods being relocated, grouped by intent.

#### Callers that continue to work (backward compat)

Bullet per caller with clickable link, one line why it stays green.

#### Tests

- **Existing pins** — tests that lock current behaviour, with `[file.ts:line](path#Lline)` links.
- **New tests this PR adds** — one bullet per spec.
- **Gaps** — behaviour not currently covered; flag as risk.

#### Risks + mitigation

One risk per line, colon-separated from its mitigation.

#### Alternatives considered (from the DEC)

- **Chosen**: <pattern> — why.
- **Rejected**: <alt> — why not.

#### Destination

- Worktree: `<WT_PATH>` (worktree mode) OR current checkout (inplace)
- Branch: `<BRANCH>`
- Base: `<BASE>`

#### Ask

Close with this exact prompt — four options, not two:

```
Ready to implement? Reply with one of:
  yes                         — proceed as shown
  no                          — abort, no changes
  show more                   — dump the full PR section from the DEC file
  tweak: <what to change>     — adjust the plan, I'll re-preview
```

On `tweak: <...>`: re-derive the affected sections (Files, What moves, Callers, Tests, Risks, and the Architecture diagram if structure changed) and print the full preview again with the adjustment applied. Loop until `yes`, `no`, or `show more`.

### 5. Implement

Touch the session approval marker at `${TMPDIR:-/tmp}/architecture-first/<md5($WT_PATH or $REPO_ROOT)>-<session_id>.approved` so the hook allows edits.

In **worktree mode**, treat the worktree as the active project: all subsequent `Edit`/`Write` calls use absolute paths under `$WT_PATH`; `Bash` commands run with `cd "$WT_PATH" && …`.

Produce the code per the PR plan. No re-planning — the DEC is the plan of record.

### 6. Verify

Read `commands.test` and `commands.build` from `.arch-profile.yaml` at the active path. Run both inside the worktree (or current dir for inplace). If either fails:

- worktree: leave it on disk for inspection, report failure with first 40 lines of output.
- inplace: `git restore .` and report.

### 7. Commit

On green, inside the active path:

- `git add -A`
- `git commit -m "refactor(<scope>): <PR title> [DEC-<padded> PR-<M>/<total>]"`

### 7a. Auto-push (worktree mode default)

Unless `--no-push` was passed OR mode is inplace, push the branch:

- `git push -u origin "$BRANCH"` (from within the worktree)
- If push **fails** (auth, non-fast-forward, protected branch, network, etc.): leave the worktree alive, skip removal, report the git error with its first 20 lines, and tell the user exactly how to retry — `cd "$WT_PATH" && git push -u origin "$BRANCH"`. Still proceed to step 8 to record the commit in the DEC execution log (so the work is not lost).
- If push **succeeds**: continue to step 7b.

### 7b. Auto-remove worktree (worktree mode default)

Unless `--keep` was passed OR push failed OR mode is inplace:

- Return to the main checkout: `cd "$REPO_ROOT"`.
- `git worktree remove "$WT_PATH"` — removes the worktree directory and cleans up `.git/worktrees/` metadata. The branch itself stays in the local repo and tracks `origin/<BRANCH>`.
- If removal fails (e.g. nested untracked files the user added): report the error and tell the user how to force it (`git worktree remove --force "$WT_PATH"`) — do NOT force automatically.

The refactor is now:

- committed locally ✓
- pushed to origin ✓
- available as a branch for opening a PR ✓
- not sitting in a leftover directory ✓

### 8. Update the DEC file

Append the Execution log (in the ORIGINAL checkout's DEC file, not the worktree's — the source of truth is the user's main checkout):

```
- PR-<M> executed <YYYY-MM-DD>, commit <sha> on <branch> (worktree: <path>) — tests ✓, build ✓
```

### 9. Report

Pick the shape that matches what actually happened:

**Full auto (default happy path):**

```
✓ PR-<M>/<total> done.
  branch:   refactor/DEC-001-pr-1-portfolio-service
  commit:   <sha>
  pushed:   origin/refactor/DEC-001-pr-1-portfolio-service
  worktree: removed

Open a PR on GitHub:
  https://github.com/<org>/<repo>/compare/refactor/DEC-001-pr-1-portfolio-service?expand=1
  (or: gh pr create --fill)

Next PR: /arch-execute <id> PR-<M+1>
```

**`--no-push` or push failed:**

```
✓ PR-<M>/<total> implemented, but not pushed.
  worktree: <WT_PATH>
  branch:   <BRANCH>
  commit:   <sha>

Push when ready:
  cd <WT_PATH>
  git push -u origin <BRANCH>

After merge, clean up:
  git worktree remove <WT_PATH>
```

**`--keep`:**

```
✓ PR-<M>/<total> done, worktree kept for review.
  branch:   <BRANCH>
  commit:   <sha>
  pushed:   origin/<BRANCH>
  worktree: <WT_PATH> (kept)

After you're done with it:
  git worktree remove <WT_PATH>
```

**Inplace mode:** user is already on the branch, commit done, no push. Mention the branch name and remind them to push.

If this was the final PR of the DEC, update the file header `Status:` to `done` and add a concluding line to Execution log.
