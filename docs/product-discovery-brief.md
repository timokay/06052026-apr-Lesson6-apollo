# Product Discovery Brief — Apollo (RU)

> Phase 0 output. QUICK mode. Reverse-engineering inspiration: **Apollo.io**.
> Geography: Россия. Source: knowledge base + seed dataset (25 РФ-компаний).
> `[H]` = гипотеза, требует валидации в Phase 1-2.

## 1. Project Identity

| | |
|---|---|
| **Codename** | Apollo (RU) |
| **One-liner** | Российский Apollo.io — B2B Sales Intelligence платформа: поиск компаний по ИНН/ОКВЭД/региону, контакты ЛПР, мульти-канальные кампании. |
| **Inspiration** | Apollo.io (US, ~$1.6B valuation 2023) [H] |
| **Geography** | Россия → СНГ (Phase 2) |
| **Status** | Pre-seed / MVP scoping |

---

## 2. Module M2 — Product & Customers

### 2.1 Segments (ICP)

| # | Segment | Описание | Размер РФ [H] | Priority |
|---|---------|----------|---------------|----------|
| **S1** | **B2B Sales (SDR/AE)** | Менеджеры и SDR-команды российских B2B-компаний (IT, услуги, оборудование). Делают cold outreach через email/звонки/Telegram. | ~150-300 тыс. человек | 🥇 P0 |
| **S2** | **B2B Marketers / Demand Gen** | Маркетологи, отвечающие за лидген: ICP-анализ, account-based marketing, сегментация рынка. | ~30-80 тыс. | 🥈 P1 |
| **S3** | **M&A / Investment Analysts** | Аналитики, скрейпящие рынок для сделок: поиск компаний по выручке/отрасли/географии. | ~5-10 тыс. | 🥉 P2 |

### 2.2 Voice of Customer (Pain Points)

> Источники [H]: типичные жалобы B2B-сейлзов в РФ, форумы Habr/vc.ru, обзоры альтернатив.

**S1 Sales:**
- «Захожу в СПАРК/Контур.Фокус — там карточка компании, но **нет почты ЛПР**. Гуглю Хабр-CV, LinkedIn заблокирован — собираю контакты по 3 часа в день вручную.»
- «Делаю outreach через Telegram, но нет инструмента для **массовой персонализации**. Пишу руками 100 сообщений в день.»
- «AmoCRM/Bitrix24 импортируют контакты, но **не обогащают** их — ИНН без выручки, без ЛПР.»

**S2 Marketers:**
- «Хочу построить ICP — выгрузить все строительные компании Урала с выручкой 100-500M, до 50 человек. **Нет такого фильтра** ни в одном русском сервисе.»
- «Конкуренты: ZoomInfo, Apollo, Lusha — США/ЕС, **нет данных по РФ**. Локальные (Контур.Компас) — дорого и закрыто.»

**S3 M&A:**
- «E-disclosure + СКБ + RBC — три источника, ручная сборка. Нужна **единая база с выручкой и отраслью**.»

### 2.3 JTBD (Jobs-to-be-Done)

**Главный JTBD:**
> _Когда я ищу новых клиентов в B2B, я хочу за 5 минут получить список компаний по точным фильтрам и контакты ЛПР, чтобы я мог потратить рабочий день на продажи, а не на ресёрч._

**Sub-jobs:**
1. **Search** — найти N компаний по фильтру (отрасль ОКВЭД, регион, выручка, employees, юр.форма)
2. **Reveal** — раскрыть контакт конкретного ЛПР (email, телефон, telegram)
3. **Enrich** — обогатить свой список (загрузил ИНН → получил выручку, ЛПР, ОКВЭД)
4. **Outreach** — отправить персонализированную кампанию через Telegram (MVP) / Email (Phase 2)
5. **ICP-analyze** — проанализировать существующую CRM-базу → найти похожих компаний (look-alike)

### 2.4 Value Proposition

