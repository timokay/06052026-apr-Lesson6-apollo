# Solution Strategy: Apollo (RU)

> SPARC Phase 2 output. First Principles + 5 Whys + SCQA + TRIZ + Game Theory.

## SCQA Frame

- **Situation:** Российские B2B-сейлзы используют 3-5 разрозненных инструментов (СПАРК для данных, ручной парсинг для контактов, Telegram/email вручную для outreach).
- **Complication:** LinkedIn заблокирован, Apollo.io нет данных по РФ, СПАРК/Контур.Фокус — только данные без outreach. Сейлз тратит 30-40% времени на ресёрч вместо продаж.
- **Question:** Можно ли создать единую B2B Sales Intelligence платформу под российский рынок, объединяющую данные из открытых регистров + AI ICP + Telegram-first outreach, по цене SaaS-подписки?
- **Answer:** Да — Apollo (RU): данные из ЕГРЮЛ/ОКВЭД/e-disclosure + парсинг контактов с публичных источников + LLM-обогащение + Telegram Bot API outreach + AES-encrypted client-side credentials. Целевой ARPU ₽10K/мес, target 300 клиентов в Y1.

## First Principles Analysis

**Что фундаментально нужно B2B-сейлзу для cold outreach?**

1. **Список целевых компаний** (отрасль, размер, регион, выручка) — фундаментально это **фильтрация структурированных данных**. Источник: государственные регистры (ЕГРЮЛ — открытые данные, бесплатно).

2. **Контакт ЛПР** (email, телефон, telegram) — фундаментально это **идентификация конкретного человека** в компании. Источник: корпоративные сайты + LinkedIn (заблокирован) + Telegram username + публичные интервью/публикации.

3. **Способ доставить сообщение** — фундаментально это **канал коммуникации**. В РФ актуальны: Telegram (де-факто стандарт B2B), email, иногда WhatsApp, телефон.

4. **Релевантное сообщение** — фундаментально это **персонализация под контекст компании**. Решается LLM (генерация на основе профиля компании).

5. **Учёт реакций** — фундаментально это **трекинг событий** (отправлено, прочитано, ответили, отказались). Решается Telegram Bot API events + UI dashboard.

**Вывод:** Все 5 компонентов решаются типовыми технологиями. Барьеры — не технологические, а:
- Доступ к качественным данным (СПАРК — дорого, парсинг — медленно/нелегально)
- Compliance (152-ФЗ, opt-out)
- UX, который делает workflow в 5 раз быстрее ручного

## 5 Whys

1. **Why** российские сейлзы тратят 2-3 часа в день на ресёрч?
   → Нет единого инструмента. Используют 3-5 источников.

2. **Why** нет единого инструмента?
   → Apollo.io не работает с РФ; СПАРК — только данные; Контур — закрытое API.

3. **Why** русские игроки не сделали аналог?
   → СПАРК/Контур — corporate-data компании. Их KPI — точность данных, а не sales productivity. Outreach они считают «не своим» доменом.

4. **Why** стартапы не закрыли нишу?
   → Высокий порог входа (нужен dataset, юр-compliance, дистрибуция). Большинство пробуют делать только outreach (smartsender и пр.) или только данные (rusprofile).

5. **Why** именно сейчас момент? (root cause)
   → **Сошлись три фактора:** (1) LinkedIn заблокирован → освободилась ниша B2B-контактов; (2) Telegram стал де-факто B2B-каналом в РФ; (3) LLM удешевили персонализацию в 10x. Window of opportunity ~12-18 месяцев до прихода СКБ Контур или другого крупного игрока.

## Game Theory: Stakeholders & Equilibrium

| Player | Interest | Best Response |
|--------|----------|---------------|
| **Apollo (RU)** | Захватить долю до прихода Контура | Speed + Telegram-spec + AI moat |
| **Покупатели** (B2B sales) | Низкая цена + полные данные + интеграция в workflow | Выберут платформу с лучшим UX и единой ценой |
| **СПАРК / Контур** | Защитить existing revenue | Через 6-12 мес выпустят свой outreach или купят стартап |
| **Регулятор (РКН)** | Защитить ПДн | Будет давить на массовый outreach (риск!) |
| **Telegram** | Защитить user experience | Заблокирует bot'ов с >X сообщений/день |

**Nash equilibrium:**
- Apollo (RU) занимает Telegram-niche, строит AI ICP моат, играет на 152-ФЗ-compliance.
- Контур запустит свой outreach через 12 мес — но Apollo (RU) к этому моменту уже будет иметь 500-1000 paying customers и data flywheel.
- Стратегия выживания: лояльные customers + контент-моат + Cost-leadership на mid-tier (₽10K vs ₽30K у Контура).

## Second-Order Effects

**Положительные:**
1. Telegram-outreach стандартизация → Apollo (RU) станет «выбором по умолчанию» (lock-in через привычку)
2. Data flywheel: каждый upload CSV улучшает LLM ICP-модель для всех
3. Бренд «российский Apollo» легко запоминается — virality

**Отрицательные:**
1. Регулятор увидит крупного игрока в outreach → ужесточит правила (риск pivot на enrichment-only)
2. Конкуренты копируют фичи за 6-12 мес — критичен темп релизов
3. Telegram может ввести лимит на bot messaging → нужен fallback на email

