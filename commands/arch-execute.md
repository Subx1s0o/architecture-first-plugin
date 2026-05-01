---
description: Execute PRs from decomposition plans in a sibling git worktree. `--auto` stacks all PRs of a DEC on one branch. `ALL --auto` iterates every DEC. Flags: --inplace, --no-push, --keep, --base.
---

Args: `<DEC-N|N|ALL>` [`<PR-M|M|next>`] [flags].

## Modes

- `/arch-execute 4` — PR-1 of DEC-004 with per-PR preview.
- `/arch-execute 4 PR-2` / `4 next` — specific / next unexecuted.
- `/arch-execute 4 --auto` — all remaining PRs on ONE branch `refactor/DEC-004-<slug>`, one push.
- `/arch-execute ALL --auto` — every DEC with remaining PRs, stop on first failure.

Flags: `--no-push` (commit only), `--keep` (push, keep worktree), `--inplace` (no worktree; refuse with `--auto`), `--base <branch>`.

## Steps

### 0. Pre-start hygiene

Run the same sweep as `/arch-clean-worktrees` silently:

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
WORKTREES_DIR="$REPO_ROOT/../$(basename "$REPO_ROOT").worktrees"
```

For each `WORKTREES_DIR/DEC-*`: remove if `git ls-remote --exit-code origin <branch>` succeeds, working tree is clean, and `git rev-list --count @{upstream}..HEAD` is 0. Drop `node_modules` symlinks + build-artifact files first (see scope rules in `/arch-clean-worktrees`). Use `git worktree remove` then verify with `[ ! -d "$WT_PATH" ] && git worktree list | grep -qv "$WT_PATH"`. Never `--force` automatically.

Final report line: `Cleaned N orphan worktrees, kept M` (only mention kept entries if any). For deeper or `--force` sweep, point at `/arch-clean-worktrees`.

### 1. Parse DEC state (Execution log is authoritative)

- Normalize id: `4` / `DEC-4` → `DEC-004`. Glob `docs/decomposition/DEC-<padded>-*.md`. Missing → "run `/arch-decompose` first".
- Parse Status, PR sequence (Section 4), Execution log.
- Executed via regex `^\s*-\s*PR-(\d+)\s+executed\b`. `remaining = {1..total} − executed`.
- Skip DEC when `Status∈{done,abandoned}` or `remaining=∅`.
- Target = user-specified (refuse if already executed — redo via `--inplace`) else `min(remaining)`.
- For `ALL --auto`: enumerate all DECs, show queue with `(already done: PR-X, PR-Y)` annotations.
- Belt-and-braces: `git cat-file -e <sha>` on each claimed commit; missing → treat as remaining unless `--trust-log`.

### 2. Worktree (skip if `--inplace`)

Run git directly via `Bash`. No temp scripts. Paths:

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
WORKTREES_DIR="$REPO_ROOT/../$(basename "$REPO_ROOT").worktrees"
```

- single-PR: `WT_PATH=$WORKTREES_DIR/DEC-<padded>-pr-<M>-<slug>`, `BRANCH=refactor/DEC-<padded>-pr-<M>-<slug>`
- `--auto` one DEC: `WT_PATH=$WORKTREES_DIR/DEC-<padded>-<slug>`, `BRANCH=refactor/DEC-<padded>-<slug>`

Base: `--base` arg → `.arch-profile.yaml` `default-branch:` → `origin/HEAD` → `main` → `master`.

```bash
mkdir -p "$WORKTREES_DIR" && git worktree add -b "$BRANCH" "$WT_PATH" "$BASE"
```

If path exists: ask reuse / remove / abort.

### 3. Preflight (`--inplace` only)

Fail if `git status --porcelain` non-empty. Warn on main/master.

### 4. Rich preview (no re-analysis)

DEC is the plan of record. Render preview purely from DEC contents: diagram from Section 3, files/what-moves from PR entry in Section 4, callers/tests/risks/alternatives from Sections 1-2-7-8. Missing field → write `(not captured in DEC)`, never grep source.

