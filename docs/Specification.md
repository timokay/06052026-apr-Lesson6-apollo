# Specification: Apollo (RU)

> SPARC Phase 3 output. Detailed requirements with Gherkin acceptance criteria.

## Glossary

| Term | Definition |
|------|------------|
| Reveal | Раскрытие контакта компании; списывает 1 кредит |
| Credit | Единица квоты, тратится на reveal |
| ICP | Ideal Customer Profile — целевой профиль клиента |
| Look-alike | Компании, похожие по профилю на загруженных |
| Outreach | Кампания массовой персонализированной отправки сообщений |
| Quota | Максимум reveals/messages в месяц на тарифе |
| ОКВЭД | Общероссийский классификатор видов экономической деятельности |
| ИНН | Идентификационный номер налогоплательщика (10 цифр для юрлиц, 12 для ИП) |

## Domain Model (entities)

```
User --< Subscription >-- Plan
User --< RevealEvent >-- Company
User --< Campaign --< Message >-- Contact
Company --< Contact
Company has: inn, name, okved_main, region, employee_count, revenue_range, address, director
Contact has: company_inn, name, title, email, phone, telegram
ICP belongs_to User; analyzes [Company] -> profile -> suggests [Company]
```

## Functional Requirements

### FR-1: Authentication & Account

**FR-1.1** — Регистрация по email + password (минимум 8 символов, 1 заглавная, 1 цифра)
- Email верификация через ссылку (TTL 24h)
- Согласие на обработку ПДн (галочка) — обязательно
- Согласие на email маркетинг — опционально

**FR-1.2** — Логин по email + password, JWT (access 15min + refresh 7d)
- Refresh token rotation
- Logout = invalidate refresh

**FR-1.3** — OAuth Google (P1, post-MVP)

**FR-1.4** — Восстановление пароля через email link (TTL 1h)

#### Gherkin AC

```gherkin
Feature: User Registration

  Scenario: Successful registration
    Given пользователь на странице /register
    When заполняет email "marina@example.com" и password "Strong1234"
      And отмечает галочку "Согласен на обработку ПДн"
      And нажимает "Зарегистрироваться"
    Then создаётся пользователь со статусом "pending_verification"
      And отправляется email со ссылкой verify
      And редирект на /verify-prompt

  Scenario: Email already exists
    Given существует user с email "marina@example.com"
    When заполняется форма с тем же email
    Then возвращается 409 "EMAIL_EXISTS"
      And форма показывает «Email уже зарегистрирован. <Войти>»

  Scenario: Weak password
    When password "12345"
    Then возвращается 400 "WEAK_PASSWORD"
      And форма показывает требования

  Scenario: ПДн consent missing
    When галочка "Согласен на ПДн" не отмечена
    Then кнопка "Зарегистрироваться" disabled
```

### FR-2: Company Search

**FR-2.1** — Список компаний с пагинацией (page size: 20, max page: 500)

**FR-2.2** — Фильтры:
- ОКВЭД (multi-select, prefix-match: "62" matches "62.01", "62.02")
- Region (multi-select из 89 субъектов РФ)
- Employee count (range slider: 0-1000+, buckets: 1-10, 11-50, 51-200, 201-500, 500-1000, 1000+)
- Revenue range (enum: <10M, 10M-50M, 50M-100M, 100M-500M, 500M-1B, 1B-10B, 10B+)
- Search by name / ИНН (substring match)

**FR-2.3** — Сортировка: relevance (default), revenue desc, employees desc, name asc

**FR-2.4** — Saved searches (Pro+): имя + URL-параметры, до 20 saved searches на user

#### Gherkin AC

```gherkin
Feature: Company Search

  Scenario: Filter by industry and region
    Given в БД есть 1000 компаний разного ОКВЭД и регионов
    When user открывает /search
      And выбирает ОКВЭД "62.01" (Разработка ПО)
      And выбирает Region "Москва"
    Then показывается список из ≤20 компаний
      And все компании имеют okved_main starts with "62.01"
      And все компании имеют region == "Москва"
      And отображается общее count "Найдено N компаний"

  Scenario: Search by ИНН
    When в строке поиска вводится "7707083893"
    Then в результате 1 компания с inn == "7707083893"
      And подсвечивается совпадение

  Scenario: No results
    When фильтры не дают результатов
    Then показывается empty state "Ничего не найдено. Попробуйте расширить фильтры."

  Scenario: Search performance (NFR)
    Given 100 000 компаний в БД
    When выполняется поиск с 3 фильтрами
    Then ответ возвращается < 500ms (p99)
```

