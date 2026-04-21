# Ruby on Rails profile

## Canonical layers

- `app/controllers/` — HTTP entry points
- `app/models/` — Active Record (deeply coupled to DB by design)
- `app/services/` — application logic (Rails-idiomatic extension)
- `app/domain/` or `app/lib/` — pure logic
- `app/jobs/` — Active Job / Sidekiq jobs
- `app/serializers/` or `app/views/` — presentation

## Hotspot thresholds

- controller: 200 LoC warn, 400 XL
- model: 400 LoC warn, 600 XL
- `before_action` chain length per controller: > 6 warn

## Anti-patterns

- God models (`class User < AR::Base` with 2000 LoC).
- Fat controllers with `Model.where(...)` inline.
- Callbacks (`after_create`, `before_save`) used for orchestration — invisible side effects.
- `concerns/` as a dumping ground for unrelated helpers.
- Monkey-patching standard classes in `config/initializers/`.

## Preferred decomposition patterns

- Service Object extraction (`services/<Verb><Noun>.rb`).
- Extract Aggregate — move business rules off Active Record into plain Ruby in `domain/`.
- Replace callbacks with Jobs / explicit event publication.
- Strangler Fig for splitting a Rails monolith into bounded contexts.

## Test / build commands

- test: `bin/rails test` or `bundle exec rspec`
- build: not applicable
- lint: `bundle exec rubocop`
