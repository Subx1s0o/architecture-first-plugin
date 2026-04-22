# Framework-magic reach rules — cleaner

Before declaring anything "unreferenced", rule out these invocation paths. If any applies, raise safety level (L2 → L3, L3 → L4).

| Mechanism | Examples | Rule |
|---|---|---|
| DI / decorators | `@Injectable`, `@Controller`, `@Component`, Spring `@Bean`, FastAPI `Depends(...)` | reachable via container; treat as referenced if registered in a module |
| Dynamic dispatch | `Express.Router`, NestJS `EventPattern`, Bull `@Process('name')`, CLI name registration | grep the string literal, not only the symbol |
| Reflection | `Class.forName`, `getattr`, `Reflect.getMetadata` | assume reachable unless you can prove otherwise; demote to L3 |
| Convention / scanning | Rails autoload, Next.js `page.tsx`, Django `apps.py` | path is the contract; presence in conventional location = reachable |
| Public API | Library `index.ts`, Python `__all__`, Go exported identifiers | L2 at best, usually L3 |
| Tests | Jest `describe`, pytest collection, Go `TestXxx` | reachable by framework; never delete just because "only test code uses it" |
