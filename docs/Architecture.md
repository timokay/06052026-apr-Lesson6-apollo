# Architecture: Apollo (RU)

> SPARC Phase 5 output. System design, tech stack, deployment.

## 1. Architecture Style

**Distributed Monolith (Monorepo)** — единый репозиторий с несколькими сервисами в Docker Compose, развёрнутыми на одной/нескольких VPS.

**Why this style:**
- ✅ MVP скорость: один деплой, минимум координации
- ✅ Простота операций: один docker-compose.yml, нет Kubernetes
- ✅ Возможность выделить микросервисы из bounded contexts при росте
- ❌ Trade-off: при росте >10 сервисов потребуется миграция на оркестратор

## 2. High-Level Architecture (C4 Container Diagram)

```mermaid
graph TB
  subgraph User
    U[Browser / Web App]
  end

  subgraph "Apollo (RU) — VPS HOSTKEY"
    direction TB
    subgraph "Reverse Proxy"
      NX[Nginx + TLS]
    end
    subgraph "Frontend"
      FE[Next.js App<br/>SSR + SPA]
    end
    subgraph "Backend Services"
      API[FastAPI<br/>Core API]
      WORK[Celery Worker<br/>Outreach + ICP jobs]
      ETL[ETL Service<br/>Data ingestion]
    end
    subgraph "Data Layer"
      PG[(PostgreSQL 16<br/>+ pg_trgm + pg_vector)]
      RD[(Redis 7<br/>Cache + Celery broker)]
      MN[(MinIO<br/>S3-compatible<br/>CSV uploads)]
    end
    subgraph "Observability"
      PR[Prometheus]
      GR[Grafana]
      LK[Loki]
    end
  end

  subgraph "External Services"
    YK[ЮKassa API<br/>Payments]
    TG[Telegram Bot API<br/>Outreach]
    LLM[LLM API<br/>YandexGPT primary<br/>OpenAI fallback]
    SP[СПАРК / Контур API<br/>P2 only]
    OPEN[ЕГРЮЛ open data<br/>weekly bulk]
  end

  U -->|HTTPS| NX
  NX --> FE
  NX --> API
  FE -->|API calls| API
  API --> PG
  API --> RD
  API --> MN
  API -->|enqueue| RD
  WORK --> RD
  WORK --> PG
  WORK -->|HTTPS| TG
  WORK -->|HTTPS| LLM
  API -->|HTTPS webhook| YK
  ETL --> PG
  ETL --> OPEN
  ETL --> SP
  API -->|metrics| PR
  WORK -->|metrics| PR
  PR --> GR
  API -->|logs| LK
  LK --> GR
```

## 3. Component Breakdown

### 3.1 Frontend (`frontend/`)
- **Stack:** Next.js 14 (App Router), TypeScript, TailwindCSS, shadcn/ui, React Query
- **Pages:**
  - `/` — landing (SSR for SEO)
  - `/register`, `/login`, `/verify` — auth flow
  - `/dashboard` — main app (filters + results table)
  - `/dashboard/companies/[inn]` — company card
  - `/dashboard/icp` — ICP analyzer
  - `/dashboard/campaigns` — outreach campaigns list + create
  - `/dashboard/billing` — plan management
  - `/settings/api-keys` — encrypted IndexedDB UI for user-owned API keys
  - `/optout` — public unsubscribe page
- **State:** React Query for server state, Zustand for UI state
- **Auth:** JWT in httpOnly cookie + CSRF token

### 3.2 Backend Core API (`backend-api/`)
- **Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic migrations, Pydantic v2
- **Modules:**
  - `auth/` — JWT, registration, password reset
  - `companies/` — search, filters, card view
  - `reveals/` — contact reveal + credit deduction (atomic)
  - `icp/` — ICP analysis trigger (enqueues to Celery)
  - `campaigns/` — outreach CRUD, send trigger
  - `billing/` — subscription, ЮKassa webhooks
  - `audit/` — append-only audit log writer
  - `optout/` — public opt-out endpoint with HMAC token validation
- **Patterns:** Repository pattern, Service layer, dependency injection через FastAPI DI