```
For:   российских B2B-сейлзов и маркетологов
Who:   тратят >2 часов в день на ручной поиск контактов и обогащение базы
We:    Apollo (RU) — единая платформа поиска и outreach по российскому рынку
That:  даёт фильтрацию по 8+ параметрам, обогащает ИНН → ЛПР, и автоматизирует
       Telegram/email кампании с AI-персонализацией
Unlike: СПАРК (только данные, без outreach), Контур.Компас (закрытое API, дорого),
        Apollo.io (нет данных по РФ), ручной парсинг (медленно, нелегально)
We:    объединяем данные из открытых регистров + AI ICP + multi-channel outreach
       в одном продукте по цене SaaS-подписки
```

### 2.5 Aha Moment (Module 2.5 placeholder)

**Гипотеза Aha:** _«За 30 секунд: фильтр → 247 компаний → клик "Reveal" → 12 контактов ЛПР с email/telegram → клик "Generate campaign" → AI пишет 12 персонализированных сообщений → отправил.»_

В Phase 1 (sparc-prd-mini) сделаем 3 варианта Aha + lock одного через CJM прототип.

---

## 3. Module M3 — Market & Competition

### 3.1 Market Sizing (TAM/SAM/SOM)

| Уровень | Расчёт | Размер [H] |
|---------|--------|------------|
| **TAM** | Все B2B-компании РФ × средний бюджет на sales tools | ~₽15-25 млрд / год |
| **SAM** | Только активные B2B SaaS / digital компании (S1+S2 сегменты) | ~₽3-5 млрд / год |
| **SOM (Y1)** | 1% SAM в первый год | ~₽30-50 млн ARR target |
| **SOM (Y3)** | 5-10% SAM | ~₽150-500 млн ARR |

### 3.2 Competitive Matrix

| Игрок | Тип | Данные РФ | Outreach | AI ICP | Цена/мес | Сила |
|-------|-----|-----------|----------|--------|----------|------|
| **СПАРК** | Данные | ✅ Полные | ❌ | ❌ | ₽30-100K | Регистры, кредитные риски |
| **Контур.Фокус** | Данные | ✅ Полные | ❌ | ❌ | ₽15-40K | UX, простота |
| **Контур.Компас** | Lead-gen | ✅ ЛПР | ❌ | Слабо | ₽20-50K | Контакты ЛПР |
| **rusprofile.ru** | Free | ✅ Базовые | ❌ | ❌ | Бесплатно | Open data |
| **e-disclosure.ru** | Гос-сайт | ✅ Финансы публичных | ❌ | ❌ | Бесплатно | Финотчётность |
| **Apollo.io / ZoomInfo** | Lead-gen | ❌ | ✅ | ✅ | $99-199/seat | Лучший UX |
| **AmoCRM / Bitrix24** | CRM | ❌ | Слабо | ❌ | ₽500-2000/seat | Дистрибуция |
| **Telegram outreach (Smartsender и др.)** | Channel | ❌ | ✅ TG | ❌ | ₽5-30K | Telegram automation |

### 3.3 Blue Ocean Canvas

Снизить (vs. СПАРК/Контур):
- Сложность UX (СПАРК = «корпоративный монстр» из 90-х)
- Цена входа (Pro tier ₽5-15K/мес vs ₽30-100K)

Увеличить (vs. Apollo.io):
- Полнота данных по РФ (ИНН, ОКВЭД, ЕГРЮЛ, e-disclosure)
- Соответствие 152-ФЗ (только публичные / B2B-данные)

Создать (никто не делает):
- 🌊 **AI ICP look-alike**: загрузил CRM → ML находит похожих компаний
- 🌊 **Telegram-first outreach** (под РФ-реальность, где LinkedIn заблокирован)
- 🌊 **Open data integration**: фильтр по госконтрактам (zakupki.gov.ru), судебной нагрузке (kad.arbitr.ru)

Убрать:
- ❌ Ручной парсинг данных пользователем (всё в платформе)
- ❌ Платные API-интеграции по подписке (включено в seat)

### 3.4 Game Theory Snapshot [H]

**Угрозы:**
1. **Контур запускает свой outreach** — наиболее вероятная угроза (T+12 мес). Защита: AI-моат + лучший UX + Telegram-spec.
2. **Apollo выходит на РФ** — маловероятно из-за санкций.
3. **152-ФЗ ужесточение** — высокий риск. Митигация: только публичные данные + opt-out + audit log.

---

## 4. Module M4 — Business & Finance

### 4.1 Pricing (SaaS subscription)

