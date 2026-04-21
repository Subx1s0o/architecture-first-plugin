# Go profile (stdlib / chi / gin / echo)

## Canonical layout

Package-by-feature, not package-by-layer.

- `cmd/<binary>/` — `main` entry points
- `internal/<feature>/` — feature packages: handler, service, repo, domain in one package
- `internal/<feature>/domain.go` — types, interfaces, invariants
- `internal/<feature>/service.go` — application logic
- `internal/<feature>/repo.go` — data access
- `internal/<feature>/http.go` — handlers
- `internal/platform/` — cross-cutting (logging, tracing, db, queue)

## Hotspot thresholds

- file: 300 LoC warn, 500 XL
- function: 50 LoC warn, 80 XL
- exported identifiers per package: > 20 warn (API surface)
- interfaces with one implementation inside the same package: usually fine (Go idiom — define interfaces where they are used)

## Anti-patterns

- `utils` or `common` packages — dumping grounds by definition.
- Interfaces defined in the package that produces them instead of where they are consumed.
- Package cycles "resolved" by moving types to a shared `types` package.
- Global singletons for DB/logger/config instead of passed values.
- `context.Context` missing from functions that do I/O.

## Preferred decomposition patterns

- Extract Package (per bounded context).
- Move interfaces to the consumer package (Go-idiomatic DIP).
- Replace time-ordered call chains with explicit state machines.
- Strangler Fig across services when a feature graduates to its own binary.

## Test / build commands

- test: `go test ./...`
- build: `go build ./...`
- lint: `go vet ./...` + `golangci-lint run`
