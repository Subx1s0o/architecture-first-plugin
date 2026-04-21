# Generic layered profile

Fallback when no framework-specific profile matches.

## Canonical layers

- **interface** — HTTP/GraphQL/CLI/queue handlers (thin, no business logic)
- **application** — use-cases, orchestration
- **domain** — entities, value objects, domain services, events
- **infrastructure** — DB, external APIs, file system, caches

Allowed import direction: interface → application → domain ← infrastructure. Domain knows nothing about the rest.

## Hotspot thresholds

- file: 400 LoC warn, 600 LoC XL
- function: 60 LoC warn, 100 LoC XL
- cyclomatic: 10 warn, 15 XL
- fan-in: 15 warn, 25 XL
- churn: 4 commits in 20 warn, 7 in 20 XL

## Common anti-patterns

- Business logic inside controllers/resolvers/handlers.
- Domain entities importing ORM base classes (persistence leaking).
- "Manager"/"Helper"/"Util" classes without a single responsibility noun.
- Singletons holding mutable state that is not restart-safe.

## Preferred decomposition patterns

All ten. Prefer Extract Port when crossing layer direction; Extract Module when crossing domain concern.

## Test / build commands (used by /arch-clean-approve)

- test: not assumed; ask the user once per repo.
- build: not assumed; ask the user once per repo.