### FR-3: Company Card & Contact Reveal

**FR-3.1** — Карточка компании показывает:
- Все поля companies.csv (ИНН, name, ОКВЭД, region, employees, revenue, address, director)
- Список контактов (locked если не reveal'ено)
- Кнопка "Reveal contacts" — показывает email/phone/telegram, списывает credit
- История ваших reveals по этой компании (если уже revealed — не списывает повторно)

**FR-3.2** — Reveal API:
- POST /api/v1/reveals { company_inn }
- Списывает 1 credit с user.subscription.remaining_credits
- Возвращает array of contacts
- Аудитный лог записывается

**FR-3.3** — Quota check:
- Если remaining_credits == 0 → возвращается 402 "QUOTA_EXCEEDED" с CTA "Upgrade plan"

#### Gherkin AC

```gherkin
Feature: Contact Reveal

  Scenario: Successful reveal with credits
    Given user "Marina" с Pro plan, remaining_credits == 100
      And компания с inn "7707083893" имеет 3 контакта
    When Marina нажимает "Reveal contacts" на карточке этой компании
    Then показываются 3 контакта (email, phone, telegram)
      And remaining_credits становится 99
      And создаётся reveal_event запись (user_id, company_inn, credit_cost: 1, timestamp)
      And в audit log: "Marina revealed 7707083893"

  Scenario: Reveal без credits
    Given user "Marina" с remaining_credits == 0
    When нажимает "Reveal contacts"
    Then возвращается 402 "QUOTA_EXCEEDED"
      And UI показывает modal "Лимит исчерпан. <Upgrade plan>"

  Scenario: Repeat reveal (no double-charge)
    Given Marina уже revealed компанию "7707083893" 5 минут назад
    When снова нажимает "Reveal contacts"
    Then показываются те же контакты
      And remaining_credits НЕ списывается
```

### FR-4: CSV Export

**FR-4.1** — Экспорт текущих результатов поиска (с применёнными фильтрами) в CSV
- UTF-8 encoding
- Поля: inn, name, okved_main, region, employee_count, revenue_range, address, director
- Если включён checkbox "С контактами" → добавляются revealed контакты (только revealed, остальные пустые)
- Лимит: 1 000 строк за экспорт (Free), 5 000 (Starter), 10 000 (Pro), без лимита (Team+)

**FR-4.2** — Экспорт списка контактов кампании (Pro+)

#### Gherkin AC

```gherkin
Feature: CSV Export

  Scenario: Export filtered companies
    Given Marina выбрала filter "Москва, ОКВЭД 62.01" → 247 компаний
    When нажимает "Экспорт CSV"
    Then скачивается файл "apollo-companies-YYYY-MM-DD.csv"
      And файл содержит 247 строк + header
      And encoding UTF-8 with BOM (для Excel)

  Scenario: Export limit exceeded (Free tier)
    Given Marina на Free tier, у неё в выборке 1500 компаний
    When нажимает "Экспорт CSV"
    Then экспортируется первые 1000 строк
      And отображается warning "Free tier limit. Upgrade to export more."
```

### FR-5: AI ICP Analyzer & Look-alike

**FR-5.1** — Загрузка CSV с минимум 20 ИНН существующих клиентов
- Validation: ИНН формат (10/12 цифр), уникальность
- Если ИНН не найден в БД Apollo — флагается, но не блокирует анализ

**FR-5.2** — ICP анализ (LLM):
- Извлекает: industry distribution, region distribution, size buckets, revenue buckets
- Генерирует ICP profile (текст 200-500 слов): сегменты, паттерны, рекомендации

**FR-5.3** — Look-alike suggestions:
- Алгоритм: для каждой загруженной компании ищет N=20 похожих по similarity score (отрасль×0.4 + размер×0.3 + регион×0.2 + revenue×0.1)
- Дедупликация (ICP companies исключаются)
- Top-100 ranked по среднему score

#### Gherkin AC

```gherkin
Feature: AI ICP Analyzer

  Scenario: Analyze customer base
    Given Marina загружает CSV с 50 ИНН своих клиентов
    When нажимает "Analyze ICP"
    Then в течение 30s выводится:
      | section | content |
      | Industry mix | "78% IT (62.xx), 12% Media (58.xx), 10% Finance (64.xx)" |
      | Size distribution | "60% 50-200 emp, 25% 200-500, 15% 500+" |
      | Region | "75% Москва, 15% СПб, 10% other" |
      | LLM summary | "Ваши клиенты — IT-компании среднего размера..." |
      | Suggested look-alike | список из 100 ранжированных компаний |

  Scenario: Insufficient data
    Given Marina загружает CSV с 10 ИНН (< 20)
    Then возвращается 400 "INSUFFICIENT_ICP_DATA"
      And UI показывает "Минимум 20 компаний для надёжного ICP анализа"

  Scenario: ICP performance (NFR)
    When анализ для 100 компаний
    Then результат возвращается < 30s
```

### FR-6: Telegram Outreach

**FR-6.1** — Создание кампании:
- Имя кампании
- Источник аудитории: текущая выборка / saved search / uploaded CSV
- Шаблон сообщения (с placeholder'ами: {company_name}, {industry}, {director_name})
- Опция "AI personalize each message" (Pro+)
- Schedule: send now / send at <date+time>

**FR-6.2** — Аудитория:
- Только контакты с непустым telegram username
- Дедупликация по telegram username
- Лимит per campaign: 50 (Free), 200 (Starter), 1000 (Pro), 5000 (Team+)

**FR-6.3** — Send loop:
- Throttle: max 5 msg/sec per bot
- Per-recipient lifetime limit: max 1 msg/recipient/30 days
- Opt-out обработка: если получатель ответил "стоп"/"unsubscribe" — блокировка на уровне Apollo

**FR-6.4** — Stats:
- Sent / Delivered / Read / Replied / Errored
- Per-message: timestamp, status, error_code if any

#### Gherkin AC

```gherkin
Feature: Telegram Outreach

  Scenario: Create and launch campaign
    Given Marina выбрала 50 контактов с telegram username
    When создаёт campaign "IT outreach Q4"
      And template "Здравствуйте, {company_name}! Мы помогаем..."
      And включает "AI personalize"
      And нажимает "Отправить"
    Then создаётся campaign с status "running"
      And для каждого получателя:
        - LLM генерирует персонализированный текст < 5s
        - отправляется через Telegram Bot API
        - throttle 5 msg/sec
      And per-recipient записывается message с status

  Scenario: Recipient opted out
    Given контакт @ivanov ответил "стоп" в предыдущей кампании
    When Marina включает @ivanov в новую кампанию
    Then этому получателю не отправляется
      And в кампании показывается "1 пропущен (opt-out)"

  Scenario: Per-recipient lifetime limit
    Given @ivanov получил сообщение от Marina 10 дней назад
    When Marina пытается отправить новое сообщение @ivanov
    Then этому получателю не отправляется
      And UI показывает "1 пропущен (recently contacted, retry after 20 days)"

  Scenario: Telegram API error
    Given Telegram bot заблокирован пользователем @petrov
    When отправляется сообщение @petrov
    Then message.status = "errored", error_code = "USER_BLOCKED_BOT"
      And не списывается credit за это сообщение
```

### FR-7: Billing & Subscription

**FR-7.1** — Тарифные планы:

| Plan | Price ₽/мес | Reveals | Seats | Outreach msg/мес | AI personalize | Saved searches |
|------|-------------|---------|-------|------------------|----------------|----------------|
| Free | 0 | 25 | 1 | 0 | ❌ | 3 |
| Starter | 2 990 | 500 | 1 | 200 | ❌ | 10 |
| Pro | 9 990 | 2 000 | 3 | 1 000 | ✅ | 20 |
| Team | 29 990 | 10 000 | 10 | 5 000 | ✅ | unlimited |
| Enterprise | from 99 000 | unlimited | unlimited | unlimited | ✅ | unlimited |

**FR-7.2** — Подписка через ЮKassa или CloudPayments:
- Сохранение карты для авто-продления
- Pro-rated upgrade (мгновенный апгрейд, доплата за остаток месяца)
- Downgrade в конце текущего цикла
- Cancel в любой момент, доступ до конца периода

**FR-7.3** — Квоты обновляются ежемесячно (1-го числа в 00:00 МСК)
- Неиспользованные reveals НЕ переносятся (use it or lose it)

**FR-7.4** — Webhook от ЮKassa: payment.succeeded → activate plan; payment.canceled → schedule downgrade

#### Gherkin AC

```gherkin
Feature: Subscription Billing

  Scenario: Upgrade to Pro
    Given Marina на Free tier
    When нажимает "Upgrade to Pro" → выбирает ЮKassa → вводит карту
    Then ЮKassa возвращает payment_id
      And после payment.succeeded webhook subscription становится "active", plan="pro"
      And remaining_credits = 2000
      And сохраняется payment_method для авто-продления

  Scenario: Quota reset on monthly cycle
    Given Marina на Pro plan, current period: 2026-04-01 .. 2026-05-01
      And remaining_credits = 547
    When наступает 2026-05-01 00:00 МСК
    Then remaining_credits = 2000
      And создаётся новый billing_period entry

  Scenario: Failed payment
    Given у Marina истекла карта при auto-renewal
    When ЮKassa отдаёт payment.failed
    Then subscription становится "past_due"
      And user получает email "Платёж не прошёл, обновите карту"
      And через 7 дней без оплаты → downgrade на Free
```

### FR-8: Audit Log & 152-ФЗ Compliance

**FR-8.1** — Audit log записывает:
- Кто (user_id), что (action), когда (timestamp), какой объект (entity_id)
- Actions: register, login, reveal_contact, send_message, export_csv, upload_icp, change_plan
- Хранение: 3 года

**FR-8.2** — Opt-out endpoint (публичный, без авторизации):
- GET /optout?email=X&token=Y
- Помечает email как opted-out → больше не появляется в reveals и outreach
- Audit log записывает событие

**FR-8.3** — Privacy & Terms:
- Privacy policy на /privacy
- Terms of service на /terms
- Чекбокс согласия при регистрации обязателен

#### Gherkin AC

```gherkin
Feature: Audit & Compliance

  Scenario: Reveal logged in audit
    When Marina выполняет reveal
    Then в audit_log запись:
      | user_id | "uuid-marina" |
      | action | "reveal_contact" |
      | entity_id | "company:7707083893" |
      | timestamp | now() |
      | metadata | { credits_used: 1 } |

  Scenario: Email opt-out
    Given в outreach campaign отправлено письмо на ivanov@example.com
      And в footer ссылка /optout?email=ivanov@example.com&token=signed
    When Иванов кликает по ссылке
    Then ivanov@example.com помечается opted_out=true
      And этот email больше не показывается в reveals
      And audit_log запись "optout"
```

## Non-Functional Requirements (детали)

### NFR-1: Performance

| Endpoint | Latency target | Throughput |
|----------|----------------|------------|
| GET /companies (search) | p99 < 500ms | 100 RPS |
| GET /companies/:inn | p99 < 200ms | 200 RPS |
| POST /reveals | p95 < 2s | 50 RPS |
| POST /icp/analyze | p95 < 30s | 5 RPS |
| Telegram send | 5 msg/sec/bot | rate-limited |

### NFR-2: Security

- TLS 1.3 only, HSTS preload
- CSP strict
- bcrypt cost 12 для паролей
- JWT signing key rotation (90 дней)
- API rate limit: 100 req/min per user IP
- SQL injection: parametrized queries only
- XSS: React автоэкранирование + DOMPurify для user-input HTML
- Encrypted IndexedDB для пользовательских API keys (LLM, Telegram bot tokens)

### NFR-3: Scalability

| Component | MVP | P2 (Y1 Q4) |
|-----------|-----|------------|
| Companies in DB | 25K | 500K |
| Contacts in DB | 100K | 2M |
| Concurrent users | 50 | 500 |
| Daily reveals | 5K | 100K |
| Daily outreach msgs | 10K | 500K |

### NFR-4: Availability

- Uptime: 99.5% MVP, 99.9% post-MVP
- RTO (Recovery Time Objective): 4h
- RPO (Recovery Point Objective): 1h (last DB snapshot)
- Maintenance window: Sun 03:00-05:00 MSK, announced 24h prior

### NFR-5: Compliance

- 152-ФЗ: регистрация в Реестре операторов ПДн
- Хранение ПДн на территории РФ (HOSTKEY VPS)
- Privacy policy, Terms of Service, согласие на обработку ПДн
- Право на удаление (GDPR-like): user может удалить свой аккаунт + все данные за 30 дней
- Audit log retention: 3 года (требование закона о финразведке для billing)

### NFR-6: Observability

- Structured logging (JSON, levels: debug/info/warn/error)
- Distributed tracing (OpenTelemetry)
- Metrics: Prometheus + Grafana dashboards
- Alerting: response time p99 > 1s, error rate > 1%, CPU > 80%

## Success Metrics (Acceptance)

| Metric | MVP target |
|--------|------------|
| Time to register first reveal | < 3 min |
| Activation rate | ≥ 40% (Free → first reveal) |
| Free → Paid conversion | ≥ 8% |
| NPS | ≥ 40 |
| Reveal accuracy | ≥ 85% (manual sampling) |
| MTTR for incidents | < 30 min |
