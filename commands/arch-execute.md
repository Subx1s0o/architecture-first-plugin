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

### 5a. Scope discipline — refuse to touch anything outside the DEC's Files-touched list

Before writing a single line, build the **allow-list** from the DEC's PR-<M> entry (Section 4, "Files touched"). Add:

- Every file path explicitly listed as `CREATE` or `MODIFY` in the PR entry.
- Its direct test file siblings (e.g. `foo.service.spec.ts` for `foo.service.ts`) if the DEC's Tests section names them.
- Nothing else.

**Forbidden to touch** (never in the allow-list unless the DEC explicitly calls them out):

- Config/infrastructure: `nest-cli.json`, `tsconfig*.json`, `package.json`, `pnpm-lock.yaml`, `yarn.lock`, `Dockerfile*`, `docker-compose*.yml`, `.eslintrc*`, `.prettierrc*`, `jest.config*`, `vite.config*`, `next.config*`.
- Git infrastructure: `.gitignore`, `.git/*`, `.husky/*` (including `pre-commit`, `pre-push`, `commit-msg`).
- CI: `.github/**`, `.gitlab-ci.yml`, `.circleci/*`, `Makefile`.
- Docs not in the DEC: `README*`, `CHANGELOG*`, `docs/**` (except `docs/adr/**` and `docs/decomposition/**` which this plugin owns).

If a refactor genuinely needs to touch one of these (e.g. add a new `package.json` dependency for an extracted module), the DEC's PR entry must list it explicitly under Files touched. If it's not listed, stop and ask the user to amend the DEC first. Do not "just include it because it obviously needs changing".

### 5b. Post-implement diff guard — before any commit

After implementing but **before** `git add`, run:

```bash
cd "$WT_PATH" && git status --porcelain
```

Review every line. For each changed path:

1. **Modified (`M`)** — must be in the allow-list. If not, `git restore -- <path>` and report a warning.
2. **Added (`A` / `??`)** — must be in the allow-list (as a CREATE entry). If not, `git restore --source=HEAD --staged --worktree -- <path>` (or `rm` if untracked). Report a warning.
3. **Deleted (`D`)** — the allow-list must include this path explicitly as a deletion. The DEC should have marked it `DELETE` in Files touched. If the path is NOT in the allow-list, this is an accidental deletion: run `git checkout HEAD -- <path>` to restore it, and report loudly: `⚠ Blocked accidental deletion of <path> — not listed in DEC-<id> PR-<M> Files touched.`
4. **Renamed (`R`)** — both source and target must be in the allow-list.

If **any** restore happened during the guard, do NOT silently commit as if nothing was wrong. Report every blocked change in the Report step, and ask the user whether to proceed with the cleaned-up diff, abort the PR, or amend the DEC to include the originally-unintended changes.

This guard runs **every** PR iteration in `--auto` mode, not just the first one. Accidental deletions compound fast across multiple PRs.

### 5-auto. Auto-mode loop

For `--auto` / `yes-all` / `yes-all-decs`:

1. ONE worktree per DEC (DEC-level slug). Create once.
2. For each remaining PR in order:
   - Implement the PR's scope.
   - Run `commands.test` + `commands.build`. On failure: stop the whole auto-run, leave worktree, report the failing PR + first 40 lines of output. Do NOT push. User fixes and resumes with `/arch-execute <N> PR-<failed> --inplace` from inside the worktree.
   - Commit: `refactor(<scope>): <PR title> [DEC-<id> PR-<M>/<total>]`.
   - Append original DEC's Execution log per-PR so progress survives aborts.
3. After final PR commits: push (step 6), then cleanup (step 7).

For `ALL --auto`: iterate DECs. Each DEC = independent worktree/branch, all branched from the same base. Stop entire queue on first DEC's first failure.

Mid-run, a single PR that removes ≥ 200 lines triggers the mass-deletion gate: pause, ask for `/arch-clean-approve`, resume.

### 6. Push (skip if `--inplace` or `--no-push`)

```bash
cd "$WT_PATH" && git push -u origin "$BRANCH"
```

On failure: keep worktree, show git error (first 20 lines), tell user how to retry with `cd <wt> && git push …`. Record commit in Execution log anyway. **Do NOT proceed to step 7** — worktree must stay for retry.

### 7. Remove worktree — MUST RUN, verify success

**This step is not optional.** Every auto-run and every default single-PR run ends here. The only cases where it's skipped:

- `--keep` flag was passed
- `--inplace` mode (no worktree existed)
- `--no-push` flag (worktree kept for manual push)
- Push failed in step 6 (worktree kept for retry)

Otherwise you **must**:

```bash
cd "$REPO_ROOT" && git worktree remove "$WT_PATH"
```

Then **verify** with one of these (must succeed, otherwise report the state truthfully):

```bash
[ ! -d "$WT_PATH" ] && echo "removed" || echo "still exists"
git worktree list | grep -q "$WT_PATH" && echo "still registered" || echo "unregistered"
```

Both checks should show the worktree gone and unregistered. If the remove failed (nested untracked files, permission, etc.) — do NOT retry with `--force` automatically. Report the exact error and tell the user the precise command: `git worktree remove --force "$WT_PATH"`.

**Never claim "worktree removed" in the report unless the verification above passed.** Under-promising here is fine; lying about state is not.

### 8. Update DEC

Append to Execution log (in the ORIGINAL checkout, not the worktree):

```
- PR-<M> executed <YYYY-MM-DD>, commit <sha> on <branch> (worktree: <removed|kept at <path>|kept — push failed>) — tests <status>, build <status>[, auto: true]
```

The worktree field must reflect what step 7's verification actually observed — not what the command was supposed to do.

Final PR of a DEC → update `Status:` to `done`.

### 9. Report — self-check before claiming success

Before emitting the report, run one last verification:

- If step 7 was supposed to run but `$WT_PATH` still exists → the report says `worktree: kept — remove failed (<reason>)` with the exact remove command. It does NOT say "worktree removed".
- If push was supposed to run but `git ls-remote origin "$BRANCH"` returns nothing → say `pushed: no (<error>)`, not "pushed".

Report shapes:

- Full auto success (step 7 verified clean): `✓ PR-<M>/<total> done. branch: <b>, commit: <sha>, pushed, worktree removed. Open PR: https://github.com/<org>/<repo>/compare/<b>?expand=1. Next: /arch-execute <id> PR-<M+1>` (or `DEC done` on final).
- `--no-push` / push failed: branch/commit info + `cd <wt> && git push -u origin <b>`; cleanup reminder.
- `--keep`: push success + `git worktree remove <wt>` when done.
- `--inplace`: branch + reminder to push.
- Remove failed: honest state + the `git worktree remove --force` line for the user.

### Pre-start hygiene — auto-collect orphan worktrees

As the very first thing when `/arch-execute` runs (before step 1), glob `<repo>.worktrees/DEC-*` and for each `$WT`:

- If `git -C "$WT" rev-parse HEAD 2>/dev/null` shows a commit that appears in any DEC's Execution log with status `executed + pushed`, AND `git ls-remote origin <branch>` confirms the branch is on origin → run `git worktree remove "$WT"` silently. Report at the end: `Cleaned N orphan worktrees from previous runs.`
- Otherwise leave alone (either partial/failed runs user hasn't resolved, or `--keep` worktrees).

This prevents leftover worktrees from accumulating if earlier runs forgot to clean up.
