---
description: Plan a safe decomposition for one or many hotspots. Accepts a path, a row number from the last /arch-hotspot run, a range like 1-5, a list like 1,3,5, or ALL. Delegates to hotspot-decomposer sub-agent (in parallel when ≥ 2 targets).
---

Takes one argument. Forms:

- `/arch-decompose <path>` — a file or module directory.
- `/arch-decompose <N>` — row N from the latest `/arch-hotspot` state file.
- `/arch-decompose <A>-<B>` — inclusive range of rows (`1-5`).
- `/arch-decompose <A>,<B>,<C>` — comma-separated rows.
- `/arch-decompose ALL` (or `all`) — every row from the latest hotspot scan.

## Steps

1. **Resolve targets:**
   - If the argument looks like a path (contains `/` or `.`) → single target.
   - Otherwise read `${TMPDIR:-/tmp}/architecture-first/<md5(CLAUDE_PROJECT_DIR)>-hotspot.json`.
     - If the file is missing: prompt the user to run `/arch-hotspot` first, stop.
     - Parse the argument: `ALL`/`all` → all rows; `N` → single row; `A-B` → inclusive range; `A,B,C` → list.
     - Map each row number to its `path`.

2. **Dispatch:**
   - If 1 target: invoke `hotspot-decomposer` sub-agent once.
   - If ≥ 2 targets: dispatch **all hotspot-decomposer sub-agents in ONE assistant message** as parallel `Agent` tool calls. This is critical — do not loop sequentially; a single turn with N parallel invocations finishes in ~one agent's time.
     - In Cursor (no parallel agents): process sequentially but tell the user upfront it will take ~N × single-run time.

3. Each sub-agent receives: resolved path, `.arch-profile.yaml` (if present), detected stack profile.

4. Each sub-agent produces a decomposition plan written to `docs/decomposition/DEC-<next-number>-<slug>.md` using `templates/decomposition-plan.md.tmpl`. Confirm the `docs/decomposition/` directory once if it doesn't exist yet.

5. After all agents return, produce a summary table:

   | Target | DEC file | Pattern | Effort (PRs) | Recommended |
   |---|---|---|---|---|

   End with: "Pick one and I'll execute the first PR, or say `defer` to ticket them all."
