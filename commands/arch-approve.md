---
description: Unlock Edit/Write for this session after the architectural plan has been agreed. Optionally writes an ADR from the plan. Use --trivial "<reason>" for typo/formatting-only edits.
---

Markers are ephemeral — they live under `${TMPDIR:-/tmp}/architecture-first/` and NEVER in the project tree. They also auto-expire after 24 hours.

1. Compute `proj_hash = md5(CLAUDE_PROJECT_DIR)` and derive:
   `marker = ${TMPDIR:-/tmp}/architecture-first/<proj_hash>-<session_id>.approved`
   Create the parent directory if missing.

2. If the invocation has `--trivial "<reason>"`:
   - Touch the marker with `trivial: <reason>` and an ISO timestamp.
   - Stop. Do not write an ADR.

3. Otherwise:
   - Read the last architectural plan from the current conversation (sections 1–3).
   - Populate `templates/ADR.md.tmpl` and write the ADR to `docs/adr/ADR-<next>-<slug>.md`.
   - If `repo-vault-routing` skill is installed, mirror the ADR into the vault.
   - Touch the marker with `approved: ADR-<number>` and timestamp.

4. Confirm: `✓ Edit gate lifted. ADR-<number> written at <path>.` (or `✓ Edit gate lifted (trivial: <reason>).`)

Do not write anything under `<project>/.claude/`.
