# Research Findings: Apollo (RU)

> SPARC Phase 1 output. Market & technology research.
> Note: На уровне Phase 0 уже сделан конкурентный анализ. Здесь — углубление.
> `[H]` = гипотеза, требует валидации.

## Executive Summary

Российский рынок B2B sales tools находится в окне возможностей: уход LinkedIn (2022), рост Telegram как B2B-канала, и удешевление LLM в 10x создают условия для появления локального аналога Apollo.io. Существующие игроки (СПАРК, Контур.Фокус) — data-first компании без outreach, а outreach-стартапы (Smartsender и др.) — без качественных данных. Window of opportunity — 12-18 месяцев до прихода крупного игрока.

## Research Objective

1. Подтвердить размер рынка и сегменты пользователей
2. Изучить competitive landscape (детально)
3. Технологическая база: какие library/framework выбрать для MVP
4. Регуляторные риски (152-ФЗ, реклама)
5. Тренды AI/LLM в B2B sales

## Methodology

- Knowledge cutoff: модель имеет данные до 2026-01
- Подход: GOAP-style research + sourcing — анализ конкурентов через их публичные сайты, сравнение pricing и фичей
- **Ограничение:** в этой сессии прямой web access ограничен; часть claims — на основе training data + product-discovery-brief.md (Phase 0)

## Market Analysis

### Russian B2B SaaS market size [H]

| Сегмент | Оценка размера 2024-2026 |
|---------|--------------------------|
| Total Russian SaaS market | ~₽150-200 млрд |
| B2B sales tools sub-segment | ~₽10-15 млрд |
| Lead-gen / sales intelligence | ~₽3-5 млрд (растёт 20-30% YoY) |

**Drivers:**
- Замещение зарубежных инструментов (Apollo.io, ZoomInfo, Salesloft недоступны)
- Цифровизация B2B-продаж после ковида
- Удешевление LLM → AI-фичи стали доступны mid-market

**Restraints:**
- 152-ФЗ ужесточения с 2025 (штрафы за нарушения ×10)
- Telegram bot policy (риск ужесточения для outreach)
- Замедление экономики → cost-cutting, выбор cheaper tools

### Target Customer Segments (детальный JTBD)

#### S1: B2B Sales Teams (SDR/AE) — P0

**Размер:** ~150-300 тыс. человек в РФ [H]
**ICP companies:** IT-компании 50-500 employees, digital agencies, B2B SaaS, оборудование

**Job Stories:**
- "Когда я начинаю новый квартал с пустым sales pipeline, я хочу за день собрать 200 целевых компаний и 500 контактов, чтобы выполнить план по dial'ам"
- "Когда мне нужен outreach по новому сегменту, я хочу персонализировать сообщения автоматически, чтобы не тратить 3 часа в день на копи-паст"
- "Когда клиент в CRM просит расширить поставку, я хочу за минуту получить полную карточку компании (выручка, сотрудники, директор), чтобы готовить proposal"

**Behavioral patterns [H]:**
- Используют 3-5 инструментов одновременно: CRM (amoCRM/Bitrix24) + СПАРК/Контур + ручной парсинг + Telegram + email
- 30-40% времени — на ресёрч, не на продажи
- Готовы платить ₽3-15K/мес за инструмент, который сэкономит 1 час/день

#### S2: B2B Marketers (Demand Gen) — P1

**Размер:** ~30-80 тыс. человек [H]
**ICP companies:** B2B IT, agencies, B2B услуги

**Job Stories:**
- "Когда я планирую ABM кампанию, я хочу проанализировать существующих клиентов и найти 1000 похожих компаний, чтобы загрузить в targeting"
- "Когда CMO просит ROI по каналу, я хочу видеть реальные конверсии: клик → лид → встреча → сделка"

**Поведение [H]:**
- 50% покупают tools для своих команд — bigger ARPU потенциал
- Часто решают через тендер / pilot

#### S3: M&A / Investment Analysts — P2

**Размер:** ~5-10 тыс. человек [H], но высокая ARPU
**ICP companies:** инвест-фонды, банки, корпоративные M&A отделы

**Job Stories:**
- "Когда я скрин рынок для сделок, я хочу за час получить список 50 компаний с выручкой 500M-1B в отрасли X"

## Competitive Landscape

