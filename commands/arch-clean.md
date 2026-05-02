---
description: Cleanup manifest (L1-L4 safety levels). No deletions. --auto skips the directory-confirm prompt (CI mode).
---

Flags: `--auto` (CI/autonomous mode — auto-creates `docs/cleanup/` if missing, prints status instead of asking).

1. Detect the stack via `skills/architecture-first/references/stack-profiles/_detect.md`; load the profile's thresholds.
2. Resolve scope from the argument. If empty, scope is the whole repo.
3. Invoke the `cleaner` agent with the scope and the stack profile.
4. Write the returned manifest to `docs/cleanup/CLN-<next-number>-<slug>.md` using `templates/cleanup-batch.md.tmpl`. **If `--auto`:** create `docs/cleanup/` automatically if missing, print the path being used, and proceed. **Otherwise:** confirm the target path with the user once if `docs/cleanup/` does not yet exist.
5. Summarize headline numbers in two lines: total findings per level, total LoC reclaimable.
6. End with: "To execute a batch, run `/arch-clean-approve <batch-id>`. L3/L4 findings require architect review — run `/arch-review` on those files first, or let me dispatch `architect-reviewer` on them."

Do not edit any code.
