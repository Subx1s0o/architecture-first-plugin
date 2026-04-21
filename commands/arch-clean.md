---
description: Run the cleaner over a scope (path arg, default whole repo). Produces a cleanup manifest classified by safety level L1-L4. Does not delete anything.
---

1. Detect the stack via `skills/architecture-first/references/stack-profiles/_detect.md`; load the profile's thresholds.
2. Resolve scope from the argument. If empty, scope is the whole repo.
3. Invoke the `cleaner` agent with the scope and the stack profile.
4. Write the returned manifest to `docs/cleanup/CLN-<next-number>-<slug>.md` using `templates/cleanup-batch.md.tmpl`. Confirm the target path with the user once if `docs/cleanup/` does not yet exist.
5. Summarize headline numbers in two lines: total findings per level, total LoC reclaimable.
6. End with: "To execute a batch, run `/arch-clean-approve <batch-id>`. L3/L4 findings require architect review — run `/arch-review` on those files first, or let me dispatch `architect-reviewer` on them."

Do not edit any code.
