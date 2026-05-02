# Framework-magic reach rules — cleaner

Before declaring anything "unreferenced" or eligible for visibility-tightening / dead-code removal, rule out these invocation paths. If any applies, the candidate is **excluded** from the manifest (do not raise level — just exclude).

## Universal rule-outs

| Mechanism             | Examples                                                                                | Rule                                                                       |
| --------------------- | --------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| DI / decorators       | `@Injectable`, `@Controller`, `@Component`, Spring `@Bean`, FastAPI `Depends(...)`      | reachable via container; treat as referenced if registered in a module     |
| Dynamic dispatch      | `Express.Router`, NestJS `EventPattern`, Bull `@Process('name')`, CLI name registration | grep the string literal, not only the symbol                               |
| Reflection            | `Class.forName`, `getattr`, `Reflect.getMetadata`                                       | assume reachable unless you can prove otherwise; demote to L3              |
| Convention / scanning | Rails autoload, Next.js `page.tsx`, Django `apps.py`                                    | path is the contract; presence in conventional location = reachable        |
| Public API            | Library `index.ts`, Python `__all__`, Go exported identifiers                           | L2 at best, usually L3                                                     |
| Tests                 | Jest `describe`, pytest collection, Go `TestXxx`                                        | reachable by framework; never delete just because "only test code uses it" |

## Visibility-tightening rule-outs (M1)

A method/field that LOOKS like it has zero external callers may still be reached via framework binding. Exclude from M1 visibility tightening when:

| Pattern                                                                                                                                                                | Reason                                         |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| Method has any framework decorator (`@Get`, `@Post`, `@Query`, `@Mutation`, `@ResolveField`, `@EventPattern`, `@MessagePattern`, `@Subscription`, `@Process`, `@Cron`) | Framework dispatches to it via metadata        |
| Method overrides a base class / implements an interface (`override` keyword OR signature in parent)                                                                    | Polymorphic call site exists                   |
| Lifecycle hooks (`onModuleInit`, `onApplicationBootstrap`, `onModuleDestroy`, `beforeApplicationShutdown`)                                                             | Called by framework lifecycle                  |
| Constructor                                                                                                                                                            | Always called externally                       |
| Method on a class that is itself reflection-targeted (e.g. `@Schema()`, `@Entity()`)                                                                                   | Method may be invoked via metadata enumeration |

## Unused-parameter rule-outs (M-NOT-A-RULE)

Unused **parameters** are NOT cleanup candidates. They belong to ESLint / TS `noUnusedParameters` with the `_` convention. Specifically NEVER flag:

| Pattern                                              | Reason                                            |
| ---------------------------------------------------- | ------------------------------------------------- |
| `createParamDecorator((data, ctx) => ...)` (NestJS)  | Both params are framework-required positional     |
| Express middleware `(req, res, next) => ...`         | Framework calls with all four args; arity matters |
| Express error handler `(err, req, res, next) => ...` | Express identifies error handlers by 4-arg arity  |
| React component props destructured `(_props) => ...` | Type contract, not dead code                      |
| Event listeners `(e) => ...` even if `e` unused      | API shape required                                |

Cleaner does not output ANY parameter renames. Period.

## Unused-import rule-outs (L1)

Some imports look unused but have side effects:

| Pattern                                                      | Reason                          |
| ------------------------------------------------------------ | ------------------------------- |
| `import 'reflect-metadata'`                                  | Polyfill side effect            |
| `import './some-style.css'`                                  | Build-system side effect        |
| `import { Type } from '...'` used only in JSDoc / TSDoc      | Documentation-only, do not flag |
| `import type { ... }` solely consumed by ambient declaration | Often type-only side effect     |

Only flag when ALL imported names have zero references in the file's source.
