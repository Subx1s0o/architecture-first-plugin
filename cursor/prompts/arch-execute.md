Execute one PR, all PRs of one DEC, or every DEC in the repo. Modes:
  single-PR (default): /arch-execute <DEC-N|N> [PR-M|next] — preview + yes/no per PR
  auto (one DEC):      /arch-execute <N> --auto — one worktree, one branch, N commits, one push at the end; no prompts between PRs
  auto (all DECs):     /arch-execute ALL --auto — each DEC in its own worktree + branch, done in sequence, one yes-all-decs confirmation at the top

Flags: --inplace (no worktree, no push; incompatible with --auto), --no-push, --keep, --base <branch>.

Steps:

1. Resolve DEC(s) by parsing DEC file(s) on disk. The Execution log is the SINGLE source of truth for what's been done — do not use conversation memory.
   Per DEC: parse Status, PR sequence, Execution log. Match execution lines by regex `^\s*-\s*PR-(\d+)\s+executed\b`. `remaining = {1..total} - executed`.
   Skip the DEC if Status is `done` / `abandoned`, or remaining is empty.
   For ALL --auto: glob docs/decomposition/DEC-*.md, sort by DEC number, show queue WITH `(already done: PR-X, PR-Y)` annotations so the user can sanity-check the parse.
   Optional belt-and-braces: `git cat-file -e <sha>` on each claimed commit; if missing, treat the PR as still-remaining unless --trust-log.
   If the user passes explicit PR-M and it's already in the log, refuse (tell them to re-run inside the worktree with --inplace).

2. Worktree mode (default): WT_PATH=$(dirname $(git rev-parse --show-toplevel))/$(basename).worktrees/DEC-<padded>-pr-<M>-<slug>, BRANCH=refactor/DEC-<padded>-pr-<M>-<slug>, BASE=--base || .arch-profile default-branch || origin/HEAD || main || master. `git worktree add -b $BRANCH $WT_PATH $BASE`. If path exists: ask reuse/remove/abort.

3. Inplace mode (--inplace): fail if git dirty; warn if on main/master; no push, no remove.

4. RICH PREVIEW before yes/no. **Do NOT re-analyze the codebase here** — the DEC file is the plan of record. Render the preview PURELY from the DEC's contents: architecture diagram from Section 3, files/what-moves from the PR entry in Section 4, callers/tests/risks/alternatives from Sections 1-2-7-8. No grep, no new Read calls on source files. If a field is missing from the DEC, write `(not captured in DEC)` rather than going to fill the gap. Sections: Header / Architecture before→after (Mermaid flowchart LR with BEFORE+AFTER subgraphs, LoC on nodes, callers shown explicitly, delegation arrows dashed). STRICT Mermaid rules: use <br/> for line breaks (never \n which renders literally), give every edge a label (A -->|'calls'| B, A -.->|'delegates to'| B), use unique node IDs across subgraphs (rB vs rA), highlight the new/extracted unit with `style newId fill:#1b4332,stroke:#2d6a4f,color:#fff`. If the DEC lacks caller info, show a generic `clients[...]` node and note it — don't invent callers / Files touched (clickable repo-root-relative markdown links) / What moves / Callers that continue to work / Tests (existing pins + new + gaps) / Risks + mitigation / Alternatives / Destination. Ask (single-PR): `yes | yes-all | no | show more | tweak: <what>`. Auto mode prompt: `yes-all` (one DEC) or `yes-all-decs` (every DEC). On tweak re-render. On yes-all / yes-all-decs, follow the auto-mode flow: one worktree per DEC with DEC-level slug (not PR-level), commit per PR with message `refactor(<scope>): <PR title> [DEC-<id> PR-<M>/<total>]`, run tests+build between each PR, stop and leave worktree on first failure, push + remove at the end of each DEC.

5. On yes, implement per the plan.

6. Run commands.test + commands.build from .arch-profile.yaml. On failure in worktree: keep it, report. Inplace: git restore.

7. Commit: `refactor(<scope>): <PR title> [DEC-<padded> PR-<M>/<total>]`.

7a. Auto-push (default, unless --no-push or inplace): `cd $WT_PATH && git push -u origin $BRANCH`. On failure: keep worktree, show git error (first 20 lines), tell user how to retry. Still record commit in execution log so work isn't lost.

7b. Auto-remove worktree (default, unless --keep or --no-push or inplace or push failed): `cd $REPO_ROOT && git worktree remove $WT_PATH`. Never force automatically — on failure tell user how (`--force`).

8. Append the ORIGINAL checkout's DEC file Execution log: date, sha, branch, worktree path, push status, tests/build.

9. Report — pick the shape that matches what happened: full-auto (pushed + removed) shows the GitHub compare URL; --no-push shows manual push + remove commands; --keep shows push success + how to remove later; inplace just shows branch + reminder to push.
