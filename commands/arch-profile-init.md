---
description: Detect the project's stack and generate a per-repo .arch-profile.yaml tuned to it. One-time setup per repo.
---

1. Follow the detection table in `skills/architecture-first/references/stack-profiles/_detect.md` to pick the matching profile. Report the decision.
2. Read `skills/architecture-first/templates/arch-profile.yaml.tmpl`.
3. Pre-fill the template using:
   - the detected stack and its canonical layer names,
   - top-level directories under `src/` (or the stack's source root) as the initial `modules:` list,
   - the stack profile's default `thresholds`.
4. Leave `allowed-module-edges`, `hot-modules`, and `glossary` empty with a commented hint — the user fills these in.
5. Write the result to `${CLAUDE_PROJECT_DIR}/.arch-profile.yaml`. Refuse to overwrite an existing file; if one is present, show a diff and let the user merge manually.
6. Confirm with: "Profile written. Run `/arch-hotspot` to scan, or start editing code — the skill will now use this profile."
