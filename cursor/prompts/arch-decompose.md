Plan a decomposition for one or more targets. Argument forms: <PATH>, <N> (row from last /arch-hotspot), <A>-<B> (range), <A>,<B>,<C> (list), or ALL.

Resolve: if argument is a path → single target; otherwise read ${TMPDIR:-/tmp}/architecture-first/<md5(project_dir)>-hotspot.json and map row numbers to paths. If the file is missing, ask the user to run /arch-hotspot first.

For each resolved target, confirm the hotspot with the detection pyramid (size, churn, fan-in, cycles, responsibilities), pick a pattern from the playbook (Extract Module / Extract Port / Strangler Fig / Branch by Abstraction / Replace Temporal Coupling / Event-Carried State / Saga / ACL / Composition / Aggregate) via the decision tree — production-running code prefers Strangler Fig or Branch by Abstraction. Output per target: evidence table, chosen pattern + why, target architecture as Mermaid, PR sequence (≤5 PRs), rollout safety (flags, canary, parity), sunset date, risks.

Write each plan to docs/decomposition/DEC-<N>-<slug>.md. End with a summary table: Target | DEC file | Pattern | Effort (PRs) | Recommended. No code writes. In Cursor this is sequential (no parallel agents) — warn the user upfront when there are multiple targets.
