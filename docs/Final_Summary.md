# Final Summary: Apollo (RU)

> Executive summary of the SPARC documentation package.
> Sprint-ready после Phase 2 (Validation) и Phase 3 (Toolkit Generation).

## Overview

**Apollo (RU)** — российский B2B Sales Intelligence платформа. Аналог Apollo.io / ZoomInfo, локализованный под РФ-рынок: поиск компаний по ЕГРЮЛ/ОКВЭД/региону + раскрытие контактов ЛПР + Telegram-first outreach с AI-персонализацией + AI ICP look-alike. Цель — заменить ручной 2-3-часовой ресёрч и фрагментированные tools (СПАРК + парсинг + ручной TG/email) единой self-serve платформой по цене ₽3-30K/мес.

## Problem & Solution

**Problem:** Российские B2B-сейлзы тратят 30-40% рабочего времени на ручной поиск контактов. Apollo.io / ZoomInfo не работают в РФ. СПАРК / Контур — только данные без outreach. LinkedIn заблокирован, Telegram стал de-facto B2B-каналом. Нет единой платформы.

**Solution:** Apollo (RU) объединяет: (1) данные из ЕГРЮЛ + парсинг + СПАРК API (P2); (2) контакты ЛПР с указанием Telegram username; (3) Telegram outreach с LLM-персонализацией; (4) AI ICP анализ (look-alike по customer base); (5) self-serve SaaS pricing 3-5x дешевле Контура. Соответствие 152-ФЗ из коробки.

## Target Users

- **Primary (P0):** B2B Sales (SDR/AE) — 150-300K человек в РФ, ARPU target ₽10K/мес
- **Secondary (P1):** B2B Marketers — 30-80K человек, ARPU ₽30K/мес (Team plan)
- **Tertiary (P2):** M&A Analysts — 5-10K человек, Enterprise

## Key Features (MVP)

1. **Company Search & Filters** — ОКВЭД / регион / employees / revenue + ИНН search, < 500ms p99
2. **Contact Reveal** — credit-based раскрытие email/phone/telegram ЛПР с atomic quota deduction
3. **CSV Export** — выборка → CSV (UTF-8 BOM, до 10K строк на Pro)
4. **Telegram Outreach** — кампания → шаблон → 30-day per-recipient cooldown → throttle 5/sec → AI personalize (Pro+)
5. **AI ICP Analyzer** — upload CSV ИНН → distributions + LLM summary → look-alike top-100
6. **Billing** — ЮKassa subscription (Free/Starter ₽2.9K/Pro ₽9.9K/Team ₽29.9K/Enterprise)
7. **Audit & Compliance** — 152-ФЗ-ready: opt-out flow, audit log 3 года, реестр операторов ПДн

## Technical Approach

- **Architecture:** Distributed Monolith (Monorepo), Docker Compose, HOSTKEY VPS Russia
- **Stack:** Next.js 14 + FastAPI 0.115 + PostgreSQL 16 (pg_trgm + pg_vector) + Redis 7 + Celery + MinIO
- **LLM:** YandexGPT (primary, RU compliance) + OpenAI gpt-4o-mini (fallback)
- **Payments:** ЮKassa (recurrent) + CloudPayments (backup)
- **Outreach:** Telegram Bot API (5 msg/sec throttle, 30-day cooldown)
- **Security:** TLS 1.3, bcrypt(12), JWT rotation, encrypted IndexedDB (AES-GCM 256) для user-side API keys
- **Observability:** Prometheus + Grafana + Loki + Alertmanager → Telegram alerts
- **CI/CD:** GitHub Actions → ghcr.io → SSH deploy на VPS, alembic migrations, rollback на failed health-check

## Key Differentiators

1. 🎯 **Telegram-first outreach** — единственный игрок с native TG в категории
2. 🎯 **AI ICP look-alike** — на российских данных
3. 🎯 **Self-serve pricing 3-5x ниже** Контура при сопоставимой полноте по top-сегментам
4. 🎯 **152-ФЗ-first design** — opt-out, audit, реестр

## Research Highlights

- **Window of opportunity** ~12-18 месяцев до прихода Контура с собственным outreach
- **Telegram = de-facto B2B канал** в РФ после ухода LinkedIn (требует validation в Phase 2 customer interviews)
- **Hybrid data** approach снижает MVP cost: ЕГРЮЛ open (free) + парсинг + СПАРК API в P2
- **YandexGPT** дешевле OpenAI для русскоязычных промптов (~50% savings) и лучше с compliance
- **30-day per-recipient cooldown** обязателен для снижения TG bot blocking risk

## Success Metrics (Y1 targets)

