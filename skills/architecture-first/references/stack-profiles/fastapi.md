# FastAPI profile

## Canonical layers

- `routers/` or `api/` — path operations (thin)
- `services/` — application logic
- `domain/` — entities, value objects, events
- `repositories/` or `infrastructure/` — DB, external API adapters
- `schemas/` — Pydantic request/response models
- `dependencies/` — `Depends(...)` providers (the DI seam)
- `tasks/` — background jobs (Arq, Celery, Dramatiq)

## Hotspot thresholds

- file: 300 LoC warn, 500 XL
- path operation body: 40 LoC warn, 80 XL
- Pydantic schema size: > 20 fields warn (data clump)

## Anti-patterns

- Business logic inside path operations.
- Pydantic schemas reused as ORM models (dual purpose → neither done well).
- Global state in module-level singletons (makes testing painful).
- `Depends(get_db)` manually threaded into every function instead of a repository.

## Preferred decomposition patterns

- Extract Module per router.
- Extract Port — introduce a repository interface per aggregate.
- Anti-Corruption Layer at every external API.
- Replace sync-chained calls with event publishing + background workers.

## Test / build commands

- test: `pytest`
- build: not applicable (Python deploys run from source)
- lint: `ruff check` / `mypy`
