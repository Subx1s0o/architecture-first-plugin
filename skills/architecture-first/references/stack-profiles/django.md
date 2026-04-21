# Django profile

## Canonical layers

- `<app>/models.py` — persistence entities (tight ORM coupling by design)
- `<app>/views.py` or `views/` — HTTP entry points
- `<app>/serializers.py` — DRF serializers (DTOs for API)
- `<app>/services.py` or `<app>/application/` — application logic (introduced by you; not a Django default)
- `<app>/domain/` — pure logic (introduced by you)
- `<app>/tasks.py` — Celery tasks
- `<app>/signals.py` — Django signals (watch out — they are implicit coupling)

## Hotspot thresholds

- `models.py`: 400 LoC warn, 600 XL
- `views.py`: 300 LoC warn, 500 XL
- signals per app: > 5 warn (they become an invisible mesh)

## Anti-patterns

- Fat models (`class Order(models.Model)` with 1000 LoC of business logic).
- Fat views (business logic in the view, serializer does ORM traversals).
- Circular imports resolved by late imports inside functions — usually a missing service layer.
- `signals.py` used for orchestration (debugging becomes archaeology).

## Preferred decomposition patterns

- Extract Aggregate — peel business logic off models into `domain/`.
- Replace Signals with Explicit Events / Celery Tasks.
- Extract Port for external integrations.
- Strangler Fig when splitting a fat app into two.

## Test / build commands

- test: `python manage.py test` or `pytest`
- build: not applicable (deployment-specific)