| Tier | Цена/мес | Quota | Target |
|------|----------|-------|--------|
| **Free** | 0 | 25 reveals/мес, 1 user | Acquisition, виральность |
| **Starter** | ₽2 990 | 500 reveals, 1 seat, базовые фильтры | Соло-сейлзы, фрилансеры |
| **Pro** | ₽9 990 | 2 000 reveals, 3 seats, AI ICP, Telegram outreach (500/мес) | Малые B2B-команды |
| **Team** | ₽29 990 | 10 000 reveals, 10 seats, API, advanced filters, billing-roles | Sales-отделы 10-50 чел. |
| **Enterprise** | from ₽99 000 | Unlimited, SSO, SLA, on-premise СПАРК-интеграция | Корпорации |

### 4.2 Unit Economics (Pro tier, целевой) [H]

| Метрика | Значение | Комментарий |
|---------|----------|-------------|
| **ARPU** | ₽9 990 / мес | Pro tier базовый |
| **CAC** | ₽15-25K | Контент + платный SEO + outbound |
| **Payback period** | 2-3 мес | Хорошо для B2B SaaS |
| **Gross margin** | 75-85% | После затрат на data acquisition + LLM API |
| **Churn (monthly)** | 5-8% [H] | Для SMB B2B SaaS типично |
| **LTV** | ₽120-200K | (12-24 месяца × ARPU × margin) |
| **LTV/CAC** | 5-10x | Здоровый |

### 4.3 P&L Projection (Y1 baseline) [H]

```
Y1 customers: 300 paying (200 Starter + 80 Pro + 20 Team)
Y1 ARR: ~₽25M
COGS: ₽5M (data sources, infra, LLM API)
S&M: ₽12M (CAC + контент)
R&D: ₽15M (команда 5-7 человек)
G&A: ₽3M
Y1 burn: ~₽10M (нужны инвестиции pre-seed ~₽15-20M)
Break-even: Y2 Q3-Q4 при ARR ~₽60M [H]
```

### 4.4 Sensitivity

- **Если data acquisition стоит дороже** (СПАРК API дорог) → COGS +30%, перейти на open data парсинг
- **Если CAC выше ₽40K** → fokus на product-led growth, Free tier виральность через Telegram
- **Если 152-ФЗ ужесточится** → pivot на «обогащение CRM по ИНН» (без contact reveals)

---

## 5. Module M5 — Growth Engine

### 5.1 Acquisition Channels

| Канал | CAC [H] | Volume potential | Priority |
|-------|---------|------------------|----------|
| **SEO контент** (lead-gen, sales blog) | ₽5-15K | Высокий, медленно | 🥇 P0 |
| **Outbound через сам продукт** (Telegram outreach к B2B-сейлзам) | ₽3-8K | Средний, быстро | 🥇 P0 (dogfooding) |
| **Партнёрки** (CRM-интеграторы amoCRM/Bitrix24) | ₽10-20K | Средний | 🥈 P1 |
| **Telegram-каналы** (B2B-маркетинг, sales) | ₽15-30K | Средний | 🥈 P1 |
| **Конференции** (B2B Russia, Sales Up) | ₽30-80K | Низкий, brand | 🥉 P2 |
| **Платный поиск** (Яндекс.Директ) | ₽20-50K | Средний | 🥉 P2 |

### 5.2 Growth Loops

**Loop 1: Product-led (виральный):**
```
Free user отправляет Telegram сообщение → получатель видит «отправлено через Apollo» →
переходит → регистрируется → отправляет своим → ...
```
K-factor target: 0.3-0.5 [H]

**Loop 2: Data flywheel (моат):**
```
User uploads CRM (ИНН list) → платформа обогащает + узнаёт реальные ЛПР →
data improves для всех → лучше product → больше users
```

**Loop 3: Content SEO:**
```
Контент «Топ-100 B2B-компаний [отрасль]» → SEO трафик → freemium регистрация → Pro upgrade
```

### 5.3 Moats (защита от конкурентов)

1. **Data moat** — собственные пайплайны парсинга + open data + user contributions
2. **Network effect (тонкий)** — Telegram receivers видят Apollo brand
3. **AI ICP моат** — ML модель улучшается с каждой загруженной CRM
4. **Compliance moat** — выстроенный 152-ФЗ процесс (не каждый стартап потянет аудит ПДн)

