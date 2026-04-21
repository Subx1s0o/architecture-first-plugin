# Mermaid cheat sheet

Enough Mermaid to draw any architectural diagram this plugin produces. Prefer `flowchart` for most cases; fall back to `C4Container` / `sequenceDiagram` when they pay off.

## Flowchart (default choice)

```mermaid
flowchart LR
    U[User] -->|HTTPS| API(API)
    API -->|SQL| DB[(Postgres)]
    API -->|enqueue| Q[[Queue]]
    Q --> W(Worker)
    W -->|events| Bus{{Event Bus}}
```

- `[text]` — rectangle (container, process).
- `(text)` — rounded (component, module).
- `[(text)]` — cylinder (database).
- `[[text]]` — subroutine (queue, topic).
- `{{text}}` — hexagon (bus, broker).
- `{text}` — rhombus (decision).

## Subgraphs (modules / bounded contexts)

```mermaid
flowchart TB
    subgraph orders[Orders context]
        O_API(API) --> O_DB[(orders_db)]
    end
    subgraph billing[Billing context]
        B_API(API) --> B_DB[(billing_db)]
    end
    O_API -- OrderPlaced event --> B_API
```

## Sequence diagram (for flows across containers)

```mermaid
sequenceDiagram
    participant U as User
    participant API
    participant W as Worker
    participant DB
    U->>API: POST /orders
    API->>DB: INSERT order
    API->>W: enqueue ProcessOrder
    W-->>API: OrderProcessed
```

## Rules of thumb

- One diagram per response. Never two in one section.
- Label every edge with the protocol or event name.
- Dashed edge for async / best-effort; solid for synchronous / transactional.
- If you need three colours to explain it, the diagram is wrong — split it.