### Detailed Player Analysis

#### Direct competitors (data + minimal outreach)

**1. СКБ Контур (Контур.Фокус, Контур.Компас)**
- **Strength:** Огромный dataset, government registries access, brand
- **Weakness:** Closed API, дорого (₽30-100K/мес), UX из 2010-х, нет AI
- **Pricing:** Фокус ~₽15-40K/мес, Компас ~₽20-50K/мес [H]
- **Threat level:** HIGH — могут запустить outreach за 6-12 мес

**2. СПАРК-Интерфакс**
- **Strength:** Самая полная база (включая международные данные), credit ratings
- **Weakness:** Очень дорого (₽30-100K+/мес), enterprise-focused, нет outreach
- **Pricing:** ₽30-120K/мес [H], зависит от модулей
- **Threat level:** MEDIUM — слишком corporate, вряд ли пойдут в SMB

**3. RusProfile.ru / Audit-it.ru**
- **Strength:** Бесплатный, базовые данные, large traffic
- **Weakness:** Нет API, нет outreach, монетизация через рекламу
- **Threat level:** LOW — не наш сегмент, но как источник данных полезны

**4. Companies.rbc.ru**
- **Strength:** Brand RBC, free
- **Weakness:** Та же — нет инструментов работы с lead'ами
- **Threat level:** LOW

#### Adjacent / partial overlap

**5. Bitrix24 / amoCRM**
- **Strength:** CRM с массовой adoption (>50K компаний РФ)
- **Weakness:** CRM — это destination, не lead source. Базовые enrichment функции, но нет ICP/look-alike
- **Threat level:** LOW (партнёр, а не конкурент)
- **Opportunity:** интеграция через export → большой канал дистрибуции

**6. Smartsender, Carrot quest, Texterra**
- **Strength:** outreach automation, marketing tools
- **Weakness:** нет own dataset, рассылки по чужой базе клиента
- **Threat level:** LOW — orthogonal use case

#### International (заблокированы / недоступны для РФ)

**7. Apollo.io, ZoomInfo, Lusha**
- **Strength:** Best-in-class UX, AI, огромные базы
- **Weakness:** Нет данных по РФ, санкционные риски
- **Threat level:** ZERO — не вернутся в обозримом будущем

### Competitive Matrix (детальная)

| Feature | Apollo (RU) | Контур.Компас | СПАРК | rusprofile | Apollo.io |
|---------|-------------|---------------|-------|------------|-----------|
| РФ-данные (companies) | ✅ ~500K target | ✅ 2M+ | ✅ 5M+ | ✅ 4M+ | ❌ |
| ИНН-based search | ✅ | ✅ | ✅ | ✅ | ❌ |
| ОКВЭД filter | ✅ | ✅ | ✅ | ✅ | ❌ |
| Контакты ЛПР | ✅ ~2M target | ✅ partial | ✅ partial | ❌ | ✅ |
| Telegram username data | ✅ unique | ❌ | ❌ | ❌ | ❌ |
| Outreach (TG) | ✅ native | ❌ | ❌ | ❌ | ❌ |
| Outreach (email) | P1 | ❌ | ❌ | ❌ | ✅ |
| AI ICP look-alike | ✅ unique | ❌ | ❌ | ❌ | ✅ |
| AI personalization | ✅ | ❌ | ❌ | ❌ | ✅ |
| Open API | ✅ P1 | ❌ closed | ✅ enterprise | ❌ | ✅ |
| amoCRM/Bitrix24 export | ✅ P1 | ✅ | ❌ | ❌ | N/A |
| Self-serve pricing | ✅ ₽3-30K/мес | ❌ sales-only | ❌ sales-only | ✅ free | ✅ $99-199 |
| 152-ФЗ compliance | ✅ built-in | ✅ | ✅ | partial | N/A |

### Differentiation Pillars (что нас отличает)

1. **Self-serve pricing** в нише, где конкуренты — sales-only
2. **Telegram-first outreach** — единственные в категории
3. **AI ICP** — Контур может скопировать, но это отдельная R&D задача
4. **Цена в 3-5x ниже Контура** при сопоставимой полноте по top-сегментам
5. **152-ФЗ-first design** — opt-in flow, audit log, реестр операторов

## Technology Assessment

