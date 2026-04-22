---
description: Unlock Edit/Write for this session. Zero-args form — just approves. Add --adr to also write an ADR from the plan, or --trivial "reason" to log a bypass reason.
---

Three forms, all just touch an ephemeral session marker under `${TMPDIR:-/tmp}/architecture-first/`:

1. **`/arch-approve`** — bare. Touch the marker. Confirm with `✓ Edit gate lifted.`
2. **`/arch-approve --trivial "<reason>"`** — touch the marker, append the reason + timestamp to an in-memory log line. No ADR.
3. **`/arch-approve --adr`** — touch the marker AND write an ADR from sections 1–3 of the current conversation to `docs/adr/ADR-<next>-<slug>.md` using `templates/ADR.md.tmpl`. Confirm with `✓ Edit gate lifted. ADR-<N> written at <path>.`

Steps:

1. Compute `proj_hash = md5(CLAUDE_PROJECT_DIR)` and `marker = ${TMPDIR:-/tmp}/architecture-first/<proj_hash>-<session_id>.approved`. Create the parent dir if missing.
2. Touch the marker.
3. If `--adr`: populate `templates/ADR.md.tmpl` from the current plan and write it under `docs/adr/`.
4. Confirm.

Do not prompt the user for a reason. Do not write anything under `<project>/.claude/`.
