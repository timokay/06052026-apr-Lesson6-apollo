# Coding Style — Apollo (RU)

> Source: `docs/Architecture.md` Section 4 (Tech Stack), `docs/Refinement.md`.

## General

- **No emojis** в коде, комментариях, коммитах, документации (если явно не запросил пользователь).
- **No comments unless WHY is non-obvious.** Не пиши «what» — это видно из кода.
- **Не добавлять backwards-compatibility shims** без необходимости. Refactor — refactor, не rename.
- **Trust internal code** — валидация только на boundary (user input, external APIs).
- **No dead code, TODO без issue ссылки, commented-out code** в main.

## Python (backend-api/, worker/, etl/)

### Style

- **PEP 8** + Black (line length 100)
- **Ruff** для linting (`ruff check . --fix`)
- **mypy --strict** mode
- **isort** + black для imports

### Type hints

- **Required everywhere.** No `Any` без явного reason в comment.
- Pydantic v2 для request/response schemas.
- Generic types: `list[X]` not `List[X]` (Python 3.12).

### Naming

- `snake_case` для функций, переменных, модулей
- `PascalCase` для классов, Pydantic schemas
- `SCREAMING_SNAKE` для constants
- `_private` prefix для private functions/methods

### Imports

- Absolute imports от корня package: `from app.services.auth import AuthService`
- Не relative (`from ..services...`)
- Order: stdlib → third-party → local (isort default)

### FastAPI patterns

- Routers in `app/routers/<domain>.py`
- Services in `app/services/<domain>.py`
- Repositories in `app/repositories/<entity>.py`
- Dependency injection через `Depends()`
- Async везде (`async def`, `await`, `asyncpg`)

### SQLAlchemy

- 2.0 async syntax: `select()`, `await session.execute()`
- Models в `app/models/<entity>.py`
- Migrations в `alembic/versions/`
- Forward-compatible migrations (см. ADR-012)

### Error handling

- HTTPException для API errors с error code:
  ```python
  raise HTTPException(
      status_code=402,
      detail={"code": "QUOTA_EXCEEDED", "message": "..."}
  )
  ```
- Не bare `except:` — всегда specific exception type
- Logging in WARN/ERROR на recoverable errors

### Testing

- pytest + pytest-asyncio
- Test files: `tests/test_<module>.py`
- Fixtures в `conftest.py` per package
- testcontainers-python для real Postgres/Redis в integration tests

## TypeScript / React (frontend/)

### Style

- **Strict mode** в `tsconfig.json` (`"strict": true`)
- **ESLint** с recommended + react-hooks rules
- **Prettier** для formatting (line length 100)
- No `any` без `// eslint-disable-line` + comment

### Naming

- `camelCase` для functions, variables, props
- `PascalCase` для components, types, interfaces
- `SCREAMING_SNAKE` для constants
- Hooks начинаются с `use`: `useAuth`, `useReveal`

### React patterns

- **Functional components only** (no classes)
- **Hooks** для state и side-effects
- Props: explicit interface (`interface Props { ... }`)
- Custom hooks для shared logic

### State management

- **React Query** (`@tanstack/react-query`) для server state
- **Zustand** для UI state (если нужен global)
- **useState** для local component state
- Не Redux в MVP (overhead не оправдан)

### Folder structure

```
frontend/
├── app/                     # Next.js App Router
│   ├── (auth)/              # Auth route group
│   ├── (dashboard)/         # Dashboard route group
│   └── api/                 # API routes (BFF if needed)
├── components/
│   ├── ui/                  # shadcn/ui generated
│   └── <domain>/            # domain-specific components
├── lib/
│   ├── api/                 # API clients (React Query)
│   ├── auth/                # Auth utilities
│   └── utils/               # Generic utilities
├── hooks/                   # Custom hooks
└── types/                   # Shared TypeScript types
```

### Imports

- Absolute imports via `@/` alias: `import { Button } from '@/components/ui/button'`
- Order: react → next → external → @/lib → @/components → relative

### Styling

- **Tailwind CSS** utility classes
- **shadcn/ui** для базовых компонентов
- CVA (`class-variance-authority`) для variants
- НЕ inline styles, кроме dynamic values
- Dark mode: `dark:` prefix (Tailwind)

### Forms

- **react-hook-form** + zod resolver для validation
- Server actions (Next.js) для mutations где возможно
- React Query mutations для API calls

### Testing

- **Vitest** для unit tests
- **Playwright** для E2E
- Test files: `<component>.test.tsx`

## SQL

- Lowercase keywords: `select` not `SELECT`
- 4-space indent для multi-line
- One column per line в SELECT для >3 columns
- Comments в migration SQL для non-obvious changes

```sql
select
    c.inn,
    c.name,
    c.okved_main
from companies c
where
    c.region = $1
    and c.okved_main like $2
order by c.updated_at desc
limit $3
```

## YAML / JSON config

- 2-space indent
- Sorted keys для config files (где порядок не важен)
- Comments в YAML обязательны для non-obvious settings

## Markdown (docs/, README, ADRs)

- ATX-style headings (`#`, `##`)
- Tables aligned manually для читаемости
- Code blocks с language hint: \`\`\`python
- Mermaid diagrams для архитектуры
- Не emoji в headings (кроме inline статусов: ✅ ❌ ⚠️)

## Git Commit Messages

См. `.claude/rules/git-workflow.md`.

## File Organization

- One class/major function per file (исключения — small utilities)
- File size soft limit: 500 lines (refactor если больше)
- Function size soft limit: 50 lines

## Database / API conventions

- API path: `/api/v{N}/<resource>` (kebab-case или nested)
- JSON keys: `snake_case` (matches Python convention, Pydantic config aliases при необходимости)
- Timestamps: ISO 8601 UTC with timezone offset (`2026-05-06T14:30:00Z`)
- IDs: UUIDv4 (string format в API, native UUID в БД)
- Money: integer kopecks (BIGINT), never float

## Performance Guidelines

- N+1 queries: forbidden. Use SQLAlchemy `selectinload()` / `joinedload()`.
- Frontend bundle: target <200KB initial JS.
- Images: Next.js `<Image>` component, AVIF/WebP.
- API responses: pagination обязательна для list endpoints.
- Cache aggressively (Redis) для hot reads (top companies, OKVED reference).

## Documentation Comments (рідко, но если нужно)

```python
def reveal_contact(user_id: UUID, company_inn: str) -> list[Contact]:
    """
    Reveal contacts for company. Atomic deduction, idempotent.
    
    Why atomic: prevent race condition where 2 concurrent reveals
    deduct from quota=1, resulting in -1 balance.
    
    See: docs/Pseudocode.md section "Algorithm 1"
    """
```

Только когда:
- Non-obvious algorithm (со ссылкой на docs)
- Workaround для известного бага (со ссылкой на issue)
- API contract для public functions (типы говорят сами, но context — нет)

## Forbidden patterns

- `import *` (Python)
- `eval`, `exec` без namespace
- `pickle` для untrusted data
- `print()` в production code (используй logger)
- `console.log()` в production frontend
- Hardcoded URLs/secrets
- Magic numbers (используй named constants)
- Dead code (commented-out, unused functions)

## Pre-commit hooks (`.pre-commit-config.yaml`)

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks: [{ id: ruff, args: [--fix] }, { id: ruff-format }]
  - repo: https://github.com/pre-commit/mirrors-mypy
    hooks: [{ id: mypy }]
  - repo: local
    hooks:
      - id: secrets-scan
        name: Detect secrets
        entry: detect-secrets-hook
        language: python
```
