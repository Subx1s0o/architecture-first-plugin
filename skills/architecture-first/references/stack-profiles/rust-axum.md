# Rust (axum / actix-web / tower) profile

## Canonical layout

- `src/bin/<binary>.rs` — entry point
- `src/<feature>/mod.rs` — feature module root
- `src/<feature>/domain.rs` — types, traits, invariants
- `src/<feature>/service.rs` — application logic
- `src/<feature>/repo.rs` — data access
- `src/<feature>/http.rs` — handlers / routes
- `src/platform/` — cross-cutting (tracing, db pool, config)

Traits live where they are consumed (same idiom as Go).

## Hotspot thresholds

- file: 300 LoC warn, 500 XL
- function: 60 LoC warn, 100 XL
- generic parameter count per function: > 3 warn (intent getting lost)
- `.clone()` calls per file: > 10 warn (likely a borrow-modeling issue)

## Anti-patterns

- `Arc<Mutex<…>>` as a substitute for ownership design.
- Traits with one impl in the same module where they are defined (prefer inversion at the crate edge, not inside a module).
- `match` chains on an enum that should have been polymorphic traits.
- Error enums with dozens of variants that catch the whole app's errors — prefer error translation at each layer boundary.

## Preferred decomposition patterns

- Extract Crate when a feature graduates (enforced boundaries via crate visibility).
- Extract Port (trait consumed at boundary, impl elsewhere).
- Anti-Corruption Layer at every FFI/HTTP/async integration.
- Replace Inheritance with Composition — Rust has no inheritance, so this manifests as collapsing redundant trait hierarchies.

## Test / build commands

- test: `cargo test`
- build: `cargo build --release`
- lint: `cargo clippy -- -D warnings`
