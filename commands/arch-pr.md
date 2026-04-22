---
description: Architectural review of a PR — yours or someone else's. Accepts PR number (via gh), branch name, or URL. Same red-flag rules as /arch-review but on arbitrary diff.
---

Args: one of
- `123` — PR number (requires `gh`).
- `https://github.com/<org>/<repo>/pull/<N>` — URL.
- `feature/foo` — local or remote branch name, diffed against repo default branch.
- `<sha>..<sha>` — explicit diff range.

Steps:

1. Resolve to a diff:
   - PR number / URL → `gh pr diff <N>` (or `gh pr view <N> --json …` for metadata).
   - Branch name → `git diff $(git merge-base origin/HEAD <branch>)..<branch>` (or `origin/<branch>` if local absent).
   - Sha range → `git diff <range>`.
   - If `gh` is absent for PR-URL case: ask user to `brew install gh` or paste the diff manually.
2. Identify changed source files. For each:
   - Module + layer (via `.arch-profile.yaml` or stack profile).
   - Flags: imports from another module's internals (not public barrel), new event emissions without a subscriber grep-found, new queue jobs without a processor, new external/RPC calls duplicating existing, files over stack LoC threshold, new cycles.
3. Produce the same table as `/arch-review`:

| Severity | Location | Finding | Suggested seam |
|---|---|---|---|
| high/med/low | file:line | what couples to what | interface / event / port |

4. Append a summary:
   - `<N>` changed files, `<K>` modules touched.
   - PR is XS / S / M / L per tier rules.
   - Overall verdict: approve / request changes / needs ADR.

No code edits. No file writes. If user says "write findings to the PR", offer `gh pr comment <N> --body "$(…)"` as a next step — do not run it automatically.
