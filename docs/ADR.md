# Architecture Decision Records: Apollo (RU)

> Append-only log of significant architecture decisions.

## ADR-001: Distributed Monolith over Microservices for MVP

**Status:** Accepted
**Date:** 2026-05-06

**Context:** Команда 4-6 человек, MVP за 4-5 месяцев. Нужно выбрать архитектуру.

**Decision:** Distributed Monolith — несколько контейнеров (api, worker, etl, frontend) в одном репозитории + Docker Compose, общая БД, общий код-database.

**Consequences:**
- ✅ Минимум координации между разработчиками
- ✅ Одна миграция БД, нет distributed transactions
- ✅ Простота операций — один deploy, единая observability stack
- ❌ При росте >10 сервисов потребуется миграция на оркестратор
- ❌ Нельзя независимо scale отдельные компоненты до P2

**Alternatives considered:**
- Monolith one container — невозможно из-за worker pattern
- Микросервисы — overkill для MVP, замедлит team velocity
- Serverless (FaaS) — vendor lock, сложнее с long-running campaigns

---

## ADR-002: PostgreSQL 16 with pg_trgm + pg_vector as Primary Database

**Status:** Accepted
**Date:** 2026-05-06

**Context:** Нужна БД для structured data (companies, contacts, billing, audit), полнотекстового поиска (по name), и vector similarity (для look-alike в P2).

**Decision:** PostgreSQL 16 + pg_trgm extension (fuzzy name search) + pg_vector extension (embeddings до 500K rows).

**Consequences:**
- ✅ Один движок для OLTP + search + vector — упрощение ops
- ✅ ACID для billing/quota операций
- ✅ pg_vector достаточен до 500K rows (test показывает <100ms ANN на 1M vectors)
- ❌ Vertical scaling limit — при >2M rows для search нужен ES
- ❌ pg_trgm дороже full FTS engine для multi-language (но для RU достаточно)

**Migration plan to ES:** триггер при 500K rows; ES syncs from PG via Debezium CDC.

---

## ADR-003: Celery + Redis for Task Queue

**Status:** Accepted
**Date:** 2026-05-06

**Context:** Нужен async task processor для long-running операций: outreach campaigns, ICP analysis, ETL.

**Decision:** Celery 5 + Redis as broker + result backend.

**Consequences:**
- ✅ Familiar в РФ Python community, много обучающих материалов
- ✅ Достаточная performance для MVP (target ~10K tasks/day)
- ✅ Поддержка cron (Celery Beat), retry, routing по queues
- ❌ Older codebase, occasionally weird quirks
- ❌ Single Redis = single point of failure (P2: Redis Sentinel)

**Alternatives:**
- RQ — slightly simpler, but missing scheduled tasks support
- Dramatiq — modern, но малое сообщество
- Temporal — overkill, complex для команды 4-6

---

## ADR-004: Next.js 14 (App Router) for Frontend

**Status:** Accepted
**Date:** 2026-05-06

**Context:** Нужен SSR для landing/SEO + SPA для авторизованного приложения.

**Decision:** Next.js 14 with App Router, TypeScript, Tailwind, shadcn/ui.

**Consequences:**
- ✅ SEO-ready landing — критично для content moat
- ✅ SSR/SSG/ISR — гибкость per-page
- ✅ Best DX в React ecosystem на 2026
- ❌ Lock-in to Next.js conventions (App Router still maturing)
- ❌ Vercel-style hosting лучше всего, но мы на VPS — нужен docker setup

---

## ADR-005: YandexGPT Primary, OpenAI Fallback for LLM

**Status:** Accepted
**Date:** 2026-05-06

**Context:** Нужен LLM для AI ICP analysis и personalize-сообщений в outreach.

**Decision:** YandexGPT — primary provider; OpenAI gpt-4o-mini — fallback при недоступности YG.

**Consequences:**
- ✅ Соответствие 152-ФЗ — данные не покидают РФ
- ✅ Дешевле для русскоязычных промптов
- ✅ Стабильнее billing (российский эквайринг)
- ✅ Fallback обеспечивает SLA при сбоях YG
- ❌ Quality YG ниже gpt-4-class (но достаточно для шаблонной персонализации)
- ❌ OpenAI billing through РФ-посредников — operational complexity