### 5.4 2nd-Order Effects [H]

- **Положительный:** Telegram-spec → станет «выбором по умолчанию» у российских SDR (lock-in через привычку)
- **Отрицательный:** Гос-внимание к outreach → нужна предусмотрительность по согласиям (opt-in flow)
- **Нейтральный:** Конкуренты скопируют фичи за 6-12 мес — критична скорость и community

---

## 6. Constraints для Phase 1 (PRD)

```yaml
project_codename: apollo-ru
target_segments:
  primary: B2B Sales (SDR/AE)
  secondary: [Marketers, M&A Analysts]
core_jtbd: "Find B2B companies by filters → reveal DM contacts → run outreach campaign"
mvp_scope:
  must_have:
    - Search by ОКВЭД, регион, employees, revenue_range
    - Company card (full ЕГРЮЛ-style with ИНН, ОКВЭД, директор, адрес)
    - Contact reveal (email, phone, telegram) с credit-system
    - CSV export
    - Telegram outreach (templates + AI personalization)
    - LLM ICP look-alike (upload CRM → suggest similar companies)
    - Billing (ЮKassa/CloudPayments) с tier-based quotas
    - Auth + личный кабинет
  should_have:
    - Email outreach (SMTP integration)
    - amoCRM/Bitrix24 export
  out_of_scope_v1:
    - Mobile app
    - SSO/SAML
    - Госконтракты/арбитраж интеграции
    - English UI

architecture_constraints:
  pattern: Distributed Monolith (Monorepo)
  containers: Docker + Docker Compose
  infrastructure: VPS (AdminVPS / HOSTKEY)
  deploy: Docker Compose direct deploy
  ai_integration: MCP servers
  
external_apis:
  - LLM (OpenAI / YandexGPT) — ICP analysis + outreach personalization
  - Telegram Bot API — outreach
  - ЮKassa / CloudPayments — billing
  - [optional Phase 2] СПАРК/Контур.Фокус API — data enrichment
  - [optional Phase 2] ЕГРЮЛ open data — daily ETL

security_pattern: # ОБЯЗАТЕЛЬНО раз есть external APIs
  api_keys_input: "UI Settings > Integrations"
  storage: "Encrypted IndexedDB (AES-GCM 256-bit)"
  key_derivation: "PBKDF2 from user password"
  server_side: "No key storage on backend"

compliance:
  - 152-ФЗ: только публичные данные + явное согласие на хранение
  - Реестр операторов ПДн: регистрация
  - Opt-out процесс для контактов
  - Audit log всех reveals и outreach

unit_economics_targets:
  arpu_pro: 9990 # ₽/мес
  cac_target: 15000-25000
  ltv_cac: ≥5x
  gross_margin: ≥75%

risks:
  - 152-ФЗ ужесточение → pivot на enrichment-only
  - СПАРК API дорогой → fallback на open data
  - Контур запустит analog → защита через Telegram-spec + AI ICP
```

---

## 7. Open Questions для Phase 1

1. **Telegram outreach legal:** допустимо ли по 152-ФЗ массово писать в Telegram по публично открытому @username? → требует юр-консультации
2. **Data acquisition:** start с парсинга rusprofile/e-disclosure или сразу контракт со СПАРК? (стоимость vs. полнота)
3. **AI ICP:** OpenAI (качество, $) или YandexGPT (соответствие, дешевле)?
4. **Pricing:** ₽9 990 за Pro оптимально или начать с ₽4 990 для тяги?
5. **Free tier:** включать contact reveals (рискованно) или только search-only?

---

## Confidence Score: 6.5/10

- ✅ **Сегменты и JTBD:** уверенность 8/10 — стандартные B2B sales задачи
- ⚠️ **Размер рынка:** 5/10 — оценка [H], нужна валидация через интервью
- ✅ **Конкуренты:** 7/10 — известный ландшафт РФ
- ⚠️ **Unit Economics:** 5/10 — все цифры [H], проверять в живых тестах
- ✅ **Архитектура:** 8/10 — типовой B2B SaaS стек

Верификация в Phase 2 (Validation) через customer interviews + competitive deep-dive.
