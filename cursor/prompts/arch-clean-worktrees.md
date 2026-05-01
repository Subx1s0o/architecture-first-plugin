Sweep stale architecture worktrees in `<repo>.worktrees/`. Removes any whose branch is pushed to origin and clean. Reports kept ones with reason.

Modes:
default: /arch-clean-worktrees — sweep all eligible
dry-run: /arch-clean-worktrees --dry — list what would be removed
force: /arch-clean-worktrees --force — remove dirty / unpushed too (asks confirmation; warns about lost work)

Steps:

1. REPO_ROOT=$(git rev-parse --show-toplevel); WORKTREES_DIR="$REPO_ROOT/../$(basename "$REPO_ROOT").worktrees". List `$WORKTREES_DIR/DEC-*`. If none → say so and stop.

2. For each WT, compute: BRANCH = git -C $WT branch --show-current; PUSHED = `git ls-remote --exit-code origin "$BRANCH"`success?; DIRTY =`cd $WT && git status --porcelain`non-empty?; AHEAD =`git -C $WT rev-list --count "@{upstream}"..HEAD 2>/dev/null`. Decide action by table: pushed+clean+ahead=0 → remove; anything else → keep (in --force, remove with warning). --dry: never remove.

3. Pre-remove cleanup: drop the `node_modules` symlink and well-known build artifacts (`tsconfig.build.tsbuildinfo`, `dist/`, `.next/`) inside the worktree if they exist — otherwise `git worktree remove` may refuse. Never `rm -rf` arbitrary files.

4. Remove: `cd $REPO_ROOT && git worktree remove "$WT_PATH"`. Verify both `[ ! -d "$WT_PATH" ]` and `git worktree list | grep -qv "$WT_PATH"`. If either fails — DO NOT `--force` automatically. Print the user the exact `git worktree remove --force "$WT_PATH"` command, mark this row `remove failed`, continue.

5. Report a table: Worktree | Branch | Pushed | Dirty | Ahead | Action | Reason. End with `Cleaned N, kept M` (or `Would clean N, would keep M` in --dry). For each kept row, suggest the next user action (commit/stash/push/delete). Remind that branches are NOT deleted by this command — `git worktree add <path> <branch>` recreates the worktree on demand.