Load `references/arch-execute-preview.md` for Mermaid template + pattern adaptations + section order.

Ask (single-PR): `yes | yes-all | no | show more | tweak: <what>`. `--auto`: `yes-all | no`. `ALL --auto`: `yes-all-decs | no`. On `tweak`, re-render. Loop until terminal.

### 5. Implement

Touch marker: `${TMPDIR:-/tmp}/architecture-first/<md5($WT_PATH or $REPO_ROOT)>-<session_id>.approved`.

Worktree mode: `Edit`/`Write` use absolute paths under `$WT_PATH`; `Bash` runs `cd "$WT_PATH" && …`.

**Scope discipline + post-implement diff guard: see `references/scope-guard.md`.** Both must pass before any commit. If guard restores anything, do NOT silently commit — report every blocked change and ask user.

### 6. Auto-mode loop (`--auto` / `yes-all` / `yes-all-decs`)

1. ONE worktree per DEC (DEC-level slug). Create once.
2. For each remaining PR:
   - Implement scope (step 5, with guard).
   - Run `commands.test` + `commands.build`. Fail → stop whole run, keep worktree, report failing PR + first 40 lines output. Do NOT push. User fixes then `/arch-execute <N> PR-<failed> --inplace`.
   - Commit: `refactor(<scope>): <PR title> [DEC-<id> PR-<M>/<total>]`.
   - Append DEC Execution log per-PR (progress survives aborts).
3. After final PR: push (step 7), cleanup (step 8).

`ALL --auto`: iterate DECs independently. Stop queue on first DEC's first failure.

Mid-run, single PR removing ≥ 200 lines triggers mass-deletion gate: pause, ask for `/arch-clean-approve`, resume.

### 7. Push (skip if `--inplace` or `--no-push`)

```bash
cd "$WT_PATH" && git push -u origin "$BRANCH"
```

Fail → keep worktree, show first 20 lines of error, tell user retry command. Record commit in Execution log anyway. Skip step 8.

### 8. Remove worktree (MUST RUN, MUST VERIFY)

Non-optional. Skip only on: `--keep`, `--inplace`, `--no-push`, push failed.

```bash
rm -f "$WT_PATH/node_modules" "$WT_PATH/tsconfig.build.tsbuildinfo" 2>/dev/null
cd "$REPO_ROOT" && git worktree remove "$WT_PATH"
```

(The first line drops symlinks and well-known build artifacts that would otherwise make `git worktree remove` refuse — only safe targets, never `rm -rf` arbitrary paths.)

Verify both:

```bash
[ ! -d "$WT_PATH" ] && git worktree list | grep -qv "$WT_PATH"
```

If either fails: do NOT force automatically. Report exact error + `git worktree remove --force "$WT_PATH"` for user. Never claim "worktree removed" unless both checks passed.

If a previous run left this worktree behind, `/arch-clean-worktrees` sweeps it explicitly without invoking the rest of `/arch-execute`.

### 9. Update DEC

Append to Execution log (in ORIGINAL checkout, not worktree):

```
- PR-<M> executed <YYYY-MM-DD>, commit <sha> on <branch> (worktree: <removed|kept at <path>|kept — push failed>) — tests <status>, build <status>[, auto: true]
```

`worktree:` field reflects observed state, not intent. Final PR → `Status: done`.

### 10. Report (verify before claiming)

Before report: if step 8 supposed to run but `$WT_PATH` still exists → report `worktree: kept — remove failed`, include force command, NOT "removed". If push supposed to run but `git ls-remote origin "$BRANCH"` empty → report `pushed: no (<error>)`, NOT "pushed".

Shape by actual state:

- Full auto success: `✓ PR-<M>/<total> done. branch: <b>, commit: <sha>, pushed, worktree removed. Open PR: <compare URL>. Next: /arch-execute <id> PR-<M+1>` (or `DEC done` on final).
- `--no-push` / push failed: branch/commit + `cd <wt> && git push …` + cleanup reminder.
- `--keep`: push OK + `git worktree remove <wt>` when done.
- `--inplace`: branch + push reminder.
- Remove failed: honest state + force command.
