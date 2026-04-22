# Scope guard — allow-list + deny-list for /arch-execute implementation

Loaded during step 5 (Implement) of `/arch-execute`. Prevents accidental edits outside the DEC PR's Files-touched list.

## Allow-list (what you MAY touch)

Build from the DEC's PR-<M> entry (Section 4, "Files touched"):

- Every path explicitly listed as `CREATE` / `MODIFY` / `DELETE` in the PR entry.
- Direct test siblings (e.g. `foo.service.spec.ts` for `foo.service.ts`) if the DEC's Tests section names them.
- Nothing else.

## Deny-list (what you MUST NOT touch unless explicitly listed in the DEC)

- Config/infra: `nest-cli.json`, `tsconfig*.json`, `package.json`, `pnpm-lock.yaml`, `yarn.lock`, `Dockerfile*`, `docker-compose*.yml`, `.eslintrc*`, `.prettierrc*`, `jest.config*`, `vite.config*`, `next.config*`.
- Git infra: `.gitignore`, `.git/*`, `.husky/*` (pre-commit, pre-push, commit-msg).
- CI: `.github/**`, `.gitlab-ci.yml`, `.circleci/*`, `Makefile`.
- Docs outside the plugin: `README*`, `CHANGELOG*`, `docs/**` (except `docs/adr/**` and `docs/decomposition/**`).

If a refactor genuinely needs one of these, stop and ask the user to amend the DEC first. Never "just include it because it obviously needs changing".

## Post-implement diff guard (runs before every commit)

```bash
cd "$WT_PATH" && git status --porcelain
```

Per changed path:
- `M` not in allow-list → `git restore -- <path>`, warning.
- `A`/`??` not in allow-list → `git restore --staged --worktree -- <path>` or `rm`, warning.
- `D` not in allow-list → `git checkout HEAD -- <path>` (restore), loud warning: `⚠ Blocked accidental deletion of <path> — not in DEC-<id> PR-<M> Files touched.`
- `R` both endpoints must be in allow-list.

If any restore fired: do NOT silently commit. Report every blocked change. Ask user: proceed with cleaned diff / abort / amend DEC.

Runs every PR iteration in `--auto` mode. Accidental deletions compound across PRs.
