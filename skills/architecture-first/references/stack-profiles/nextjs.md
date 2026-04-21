# Next.js (App Router) profile

## Canonical structure

- `app/` — routes (server + client components). Keep business logic out.
- `app/**/_components/` — route-scoped components.
- `components/` — shared UI primitives (feature-agnostic).
- `features/<feature>/` — vertical slices: components + hooks + server actions + schema + types.
- `lib/` — cross-cutting utilities (auth, db client, tracing).
- `server/` — server-only logic (actions, data access, domain).
- `schemas/` or `zod/` — Zod schemas (cross-tier validation).

## Hotspot thresholds

- component file: 300 warn, 500 XL
- server action: 60 LoC warn, 120 XL
- prop count on a component: > 8 warn, > 12 XL

## Anti-patterns

- Business logic inside `page.tsx` or `layout.tsx`.
- `"use client"` on files that import heavy server libraries (bundles shipped to the browser).
- Server actions with > 3 responsibilities (queue, validate, write, revalidate, email — split).
- Fetching inside deep child components instead of at a route boundary.
- Global stores (Zustand/Redux) for data that belongs in server state (React Query / RSC).

## Preferred decomposition patterns

- Vertical-slice Extract Module (move a feature out of `app/` into `features/`).
- Extract Port (server action calls vendor SDK → inject via interface).
- Anti-Corruption Layer for external APIs (always).
- Branch by Abstraction for data layer swaps (e.g. Prisma → Drizzle).

## Test / build commands

- test: `npm test` (Vitest/Jest per repo)
- build: `npm run build`
- lint: `npm run lint`
