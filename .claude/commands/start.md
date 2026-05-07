---
description: Bootstrap Apollo project — creates source dirs, initializes DB, applies migrations, seeds data, runs smoke tests.
---

# /start $ARGUMENTS

## Purpose

Один раз инициализировать Apollo (RU) проект из SPARC документации. Идемпотентно — повторный запуск пропускает уже сделанное.

## Pre-flight Checks

1. ✅ `docs/PRD.md`, `docs/Architecture.md`, `docs/Specification.md` существуют
2. ✅ `.env` существует и содержит required variables (см. `.claude/rules/secrets-management.md`)
3. ✅ Docker и docker-compose доступны
4. ✅ Если уже initialized (есть `.apollo-initialized` файл) — пропустить с info, только smoke test

## Phase 1: Read Documentation

Read in this order, building context:

1. `docs/PRD.md` — project vision, personas, MVP features
2. `docs/Architecture.md` — tech stack, services, data model
3. `docs/Specification.md` — endpoints, NFR
4. `docs/Pseudocode.md` — algorithms, API contracts
5. `docs/ADR.md` — architecture decisions
6. `CLAUDE.md` — overall project context

## Phase 2: Source Code Scaffolding

Create monorepo packages (если не существуют):

### 2.1 Backend API (`backend-api/`)
Use Task tool to spawn parallel scaffolding:
```
Task: Create FastAPI backend skeleton
- backend-api/
  - app/
    - __init__.py
    - main.py             # FastAPI app setup
    - settings.py         # Pydantic Settings from env
    - database.py         # SQLAlchemy async engine + session
    - dependencies.py     # FastAPI DI providers
    - routers/
      - __init__.py
      - auth.py           # POST /auth/register, /login, /refresh, /verify
      - companies.py      # GET /companies, /companies/:inn
      - reveals.py        # POST /reveals
      - icp.py            # POST /icp/analyze, GET /icp/jobs/:id
      - campaigns.py      # POST /campaigns, /campaigns/:id/launch
      - billing.py        # POST /billing/checkout, /yookassa-webhook
      - optout.py         # GET /optout (public)
      - admin.py          # /admin/audit (admin only)
    - services/           # Business logic (one per domain)
    - repositories/       # Data access (one per entity)
    - models/             # SQLAlchemy models
    - schemas/            # Pydantic schemas (request/response)
    - middleware/         # Auth, rate limit, request_id
    - integrations/
      - llm/
        - base.py         # LLMProvider interface
        - yandexgpt.py    # YandexGPT implementation
        - openai.py       # OpenAI fallback
      - telegram.py       # Telegram Bot API client
      - yookassa.py       # YooKassa client
    - utils/
      - crypto.py         # bcrypt, HMAC, JWT
      - logging.py        # structured JSON logger
    - exceptions.py       # Custom exceptions с error codes
  - alembic/
    - alembic.ini
    - env.py
    - versions/           # Migration files
  - tests/
    - conftest.py         # pytest fixtures
    - test_auth.py
    - test_reveals.py
    - test_billing.py
  - requirements.txt
  - requirements-dev.txt
  - pyproject.toml        # ruff, black, mypy config
  - Dockerfile
  - .env.example
```

### 2.2 Worker (`worker/`)
```
worker/
  app/
    celery.py             # Celery app + config
    tasks/
      outreach.py         # send_campaign
      icp.py              # analyze
      etl.py              # refresh_companies
      billing.py          # reset_quotas, charge_renewal
      notifications.py    # send_email
  Dockerfile
```
Note: shares `app/` from backend-api via Docker volume mount or COPY.

### 2.3 ETL (`etl/`)
```
etl/
  pipelines/
    egrul_bulk.py         # Weekly EGRUL download
    e_disclosure.py       # Quarterly e-disclosure scrape
    okved_classifier.py   # Static reference data
  Dockerfile
```

### 2.4 Frontend (`frontend/`)
```
Task: Create Next.js 14 frontend skeleton
frontend/
  app/
    (auth)/
      login/page.tsx
      register/page.tsx
      verify/page.tsx
    (dashboard)/
      layout.tsx          # Authenticated layout
      page.tsx            # Dashboard home
      companies/[inn]/page.tsx
      icp/page.tsx
      campaigns/page.tsx
      campaigns/[id]/page.tsx
      billing/page.tsx
      settings/api-keys/page.tsx
    (public)/
      page.tsx            # Landing
      privacy/page.tsx
      terms/page.tsx
      optout/page.tsx
    api/                  # Next.js route handlers (BFF if needed)
  components/
    ui/                   # shadcn/ui generated
    auth/
    dashboard/
    companies/
    campaigns/
  lib/
    api/                  # React Query hooks per domain
    auth/                 # JWT cookie utilities
    crypto/               # Web Crypto API for IndexedDB
    utils/
  hooks/
  types/
  middleware.ts           # Next.js middleware (auth check)
  next.config.js
  tailwind.config.ts
  components.json         # shadcn/ui config
  package.json
  tsconfig.json
  Dockerfile
  .env.example
```

### 2.5 Nginx (`nginx/`)
```
nginx/
  nginx.conf              # TLS, rate limit, reverse proxy
  ssl/                    # Let's Encrypt certs (mounted)
  Dockerfile (optional)
```

