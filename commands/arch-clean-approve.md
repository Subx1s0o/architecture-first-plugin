---
description: Authorize and execute a cleanup batch from a manifest. Writes an ephemeral cleanup marker in /tmp so the pre-edit hook allows mass deletions for this batch only.
---

Takes `<batch-id>` (e.g. `CLN-003-batch-B`).

1. Locate the manifest file under `docs/cleanup/`. Read the batch section.
2. Refuse if the batch contains any L3/L4 finding — those need architect review first. Emit a clear error pointing at `/arch-review`.
3. List every file and line-range the batch will delete, with the per-row evidence from the manifest. Ask the user for explicit confirmation ("yes" / "approve"). If the user declines, stop.
4. Write the cleanup marker at `${TMPDIR:-/tmp}/architecture-first/<md5(CLAUDE_PROJECT_DIR)>-<session_id>.clean-approved` with `batch: <batch-id>` and an ISO timestamp. Create the parent dir if missing. Do not write anywhere under `<project>/.claude/`.
5. Execute the deletions as one logical change:
   - L1 formatting/logs: apply edits.
   - L2 orphan files: `git rm` (or `rm` if not tracked).
   - L2 deps: edit the stack manifest (`package.json`, `pyproject.toml`, `go.mod`, …) and regenerate the lockfile per the detected stack.
6. Run the stack's test and build commands from `.arch-profile.yaml` `commands:`. If anything fails, `git restore` and report the failure.
7. Append the manifest with `Status: executed on <date>, commit <sha>` and the test/build result.

The cleanup marker is session-scoped and ephemeral; it does not authorize any subsequent batch.
