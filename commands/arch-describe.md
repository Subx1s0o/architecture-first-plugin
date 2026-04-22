---
description: C4 architectural description of feature/module/service. Mermaid. Read-only.
---

Takes an optional scope (module name, feature keyword, or path). If empty, describe the whole service.

1. Load the detected stack profile and `.arch-profile.yaml` if present.
2. Produce the description in C4 order, stopping at the smallest useful level:
   - **Context** — if the scope involves external systems or users.
   - **Containers** — for cross-container work (UI ↔ worker ↔ external service).
   - **Components** — for module-level work.
   - **Code** — only if the scope is a single unit.
3. Use Mermaid for levels 2–3. See `skills/architecture-first/references/mermaid-cheatsheet.md`.
4. End with an "Intent vs. Reality" section if the profile's `allowed-module-edges` disagree with what grep shows. Flag each mismatch.

Do not edit code.
