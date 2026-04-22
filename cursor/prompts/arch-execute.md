Execute one PR from a decomposition plan. Default: create a sibling git worktree so my current checkout stays untouched and I can keep working.

Argument forms: <DEC-N|N> [PR-M|M|next] [--inplace] [--base <branch>].

Steps:
1. Resolve DEC via glob docs/decomposition/DEC-<padded>-*.md. If missing, say so and stop. Parse PR sequence + Execution log. Pick the target PR (first unexecuted by default).

2. Worktree mode (default):
   - WORKTREES_DIR = $(dirname $(git rev-parse --show-toplevel))/$(basename $(git rev-parse --show-toplevel)).worktrees
   - WT_PATH = $WORKTREES_DIR/DEC-<padded>-pr-<M>-<slug>
   - BRANCH = refactor/DEC-<padded>-pr-<M>-<slug>
   - BASE = --base arg || .arch-profile.yaml default-branch || origin/HEAD || main || master
   - `git worktree add -b $BRANCH $WT_PATH $BASE`
   - If path exists, ask: reuse / remove / abort
   - All subsequent edits use absolute paths under $WT_PATH; bash commands `cd $WT_PATH && …`.

3. Inplace mode (--inplace): fail if git tree dirty; warn if on main/master.

4. Show PR scope and destination (worktree path + branch OR current branch). Ask yes/no/show more.

5. Implement the PR — no re-planning, DEC is the plan.

6. Run commands.test + commands.build from .arch-profile.yaml at the active path. On failure in worktree mode: leave worktree for inspection. On failure inplace: git restore .

7. On green: commit with `refactor(<scope>): <PR title> [DEC-<padded> PR-<M>/<total>]`. Do NOT push.

8. Append Execution log in the ORIGINAL checkout's DEC file with date, sha, branch, worktree path, tests/build status.

9. Report with instructions: `cd <worktree>; git push -u origin <branch>`. Say next PR. Remind user how to remove the worktree after merge: `git worktree remove <path>`.
