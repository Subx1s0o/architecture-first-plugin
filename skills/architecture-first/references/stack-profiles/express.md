# Express / Fastify / Koa profile

## Canonical layers

- `routes/` or `controllers/` — HTTP entry points (thin)
- `services/` — orchestration (application layer)
- `repositories/` or `dal/` — data access
- `domain/` — pure business logic
- `middleware/` — cross-cutting concerns (auth, validation, tracing)
- `jobs/` — background workers (BullMQ, agenda)

## Hotspot thresholds

- file: 300 warn, 500 XL
- route handler: 40 LoC warn, 80 XL
- middleware chain length: > 8 warn

## Anti-patterns

- Business logic inside route handlers.
- Shared `req`/`res` mutation across middlewares (invisible coupling).
- `app.use(router)` where the router reaches into other feature's models.
- Passing raw Mongoose/Sequelize entities to response serialization — persistence leaking to UI.

## Preferred decomposition patterns

- Extract Module (by route prefix → feature module).
- Extract Port (service calls vendor SDK).
- Replace Temporal Coupling with Events (for multi-step handlers).

## Test / build commands

- test: `npm test`
- build: `npm run build` (if TS)
- lint: `npm run lint`
