---
description: Execute one PR from a decomposition plan produced by /arch-decompose. Takes DEC id/number and optionally a PR number. Implements the scope, runs tests + build from .arch-profile.yaml, commits on green, appends the DEC file.
---

Takes: `<DEC-N|N>` optionally followed by `<PR-M|M>` (default: first unexecuted PR).

## Argument forms

- `/arch-execute 4` → PR-1 of DEC-004 (first unexecuted)
- `/arch-execute DEC-004` → same as above
- `/arch-execute 4 PR-2` → PR-2 specifically
- `/arch-execute 4 2` → same
- `/arch-execute DEC-004 next` → next unexecuted PR (explicit)

## Steps

### 1. Resolve the DEC file
- Normalize the id: `4` → `DEC-004`, `DEC-4` → `DEC-004`, already-padded accepted.
- Glob `docs/decomposition/<padded>-*.md`. If missing: say "DEC-<id> not found; run `/arch-decompose` first" and stop.
- Read the file. Extract: Target, chosen Pattern, full PR sequence (Section 4), Success criteria (Section 8), Execution log (if any).

### 2. Resolve the PR
- If specified: use it. Error if out-of-range.
- Otherwise: pick the lowest PR number that does NOT appear in the Execution log. If all are done → say "All PRs for this DEC have been executed" and stop.

### 3. Preflight
- `git status --porcelain` — if non-empty, stop and say: "Working tree has uncommitted changes. Commit or stash first."
- Show the user the current branch. If on main/master/develop, recommend:
  `git checkout -b refactor/<DEC-id>-pr-<M>-<slug>` (do not auto-run; user's call).
- Display the PR scope: files changing, new seams, rollout notes, dependencies on earlier PRs.

### 4. Confirm
Ask: "Implement PR-<M> of DEC-<id> now? [yes / no / show more]".
- `show more` → dump the full PR section from the DEC file.
- `no` → stop.
- `yes` → proceed.

### 5. Implement
Invoke the architecture-first skill with the PR scope as the user request. The skill produces Section 1–3 grounded in the DEC plan (no re-planning — the plan already exists) and then writes Section 4 code directly, because the plan is approved via the DEC file.

Touch the session approval marker at `${TMPDIR:-/tmp}/architecture-first/<md5(CLAUDE_PROJECT_DIR)>-<session_id>.approved` so the hook allows edits.

### 6. Verify
Read `commands.test` and `commands.build` from `.arch-profile.yaml`:
- If both defined: run both. On either failure → `git restore .`, report the failure with the first 40 lines of output, leave working tree clean, stop.
- If neither defined: ask the user for the test command once.

### 7. Commit
On green:
- `git add -A`
- `git commit -m "refactor(<scope>): <PR title> [DEC-<id> PR-<M>/<total>]"` where `<scope>` is inferred from the paths changed (or the module name from `.arch-profile.yaml`), `<PR title>` is the first line of PR-<M> in the DEC file.
- Do NOT push — user pushes manually after reviewing.

### 8. Update the DEC file
Append to the Execution log section:
```
- PR-<M> executed <YYYY-MM-DD>, commit <sha> — tests <status>, build <status>
```

### 9. Report
- If PRs remain: `✓ PR-<M> done. Next: /arch-execute <id> PR-<M+1>`.
- If final PR: update the DEC `Status:` to `done` in the header. Say: `✓ DEC-<id> complete.`
- If the DEC has a linked ADR: remind the user to update the ADR status accordingly.
