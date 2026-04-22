---
description: Execute one PR, all PRs of one DEC, or every DEC in the repo. Default: sibling git worktree → implement → tests + build → commit → push → remove. `--auto` stacks all PRs of a DEC on one branch after one yes-all. `ALL --auto` iterates every DEC. Flags: --inplace, --no-push, --keep, --base.
---

Args: `<DEC-N|N|ALL>` [`<PR-M|M|next>`] [flags].

Modes:

- `/arch-execute 4` — PR-1 of DEC-004, per-PR preview.
- `/arch-execute 4 PR-2` / `4 next` — specific / next unexecuted PR.
- `/arch-execute 4 --auto` — all remaining PRs, ONE branch `refactor/DEC-004-<slug>`, N commits, one push.
- `/arch-execute ALL --auto` — every DEC with remaining PRs, each in its own branch, stop on first failure.

Flags: `--no-push` (commit only), `--keep` (push, keep worktree), `--inplace` (no worktree, no push; refuse if paired with `--auto`), `--base <branch>` (branch base).

## Steps

### 1. Parse DEC state — the Execution log is the only source of truth

- Normalize id: `4` / `DEC-4` → `DEC-004`. Glob `docs/decomposition/DEC-<padded>-*.md`. Missing → "run `/arch-decompose` first".
- Read Status header + PR sequence (Section 4) + Execution log.
- Executed PR numbers via regex `^\s*-\s*PR-(\d+)\s+executed\b`. `remaining = {1..total} − executed`.
- Skip DEC when `Status∈{done,abandoned}` or `remaining=∅`.
- Target PR = user-specified (refuse if already executed — redo via `--inplace` in the worktree) else `min(remaining)`.
- For `ALL --auto`: enumerate every DEC, show queue annotated with `(already done: PR-X, PR-Y)` per DEC as a sanity check.
- Belt-and-braces: `git cat-file -e <sha>` on each claimed commit; if missing, treat as remaining unless `--trust-log`.

### 2. Worktree (skip if `--inplace`)

Run git directly via `Bash`. **No temporary scripts** — one call per git command, chain with `&&`. Paths:

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
REPO_NAME="$(basename "$REPO_ROOT")"
WORKTREES_DIR="$REPO_ROOT/../${REPO_NAME}.worktrees"
```

Names:

- single-PR: `WT_PATH=$WORKTREES_DIR/DEC-<padded>-pr-<M>-<slug>`, `BRANCH=refactor/DEC-<padded>-pr-<M>-<slug>`
- `--auto` one DEC: `WT_PATH=$WORKTREES_DIR/DEC-<padded>-<slug>`, `BRANCH=refactor/DEC-<padded>-<slug>`

Base: `--base` arg ‖ `.arch-profile.yaml` `default-branch:` ‖ `origin/HEAD` ‖ `main` ‖ `master`.

```bash
mkdir -p "$WORKTREES_DIR" && git worktree add -b "$BRANCH" "$WT_PATH" "$BASE"
```

If `$WT_PATH` exists: ask reuse / remove / abort.

### 3. Preflight (`--inplace` only)

Fail if `git status --porcelain` non-empty. Warn on main/master.

### 4. Rich preview

**Do NOT re-analyze source.** DEC is the plan of record. Render purely from DEC file contents: diagram from Section 3, files/what-moves from the PR entry in Section 4, callers/tests/risks/alternatives from Sections 1-2-7-8. Missing field → write `(not captured in DEC)`, never silently fill by grepping source.

Load `references/arch-execute-preview.md` for Mermaid template + pattern adaptations + section order.

Ask (single-PR mode):

```
yes | yes-all | no | show more | tweak: <what>
```

Ask (`--auto` one DEC): `yes-all | no`. (`ALL --auto`): `yes-all-decs | no`. On `tweak`, re-render affected sections. Loop until terminal.

### 5. Implement

Touch session approval marker: `${TMPDIR:-/tmp}/architecture-first/<md5($WT_PATH or $REPO_ROOT)>-<session_id>.approved`.

In worktree mode, all `Edit`/`Write` use absolute paths under `$WT_PATH`; `Bash` runs `cd "$WT_PATH" && …`.

### 5-auto. Auto-mode loop

For `--auto` / `yes-all` / `yes-all-decs`:

1. ONE worktree per DEC (DEC-level slug). Create once.
2. For each remaining PR in order:
   - Implement the PR's scope.
   - Run `commands.test` + `commands.build`. On failure: stop the whole auto-run, leave worktree, report the failing PR + first 40 lines of output. Do NOT push. User fixes and resumes with `/arch-execute <N> PR-<failed> --inplace` from inside the worktree.
   - Commit: `refactor(<scope>): <PR title> [DEC-<id> PR-<M>/<total>]`.
   - Append original DEC's Execution log per-PR so progress survives aborts.
3. After final PR commits: one `git push -u origin "$BRANCH"` (unless `--no-push`), then `git worktree remove "$WT_PATH"` (unless `--keep`).

For `ALL --auto`: iterate DECs. Each DEC = independent worktree/branch, all branched from the same base. Stop entire queue on first DEC's first failure.

Mid-run, a single PR that removes ≥ 200 lines triggers the mass-deletion gate: pause, ask for `/arch-clean-approve`, resume.

### 6. Verify + 7. Commit + 7a. Push + 7b. Remove worktree

Single-PR mode: same per-PR commit/push/remove as step 5-auto does per iteration.

On push failure: keep worktree, show git error (first 20 lines), tell user how to retry. Still record commit in Execution log.

### 8. Update DEC

Append to Execution log (in the ORIGINAL checkout, not the worktree):

```
- PR-<M> executed <YYYY-MM-DD>, commit <sha> on <branch> (worktree: <path>) — tests <status>, build <status>[, auto: true]
```

Final PR of a DEC → update `Status:` to `done`.

### 9. Report

Shape by what happened:

- Full auto success: `✓ PR-<M>/<total> done. branch: <b>, commit: <sha>, pushed, worktree removed. Open PR: https://github.com/<org>/<repo>/compare/<b>?expand=1. Next: /arch-execute <id> PR-<M+1>` (or `DEC done` on final).
- `--no-push` / push failed: branch/commit info + `cd <wt> && git push -u origin <b>`; cleanup reminder.
- `--keep`: push success + `git worktree remove <wt>` when done.
- `--inplace`: branch + reminder to push.
