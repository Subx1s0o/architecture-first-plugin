Execute one PR from a decomposition plan. Default flow: create a sibling git worktree → implement → test + build → commit → push → remove worktree. Result: clean checkout + ready-to-PR branch on origin.

Argument forms: <DEC-N|N> [PR-M|M|next] [--inplace] [--no-push] [--keep] [--base <branch>].

Steps:

1. Resolve DEC via glob docs/decomposition/DEC-<padded>-\*.md. Parse PR sequence + Execution log. Pick the target PR.

2. Worktree mode (default): WT_PATH=$(dirname $(git rev-parse --show-toplevel))/$(basename).worktrees/DEC-<padded>-pr-<M>-<slug>, BRANCH=refactor/DEC-<padded>-pr-<M>-<slug>, BASE=--base || .arch-profile default-branch || origin/HEAD || main || master. `git worktree add -b $BRANCH $WT_PATH $BASE`. If path exists: ask reuse/remove/abort.

3. Inplace mode (--inplace): fail if git dirty; warn if on main/master; no push, no remove.

4. RICH PREVIEW before yes/no. **Do NOT re-analyze the codebase here** — the DEC file is the plan of record. Render the preview PURELY from the DEC's contents: architecture diagram from Section 3, files/what-moves from the PR entry in Section 4, callers/tests/risks/alternatives from Sections 1-2-7-8. No grep, no new Read calls on source files. If a field is missing from the DEC, write `(not captured in DEC)` rather than going to fill the gap. Sections: Header / Architecture before→after (Mermaid flowchart LR with BEFORE+AFTER subgraphs, LoC on nodes, callers shown explicitly, delegation arrows dashed). STRICT Mermaid rules: use <br/> for line breaks (never \n which renders literally), give every edge a label (A -->|'calls'| B, A -.->|'delegates to'| B), use unique node IDs across subgraphs (rB vs rA), highlight the new/extracted unit with `style newId fill:#1b4332,stroke:#2d6a4f,color:#fff`. If the DEC lacks caller info, show a generic `clients[...]` node and note it — don't invent callers / Files touched (clickable repo-root-relative markdown links) / What moves / Callers that continue to work / Tests (existing pins + new + gaps) / Risks + mitigation / Alternatives / Destination. Ask: `yes | no | show more | tweak: <what>`. On tweak re-render.

5. On yes, implement per the plan.

6. Run commands.test + commands.build from .arch-profile.yaml. On failure in worktree: keep it, report. Inplace: git restore.

7. Commit: `refactor(<scope>): <PR title> [DEC-<padded> PR-<M>/<total>]`.

7a. Auto-push (default, unless --no-push or inplace): `cd $WT_PATH && git push -u origin $BRANCH`. On failure: keep worktree, show git error (first 20 lines), tell user how to retry. Still record commit in execution log so work isn't lost.

7b. Auto-remove worktree (default, unless --keep or --no-push or inplace or push failed): `cd $REPO_ROOT && git worktree remove $WT_PATH`. Never force automatically — on failure tell user how (`--force`).

8. Append the ORIGINAL checkout's DEC file Execution log: date, sha, branch, worktree path, push status, tests/build.

9. Report — pick the shape that matches what happened: full-auto (pushed + removed) shows the GitHub compare URL; --no-push shows manual push + remove commands; --keep shows push success + how to remove later; inplace just shows branch + reminder to push.