**Нейтральные:**
1. Купят (M&A target для Контура/Сбер.Корп) — это не плохо для founders, но смещает focus

## TRIZ Contradictions Resolved

| Contradiction | TRIZ Principle | Resolution |
|---------------|----------------|------------|
| Нужны точные данные ↔ нельзя платить за СПАРК на старте | **Принцип 5 (Объединение)** + **Принцип 35 (Изменение свойств)** | Hybrid data: ЕГРЮЛ open data (бесплатно, базовая полнота) + парсинг top-100 источников + user-uploaded (для длинного хвоста) |
| Нужен outreach ↔ риски 152-ФЗ для массовой рассылки | **Принцип 25 (Самообслуживание)** + **Принцип 10 (Предварительное действие)** | Opt-in flow + audit log каждого reveal + только публичные каналы + явное согласие пользователя |
| Нужна AI-персонализация ↔ LLM API дорого на масштабе | **Принцип 24 (Посредник)** + **Принцип 31 (Пористые материалы)** | Кэширование промптов (схожие компании = один LLM-запрос на template); freemium = базовая персонализация (template), Pro = LLM |
| Нужна простота UI ↔ много фильтров и фич | **Принцип 1 (Дробление)** + **Принцип 17 (Переход в другое измерение)** | Базовые 4 фильтра по умолчанию + Advanced раскрывается по клику; «smart defaults» по типу пользователя |
| Нужны интеграции ↔ MVP должен запуститься быстро | **Принцип 27 (Дешёвая недолговечность)** + **Принцип 24 (Посредник)** | CSV import/export как универсальная интеграция в MVP; webhooks/API в P1; нативные интеграции (amoCRM/Bitrix24) после PMF |

## Recommended Approach

### Strategy: «Telegram-first B2B Sales OS»

**3 фазы развития:**

**Phase 1 (Months 1-5, MVP):**
- Core search + reveal + Telegram outreach + AI ICP
- Data: ЕГРЮЛ open data + парсинг top-25 источников (как seed dataset)
- 1 канал: Telegram. Email — позже.
- Beta: 50 free пользователей, 10 paying за ₽4 990 (early-bird)

**Phase 2 (Months 6-9, GTM):**
- Расширение dataset до 100K компаний (парсинг + СПАРК basic API)
- Email outreach
- amoCRM/Bitrix24 export
- Платный маркетинг: SEO + контент + Telegram-каналы B2B
- Target: 100 paying customers, ARR ₽12M

**Phase 3 (Months 10-12, scale):**
- 1M+ компаний (СПАРК full API contract)
- Team plans, SSO
- API для разработчиков
- Партнёрки: Bitrix24, amoCRM, Calltouch, Roistat
- Target: 300 paying, ARR ₽25M

### Differentiation Pillars

1. **Telegram-first** — единственный игрок с native Telegram outreach в РФ
2. **AI ICP look-alike** — никто не делает на российских данных
3. **152-ФЗ-compliance из коробки** — opt-out, audit, реестр операторов ПДн
4. **Цена в 3-5x ниже** Контур.Компас при сопоставимой полноте данных по top-сегментам

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| 152-ФЗ ограничит outreach | M (30%) | H | Юр-аудит до запуска, opt-in flow, audit log, готовый pivot на enrichment-only |
| TG заблокирует bot | H (50%) | H | Rate-limit (5 msg/contact/мес), opt-in, fallback на email в P1 |
| Контур запустит analog | M (40%) | H | Speed (MVP за 5 мес), AI ICP moat, lock-in через привычку |
| Data acquisition дорогой | H (60%) | M | Hybrid (open + парсинг + СПАРК), gradual scaling |
| Не наберём PMF за 6 мес | M (35%) | H | Customer interviews до запуска, pivot готовность к enrichment-only продукту |
| LLM цены вырастут | L (15%) | M | YandexGPT primary, кэширование, fallback на templates |

## Decision Matrix (key choices)

| Decision | Option A | Option B | Choice | Why |
|----------|----------|----------|--------|-----|
| LLM provider | OpenAI | YandexGPT | **YandexGPT primary, OpenAI fallback** | Compliance, дешевле для РФ, API стабильнее |
| Data primary | СПАРК API | Hybrid (open + парсинг) | **Hybrid в MVP, СПАРК в P2** | Cost-control, постепенное масштабирование |
| Outreach channel | Telegram | Email | **Telegram MVP, Email P1** | Telegram = de-facto B2B канал в РФ, email перегружен спамом |
| Frontend | React SPA | Next.js | **Next.js (App Router)** | SEO для контент-моата, SSR для авторизованных страниц |
| Backend | Python (FastAPI) | Node (NestJS) | **Python FastAPI** | ML/data pipelines, лучшая совместимость с pandas/scikit-learn |
| Database | PostgreSQL | MongoDB | **PostgreSQL** | Структурированные данные, JOIN'ы, типобезопасность |
| Search engine | Elasticsearch | PostgreSQL FTS | **PostgreSQL FTS в MVP, ES в P2** | YAGNI, MVP не требует ES |
| Hosting | AdminVPS | HOSTKEY | **HOSTKEY** | Лучшие SLA для production, российская юрисдикция |
