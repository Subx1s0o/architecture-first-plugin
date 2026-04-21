# Laravel profile

## Canonical layers

- `app/Http/Controllers/` — HTTP entry points
- `app/Http/Requests/` — validation
- `app/Models/` — Eloquent models
- `app/Services/` — application logic (you introduce this)
- `app/Domain/` — pure business logic (you introduce this)
- `app/Jobs/` — queue jobs
- `app/Events/` + `app/Listeners/` — framework events
- `app/Repositories/` — optional repository abstractions

## Hotspot thresholds

- controller: 200 LoC warn, 400 XL
- Eloquent model: 400 warn, 600 XL (scopes, mutators and relations add up fast)
- service: 300 warn, 500 XL

## Anti-patterns

- Fat models (Eloquent encourages it; resist).
- Fat controllers with query building inline.
- Relying on global helpers for business logic (`auth()->user()` deep in the domain).
- Facades called from domain code (persistence + framework leaking).
- Observer/event chains no one can mentally trace (implicit orchestration).

## Preferred decomposition patterns

- Extract Service + Action classes (one class = one use case).
- Extract Aggregate — peel business logic off Eloquent into `Domain/`.
- Replace observer cascades with explicit Saga/Process Manager via Jobs.
- Anti-Corruption Layer for every third-party SDK.

## Test / build commands

- test: `php artisan test` or `./vendor/bin/phpunit`
- build: not applicable
- lint: `./vendor/bin/pint` (or `php-cs-fixer`)
