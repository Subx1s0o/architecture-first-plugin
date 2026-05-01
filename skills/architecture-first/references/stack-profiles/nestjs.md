# NestJS profile

## Canonical layers

- `operations/` or `use-cases/` — orchestration (application layer)
- `services/` — DB + cache + framework glue (infrastructure-adjacent)
- `models/` — persistence entities (ORM-coupled)
- `domain/` — pure business logic (no `@Injectable`)
- `events/` — listeners for cross-service or cross-module events
- `processors/` — Bull/BullMQ job processors
- `rpc/` — inbound/outbound service calls
- `graphql/` or `http/` — resolvers / controllers / DTOs

Each feature module exposes a `public.ts` barrel. Cross-module imports go only through barrels.

## Hotspot thresholds

- file: 400 LoC warn, 600 XL
- module: > 12 files without sub-folders → split candidate
- providers in one module: > 15 → responsibility split

## Anti-patterns

- Controller directly injecting a repository (skip application layer).
- Event handler doing DB writes and cache invalidation inline (belongs in an operation).
- `@Global()` modules (hidden coupling).
- Deep import paths `from '@/other/services/inner/thing'` (use the module barrel).
- `forwardRef(() => …)` cycles — almost always a missing domain event.
- **Resolver/controller split by HTTP verb on the same entity.** `XxxBrowseResolver` + `XxxAdminResolver`, `XxxReadController` + `XxxWriteController`, `XxxQueriesResolver` + `XxxMutationsResolver` — both files DI-inject the same operations, bind to the same `@Resolver(() => Xxx)`, and operate on the same model. This is a technical-layer split, not a domain split (see decomposition-playbook A1). Acceptable only when CQRS with separate read models / write models is already the chosen architecture.
- **Cosmetic file-size cuts.** Splitting a 600-LoC file in half "to fit the threshold" without a named responsibility boundary. The new files have no public contract reviewers can articulate.

## Preferred decomposition patterns

- Extract Module (by bounded context).
- Extract Port (operation imports concrete adapter).
- Event-Carried State Transfer between modules (replace `forwardRef`).
- Saga (for multi-module Bull job chains).

## Testing shape

- Unit: `domain/*.spec.ts` — no Nest testing module.
- Integration: `tests/<module>.integration.spec.ts` — real DB, real Redis.
- E2E: `tests/<feature>.e2e.spec.ts` — over GraphQL/HTTP.

## Test / build commands

- test: `npm test` (or `npm run test:int` for integration)
- build: `npm run build`
- lint: `npm run lint`
