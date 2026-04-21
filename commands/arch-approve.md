---
description: Unlock Edit/Write for this session after the architectural plan has been agreed. Optionally writes an ADR from the plan. Use --trivial "<reason>" for typo/formatting-only edits.
---

1. Resolve the session marker path: `${CLAUDE_PROJECT_DIR}/.claude/.arch-approved-<session_id>`.
   The session id comes from the hook JSON input or, if unknown, use `default`.

2. If the invocation has `--trivial "<reason>"`:
   - Touch the marker with contents `trivial: <reason>` and an ISO timestamp.
   - Append the same line to `${CLAUDE_PROJECT_DIR}/.claude/arch-approvals.log`.
   - Stop. Do not write an ADR.

3. Otherwise:
   - Read the last architectural plan from the current conversation (sections 1–3).
   - Populate `templates/ADR.md.tmpl` and write it to `docs/adr/ADR-<next-number>-<slug>.md` (ask the user once if the path should differ for this repo).
   - If a `repo-vault-routing` skill is installed, mirror the ADR into the vault under `decisions/`.
   - Touch the marker with contents `approved: ADR-<number>` and timestamp.
   - Append to `arch-approvals.log`.

4. Confirm to the user: `✓ Edit gate lifted. ADR-<number> written at <path>.`

Do not invoke any sub-agent; this command is a small on-disk bookkeeping operation.
