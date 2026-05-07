# Apollo (RU)

> B2B Sales Intelligence platform для российского рынка. Аналог Apollo.io / ZoomInfo, локализованный под РФ: ЕГРЮЛ-data, Telegram-first outreach, AI ICP look-alike, 152-ФЗ-compliant.

**Status:** Pre-MVP (sprint planning)
**Stage:** Documentation + Toolkit ready, Implementation pending

## Что это

Apollo (RU) — единая B2B sales OS:
- 🔍 **Поиск компаний** по ИНН/ОКВЭД/региону/выручке/числу сотрудников
- 📇 **Раскрытие контактов ЛПР** (email, phone, telegram) с credit-system
- 📊 **AI ICP анализ** — upload CRM CSV → LLM находит look-alike компаний
- 💬 **Telegram outreach** — массовая рассылка с AI-персонализацией, cooldown, opt-out
- 💳 **Self-serve SaaS billing** через ЮKassa (Free / Starter ₽2.9K / Pro ₽9.9K / Team ₽29.9K / Enterprise)

**Целевая аудитория:** B2B-сейлзы (P0), маркетологи / demand gen (P1), M&A аналитики (P2).

## Зачем

Российские B2B-сейлзы тратят 30-40% времени на ручной поиск контактов. Apollo.io / ZoomInfo не работают в РФ. СПАРК / Контур — только данные без outreach. LinkedIn заблокирован, Telegram стал de-facto B2B-каналом. Нет единой self-serve платформы.

Apollo (RU) объединяет данные из ЕГРЮЛ + парсинг + СПАРК API (в P2) + AI ICP + Telegram-first outreach в одной подписке по цене 3-5x ниже Контур.Компас.

## Architecture

**Distributed Monolith (Monorepo)** на Docker Compose / HOSTKEY VPS Russia.

```
backend-api/   FastAPI 0.115 (Python 3.12)
worker/        Celery 5 + Redis (outreach, ICP, ETL)
etl/           ЕГРЮЛ open data + парсинг
frontend/      Next.js 14 (App Router, TS, Tailwind, shadcn/ui)
postgres/      PG 16 + pg_trgm + pg_vector
redis/         Cache + Celery broker
minio/         S3-compatible (CSV uploads)
nginx/         Reverse proxy + TLS
monitoring/    Prometheus + Grafana + Loki
```

См. `docs/Architecture.md` + `docs/C4_Diagrams.md`.

## Tech Stack

| Layer | Choice |
|-------|--------|
| Backend | Python 3.12, FastAPI 0.115, SQLAlchemy 2.0 (async), Pydantic v2, Alembic, Celery 5 |
| Frontend | Next.js 14 App Router, TypeScript, TailwindCSS, shadcn/ui, React Query, Zustand |
| Database | PostgreSQL 16 + pg_trgm + pg_vector |
| Cache | Redis 7 |
| LLM | YandexGPT primary (RU compliance) + OpenAI fallback |
| Outreach | Telegram Bot API |
| Payments | ЮKassa (CloudPayments backup) |
| Hosting | HOSTKEY VPS Russia |
| CI/CD | GitHub Actions → ghcr.io → SSH deploy |

15 ADRs documented в `docs/ADR.md`.

## Quick Start

```bash
# 1. Clone
git clone https://github.com/timokay/06052026-apr-Lesson6-apollo.git
cd 06052026-apr-Lesson6-apollo

# 2. Configure
cp .env.example .env
# Edit .env с вашими ключами (см. .claude/rules/secrets-management.md)

# 3. Bootstrap (через Claude Code)
/start

# 4. Verify
curl http://localhost:8000/health
curl http://localhost:3000/
```

После `/start`:
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- Grafana: http://localhost:3001 (admin / см. `GRAFANA_ADMIN_PASSWORD`)
- MinIO console: http://localhost:9001

## Development

Build features через Claude Code:

```
/next                    # Что делать дальше
/go user-auth            # Auto-pick pipeline (/plan or /feature)
/feature user-auth       # Full SPARC lifecycle (Plan → Validate → Implement → Review)
/run mvp                 # Autonomous build всех MVP features
```

См. `DEVELOPMENT_GUIDE.md` для полного workflow.