### 3.3 Worker Service (`worker/`)
- **Stack:** Celery 5 + Redis broker
- **Tasks:**
  - `outreach.send_campaign(campaign_id)` — итерирует по получателям, throttle, retry on TG errors
  - `icp.analyze(user_id, file_id)` — LLM анализ + look-alike алгоритм
  - `etl.refresh_companies()` — еженедельная загрузка из ЕГРЮЛ open data
  - `billing.reset_quotas()` — cron 1-го числа месяца 00:00 MSK
  - `notifications.send_email(template, user_id)` — email через SMTP

### 3.4 ETL Service (`etl/`)
- **Stack:** Python pandas + httpx (для парсинга)
- **Pipelines:**
  - `egrul_bulk` — еженедельный download .json от ФНС, upsert в PostgreSQL
  - `e_disclosure_scraper` — публичная отчётность ПАО (раз в квартал)
  - `okved_classifier` — справочник ОКВЭД (статичный, обновляется редко)
  - **P2:** `spark_api_sync` — инкрементальная синхронизация со СПАРК API
- **Schedule:** через Celery Beat

### 3.5 Data Layer

| Component | Tech | Purpose |
|-----------|------|---------|
| **PostgreSQL 16** | Primary DB | Все entities (users, companies, contacts, reveals, campaigns, billing) |
| **pg_trgm extension** | Search | Trigram index для fuzzy company name search |
| **pg_vector extension** | Embeddings | Векторы для look-alike (M2: similarity по embeddings) |
| **Redis 7** | Cache + Broker | Кэш топ-100 поисковых запросов, sessions, Celery broker |
| **MinIO** | S3-compat | Загрузки CSV (ICP, кампании), экспорты |

