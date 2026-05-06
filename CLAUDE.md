# CLAUDE.md — Apollo (RU)

> Project context for Claude Code. Read this first in every session.

## Project: Apollo (RU)

**Type:** B2B Sales Intelligence Platform (Russian Apollo.io analog)
**Stage:** Pre-MVP (Sprint planning)
**Geography:** Russia → CIS (P2)
**Stack:** Distributed Monolith (Monorepo), Docker Compose, HOSTKEY VPS, MCP servers

## Overview

Apollo (RU) — поиск компаний по ЕГРЮЛ/ОКВЭД/региону + раскрытие контактов ЛПР + Telegram-first outreach с AI-персонализацией + AI ICP look-alike. Замена ручного workflow (СПАРК + парсинг + manual TG) единой self-serve платформой ₽3-30K/мес.

**Source of truth:** `docs/PRD.md`, `docs/Architecture.md`, `docs/Specification.md`

## Architecture

**Pattern:** Distributed Monolith в Monorepo

```
backend-api/       FastAPI 0.115 (Python 3.12) — REST API
worker/            Celery 5 + Redis — async tasks (outreach, ICP, ETL)
etl/               Python — данные из ЕГРЮЛ open data + парсинг
frontend/          Next.js 14 (App Router) + TypeScript + Tailwind + shadcn/ui
nginx/             Reverse proxy + TLS + rate limiting
postgres/          PostgreSQL 16 + pg_trgm + pg_vector
redis/             Redis 7 (cache + broker)
minio/             S3-compatible (CSV uploads)
monitoring/        Prometheus + Grafana + Loki
```

См. `docs/Architecture.md` для C4 диаграмм, `docs/C4_Diagrams.md` для visual reference.

## Tech Stack Decisions

| Layer | Choice | ADR |
|-------|--------|-----|
| Backend | FastAPI 0.115 (Python 3.12, async) | ADR-001, ADR-011 |
| Frontend | Next.js 14 (App Router, SSR) | ADR-004 |
| Database | PostgreSQL 16 + pg_trgm + pg_vector | ADR-002 |
| Cache/Broker | Redis 7 | ADR-003 |
| Task queue | Celery 5 | ADR-003 |
| LLM | YandexGPT primary, OpenAI fallback | ADR-005 |
| Outreach | Telegram Bot API | ADR-006 |
| Payments | ЮKassa (CloudPayments backup) | ADR-010 |
| Hosting | HOSTKEY VPS Russia | ADR-008 |
| Auth | JWT (httpOnly cookies, rotation) | ADR-001 |

См. `docs/ADR.md` для всех 15 архитектурных решений.

## Key Algorithms (см. `docs/Pseudocode.md`)

1. **Reveal Contact** — atomic с SELECT FOR UPDATE, idempotent по (user_id, company_inn)
2. **Company Search** — multi-filter с pg_trgm для fuzzy name search
3. **AI ICP Analysis** — distributions + LLM summary + look-alike scoring
4. **Outreach Send Loop** — throttle 5 msg/sec, 30-day per-recipient cooldown, opt-out check
5. **Quota Reset** — Celery Beat 1-го числа месяца, ЮKassa auto-renewal

## Security Rules

⚠️ **CRITICAL — соблюдать при работе с любым кодом:**

1. **152-ФЗ:** только публичные данные о компаниях, opt-out flow, audit log 3 года
2. **User-side API keys** (LLM, TG bot tokens пользователя) — Encrypted IndexedDB (AES-GCM 256, PBKDF2). **Никогда** на сервер.
3. **Параметризированные SQL** только. SQL injection = blocker.
4. **bcrypt(cost=12)** для паролей.
5. **JWT в httpOnly cookies**, refresh rotation, signing key rotation 90 дней.
6. **TLS 1.3 only**, HSTS preload.
7. **Webhook signature verification** обязательно (ЮKassa HMAC).
8. **Rate limiting** per-endpoint (см. `docs/Refinement.md`).
9. **Audit log** все critical actions (reveal, send_message, change_plan, opt_out).
10. **Никогда не логировать** passwords, JWTs, ЮKassa secrets, user-API keys. Email/phone/ИНН — маскируются.

