---
description: Sweep stale architecture worktrees in `<repo>.worktrees/`. Removes any whose branch is pushed to origin and clean. Reports kept ones with reason. Use when worktrees pile up after `/arch-execute` runs (especially across sessions).
---

Args: `[--dry|--force]`.

## Modes

- `/arch-clean-worktrees` — sweep all eligible (default).
- `/arch-clean-worktrees --dry` — list what would be removed without acting.
- `/arch-clean-worktrees --force` — also remove dirty / unpushed worktrees. Asks for explicit confirmation first; warns that uncommitted work will be lost.

## Steps

### 1. Discover worktrees

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
WORKTREES_DIR="$REPO_ROOT/../$(basename "$REPO_ROOT").worktrees"
ls -1d "$WORKTREES_DIR"/DEC-* 2>/dev/null
```

If no `<repo>.worktrees/DEC-*` paths exist → report "no architecture worktrees to clean" and stop.

### 2. Classify each worktree

For each `WT`:

- `BRANCH=$(git -C "$WT" branch --show-current)`
- `PUSHED=yes` if `git ls-remote --exit-code origin "$BRANCH"` succeeds, else `no`.
- `DIRTY=yes` if `cd "$WT" && git status --porcelain` non-empty, else `no`.
- `AHEAD=$(git -C "$WT" rev-list --count "@{upstream}"..HEAD 2>/dev/null || echo unset)` — local commits not on remote.

Decision matrix:

| pushed | dirty | ahead | action (default)          | action (--force) |
| ------ | ----- | ----- | ------------------------- | ---------------- |
| yes    | no    | 0     | **remove**                | remove           |
| yes    | yes   | 0     | keep (uncommitted)        | remove (warn)    |
| yes    | no    | >0    | keep (unpushed commits)   | remove (warn)    |
| yes    | yes   | >0    | keep                      | remove (warn)    |
| no     | \*    | \*    | keep (unpublished branch) | remove (warn)    |

`--dry`: never remove; just print the table.

### 3. Remove (mirrors `/arch-execute` step 8 verification)

For each worktree marked `remove`:

```bash
cd "$REPO_ROOT" && git worktree remove "$WT_PATH"
```

Then verify both:

```bash
[ ! -d "$WT_PATH" ] && git worktree list | grep -qv "$WT_PATH"
```

If either check fails: do NOT auto-`--force`. Report the exact `git worktree remove --force "$WT_PATH"` command for the user, mark this entry as `remove failed` in the report, continue with the next.

Symlinks inside the worktree (e.g. `node_modules` symlinked from main) and ignored build artifacts (`tsconfig.build.tsbuildinfo`, `.next/`, `dist/`) may cause `git worktree remove` to refuse. Before the remove, drop them:

```bash
rm -f "$WT_PATH/node_modules" "$WT_PATH/tsconfig.build.tsbuildinfo" 2>/dev/null
```

(Only safe to delete _symlinks_ and well-known build artifacts; do NOT `rm -rf` arbitrary files.)

### 4. Report

Emit a table:

```
| Worktree | Branch | Pushed | Dirty | Ahead | Action | Reason |
|---|---|---|---|---|---|---|
| DEC-005-portfolios-resolver | refactor/DEC-005-portfolios-resolver | yes | no | 0 | removed | clean and on origin |
| DEC-019-core-module-cycle | refactor/DEC-019-core-module-cycle | yes | no | 0 | removed | clean and on origin |
| DEC-002-portfolios-service | refactor/DEC-002-portfolios-service | yes | yes | 0 | kept | uncommitted local changes |
```

End line: `Cleaned <N> worktrees, kept <M>` (or in `--dry` mode: `Would clean <N>, would keep <M>`).

If any `kept` row exists, list the user-actionable next steps:

- For `uncommitted local changes`: `cd <wt> && git status` to inspect, commit or stash, then re-run.
- For `unpushed commits`: `cd <wt> && git push` first, then re-run.
- For `unpublished branch`: decide whether to push or delete; re-run after.

### 5. Branches stay

Removing a worktree does NOT delete the branch — local and remote refs are untouched. Recreating the worktree on demand is one command:

```bash
git worktree add "$WORKTREES_DIR/<slug>" "<branch>"
```

Mention this in the closing report so users don't worry the work is gone.
