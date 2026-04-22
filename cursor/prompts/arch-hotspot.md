Scan the whole repo for architectural hotspots. Run in order: Tier 0 (top 30 files by LoC via wc, top 30 by 90-day churn via git log), Tier 1 (fan-in via grep on top-20 exports, cycles via `madge --circular` for JS/TS or `pydeps --show-cycles` for Python if available). Cross-reference: files in BOTH top-size AND top-churn are primary hotspots. Produce a ranked table: Rank | Path | Size | Churn | Cycle? | Smell | Suggested pattern.

After the table, write a state file at ${TMPDIR:-/tmp}/architecture-first/<md5(project_dir)>-hotspot.json with shape: {"timestamp":"...","project":"...","rows":[{"rank":N,"path":"...","size":N,"churn":"X/20","cycle":bool,"smell":"...","pattern":"..."}, ...]}. Overwrite on every run.

End with: "Run /arch-decompose <N> for row N, /arch-decompose 1-5 for a range, /arch-decompose 1,3,5 for a list, or /arch-decompose ALL to plan every row sequentially." (No edits.)