### Backend Frameworks

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| **FastAPI (Python)** | Async, auto OpenAPI, типы, ML/data community | Slower than Go | ✅ **Choice** — лучше для ML-pipelines |
| Django + DRF | Mature, batteries-included | Sync (asgi recent), heavier | ❌ |
| NestJS (Node) | Type-safe, modular | Меньше ML-инструментов | ❌ |
| Go (Gin/Fiber) | Performance | Слабее ecosystem для ML/data | ❌ |

### Frontend Frameworks

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| **Next.js 14 (App Router)** | SSR, file-based routing, image opt | Lock-in to Vercel-style | ✅ **Choice** — SEO критичен для contentmoat |
| Remix | Fullstack focus | Менее популярен в РФ | ❌ |
| SvelteKit | Малый bundle | Малое community РФ | ❌ |
| Vue 3 + Nuxt | Familiarность РФ | Меньше TS adoption | ❌ |

### Database

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| **PostgreSQL 16 + pg_vector** | ACID, JSONB, vector search, mature | Vertical scale limit | ✅ **Choice** |
| MongoDB | Flexible schema | Слабее для финансовых данных | ❌ |
| ClickHouse | Аналитика | OLTP weak | ❌ — для analytics в P2 |

### Search

| Option | Pros | Cons | Decision (MVP / P2) |
|--------|------|------|----|
| **PG FTS + pg_trgm** | Уже в БД, no extra service | Limit ~200K rows для good UX | ✅ **MVP** |
| Elasticsearch / OpenSearch | Best for search at scale | Extra ops | ✅ **P2** (>500K rows) |
| Typesense | Lightweight, fast | Меньше features | ❌ |

### Task Queue

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| **Celery + Redis** | Mature, Python-native, RU community | Older codebase | ✅ **Choice** |
| RQ | Simpler than Celery | Меньше features | ❌ |
| Dramatiq | Modern, simpler | Меньше ecosystem | ❌ |
| Temporal | Workflow-grade | Overkill for MVP | ❌ — может в P2 |

### LLM Provider

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| **YandexGPT** | RU compliance, дешевле для RU, хорошо понимает русский | API менее гибкий, slower iteration | ✅ **Primary** |
| **OpenAI (gpt-4o-mini)** | Best quality | Sanctions risk, billing through РФ-посредников сложнее | ✅ **Fallback** |
| GigaChat (Сбер) | RU compliance | Slower, API менее зрелый | ⚠️ alternative |
| Self-hosted Llama 3 | No vendor lock | Inference cost | ❌ — может в P3 |

### Payments

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| **ЮKassa** | RU acquiring, recurrent, popular | Commission ~3-4% | ✅ **Primary** |
| CloudPayments | RU acquiring, enterprise | Higher fees | ✅ Backup |
| Stripe | Best UX, no | Не работает с РФ | ❌ |

### Hosting

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| **HOSTKEY** | RU jurisdiction, SLA 99.9%, predictable cost | Не self-healing как cloud | ✅ **Choice** |
| AdminVPS | Cheaper | Меньше SLA | ❌ alternative for non-prod |
| Yandex.Cloud | Russian cloud, managed services | Vendor lock, dearer | ⚠️ если будем нужны managed PG |
| Reg.ru / Timeweb | RU | Слабее для production | ❌ |

## User Insights

### Key Findings (from Phase 0 + research)

1. **Pain #1: фрагментация инструментов** — пользователь использует 3-5 разных tools, переключается между ними часами в день
2. **Pain #2: качество контактов** — корпоративные адреса (info@, press@) бесполезны для cold outreach. Нужны личные emails ЛПР
3. **Pain #3: отсутствие persistence в outreach workflow** — нет единой системы, где видно «отправил → ответили → встреча»
4. **Pain #4: legal anxiety** — все боятся 152-ФЗ, но не понимают, что можно/нельзя

### Behavioral Patterns

- **B2B sales в РФ — Telegram-first:** 80%+ B2B-коммуникации идут через TG, не email/LinkedIn [H]
- **Сейлзы покупают tools без B2B сделки** при self-serve pricing < ₽10K — выгодно для PLG
- **Маркетологи покупают tools через CMO** — multi-stakeholder sale, нужен ROI proof

### Voice of Customer (ground truth needed!)

