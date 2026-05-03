Close the architecture session. Read all `docs/decomposition/DEC-*.md` modified in the last 7 days (or `<N>d` from arg). For each, capture ID, status, target. Compute window deltas: `git diff <baseline>..HEAD --shortstat`, `madge --circular` count at HEAD vs baseline if available, count of listeners/façades added (`*.listener.ts`, `*.facade.ts`, `*-service.ts` under `src/`), count of deleted files.

Render a ledger table with DECs by status (executed | no-op | abandoned | proposed), then a code delta block (LOC net, cycles before/after, files added/deleted), then an honest ratio: worth-it (executed DECs delivering shippable value) vs ceremony (no-op + abandoned + deleted docs in window).

End with one of three lines:

- "**Session was net-positive.** Carry on." (≥ 60% worth-it)
- "**Session was mixed.**" (50–60%)
- "**Session was mostly ceremony.** Recommend `/arch-clean` only for next pass." (< 50%)

Output is conversational only. Do NOT write to repo. Do NOT commit. Do NOT stage. The user will paste the ledger into their own notes if they want it persisted.
