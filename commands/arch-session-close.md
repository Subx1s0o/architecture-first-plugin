---
description: Close the architecture session. Honest ledger of what shipped vs what was ceremony. Output to user only, never to repo.
---

Produce a session-close ledger so the user can calibrate expectations for next session. This command writes nothing to the repo — its output is conversational only.

## Steps

1. **Find the session boundary.**
   - Default: 7 days back from now.
   - User-provided: `/arch-session-close <N>d` for last N days, or `/arch-session-close <since-commit>` for everything since a given commit.

2. **Gather DECs touched.**
   - Read all `docs/decomposition/DEC-*.md` whose `Status:` line matches `proposed | in progress | done | executed | abandoned | no-op`.
   - For each, capture: ID, status, target, date.
   - Cross-reference with `${TMPDIR:-/tmp}/architecture-first/<md5(CLAUDE_PROJECT_DIR)>-active-decs.json` if it exists.

3. **Compute deltas in window.**

   ```bash
   BASELINE="$(git log --before='<N> days ago' --format=%H -n1)"
   git diff $BASELINE..HEAD --shortstat
   git diff $BASELINE..HEAD --numstat -- 'src/*' | awk '{add+=$1; del+=$2} END {print add, del, add-del}'
   ```

4. **Cycle delta.** Run `madge --circular --extensions ts src` (or stack equivalent) at HEAD; compare to count at `BASELINE` if available in git history. State both numbers.

5. **Listener / façade tallies.** `git diff --diff-filter=A --name-only $BASELINE..HEAD -- src` filtered for `*.listener.ts`, `*.facade.ts`, `*-service.ts` patterns.

6. **Cleanup tally.** `git diff --diff-filter=D --name-only $BASELINE..HEAD -- src | wc -l`. List the deleted files.

7. **Render the ledger.**

   ```markdown
   ## Session ledger (<DATE_FROM> → <DATE_TO>)

   ### DECs by status

   | ID      | Target                   | Status    | Verdict        | Notes              |
   | ------- | ------------------------ | --------- | -------------- | ------------------ |
   | DEC-016 | CopyPortfolioOperation   | executed  | act            | 3 PRs landed       |
   | DEC-027 | copy-portfolio dual-path | no-op     | "Це норм"      | closed immediately |
   | DEC-023 | V4TransportService       | abandoned | act → over-eng | PR #53 closed      |

   ### Code delta

   - Files changed: <N>
   - LOC net: +<X> / -<Y> = <signed sum>
   - Files added: <N> (listeners: <M>, façades: <K>)
   - Files deleted: <N>
   - Cycles: <BEFORE> → <AFTER>

   ### Honest ratio

   - **Worth-it work:** DECs with status `executed` whose target file changed in a way the user would call shippable value. Tally LOC + count.
   - **Ceremony:** DECs with status `no-op | abandoned`, plus any docs (`docs/architecture/*`, `docs/decomposition/*`) created and later deleted in window.
   - Ratio: <worth-it %> / <ceremony %>.

   ### Carry to next session

   - Open DECs (`proposed | in progress`): list with one-line trigger condition each.
   - Known anti-patterns observed: any new heuristic worth adding to `references/known-antipatterns.md`.
   ```

8. **Conclude with one line.** Either:
   - "**Session was net-positive.** Carry on." (≥ 60% worth-it ratio)
   - "**Session was mostly ceremony.** Recommend `/arch-clean` only for next pass; skip decomposers." (< 50% worth-it ratio)
   - "**Session was mixed.**" (50–60%)

## Output target

This command writes nothing to the repo. The ledger is for the user's own calibration. Do not save to `docs/`, do not commit, do not stage.

If the user wants the ledger persisted, suggest they paste it into their own notes / vault / PR description manually.
