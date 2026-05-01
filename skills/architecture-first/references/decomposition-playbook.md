# Decomposition playbook

Ten patterns. Choose by trigger, not taste. Format: **name → trigger / strategy / safety note**.

## 1. Extract Module (bounded context split)

- **Trigger.** Module surface spans ≥ 2 noun-phrases joined by "and". Or: churn shows 2 disjoint file-cluster subsets.
- **Strategy.** Cut dep graph at sparsest edge; move smaller half to new module with public barrel; replace cross-cluster imports with events or interfaces.
- **Safety.** PR1: new module as re-export shell. PR2: migrate imports. PR3: collapse shell.

## 2. Extract Port (DI)

- **Trigger.** High-level code imports a low-level concrete (HTTP client, ORM, SDK). Or: you want a test double for one call.
- **Strategy.** Interface in domain/application reflecting the _caller's_ need, not the vendor's API. Adapter in infrastructure. Wire via DI.
- **Safety.** Port + adapter as pass-through first. Migrate one use-case, prove parity, migrate rest.

## 3. Strangler Fig (incremental replacement, prod)

- **Trigger.** Unit too heavy to replace atomically, runs in production.
- **Strategy.** New impl beside old. Router/facade delegates case-by-case. Migrate until old has 0 callers. Delete.
- **Safety.** Feature flag per case + both-path metrics + prod parity proof before migrating. ADR sunset date.

## 4. Branch by Abstraction (cross-cutting, prod)

- **Trigger.** Replacing auth / logging / persistence layer with many dependents. Strangler too coarse.
- **Strategy.** Abstraction over current impl. Route all callers through it. Add new impl behind it. Flip via flag.
- **Safety.** Abstraction PR zero-behaviour. Flag defaults old. Canary. Flip. Remove old. Remove abstraction.

## 5. Replace Temporal Coupling with Event

- **Trigger.** "Call X before Y" invariants, implicit ordering, sequential lifecycle hooks.
- **Strategy.** X emits domain event on completion. Y subscribes. Order = causality, not discipline.
- **Safety.** Publish-only first. Subscriber in PR2. Remove direct call in PR3. Outbox pattern for transactional invariants.

## 6. Event-Carried State Transfer (read-coupling)

- **Trigger.** Module A reads B's tables/state directly. Or cross-service RPC for rarely-changing data.
- **Strategy.** B publishes state snapshots. A keeps local projection. Reads local; consistency eventual.
- **Safety.** Dual-read (projection + authoritative fallback) first. Drop fallback after parity. Never for strongly-consistent data (balances, inventory).

## 7. Saga / Process Manager (write-coupling)

- **Trigger.** One operation mutates state in 3+ modules with compensation on partial failure.
- **Strategy.** Orchestration into dedicated saga. Steps emit events; saga listens and issues next command. Compensations on failure.
- **Safety.** Happy path first. Compensations per step with chaos-test failure injection. Not 2PC — eventual consistency.

## 8. Anti-Corruption Layer

- **Trigger.** Integrating legacy / third-party / external bounded context whose model you don't want leaking.
- **Strategy.** All traffic through translator mapping foreign concepts to local domain.
- **Safety.** ACL from day 1 of integration. Adding later costs 10×.

## 9. Replace Inheritance with Composition

- **Trigger.** Hierarchy ≥ 3 levels, or base whose children override > 50% of methods.
- **Strategy.** Axes of variation → injected strategies. Concrete classes = compositions, not subclasses.
- **Safety.** Migrate one subclass, prove parity, repeat. Remove base when last heir gone.

## 10. Extract Aggregate (DDD)

- **Trigger.** Invariants span entities loaded/saved independently. Bugs cluster around partial-update states.
- **Strategy.** Invariant boundary = aggregate. Root mediates load/save. External code can't reach internal entities.
- **Safety.** Consolidate repositories behind aggregate repo. Migrate callers by root. Retire old repos. Small aggregates, sharp invariants.

## Decision tree

```
Production traffic? → yes: Strangler Fig / Branch by Abstraction
Read-coupling across modules? → yes: Event-Carried State Transfer
Write-coupling across modules? → yes: Saga
Heavy single class/file? → yes: Extract Module / Port / Composition
Integration boundary? → yes: ACL
```

Every non-trivial decomposition ships with an ADR recording: evidence, pattern, rollout sequence, sunset date.

## Anti-patterns — never propose these

These splits look like decomposition but produce no real decoupling. They fragment a file by surface mechanics, not by responsibility.

### A1. Technical-layer split on the same entity

❌ Splitting one entity's resolver/controller/handler into "queries vs mutations", "read vs write", "GET vs POST", "browse vs admin" when both halves operate on the same domain object with the same DI graph.

**Why it's wrong.** Both halves still depend on the same operations, the same model, the same auth/permissions surface. You moved code, you didn't decouple anything. The dep graph is unchanged. Churn pressure on the original concept is unchanged (a bug fix in `findPortfolio` and `createPortfolio` still touch sibling files in the same module).

**Examples to refuse:**

- `PortfoliosBrowseResolver` + `PortfoliosAdminResolver` — same entity, just queries vs mutations
- `UsersReadController` + `UsersWriteController`
- `OrderQueryHandler` + `OrderCommandHandler` _unless_ CQRS with separate read models is already the architecture

**What's acceptable instead:** if the file is too large, look for **sub-domain extractions** — a related-but-distinct concept inside it (e.g. `PortfolioFavoritesResolver` because favorites have their own service, lifecycle, throttle policy, and could be feature-flagged independently). Domain-driven, not verb-driven.

### A2. Splitting by file size alone

❌ "File is 600 LoC, let's cut it in half" with no semantic boundary.

**Why it's wrong.** Arbitrary cuts produce artifacts that have no name, no responsibility, no public contract. Reviewers can't tell why the cut is where it is. A future change usually has to bridge both halves, undoing the split.

**What's acceptable instead:** find the cohesion boundary first (responsibility heterogeneity, fan-out groups, churn clusters), then cut there. If no boundary exists, keep the file and accept the size.

### A3. Speculative generality / interface for one impl

❌ Extracting an interface, port, or abstraction with exactly one implementation and no concrete second use case.

**Why it's wrong.** Adds indirection without flexibility. Tests can mock the concrete just as easily.

**What's acceptable instead:** extract only when (a) a real second implementation exists or is days away, or (b) you need the seam for an isolation reason (test boundaries, transactional boundaries, deployment boundaries) that you can name.

---

Before writing a DEC, the decomposer must verify the proposed split is a domain split, not one of the above. If it cannot, refuse the hotspot with a one-line note ("file is large but has no internal decomposition boundary; accept the size or find a sub-domain to extract").
