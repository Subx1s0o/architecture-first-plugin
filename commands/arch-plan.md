---
description: Capture the current architectural plan from the conversation as a persistent ADR. Useful mid-discussion to freeze a decision before diving into code.
---

1. Collect the latest architect-style plan in the conversation (sections 1–3 of the 4-step response).
2. Populate `skills/architecture-first/templates/ADR.md.tmpl` with:
   - a concise title derived from the decision,
   - Context from section 1 (Situation),
   - Decision from section 2 (Plan),
   - Consequences — positive, costs, follow-ups you can infer,
   - Alternatives considered — any rejected options the conversation discussed.
3. Write the ADR to `docs/adr/ADR-<next-number>-<slug>.md`. Confirm path with user once if `docs/adr/` does not yet exist.
4. Mirror to the Obsidian vault if `repo-vault-routing` skill is installed and a vault path is configured.
5. Do not touch the session plan marker — this command only persists intent, it does not unlock edits. Use `/arch-approve` for that.