| Metric | Target Q4 Y1 | How measured |
|--------|--------------|--------------|
| Paying customers | 300 | ЮKassa |
| ARR | ₽25M | sum(active subs) |
| Activation (Free → 1st reveal) | ≥ 40% | event tracking |
| Free → Paid conversion | ≥ 8% | cohort analysis |
| Monthly churn | ≤ 7% | YK data |
| NPS | ≥ 40 | quarterly survey |
| Reveal accuracy | ≥ 85% | manual sampling |

## Timeline & Phases

| Phase | Features | Timeline | Customers target |
|-------|----------|----------|------------------|
| **MVP (Sprint 1-5)** | Search, reveal, CSV export, billing, TG outreach, AI ICP | 4-5 мес | 50 free + 10-20 paying (early-bird ₽4.9K) |
| **GTM (Month 6-9)** | Email outreach, amoCRM/Bitrix24 export, dataset 100K | 4 мес | 100 paying, ARR ₽12M |
| **Scale (Month 10-12)** | СПАРК full API, Team plans, public API, partnerships | 3 мес | 300 paying, ARR ₽25M |

## Top 5 Risks & Mitigations

| # | Risk | P×I | Mitigation |
|---|------|-----|------------|
| 1 | 152-ФЗ ужесточит outreach | M×H | Юр-аудит до запуска, opt-in flow, готовый pivot на enrichment-only |
| 2 | TG заблокирует bot за массовую рассылку | H×H | 30-day cooldown, opt-in, multi-bot pool, fallback email |
| 3 | Контур запустит analog | M×H | Speed (MVP 5 мес), AI ICP moat, lock-in через привычку |
| 4 | Data acquisition дорого | H×M | Hybrid (open + парсинг + СПАРК поэтапно) |
| 5 | Не наберём PMF за 6 мес | M×H | Customer interviews ДО запуска, pivot к enrichment-only |

## Immediate Next Steps

1. ✅ **Phase 2: Validation** — запустить swarm of validators (INVEST/SMART/coherence) на этой документации
2. ✅ **Phase 3: Toolkit Generation** — сгенерировать .claude/commands, agents, rules для проекта (`/start`, `/run`, `/feature`, `/next`, `/go`, `/plan`, `/docs`, `/myinsights`)
3. 🔜 **Phase 4: Finalize** — `docker-compose.yml`, `Dockerfile`, `.gitignore`, `CLAUDE.md`, init commit
4. 🔜 **Customer Interviews (5-10)** — validate Telegram = de-facto channel hypothesis
5. 🔜 **Юр-консультация** — 152-ФЗ для outreach + opt-out
6. 🔜 **Hire team** — 1 PM, 2 BE, 2 FE, 1 ML/Data (или 1 senior fullstack)
7. 🔜 **Pre-seed fundraising** — ~₽15-20M для команды + 4-5 месяцев runway

## Documentation Package

| File | Purpose | Lines |
|------|---------|-------|
| **PRD.md** | Product Requirements (vision, personas, user stories, MVP matrix) | ~250 |
| **Solution_Strategy.md** | Problem analysis (SCQA, First Principles, 5 Whys, TRIZ, Game Theory) | ~200 |
| **Specification.md** | Detailed requirements + Gherkin AC + NFR | ~500 |
| **Pseudocode.md** | Algorithms, API contracts, state machines, error handling | ~450 |
| **Architecture.md** | C4 + Tech stack + Data model + Security + Deployment | ~600 |
| **Refinement.md** | Edge cases, testing strategy, optimizations, security hardening | ~500 |
| **Completion.md** | Deployment, CI/CD, monitoring, runbooks, handoff checklists | ~600 |
| **Research_Findings.md** | Market analysis, competitor matrix, technology assessment | ~400 |
| **C4_Diagrams.md** | System Context + Container + Component diagrams + sequences | ~300 |
| **ADR.md** | 15 architecture decisions with rationale | ~400 |
| **Final_Summary.md** | This document — executive summary | ~150 |
| **product-discovery-brief.md** | Phase 0 input | ~310 |

**Total:** ~12 documents, ~4500 lines of architecture/product documentation.

## Confidence

- 🟢 **HIGH:** Architecture, technology choices, security pattern (8/10)
- 🟡 **MEDIUM:** Market sizing, competitor pricing, technology integration (6/10)
- 🔴 **LOW:** Customer behavior assumptions, willingness-to-pay, exact unit economics (4/10) — все требует Phase 2 validation через customer interviews + competitive deep-dive

## Definition of Ready (для Phase 2 Validation)

- [x] Все 11 SPARC документов созданы
- [x] User Stories в Gherkin формате
- [x] Edge cases identified
- [x] Architecture diagrams (Mermaid)
- [x] Tech stack chosen with rationale (ADRs)
- [x] Risks identified with mitigations
- [x] NFR specified (performance, security, scalability, compliance)
- [x] Deployment plan
- [x] Test strategy
- [ ] **Pending:** Phase 2 swarm validation (INVEST score ≥70, SMART, coherence)

🚀 **READY FOR PHASE 2: VALIDATION**