**Quality monitoring:** ежемесячный sampling 50 outputs, manual review.

---

## ADR-006: Telegram-First Outreach, Email Later

**Status:** Accepted
**Date:** 2026-05-06

**Context:** Phase 0 research показал, что в РФ B2B Telegram = de-facto канал; LinkedIn заблокирован; email перегружен.

**Decision:** MVP включает только Telegram outreach. Email в P1.

**Consequences:**
- ✅ Уникальное differentiation от Apollo.io / ZoomInfo
- ✅ Меньше регуляторных рисков (TG не требует opt-in так строго как email)
- ✅ Меньше effort на MVP — один канал
- ❌ Если гипотеза «TG = de-facto B2B канал» неверна — pivot потребует месяцы
- ❌ Telegram может ужесточить политику для bot massaging

**Mitigation:** customer interviews в Phase 2 для validation; готовый pivot на email в P1.

---

## ADR-007: Encrypted IndexedDB for User-Side API Keys

**Status:** Accepted
**Date:** 2026-05-06

**Context:** Если разрешим пользователю настраивать собственные LLM keys (для cost optimization) или Telegram bot tokens — где хранить?

**Decision:** Web Crypto API + AES-GCM 256-bit + PBKDF2 key derivation + IndexedDB. Никогда не отправляются на сервер.

**Consequences:**
- ✅ Zero-knowledge security — даже мы не имеем доступа к user-keys
- ✅ Соответствует security pattern из p-replicator constraints
- ❌ Невозможно использовать user-keys на serverside (worker tasks); только при клиентских запросах
- ❌ User теряет ключи при clear browser data (no backup)
- ⚠️ MVP scope: эта фича P1 — в MVP используются наши shared keys

---

## ADR-008: HOSTKEY VPS over Public Cloud (AWS/GCP/Yandex.Cloud)

**Status:** Accepted
**Date:** 2026-05-06

**Context:** Нужен hosting с RU jurisdiction (152-ФЗ), стабильным billing (no sanctions risk), предсказуемой ценой.

**Decision:** HOSTKEY VPS (Россия). Альтернатива — AdminVPS для non-prod.

**Consequences:**
- ✅ RU jurisdiction — compliance из коробки
- ✅ Предсказуемая цена (~₽3-15K/мес за VPS)
- ✅ SLA 99.9% (контракт)
- ✅ Нет sanctions risk
- ❌ Нет managed services (PG, Redis) — всё self-hosted в Docker
- ❌ Нет auto-scaling — manual VPS upgrade (с ~30 min downtime)
- ❌ Single-region (Москва) — DR требует contract second VPS

**Alternative considered:** Yandex.Cloud — managed PG/Redis есть, но дороже и vendor lock.

---

## ADR-009: Hybrid Data Acquisition (Open + Parsing + СПАРК in P2)

**Status:** Accepted
**Date:** 2026-05-06

**Context:** Нужен dataset 25K+ компаний для MVP, 500K+ для P2. СПАРК API ~₽1-3M/год — слишком дорого для MVP.

**Decision:**
- MVP: ЕГРЮЛ open data (бесплатно, weekly bulk) + парсинг top источников + seed dataset (25 компаний)
- P2 (Y1 Q3): добавить СПАРК basic API contract
- P3: full СПАРК + Контур.Фокус (если bandwidth позволит)

**Consequences:**
- ✅ Cost control в MVP (~₽0 за data)
- ✅ Постепенное масштабирование data quality
- ❌ В MVP полнота данных хуже, чем у Контура — нужно communicate honestly
- ❌ Парсинг — серая зона, юр-аудит обязателен

---

## ADR-010: ЮKassa for Payments

**Status:** Accepted
**Date:** 2026-05-06

**Context:** Нужен RU payment provider с поддержкой recurrent payments.

**Decision:** ЮKassa — primary. CloudPayments — backup на случай sanctions on Yandex.

**Consequences:**
- ✅ Лучший UX для российских пользователей
- ✅ Recurrent payments support
- ✅ Webhook-based intergration (стандарт)
- ❌ Commission 3-4% — выше чем Stripe (1-2%), но Stripe недоступен
- ❌ Sanctions risk на Yandex (low probability)

