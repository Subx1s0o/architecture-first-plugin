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

## Syntax gotchas (the ones that actually bite)

- **Line breaks inside node labels: use `<br/>`, never `\n`.** A quoted label like `"Foo\nBar"` renders with a literal `\n` in the box. Use `"Foo<br/>Bar"` instead.
- **Node IDs are global within a diagram.** Defining `r1[…]` in `subgraph BEFORE` and `r1[…]` in `subgraph AFTER` merges them into one node spanning both subgraphs. Use distinct IDs per side (`rB` vs `rA`, or `beforeResolver` vs `afterResolver`).
- **Quote labels with spaces or special characters.** `A[My Label]` sometimes works, `A["My Label"]` always works.
- **Edge labels need the pipe form** `A -->|"label"| B` — not `A -->"label" B`.
- **Styling a node** uses a separate statement, not inline: `style nodeId fill:#1b4332,stroke:#2d6a4f,color:#fff`.
- **`direction LR` inside a subgraph** fixes weird vertical layout when the outer flowchart is also `LR`.

## Before → after pattern (for `/arch-decompose` and `/arch-execute`)

```mermaid
flowchart LR
  subgraph B["BEFORE"]
    direction LR
    cB["GraphQL callers<br/>(N endpoints)"] -->|"uses"| rB["OldUnit<br/>1000 LoC<br/>concern-A + concern-B"]
    rB -->|"uses"| depB["Dependency"]
  end
  subgraph A["AFTER PR-1"]
    direction LR
    cA["GraphQL callers<br/>(concern-A)"] -->|"uses"| newA["ExtractedUnit<br/>~200 LoC<br/>concern-A only"]
    cA2["GraphQL callers<br/>(concern-B)"] -->|"uses"| rA["OldUnit<br/>~800 LoC<br/>concern-B only"]
    newA -->|"uses"| depA["Dependency"]
    rA -.->|"no longer uses"| depA
    style newA fill:#1b4332,stroke:#2d6a4f,color:#fff
  end
```
