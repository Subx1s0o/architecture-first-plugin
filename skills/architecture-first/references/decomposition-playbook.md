# Decomposition playbook

Ten canonical patterns for breaking a heavy unit safely. Each entry: **trigger → strategy → rollout safety → pitfalls**. Choose by trigger, not by taste.

## 1. Extract Module (bounded context split)

- **Trigger.** A module's public surface spans ≥ 2 noun-phrases joined by "and" (`user-and-billing`, `orders-and-inventory`). Or: git churn reveals two sub-clusters of files touched by disjoint PR sets.
- **Strategy.** Draw a dependency graph inside the module; cut at the sparsest edge; move the smaller half to a new module with its own public barrel; replace cross-cluster imports with explicit interfaces or events.
- **Rollout.** One PR creates the new module as a re-export shell (no behaviour change). Second PR migrates imports. Third PR collapses the shell. Green builds between each.
- **Pitfalls.** Cutting the graph at the shortest-name edge instead of the semantic edge. Use the language of the domain.

## 2. Extract Port (Dependency Inversion)

- **Trigger.** High-level code (use-case/operation) imports a low-level concrete (HTTP client, ORM entity, SDK). Or: you need a test double for one specific call.
- **Strategy.** Define an interface in the domain/application layer reflecting the _caller's_ need (not the vendor's API). Adapter implements it in infrastructure. Wire via DI.
- **Rollout.** Introduce port + adapter behind the existing concrete as a pass-through. Migrate the first use-case. Prove parity. Migrate the rest.
- **Pitfalls.** Naming the port after the vendor (`IStripeClient` instead of `PaymentGateway`). The port should survive vendor changes.

## 3. Strangler Fig (incremental replacement)

- **Trigger.** A unit is too heavy to replace atomically and runs in production.
- **Strategy.** New implementation lives beside the old. A router/facade delegates case-by-case. Migrate cases one at a time until the old implementation has zero live callers. Delete.
- **Rollout.** Feature flag per case. Metrics on both paths. No case is migrated without prod parity proof.
- **Pitfalls.** "Temporary" strangler that becomes permanent. Set an explicit sunset date in the ADR.

## 4. Branch by Abstraction

- **Trigger.** Replacing a cross-cutting concern (auth, logging, persistence layer) that many files depend on. Strangler Fig is too coarse.
- **Strategy.** Introduce an abstraction over the existing implementation. Route all callers through it. Add the new implementation behind the abstraction. Flip via config/flag. Remove the old.
- **Rollout.** Abstraction-first PR has zero behaviour change. Flag defaults to old. Canary. Flip. Clean up.
- **Pitfalls.** Leaving the abstraction after cleanup "just in case" — it will leak second-implementation details and rot.

## 5. Replace Temporal Coupling with a Domain Event

- **Trigger.** "Call X before Y" invariants, implicit ordering between services, lifecycle hooks that must fire in sequence.
- **Strategy.** Reframe X's completion as a domain event. Y becomes a subscriber. Order is a consequence of causality, not discipline.
- **Rollout.** Publish-only first (no subscribers). Attach subscriber in a second PR. Remove the direct call in a third.
- **Pitfalls.** Eventing synchronous business invariants that need transactional guarantees — use outbox pattern, not raw emit.

## 6. Event-Carried State Transfer (break cross-module reads)

- **Trigger.** Module A reads B's tables/state directly, creating read-coupling. Or cross-service RPC for data that rarely changes.
- **Strategy.** B publishes state snapshots as events. A keeps a local projection. Reads are local; consistency is eventual.
- **Rollout.** Start with dual-read (local projection + authoritative fallback). Once projection is proven, drop the fallback.
- **Pitfalls.** Using this for strongly consistent data (balances, inventory counters). Those need synchronous reads or sagas.

## 7. Saga / Process Manager (break cross-module orchestration)

- **Trigger.** A single operation mutates state in 3+ modules, with compensation logic needed on partial failure.
- **Strategy.** Move orchestration out of individual services into a dedicated saga. Each step emits an event; the saga listens and issues the next command. Compensating commands on failure.
- **Rollout.** Extract one happy path first. Add compensations per step with chaos-test style failure injection.
- **Pitfalls.** Distributed-transaction-flavoured sagas. Sagas are not 2PC; accept eventual consistency and compensation semantics.

## 8. Anti-Corruption Layer (ACL)

- **Trigger.** Integrating with a legacy system, third-party API, or a bounded context whose model you do not want to leak.
- **Strategy.** All traffic to/from the foreign system passes through a translator that maps foreign concepts to local domain concepts.
- **Rollout.** Put the ACL in from day one of the integration. Adding it later costs 10×.
- **Pitfalls.** Skipping the ACL for "simple" integrations. Simplicity is temporary; the coupling is forever.

## 9. Replace Inheritance with Composition

- **Trigger.** Class hierarchy with ≥ 3 levels, or a base class whose subclasses override > 50% of its methods.
- **Strategy.** Identify the varying axes. Each axis becomes an injected strategy. The concrete classes become compositions, not subclasses.
- **Rollout.** Migrate one subclass to composition. Prove parity. Repeat. Remove base class when the last heir is gone.
- **Pitfalls.** Creating a parallel "composition hierarchy" — just move toward flat objects with injected behaviour.

## 10. Extract Aggregate (DDD tactical)

- **Trigger.** Invariants span multiple entities currently loaded and saved independently. Bugs cluster around partial-update states.
- **Strategy.** Identify the invariant's boundary. All entities inside that boundary become one aggregate with a root. Save/load happens through the root. External code cannot reach internal entities directly.
- **Rollout.** Consolidate repositories behind a single aggregate repository. Update callers to load by root. Retire old repositories.
- **Pitfalls.** Oversized aggregates (whole domain in one aggregate) — contention and lost concurrency. Small aggregates, sharp invariants.

## Choosing between patterns

Decision tree:

```
Is the code in production with real traffic?
├─ yes  → Strangler Fig or Branch by Abstraction
└─ no   → any pattern
                |
                v
Is the pain read-coupling across modules?
├─ yes  → Event-Carried State Transfer
└─ no   → next
                |
                v
Is the pain write-coupling across modules?
├─ yes  → Saga / Process Manager
└─ no   → next
                |
                v
Is the pain one heavy class/file?
├─ yes  → Extract Module / Extract Port / Replace Inheritance with Composition
└─ no   → next
                |
                v
Is the pain an integration boundary?
└─ yes  → Anti-Corruption Layer
```

## The decomposition ADR

Every non-trivial decomposition ships with an ADR from `templates/ADR.md.tmpl` that records: the hotspot evidence, the pattern chosen, the rollout sequence, and the sunset date for any transitional abstraction.
