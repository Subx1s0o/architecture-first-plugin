Execute one PR from a decomposition plan. Default: create a sibling git worktree so my current checkout stays untouched.

Argument forms: <DEC-N|N> [PR-M|M|next] [--inplace] [--base <branch>].

Steps:
1. Resolve DEC via glob docs/decomposition/DEC-<padded>-*.md. Parse PR sequence + Execution log. Pick the target PR (first unexecuted by default).

2. Worktree mode (default): WT_PATH=$(dirname $(git rev-parse --show-toplevel))/$(basename).worktrees/DEC-<padded>-pr-<M>-<slug>, BRANCH=refactor/DEC-<padded>-pr-<M>-<slug>, BASE=--base || .arch-profile default-branch || origin/HEAD || main || master. `git worktree add -b $BRANCH $WT_PATH $BASE`. If path exists: ask reuse/remove/abort. All subsequent edits and bash use $WT_PATH.

3. Inplace mode (--inplace): fail if git dirty; warn if on main/master.

4. RICH PREVIEW before asking yes/no. Sections in order:
   - Header: DEC-<id> · PR-<M>/<total> — <PR title>, Pattern, estimated diff size.
   - Architecture before→after — Mermaid `flowchart LR` with two subgraphs (BEFORE | AFTER), nodes annotated with LoC, callers shown, delegation arrows dashed.
   - Files touched — table with clickable repo-root-relative markdown links: [`file.ts`](path/to/file.ts). Columns: Action | File | Reason.
   - What moves — inline-code list of symbols grouped by intent.
   - Callers that continue to work — bullets with links, one line why each stays green.
   - Tests — existing pins (with [file:line](path#Lline)), new tests this PR adds, coverage gaps.
   - Risks + mitigation — one per line.
   - Alternatives considered — chosen vs rejected + why, pulled from the DEC.
   - Destination — worktree path, branch, base.
   - Ask: exactly this block —
     ```
     Ready to implement? Reply with one of:
       yes                         — proceed as shown
       no                          — abort, no changes
       show more                   — dump the full PR section from the DEC file
       tweak: <what to change>     — adjust the plan, I'll re-preview
     ```
   On `tweak: <...>`, re-derive affected sections (and the diagram if structure changed) and print the full preview again. Loop until yes/no/show more.

5. On yes, implement the PR — no re-planning, DEC is the plan.

6. Run commands.test + commands.build from .arch-profile.yaml at the active path. Failure in worktree: leave it for inspection. Inplace: git restore.

7. On green: commit `refactor(<scope>): <PR title> [DEC-<padded> PR-<M>/<total>]`. Do NOT push.

8. Append Execution log in the ORIGINAL checkout's DEC file: date, sha, branch, worktree path, tests/build status.

9. Report: `cd <worktree>; git push -u origin <branch>`. Say next PR. Remind how to remove worktree after merge.
