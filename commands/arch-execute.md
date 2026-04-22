---
description: Execute one PR from a decomposition plan produced by /arch-decompose. Creates a sibling git worktree (default) so your current checkout stays untouched — you can keep working. Implements the scope, runs tests + build, commits on green, appends the DEC file. Use --inplace for the legacy same-checkout behaviour.
---

Takes: `<DEC-N|N>` optionally followed by `<PR-M|M|next>` and optional flags.

## Argument forms

- `/arch-execute 4` → PR-1 of DEC-004 in a fresh worktree
- `/arch-execute DEC-004 PR-2` → PR-2 specifically, in a worktree
- `/arch-execute 4 --inplace` → old behaviour (requires clean tree, mutates current checkout)
- `/arch-execute 4 --base develop` → base the branch off `develop` instead of the repo default

## Steps

### 1. Resolve the DEC file and PR
- Normalize id: `4` → `DEC-004`, globbed at `docs/decomposition/DEC-<padded>-*.md`. If missing → stop and say "run `/arch-decompose` first".
- Parse: Target, chosen Pattern, full PR sequence, Execution log.
- If PR not given, pick the lowest PR not in the Execution log. If all done → stop and say so.

### 2. Provision isolated worktree (default)

**Skip this whole section if `--inplace` was passed.**

- Derive paths:
  - `REPO_ROOT = $(git rev-parse --show-toplevel)`
  - `REPO_NAME = basename of REPO_ROOT`
  - `WORKTREES_DIR = $REPO_ROOT/../${REPO_NAME}.worktrees`  (sibling dir; add it to the user's global gitignore if they want it out of IDE)
  - `WT_PATH = $WORKTREES_DIR/DEC-<padded>-pr-<M>-<slug>`
  - `BRANCH = refactor/DEC-<padded>-pr-<M>-<slug>` (slug from PR-M title, kebab-case, ≤ 40 chars)
- Resolve the base branch: first of `--base <name>` / `.arch-profile.yaml` `default-branch:` / `origin/HEAD` / `main` / `master` that exists.
- `mkdir -p "$WORKTREES_DIR"`
- If `"$WT_PATH"` already exists:
  - Tell the user and ask: reuse (work in it as-is, no new branch), blow away (`git worktree remove --force "$WT_PATH"`), or abort.
- Otherwise create: `git worktree add -b "$BRANCH" "$WT_PATH" "$BASE"`
- Copy `.arch-profile.yaml` if it only exists in the current checkout (untracked); otherwise it's already there via git.
- **The user's original checkout is never modified. They can keep working on whatever branch/feature they have.**

### 3. Preflight (inplace mode only)
- `git status --porcelain` — if non-empty, stop and say: "Working tree has uncommitted changes. Either commit/stash them, drop `--inplace`, or pass `--inplace --force` (not recommended)."
- If on main/master, warn and suggest a named branch.

### 4. Display scope + confirm
Show the user: target file, PR-<M> scope (files touched, seams, rollout), and the destination:
- worktree mode: `→ worktree: $WT_PATH, branch: $BRANCH, base: $BASE`
- inplace mode: `→ current checkout, branch: $(git branch --show-current)`

Ask: `Implement PR-<M>? [yes / no / show more]`.

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
- **No push.** User reviews and pushes manually.

### 8. Update the DEC file
Append the Execution log (in the ORIGINAL checkout's DEC file, not the worktree's — the source of truth is the user's main checkout):
```
- PR-<M> executed <YYYY-MM-DD>, commit <sha> on <branch> (worktree: <path>) — tests ✓, build ✓
```

### 9. Report + cleanup guidance

**Worktree mode:**
```
✓ PR-<M> done.
  worktree: /path/to/repo.worktrees/DEC-001-pr-1-portfolio-service
  branch:   refactor/DEC-001-pr-1-portfolio-service
  commit:   <sha>

Review the diff, push when ready:
  cd /path/to/repo.worktrees/DEC-001-pr-1-portfolio-service
  git push -u origin refactor/DEC-001-pr-1-portfolio-service

Next PR: /arch-execute <id> PR-<M+1>  (will create its own worktree)

When the PR is merged, clean up:
  git worktree remove /path/to/repo.worktrees/DEC-001-pr-1-portfolio-service
```

**Inplace mode:** as before — user is already on the branch, just needs to push.

If this was the final PR of the DEC, update the file header `Status:` to `done` and add a concluding line to Execution log.