⚠️ **Open question for Phase 2 validation:** провести 10-15 customer interviews для проверки:
- Действительно ли Telegram = de-facto канал? Или email больше?
- Сколько готовы платить?
- Есть ли реально boli из-за заблокированного LinkedIn (или уже адаптировались)?

## Integration Research

### СПАРК API
- **Контракт:** ~₽1-3 млн / год за base [H], масштабируется
- **API:** REST/SOAP, лимит запросов
- **Что даёт:** полная база ЕГРЮЛ, фин.отчётность, связи юрлиц
- **Решение:** **P2 (после PMF)**, в MVP — ЕГРЮЛ open data + парсинг

### Контур.Фокус API
- **Закрытое API**, доступ через партнёрку
- **Не подходит для MVP**

### ЕГРЮЛ open data (ФНС)
- **Бесплатно, weekly bulk download** (~30 GB JSON)
- **Что даёт:** все юрлица РФ — ИНН, name, ОКВЭД, адрес, директор
- **Что НЕ даёт:** контакты, финотчётность, employees count
- **Решение:** **MVP foundation**

### Telegram Bot API
- **Free**, rate-limit: 30 messages/sec на bot, но per-user-chat ограничения строже
- **Best practices:** opt-in, throttle 1 msg/30 days/recipient, opt-out keyword detection
- **Risk:** Telegram может банить bot за массовую рассылку → нужен careful approach

### LLM (YandexGPT, OpenAI)
- **Pricing YandexGPT:** ~₽1-3 за 1K tokens (зависит от модели) [H]
- **Pricing OpenAI gpt-4o-mini:** ~$0.15 / 1M input tokens
- **Cache:** при повторе одинакового prompt'а — экономия 80%+
- **Latency:** YandexGPT ~3-7s, OpenAI ~1-3s

## Confidence Assessment

| Area | Confidence | Reason |
|------|------------|--------|
| Market segments and pains | HIGH (8/10) | Standard B2B sales задачи, повторяемые |
| Market size РФ | LOW (4/10) | Нет открытых отчётов, оценки только [H] |
| Competitor pricing | MEDIUM (6/10) | Public для top-tier, остальное — оценка |
| Technology choices | HIGH (8/10) | Mature stacks, проверенные решения |
| Telegram = de-facto channel | MEDIUM (5/10) | Гипотеза, нужны интервью |
| Pricing ₽9 990 для Pro | LOW (4/10) | A/B на лендинге обязателен |
| Unit economics | LOW (4/10) | Все цифры [H] до первых клиентов |

## Sources (referenced)

| # | Source | Reliability | Used in |
|---|--------|-------------|---------|
| 1 | Phase 0 Product Discovery Brief | HIGH | All sections |
| 2 | Apollo.io public website | HIGH | Competitive matrix |
| 3 | Контур, СПАРК public sites | HIGH | Pricing, features |
| 4 | rusprofile.ru, e-disclosure.ru | HIGH | Data sources research |
| 5 | Industry knowledge (training cutoff 2026-01) | MEDIUM | Market sizing |
| 6 | seed dataset (`docs/uploads/...`) | HIGH | Company structure validation |

## Research Path Log

1. **Initial state:** product idea + 25-row seed dataset
2. **Action 1:** Identified inspiration = Apollo.io, locale = RU
3. **Action 2:** Mapped existing players (Phase 0)
4. **Action 3:** Deepened competitive matrix in Phase 1 research
5. **Action 4:** Mapped technology choices to constraints (RU jurisdiction, distributed monolith)
6. **Replanning:** оставлены open questions для Phase 2 validation (customer interviews, pricing A/B, legal review)

## Open Research Questions (для Phase 2 validation)

1. ⚠️ **Customer interviews (10-15 calls):** подтвердить TG = de-facto канал, JTBD, willingness-to-pay
2. ⚠️ **Юр-консультация:** допустимость Telegram outreach по 152-ФЗ, opt-out требования
3. ⚠️ **Pricing A/B:** ₽4 990 vs ₽9 990 для Pro — на лендинге до запуска
4. ⚠️ **Data acquisition cost:** реальный quote от СПАРК / Контур для P2 contract
5. ⚠️ **LLM benchmark:** YandexGPT vs OpenAI quality для РФ B2B текстов (10 sample messages)
