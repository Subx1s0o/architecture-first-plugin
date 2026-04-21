---
description: Authorize and execute a cleanup batch from a manifest. Writes the session's cleanup marker so the pre-edit hook allows mass deletions for this batch only.
---

Takes `<batch-id>` (e.g. `CLN-003-batch-B`).

1. Locate the manifest file containing the batch under `docs/cleanup/`. Read the batch section.
2. Refuse if the batch contains any L3/L4 finding — those need architect review first. Emit a clear error pointing at `/arch-review`.
3. List every file and line-range the batch will delete, with the per-row evidence from the manifest. Ask the user for explicit confirmation ("yes" / "approve" / a number of items). If the user declines, stop.
4. Write the cleanup marker: `${CLAUDE_PROJECT_DIR}/.claude/.clean-approved-<session_id>` containing `batch: <batch-id>` and an ISO timestamp.
5. Execute the deletions as one logical change:
   - For L1 formatting/logs: apply the edits.
   - For L2 orphan files: delete with `git rm` (or `rm` if not tracked).
   - For L2 deps: edit the manifest (`package.json`, `pyproject.toml`, `go.mod`, etc.) and regenerate the lockfile per the detected stack.
6. Run the stack's default test command and the build command (from the stack profile). If anything fails, revert the change (`git restore`) and report the failure.
7. Append the manifest with `Status: executed on <date>, commit <sha>` and the test/build summary.

The cleanup marker is session-scoped; it does not authorize any subsequent batch.
