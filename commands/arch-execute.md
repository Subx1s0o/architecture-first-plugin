---
description: Execute PRs from decomposition plans in a sibling git worktree. `--auto` stacks all PRs of a DEC on one branch and opens a draft PR. `ALL --auto` iterates every DEC. Flags: --inplace, --no-push, --no-pr, --keep, --base, --label.
---

Args: `<DEC-N|N|ALL>` [`<PR-M|M|next>`] [flags].

## Modes

- `/arch-execute 4` — PR-1 of DEC-004 with per-PR preview.
- `/arch-execute 4 PR-2` / `4 next` — specific / next unexecuted.
- `/arch-execute 4 --auto` — all remaining PRs on ONE branch `refactor/DEC-004-<slug>`, one push, opens **draft PR automatically**.
- `/arch-execute ALL --auto` — every DEC with remaining PRs, stop on first failure. Each DEC gets its own draft PR.

Flags: `--no-push` (commit only), `--no-pr` (push but don't open PR), `--keep` (push, keep worktree), `--inplace` (no worktree; refuse with `--auto`), `--base <branch>`, `--label <name>` (PR label, default `arch-bot`).

**PR creation defaults:**

- `--auto` mode → draft PR opened automatically (label: `arch-bot`)
- single-PR mode → no PR by default; pass `--pr` to opt in
- `--no-pr` always wins; useful for local dry-runs

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

Fail → keep worktree, show first 20 lines of error, tell user retry command. Record commit in Execution log anyway. Skip steps 7.5 + 8.

### 7.5. Open PR (skip if `--no-pr`, `--inplace`, `--no-push`, push failed, or single-PR mode without `--pr`)

Open a **draft** PR automatically so the user sees the work landing on GitHub the moment the branch is pushed. Eliminates the manual `gh pr create` step that every CI workflow used to write by hand.

**When this runs:**

- `--auto` mode (single DEC or `ALL`): YES, by default
- single-PR mode: NO, unless `--pr` is passed
- Always skip if `--no-pr`

**Build the PR title:**

- single-PR with `--pr`: `refactor(<scope>): <PR title from DEC Section 4> [DEC-<id> PR-<M>/<total>]`
- `--auto`: `refactor(<scope>): <DEC title from Section 1 first sentence> [DEC-<id>]`

`<scope>` = the module slug from the DEC's target path (`src/portfolios/portfolios.resolver.ts` → `portfolios`). Match the convention used by recent merged refactor PRs in the repo if obvious from `git log --oneline -10`.

**Build the PR body** (markdown):

```
## Summary

<one-paragraph description from DEC Section 1 — the "Why">

Source plan: [`docs/decomposition/DEC-<id>-<slug>.md`](docs/decomposition/DEC-<id>-<slug>.md)

## What this PR does

<bullet list copied from DEC Section 4 PR sequence — one bullet per executed PR-N, with its commit subject>

## Verification

- `<commands.test from .arch-profile.yaml>` — passed before push
- `<commands.build from .arch-profile.yaml>` — passed before push

## How to review

Read the DEC plan first, then walk the diff in PR-step order. Mermaid before/after diagrams live in the DEC file.

---

Generated by `architecture-first` plugin. Marked **draft** for human review.
```

If any DEC field is missing for a section, write `(not captured in DEC)` — never re-analyze source.

**Run:**

```bash
LABEL="${LABEL:-arch-bot}"   # from --label flag, default arch-bot
PR_URL=$(cd "$WT_PATH" && gh pr create \
  --draft \
  --base "$BASE" \
  --head "$BRANCH" \
  --label "$LABEL" \
  --title "$PR_TITLE" \
  --body "$PR_BODY" 2>&1) || PR_OPEN_FAILED=1
```

**Failure handling** (do NOT abort the run):

- `gh` not installed / not authenticated → print one-line warning + the `gh pr create` command for user to run manually. Continue to step 8.
- Label doesn't exist → retry once without `--label`, warn user that the label needs creating. Continue.
- API rate-limited / network → print error + retry command. Continue to step 8.

In all cases, **never fail the run because of PR creation** — the branch is pushed, the work exists, the PR is the cherry on top.

**On success:**

- Print: `🔗 PR opened: <PR_URL>`
- If env var `GITHUB_STEP_SUMMARY` is set, append:

  ```bash
  if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
    echo "## ✅ arch-execute opened a PR" >> "$GITHUB_STEP_SUMMARY"
    echo "$PR_URL" >> "$GITHUB_STEP_SUMMARY"
  fi
  ```

  This puts the PR URL on the GitHub Actions run dashboard without needing to scroll the log.

- Record `pr: <PR_URL>` field in the Execution log alongside `pushed: yes`.

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
- PR-<M> executed <YYYY-MM-DD>, commit <sha> on <branch> (worktree: <removed|kept at <path>|kept — push failed>) — tests <status>, build <status>[, auto: true][, pr: <URL>]
```

`worktree:` field reflects observed state, not intent. Final PR → `Status: done`.

### 10. Report (verify before claiming)

Before report: if step 8 supposed to run but `$WT_PATH` still exists → report `worktree: kept — remove failed`, include force command, NOT "removed". If push supposed to run but `git ls-remote origin "$BRANCH"` empty → report `pushed: no (<error>)`, NOT "pushed". If step 7.5 supposed to run but PR URL was not captured → report `pr: failed (<error>)` with the manual `gh pr create` command, NOT "PR opened".

Shape by actual state:

- Full auto success **with PR**: `✓ PR-<M>/<total> done. branch: <b>, commit: <sha>, pushed, worktree removed. 🔗 PR: <PR_URL>. Next: /arch-execute <id> PR-<M+1>` (or `DEC done` on final).
- Full auto success without PR (`--no-pr` or single-PR without `--pr`): `✓ … pushed, worktree removed. Open PR: <compare URL>` (compare URL, not actual PR).
- `--no-push` / push failed: branch/commit + `cd <wt> && git push …` + cleanup reminder. No PR step.
- PR creation failed (push succeeded): full success line + `⚠ PR not opened: <error>. Manual: gh pr create --draft --base <base> --head <branch> ...`. Run is still considered successful overall.
- `--keep`: push OK + `git worktree remove <wt>` when done.
- `--inplace`: branch + push reminder.
- Remove failed: honest state + force command.