См. `.claude/rules/security.md` и `.claude/rules/secrets-management.md`.

## Coding Standards

- **Python:** PEP 8, ruff + black, mypy strict, type hints везде
- **TypeScript:** strict mode, eslint + prettier
- **Imports:** absolute от корня package
- **Naming:** `snake_case` (Python), `camelCase` (TS), `PascalCase` (классы), `SCREAMING_SNAKE` (constants)
- **No emojis** в коде/комментариях/коммитах
- **Comments:** только если "почему", не "что"

См. `.claude/rules/coding-style.md`.

## Parallel Execution Strategy

Используй `Task` tool для:
- **Independent fields** в большой фиче (frontend + backend + tests параллельно)
- **Tests + linting + type-check** одновременно при review
- **Multiple agents** для validation swarm (5 параллельных в Phase 2)
- **ETL pipelines** — 3-5 источников параллельно

**Не параллелить** при data dependencies (например, миграция БД блокирует API restart).

## Swarm Agents (для сложных задач)

Когда нужно:
- **Validation swarm:** 5 валидаторов параллельно (Stories, AC, Architecture, Pseudocode, Coherence)
- **Review swarm:** 5 ревьюеров параллельно (code-quality, architecture, security, performance, testing)
- **Implementation swarm:** 3-5 implementer'ов на разные файлы/модули

Координация через `/feature` команду — она оркестрирует свармы автоматически.

## Available Agents (`.claude/agents/`)

| Agent | When to use |
|-------|-------------|
| `planner` | Декомпозиция фич, оценка сложности, dependency analysis |
| `architect` | Системные решения, выбор технологий, ADR drafting |
| `code-reviewer` | Brutal honesty review (Bach + Ramsay стиль) |

## Available Skills (`.claude/skills/`)

| Skill | Purpose | When to use |
|-------|---------|-------------|
| `sparc-prd-mini` | Документация по SPARC | `/feature` Phase 1 |
| `requirements-validator` | INVEST/SMART checks + BDD | `/feature` Phase 2 |
| `brutal-honesty-review` | Безжалостный ревью | `/feature` Phase 4 |
| `explore` | Сократические вопросы | Pre-flight clarification |
| `goap-research-ed25519` | GOAP A* research | Sourcing с верификацией |
| `problem-solver-enhanced` | TRIZ + 5 Whys + First Principles | Tricky design problems |
| `project-context` | Apollo-specific domain knowledge | Auto-loaded |
| `coding-standards` | Python/TS patterns для Apollo | Auto-loaded |
| `testing-patterns` | pytest-bdd / Playwright / k6 | При написании тестов |
| `feature-navigator` | Roadmap navigation | `/next` команда |
| `security-patterns` | Encrypted IndexedDB, OWASP | При работе с auth/secrets |

## Quick Commands (`.claude/commands/`)

### Pipeline (orchestration)
- `/start` — инициализация проекта (БД, миграции, seed, smoke test)
- `/run` / `/run mvp` / `/run all` — автономный build loop через roadmap
- `/next` / `/next [feature-id]` — что делать дальше / mark done
- `/go [feature]` — авто-выбор `/plan` или `/feature` по сложности

### Development
- `/feature [name]` — full SPARC lifecycle (Plan → Validate → Implement → Review)
- `/plan [task]` — lightweight plan в `docs/plans/`
- `/test [scope]` — запуск/генерация тестов
- `/deploy [env]` — deploy в staging / production

### Knowledge & Docs
- `/myinsights [insight]` — захват грабель в knowledge base
- `/docs` / `/docs eng` — генерация документации (RU/EN bilingual)
- `/harvest` — extraction reusable knowledge

## Development Insights (knowledge base)

При работе с error'ами: **сначала grep в `myinsights/1nsights.md`** — возможно эта проблема уже решена.

При обнаружении нового workaround/gotcha — `/myinsights` для записи в базу. Auto-commit через Stop hook.

