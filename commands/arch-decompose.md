---
description: Plan a safe decomposition for one hotspot. Delegates to the hotspot-decomposer sub-agent. Produces a decomposition-plan document. No writes to src/.
---

Takes a path argument — a file, directory, or module name.

1. Resolve the path. If it refers to a module directory, operate on the whole directory.
2. Invoke the `hotspot-decomposer` agent with:
   - the resolved path,
   - `.arch-profile.yaml` if it exists,
   - the detected stack profile file.
3. Write the returned plan to `docs/decomposition/DEC-<next-number>-<slug>.md` using `templates/decomposition-plan.md.tmpl`. Confirm the target path with the user once if `docs/decomposition/` does not yet exist.
4. Summarize the plan's headline in two sentences and ask which of the three options the user wants: **proceed / defer / patch-in-place**.