### 3.6 Reverse Proxy (`nginx/`)
- TLS termination (Let's Encrypt + acme.sh autorenew)
- HTTP → HTTPS redirect, HSTS preload
- Static assets cache
- Rate limiting (100 req/min per IP)
- Reverse proxy to Next.js (port 3000) and FastAPI (port 8000)

### 3.7 Observability stack
- **Prometheus** — metrics scrape (FastAPI middleware exposes /metrics)
- **Grafana** — dashboards (request rate, latency p50/p95/p99, error rate, queue depth, DB connections)
- **Loki + Promtail** — log aggregation
- **Alertmanager** — Telegram alerts to ops channel

## 4. Tech Stack Summary

| Layer | Technology | Version | Rationale |
|-------|-----------|---------|-----------|
| **Frontend Framework** | Next.js | 14.x (App Router) | SSR for SEO landing, SPA for app |
| **Frontend Language** | TypeScript | 5.x | Type safety |
| **CSS** | TailwindCSS | 3.x | Utility-first, fast iteration |
| **UI Components** | shadcn/ui | latest | Headless, customizable |
| **Frontend State** | React Query + Zustand | latest | Server cache + UI state |
| **Backend Framework** | FastAPI | 0.115+ | Async, OpenAPI auto, типы |
| **Backend Language** | Python | 3.12 | Best for ML/data |
| **ORM** | SQLAlchemy 2.0 | async | Mature, type-safe |
| **Migrations** | Alembic | latest | Standard for SQLAlchemy |
| **Validation** | Pydantic v2 | latest | Performance + types |
| **Task queue** | Celery | 5.x | Mature, RU community familiar |
| **Database** | PostgreSQL | 16 | JOIN-heavy domain, JSONB для metadata |
| **Cache** | Redis | 7 | Standard |
| **Object Storage** | MinIO | latest | Self-hosted S3 |
| **Reverse Proxy** | Nginx | 1.27 | Standard |
| **Container** | Docker | 27 | Standard |
| **Orchestration** | Docker Compose | v2 | MVP scope |
| **Hosting** | HOSTKEY VPS | — | Russian jurisdiction, SLA 99.9% |
| **CI/CD** | GitHub Actions | — | Free, integrates with repo |
| **LLM Primary** | YandexGPT | API v3 | Russian compliance, лучше для русского |
| **LLM Fallback** | OpenAI | gpt-4o-mini | Если YandexGPT недоступен |
| **Payments** | ЮKassa | API v3 | Russian acquiring, recurrent payments |
| **Outreach** | Telegram Bot API | latest | De-facto B2B канал РФ |
| **Email transactional** | Unisender Go (P1) | API | Verified в РФ |

## 5. Data Architecture

### 5.1 Core Tables (PostgreSQL)

```sql
-- Users & Auth
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('pending_verification','active','suspended','deleted')),
  pdn_consent_at TIMESTAMPTZ NOT NULL,
  marketing_consent_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Subscriptions & Billing
CREATE TABLE plans (
  code TEXT PRIMARY KEY,        -- 'free', 'starter', 'pro', 'team', 'enterprise'
  price_kopecks BIGINT NOT NULL,
  reveal_quota INT NOT NULL,
  outreach_quota INT NOT NULL,
  seats INT NOT NULL,
  ai_personalize BOOLEAN NOT NULL
);

CREATE TABLE subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  plan_code TEXT REFERENCES plans(code),
  status TEXT CHECK (status IN ('trialing','active','past_due','canceled')),
  period_start TIMESTAMPTZ NOT NULL,
  period_end TIMESTAMPTZ NOT NULL,
  remaining_reveals INT NOT NULL,
  remaining_outreach INT NOT NULL,
  yookassa_payment_method_id TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Companies (denormalized for search performance)
CREATE TABLE companies (
  inn TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  okved_main TEXT,
  region TEXT,
  employee_count INT,
  revenue_range TEXT,         -- enum
  address TEXT,
  director TEXT,
  embedding vector(384),      -- for look-alike (P2)
  data_source TEXT,           -- 'egrul', 'edisclosure', 'manual', 'spark'
  updated_at TIMESTAMPTZ DEFAULT now(),
  CONSTRAINT inn_format CHECK (inn ~ '^[0-9]{10,12}$')
);

CREATE INDEX idx_companies_okved ON companies(okved_main);
CREATE INDEX idx_companies_region ON companies(region);
CREATE INDEX idx_companies_revenue ON companies(revenue_range);
CREATE INDEX idx_companies_name_trgm ON companies USING gin(name gin_trgm_ops);
CREATE INDEX idx_companies_embedding ON companies USING ivfflat (embedding vector_cosine_ops);

-- Contacts
CREATE TABLE contacts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_inn TEXT REFERENCES companies(inn),
  name TEXT,
  title TEXT,
  email TEXT,
  phone TEXT,
  telegram TEXT,
  source_url TEXT,
  confidence TEXT CHECK (confidence IN ('low','medium','high')),
  opted_out BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_contacts_company ON contacts(company_inn);

-- Reveals (audit + cache)
CREATE TABLE reveal_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  company_inn TEXT REFERENCES companies(inn),
  credit_cost INT NOT NULL DEFAULT 1,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_id, company_inn)
);

-- ICP Profiles
CREATE TABLE icp_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  name TEXT,
  uploaded_inns TEXT[] NOT NULL,
  llm_summary TEXT,
  industry_distribution JSONB,
  size_distribution JSONB,
  region_distribution JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Campaigns
CREATE TABLE campaigns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  name TEXT NOT NULL,
  channel TEXT CHECK (channel IN ('telegram','email')),
  template TEXT NOT NULL,
  ai_personalize BOOLEAN DEFAULT FALSE,
  status TEXT CHECK (status IN ('draft','scheduled','running','completed','canceled')),
  scheduled_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE campaign_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_id UUID REFERENCES campaigns(id),
  contact_id UUID REFERENCES contacts(id),
  rendered_text TEXT,
  status TEXT CHECK (status IN ('queued','sent','delivered','read','replied','errored','skipped')),
  error_code TEXT,
  sent_at TIMESTAMPTZ,
  delivered_at TIMESTAMPTZ
);
CREATE INDEX idx_messages_campaign_status ON campaign_messages(campaign_id, status);

-- Audit Log (append-only, partitioned by month)
CREATE TABLE audit_log (
  id BIGSERIAL,
  user_id UUID,
  action TEXT NOT NULL,
  entity_type TEXT,
  entity_id TEXT,
  metadata JSONB,
  ip TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
) PARTITION BY RANGE (created_at);

-- Opt-out registry
CREATE TABLE opt_outs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  identifier TEXT NOT NULL,    -- email, phone, telegram username
  identifier_type TEXT CHECK (identifier_type IN ('email','phone','telegram')),
  source TEXT,                  -- 'user_link', 'reply_stop', 'manual'
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(identifier, identifier_type)
);
```

### 5.2 Data Flow Diagrams

**Reveal Flow:**
```
User clicks "Reveal" 
  → POST /reveals { company_inn }
  → API: BEGIN TX
  → SELECT remaining_reveals FROM subscriptions WHERE user_id = ? FOR UPDATE
  → IF 0: ROLLBACK, return 402
  → SELECT * FROM contacts WHERE company_inn = ? AND opted_out = false
  → INSERT INTO reveal_events ...
  → UPDATE subscriptions SET remaining_reveals = remaining_reveals - 1
  → INSERT INTO audit_log ...
  → COMMIT
  → return contacts
```

**Outreach Send Flow (Celery):**
```
User clicks "Send campaign"
  → API: enqueue outreach.send_campaign(campaign_id)
  → Worker:
      FOR each contact in campaign:
        IF contact.telegram is null OR opt_out: skip
        IF last_message_to_contact < 30d: skip
        IF ai_personalize:
          rendered = LLM.generate(template, company_context)
        ELSE:
          rendered = render_template(template, contact)
        result = telegram.send(@username, rendered)
        INSERT campaign_messages (status, error_code, ...)
        sleep(0.2)  # 5/sec
```

## 6. Security Architecture

### 6.1 Authentication
- bcrypt(cost=12) для паролей
- JWT с разделением access (15 min) + refresh (7 days, rotation)
- httpOnly cookies, SameSite=Lax, Secure
- CSRF: double-submit cookie pattern

### 6.2 Authorization
- RBAC: roles `owner`, `admin`, `member` (для Team plans)
- Resource ownership: все queries фильтруются по `user_id`
- API key (P2): HMAC-signed, scoped per-resource

### 6.3 Data Encryption
- **At Rest:** PostgreSQL TDE (full-disk encryption на VPS), MinIO bucket encryption (SSE-S3)
- **In Transit:** TLS 1.3 only
- **User-side secrets** (LLM API keys, Telegram bot tokens пользователя):
  - **Pattern:** Encrypted IndexedDB (AES-GCM 256-bit) + PBKDF2 from user password
  - Never sent to backend
  - Web Crypto API
  - Auto-lock after 30 min idle

### 6.4 Application Security
- Input validation: Pydantic schemas в API
- SQL injection: parametrized queries (SQLAlchemy)
- XSS: React автоэкранирование + DOMPurify для user-input HTML
- CSRF: токены
- Rate limiting: Nginx (basic) + FastAPI middleware (per-user)
- Secrets management: Docker secrets / .env (не в git!)

### 6.5 Compliance
- **152-ФЗ:**
  - Реестр операторов ПДн (регистрация в Роскомнадзоре)
  - Privacy policy + Terms of Service на /privacy, /terms
  - Согласие на обработку ПДн (чекбокс) при регистрации
  - Право на удаление аккаунта (soft delete + hard delete через 30 дней)
  - Только публичные данные в reveals
  - Opt-out flow с HMAC-токенами (нельзя угадать ссылку другого пользователя)
- **Audit:**
  - Все critical actions в audit_log (3 года retention)
  - Партиционирование по месяцу

## 7. Scalability Strategy

### 7.1 Vertical scaling (MVP)
- VPS HOSTKEY: 8 vCPU, 16GB RAM, 200GB NVMe SSD
- PostgreSQL connection pool: 20 (FastAPI) + 10 (Worker)
- Redis maxmemory 2GB

### 7.2 Horizontal scaling (Y1 Q4)
- Сделать API stateless (вынести sessions в Redis)
- 2-3 replicas FastAPI за nginx upstream
- 3-5 Celery workers
- PostgreSQL read replica (для search queries)
- Redis Sentinel или Redis Cluster

### 7.3 Bottlenecks (anticipated)
| Bottleneck | Resolution |
|-----------|------------|
| Search queries on 500K rows | Materialized views по популярным фильтрам, ES в P2 |
| LLM API rate limits | Response caching по hash(prompt), batch processing |
| Telegram Bot API rate | Multiple bot tokens с round-robin, queue priority |
| ETL bulk загрузка | COPY вместо INSERT, partitioning by region |

## 8. Deployment Architecture

```yaml
# docker-compose.yml (production)
services:
  nginx:
    image: nginx:1.27-alpine
    ports: ["80:80", "443:443"]
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certbot/conf:/etc/letsencrypt:ro
      - ./certbot/www:/var/www/certbot:ro
    depends_on: [frontend, backend-api]

  frontend:
    build: ./frontend
    environment:
      NEXT_PUBLIC_API_URL: https://apollo-ru.example.com/api
    expose: ["3000"]

  backend-api:
    build: ./backend-api
    environment:
      DATABASE_URL: postgresql+asyncpg://apollo:${DB_PASSWORD}@postgres:5432/apollo
      REDIS_URL: redis://redis:6379/0
      JWT_SECRET: ${JWT_SECRET}
      YOOKASSA_SHOP_ID: ${YOOKASSA_SHOP_ID}
      YOOKASSA_SECRET_KEY: ${YOOKASSA_SECRET_KEY}
      LLM_PROVIDER: yandexgpt
      YANDEXGPT_API_KEY: ${YANDEXGPT_API_KEY}
    expose: ["8000"]
    depends_on: [postgres, redis]

  worker:
    build: ./backend-api
    command: celery -A app.celery worker -Q outreach,icp,etl,billing
    environment: ... # same as backend-api
    depends_on: [postgres, redis]

  beat:
    build: ./backend-api
    command: celery -A app.celery beat
    depends_on: [redis]

  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: apollo
      POSTGRES_USER: apollo
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes: [postgres_data:/var/lib/postgresql/data]

  redis:
    image: redis:7-alpine
    volumes: [redis_data:/data]
    command: redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    volumes: [minio_data:/data]

  prometheus:
    image: prom/prometheus
    volumes: [./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro]

  grafana:
    image: grafana/grafana
    volumes: [grafana_data:/var/lib/grafana]

volumes:
  postgres_data:
  redis_data:
  minio_data:
  grafana_data:
```

### 8.1 CI/CD (GitHub Actions)

```
.github/workflows/
├── ci.yml          # PR: lint + test + type-check + build
├── deploy-prod.yml # main: build images, push to registry, SSH deploy
└── nightly.yml     # ETL jobs, backups
```

**Deploy flow:**
1. Push to `main` → triggers deploy-prod.yml
2. Build Docker images (parallel for frontend, backend-api, worker, etl)
3. Push to GitHub Container Registry (ghcr.io)
4. SSH to VPS, pull new images, `docker compose up -d --no-deps <service>`
5. Smoke tests (curl /health for each service)
6. Rollback on failure: `docker compose up -d --rollback`

### 8.2 MCP Servers (AI integrations for development)

```yaml
# .mcp.json (project-scoped MCP servers for Claude Code dev workflow)
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres", "${DATABASE_URL}"]
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "./"]
    }
  }
}
```

## 9. Module/Service Boundaries (для будущего split на микросервисы)

| Bounded Context | Current package | Future service |
|----------------|-----------------|----------------|
| Auth & Users | `backend-api/auth/` | auth-service |
| Companies & Contacts | `backend-api/companies/` | data-service |
| Reveals & Quotas | `backend-api/reveals/` | usage-service |
| Outreach (TG/email) | `worker/outreach/` | outreach-service |
| ICP & Look-alike | `worker/icp/` | ml-service |
| Billing | `backend-api/billing/` | billing-service |
| ETL | `etl/` | data-pipeline-service |

## 10. Architecture Decisions (краткие, полный список в ADR.md)

| ID | Decision | Rationale |
|----|----------|-----------|
| ADR-001 | Distributed Monolith over Microservices | MVP scope, team size 4-6 |
| ADR-002 | PostgreSQL 16 + pg_vector over MongoDB+Pinecone | Структурированные данные, ACID |
| ADR-003 | Celery + Redis over Kafka/RabbitMQ | Familiar stack, MVP throughput suffices |
| ADR-004 | Next.js over CRA / Remix | SSR для SEO landing |
| ADR-005 | YandexGPT primary, OpenAI fallback | 152-ФЗ compliance, cheaper RU |
| ADR-006 | Telegram-first, email later | Phase 0 research: TG = de-facto B2B канал в РФ |
| ADR-007 | Encrypted IndexedDB for user API keys | Security pattern: client-side only |
| ADR-008 | HOSTKEY VPS over AWS/GCP/Yandex.Cloud | RU jurisdiction, predictable cost, нет sanctions risk |

## 11. Open Architecture Questions

1. **Search engine choice for 1M+ companies:** PG FTS sufficient до 200K, перейти на ES при 500K+ ? Или сразу ES с MVP?
2. **Multi-tenancy:** через row-level security в PG или через отдельные schemas per Team plan?
3. **Backup strategy:** WAL streaming в S3 или daily snapshots?
4. **Disaster recovery:** Cross-region replica (Yandex.Cloud в Москве + HOSTKEY в Владивостоке)?