### 2.6 Monitoring (`monitoring/`)
```
monitoring/
  prometheus.yml
  grafana/
    dashboards/
      apollo-overview.json
      apollo-business.json
    provisioning/
  loki-config.yml
  alertmanager.yml
```

## Phase 3: Database Initialization

### 3.1 Start Postgres + Redis
```bash
docker compose up -d postgres redis
sleep 10  # wait for postgres to be ready
```

### 3.2 Create Extensions
```bash
docker compose exec postgres psql -U apollo -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
docker compose exec postgres psql -U apollo -c "CREATE EXTENSION IF NOT EXISTS vector;"
docker compose exec postgres psql -U apollo -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"
```

### 3.3 Apply Migrations (Alembic)
```bash
docker compose run --rm backend-api alembic upgrade head
```

If migration scripts не созданы — generate initial:
```bash
docker compose run --rm backend-api alembic revision --autogenerate -m "init schema"
docker compose run --rm backend-api alembic upgrade head
```

### 3.4 Seed Data (`--skip-seed` to skip)

Unless `$ARGUMENTS` contains `--skip-seed`:

```bash
# Seed plans (Free, Starter, Pro, Team, Enterprise)
docker compose run --rm backend-api python -m app.scripts.seed_plans

# Seed companies from existing CSV
docker compose run --rm backend-api python -m app.scripts.seed_companies \
  --file docs/uploads/Title\ unclear\ without\ content\ context/companies.csv

# Seed contacts
docker compose run --rm backend-api python -m app.scripts.seed_contacts \
  --file docs/uploads/Title\ unclear\ without\ content\ context/contacts.csv

# Create admin user
docker compose run --rm backend-api python -m app.scripts.create_admin \
  --email admin@apollo-ru.example.com --password $(openssl rand -base64 16)
```

## Phase 4: Start All Services

```bash
docker compose up -d
docker compose ps  # verify all healthy
```

## Phase 5: Smoke Tests

### Health checks
```bash
# API health
curl -fsS http://localhost:8000/health
# Expected: {"status":"ok","version":"x.y.z"}

# Frontend
curl -fsS http://localhost:3000/ | grep -q "Apollo"

# Database connectivity
docker compose exec backend-api python -c "
from app.database import engine
import asyncio
async def check():
    async with engine.connect() as conn:
        result = await conn.execute('SELECT 1')
        print('DB OK' if result.scalar() == 1 else 'DB FAIL')
asyncio.run(check())
"

# Redis
docker compose exec redis redis-cli ping
# Expected: PONG

# Celery worker
docker compose exec worker celery -A app.celery inspect ping
```

### Seed verification
```bash
docker compose exec backend-api python -m app.scripts.verify_seed
# Expected output:
# Plans: 5 ✓
# Companies: 25 ✓
# Contacts: 25 ✓
# Admin user: 1 ✓
```

## Phase 6: Mark Initialized

```bash
touch .apollo-initialized
git add .apollo-initialized
git commit -m "chore: project initialized via /start"
```

## Phase 7: Post-Init Summary

```
═══════════════════════════════════════════════════════════════
✅ APOLLO (RU) — INITIALIZED

🎯 Stack:
  • Backend: http://localhost:8000  (FastAPI)
  • Frontend: http://localhost:3000  (Next.js)
  • Postgres: localhost:5432  (database: apollo)
  • Redis: localhost:6379
  • MinIO: http://localhost:9001  (console)
  • Grafana: http://localhost:3001  (admin/<see GRAFANA_ADMIN_PASSWORD in .env>)

🔑 Admin user created:
  Email: admin@apollo-ru.example.com
  Password: <printed once above — save it>

📦 Seeded:
  • 5 plans (Free, Starter ₽2.9K, Pro ₽9.9K, Team ₽29.9K, Enterprise)
  • 25 companies (top RU public corps)
  • 25 contacts

🚀 Next:
  1. /next         — see what to develop first (suggested: auth module)
  2. /go <feature> — auto-pick implementation pipeline
  3. /run mvp      — autonomous MVP build loop
═══════════════════════════════════════════════════════════════
```

## Idempotency

If `.apollo-initialized` exists:
- Skip Phase 2 (scaffolding)
- Skip Phase 3.4 (seed) unless `--reseed` flag
- Always run Phase 4-5 (start + smoke test)

## Flags

| Flag | Effect |
|------|--------|
| `--skip-seed` | Skip seed data step |
| `--reseed` | Force re-seed (truncate + reload) |
| `--prod` | Use production env file (`.env.production`) |
| `--no-monitoring` | Skip Prometheus/Grafana |

## Error Handling

При сбое любой Phase:
1. Лог в `logs/start-YYYYMMDD-HHMMSS.log`
2. Не trigger следующую Phase
3. Show error + suggested fix
4. Не commit `.apollo-initialized`

Common errors:
- `pg_trgm extension не доступен` → проверь PostgreSQL version (≥16) и pgvector image tag
- `alembic не находит models` → проверь `alembic/env.py` import paths
- `Migration FAIL` → возможно DB не пустая; используй `alembic downgrade base` если safe
- `Health check timeout` → check `docker compose logs backend-api`
