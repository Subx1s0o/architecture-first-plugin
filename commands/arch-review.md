---
description: Review the current git diff for architectural red flags (cross-boundary imports, missing seams, event orphans, a service reaching into another module's internals). Fast path — no sub-agent.
---

Run `git diff --stat` and `git diff` (staged + unstaged), then for every changed source file under `src/` (or the stack profile's source root):

1. Identify the module and layer using `.arch-profile.yaml` if present, else the stack profile's layer map.
2. Flag:
   - imports from another module's internals instead of its public barrel,
   - new event emissions without a matching subscriber found by grep,
   - new queue jobs without a registered processor,
   - new external/RPC calls that duplicate an existing one in the repo,
   - files that exceed the stack profile's LoC threshold,
   - new circular dependencies introduced by the diff.
3. Produce the report in the same table format as the `architect-reviewer` sub-agent (Severity / Location / Finding / Suggested seam).

Do not edit code. Do not invoke `architect-reviewer` — this command is the fast path; suggest it at the end only if findings warrant a deeper review.
