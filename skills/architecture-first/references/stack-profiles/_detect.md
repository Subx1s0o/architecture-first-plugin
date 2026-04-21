# Stack detection

Read the project root (respect `CLAUDE_PROJECT_DIR`). Match in priority order. Use the first hit.

| Evidence | Profile |
|---|---|
| `package.json` contains `"@nestjs/core"` | nestjs.md |
| `package.json` contains `"next"` | nextjs.md |
| `package.json` contains `"express"` or `"fastify"` or `"koa"` | express.md |
| `package.json` exists, none of the above | generic-layered.md (JS/TS) |
| `pom.xml` or `build.gradle*` mentions `spring-boot` | spring-boot.md |
| `composer.json` contains `"laravel/framework"` | laravel.md |
| `manage.py` + `settings.py` present | django.md |
| `pyproject.toml` or `requirements.txt` mentions `fastapi` | fastapi.md |
| `Gemfile` contains `"rails"` | rails.md |
| `go.mod` exists | go-stdlib.md |
| `Cargo.toml` mentions `axum` | rust-axum.md |
| None of the above | generic-layered.md |

Each profile file specifies: canonical layer names, hotspot thresholds tuned for that stack, stack-specific anti-patterns, preferred decomposition patterns, and the stack's default test/build commands used by `/arch-clean-approve`.