## MVP Roadmap (`.claude/feature-roadmap.json`)

18 features в 6 спринтах (~110 hours total):

| Sprint | Features | Focus |
|--------|----------|-------|
| **1** | user-auth, company-search, company-card, csv-export-basic | Foundation |
| **2** | audit-log, reveal-with-quota, csv-export-pro | Reveal flow |
| **3** | billing-plans, billing-yookassa, quota-reset | Monetization |
| **4** | telegram-outreach-mvp, outreach-personalize, opt-out-flow | Outreach |
| **5** | icp-analyzer, icp-look-alike | AI features |
| **6** | team-seats, monitoring-dashboards, e2e-tests-suite | Polish |

Target end of Y1: 300 paying customers, ARR ₽25M.

## Documentation

Все SPARC-документы в `docs/`:

| Document | Purpose | Lines |
|----------|---------|-------|
| `PRD.md` | Product requirements | 188 |
| `Solution_Strategy.md` | Problem analysis (TRIZ + Game Theory) | 143 |
| `Specification.md` | Detailed requirements + 23 Gherkin AC + NFR | 451 |
| `Pseudocode.md` | 5 algorithms + API contracts + state machines | 692 |
| `Architecture.md` | C4 + tech stack + data model + security | 570 |
| `Refinement.md` | Edge cases + testing strategy + optimizations | 307 |
| `Completion.md` | Deployment + CI/CD + monitoring + 5 runbooks | 526 |
| `Research_Findings.md` | Market + competitors + tech assessment | 317 |
| `C4_Diagrams.md` | Mermaid diagrams (System + Container + Component) | 417 |
| `ADR.md` | 15 architecture decisions | 313 |
| `Final_Summary.md` | Executive summary | 136 |
| `validation-report.md` | Phase 2 validation (avg 78/100, 0 blocked) | — |
| `test-scenarios.md` | 65 BDD scenarios (13 happy + 21 errors + 17 edge + 14 sec) | — |
| `product-discovery-brief.md` | Phase 0 reverse-eng of Apollo.io for RU launch | 309 |

## Project Toolkit (Claude Code)

10 commands, 3 agents, 11 skills, 7 rules — все в `.claude/`.

См. `CLAUDE.md` (root) для полного project context.

## Compliance

- 🇷🇺 **152-ФЗ:** регистрация в Реестре операторов ПДн, opt-out, audit log 3 года
- 🔐 **Security:** TLS 1.3, JWT rotation 90d, bcrypt(12), encrypted IndexedDB для user-side keys (AES-GCM 256 + PBKDF2)
- 📍 **Hosting:** HOSTKEY VPS Russia (РФ юрисдикция)
- 📊 **Audit:** все critical actions (reveal, send_message, billing) — 3 года retention

## Key Differentiators

1. 🎯 **Telegram-first outreach** — единственный игрок с native TG в категории РФ
2. 🤖 **AI ICP look-alike** — на российских данных
3. 💸 **Self-serve pricing 3-5x ниже** Контур.Компас
4. 🛡️ **152-ФЗ-first design** — opt-out flow, audit, реестр

## Risks & Mitigations

| # | Risk | Mitigation |
|---|------|------------|
| 1 | 152-ФЗ ужесточит outreach | Юр-аудит, opt-in flow, готовый pivot на enrichment-only |
| 2 | TG заблокирует bot за рассылку | 30d cooldown, opt-in, multi-bot pool, fallback email |
| 3 | Контур запустит analog | Speed (MVP 5 мес), AI ICP moat, Telegram-spec |
| 4 | Data acquisition дорого | Hybrid: ЕГРЮЛ open + парсинг + СПАРК поэтапно |

## Contributing

См. `.claude/rules/git-workflow.md` для commit format и branch strategy.

Workflow:
1. Создать feature branch от `develop`
2. `/feature <name>` или `/plan <name>` для structured implementation
3. Commit per logical unit (semantic format)
4. PR → develop (≥1 review) → main (≥2 review)
5. Auto-deploy via GitHub Actions

## License

Proprietary. Все rights reserved.

## Contacts

См. `docs/Completion.md` Section "Handoff Checklists" для team contacts.

---

🚀 **Ready for development:** `/start` → `/run mvp`
