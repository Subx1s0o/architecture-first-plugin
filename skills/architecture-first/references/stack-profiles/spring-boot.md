# Spring Boot profile

## Canonical layers

- `controller/` or `web/` — REST/GraphQL entry points
- `service/` — application services, orchestration
- `domain/` — entities, value objects, domain events
- `repository/` — Spring Data JPA or JDBC access
- `config/` — `@Configuration`, beans, security
- `integration/` — external clients (Feign, WebClient, Kafka producers)

Package-by-feature is preferred over package-by-layer at the top level: `com.org.billing.*` over `com.org.controllers.billing`.

## Hotspot thresholds

- file: 300 LoC warn, 500 XL
- method: 50 LoC warn, 80 XL
- `@Autowired` fields in one class: > 8 warn
- `@Service` classes in one package: > 12 warn

## Anti-patterns

- `@Component` grab-bags with unrelated methods.
- Direct JPA entity exposure in REST responses (leaking persistence).
- `@Transactional` on controllers (should be on application services).
- Field injection everywhere (`@Autowired` on fields) — prefer constructor injection for testability.
- Static utility classes that hide dependencies.

## Preferred decomposition patterns

- Extract Module (package-by-feature split).
- Extract Port (interface in `domain`, adapter in `integration`).
- Saga via Spring Events or outbox pattern for multi-service writes.
- Anti-Corruption Layer for every external integration.

## Test / build commands

- test: `mvn test` or `./gradlew test`
- build: `mvn package` or `./gradlew build`