См. `.claude/rules/insights-capture.md` для протокола.

## Feature Development Lifecycle

См. `.claude/rules/feature-lifecycle.md` — формальный 4-фазный процесс:

```
Phase 1: PLAN     → /feature запускает sparc-prd-mini → docs/features/<name>/sparc/
Phase 2: VALIDATE → 5 validators swarm → score ≥70 required → BDD scenarios
Phase 3: IMPLEMENT → parallel agents читают validated docs → код + тесты
Phase 4: REVIEW   → brutal-honesty-review swarm → fix criticals
```

Для **простых задач** (<3 файлов) — `/plan` вместо `/feature` (5x faster).

## Feature Roadmap

См. `.claude/feature-roadmap.json` — все фичи MVP с статусами и зависимостями.

Используй `/next` для навигации, `/go [feature]` для автоматического выбора пайплайна.

## Implementation Plans

`docs/plans/` — для lightweight планов от `/plan` команды. Не `git ignore` — нужны для трассируемости.

## Automation Commands

| Сценарий | Команда |
|----------|---------|
| Одна фича | `/go feature-name` |
| Весь MVP | `/run` или `/run mvp` |
| Весь проект | `/run all` |
| Что делать дальше | `/next` |
| Документация | `/docs`, `/docs eng`, `/docs update` |

Иерархия: `/run` → `/start` → loop[`/next` → `/go` → `/plan` или `/feature`]

## Project-Specific Gotchas

- **ИНН формат:** 10 цифр (юрлица) или 12 (ИП). Regex `^\d{10}$|^\d{12}$`. Никогда не number — leading zeros.
- **ОКВЭД префикс-матчинг:** "62" matches "62.01", "62.02.1". Используем LIKE / starts_with.
- **Telegram username:** strip leading `@`. `@ivanov` и `ivanov` — одно и то же.
- **Денежные суммы:** только в копейках (BIGINT). Никогда float.
- **Timezone:** все timestamps в UTC. UI converts в МСК (Europe/Moscow).
- **Pagination:** max page_size=100. Default 20.
- **152-ФЗ:** opt-out URL должен иметь HMAC token (предотвращение enumeration).
- **Idempotency:** ЮKassa charges с idempotence_key=hash(sub_id, period_end). Без него — повторное списание.
- **Forward-compatible migrations:** новые колонки NULLABLE или с DEFAULT (см. ADR-012).

## Resources

| Document | Purpose |
|----------|---------|
| `docs/PRD.md` | Product requirements |
| `docs/Architecture.md` | System design + tech stack |
| `docs/Specification.md` | Detailed requirements + Gherkin AC |
| `docs/Pseudocode.md` | Algorithms + API contracts |
| `docs/Refinement.md` | Edge cases, testing, optimizations |
| `docs/Completion.md` | Deployment, CI/CD, runbooks |
| `docs/ADR.md` | 15 architecture decisions |
| `docs/test-scenarios.md` | 65 BDD scenarios |
| `docs/validation-report.md` | Phase 2 validation results |
| `DEVELOPMENT_GUIDE.md` | Setup → develop → deploy guide |

## Constraints (никогда не нарушать)

- Distributed Monolith (Monorepo) — НЕ микросервисы в MVP
- Docker Compose — НЕ Kubernetes в MVP
- Российский хостинг (HOSTKEY) — НЕ AWS/GCP
- YandexGPT primary — НЕ OpenAI primary (compliance)
- Telegram-only outreach в MVP — Email в P1
- Только публичные данные о компаниях (152-ФЗ)
- Self-serve pricing — НЕ sales-only enterprise

## Working Style

- **Pragmatic over perfect** — MVP shipping > theoretical optimum
- **Test critical paths 100%** — auth, billing, reveal, audit
- **Document decisions** — каждое значимое архитектурное решение → новый ADR
- **Read docs first** — never hallucinate; всегда проверять `docs/`
- **Commit often** — semantic commits (см. `.claude/rules/git-workflow.md`)
- **Capture insights** — каждый workaround / gotcha → `/myinsights`