---

## ADR-011: Distributed Monolith Service Boundaries

**Status:** Accepted
**Date:** 2026-05-06

**Context:** Как разделить код на сервисы внутри monorepo, чтобы потом легко выделить в микросервисы?

**Decision:** Bounded contexts:
1. `auth/` — users, sessions, JWT
2. `companies/` — search, cards
3. `reveals/` — quota deduction, audit
4. `icp/` — analysis, look-alike
5. `campaigns/` — outreach orchestration
6. `billing/` — subscriptions, ЮKassa
7. `etl/` — data ingestion (separate container)
8. `worker/` — async tasks (separate container)

**Consequences:**
- ✅ Чёткие границы для будущего split
- ✅ Тесты пишутся per-context
- ❌ Расходы на data passing между контекстами (но через DB, не RPC)

---

## ADR-012: Forward-Compatible Database Migrations

**Status:** Accepted
**Date:** 2026-05-06

**Context:** Rolling deploy требует, чтобы новые миграции работали со старым кодом (and vice versa).

**Decision:** Все миграции должны быть FORWARD-COMPATIBLE:
- Adding column → NULLABLE или с DEFAULT
- Removing column → 2-phase (deploy code, потом drop column)
- Renaming → 3-phase (add new + dual-write + drop old)
- Adding index → CONCURRENTLY на больших таблицах

**Consequences:**
- ✅ Zero-downtime deploy
- ✅ Безопасный rollback (downgrade миграции работает с любой версией кода)
- ❌ Больше итераций для breaking changes (3 PR вместо 1)

---

## ADR-013: Audit Log Partitioned by Month, 3-Year Retention

**Status:** Accepted
**Date:** 2026-05-06

**Context:** 152-ФЗ требует audit trail; финразведка требует 3 года для billing-related операций.

**Decision:** `audit_log` table partitioned by month (PARTITION BY RANGE(created_at)). После 6 месяцев — archive partition в MinIO. После 3 лет — delete.

**Consequences:**
- ✅ Performance — queries только в текущую партицию
- ✅ Compliance — retention 3 года
- ✅ DR friendly — старые партиции можно бэкапить отдельно
- ❌ Дополнительная сложность ops (auto-create partitions через cron)

---

## ADR-014: 30-Day Per-Recipient Outreach Cooldown

**Status:** Accepted
**Date:** 2026-05-06

**Context:** Telegram bot blocking riskи + спам-этика в B2B.

**Decision:** Один контакт не может получить более 1 сообщения / 30 дней через Apollo (across все campaigns одного user).

**Consequences:**
- ✅ Снижает риск Telegram bot block
- ✅ Защищает receiver от spam
- ✅ Качество > количество подход
- ❌ Снижает theoretical max throughput
- ❌ Может расстроить sales-команды, которые хотят drip campaigns

**Future:** В Pro+ может появиться 7-day cooldown с явным согласием receiver (opt-in).

---

## ADR-015: AUTO Mode for SPARC Documentation Generation (this project)

**Status:** Accepted
**Date:** 2026-05-06

**Context:** Phase 1 sparc-prd-mini — выбор между AUTO и MANUAL.

**Decision:** AUTO режим для текущего проекта. Reasons:
- Pre-filled context из Phase 0 (product-discovery-brief.md) высокого качества
- Constraints явные (Distributed Monolith, Docker, VPS, MCP)
- Скорость важнее checkpoint per-phase для educational пайплайна

**Consequences:**
- ✅ Все 11 docs созданы за один проход
- ✅ Можно итерировать на validation (Phase 2) перед toolkit
- ❌ Меньше контроля от пользователя на каждой Phase

---

## Pending / In Progress

- ADR-016: Search engine choice (PG FTS vs Elasticsearch threshold) — TBD при первых 100K rows
- ADR-017: Multi-tenancy strategy (RLS vs schemas) — TBD при первой Team plan
- ADR-018: API versioning strategy (URL vs header) — TBD при public API release
- ADR-019: i18n approach (next-intl vs message catalogs) — TBD когда дойдём до English UI
