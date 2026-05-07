# Test Scenarios (BDD): Apollo (RU)

> SPARC Phase 2 output. BDD/Gherkin scenarios for QA + automated tests.
> Generated from Specification.md, expanded with: happy path (1-2), errors (2-3), edge cases (1-2), security checks per feature.

## Coverage Map

| Feature | Happy | Errors | Edge cases | Security |
|---------|-------|--------|------------|----------|
| F1. Auth | 2 | 3 | 2 | 3 |
| F2. Search | 2 | 2 | 2 | 1 |
| F3. Reveal | 2 | 3 | 3 | 2 |
| F4. CSV Export | 1 | 2 | 2 | 1 |
| F5. ICP Analysis | 1 | 3 | 2 | 1 |
| F6. Outreach | 2 | 3 | 3 | 2 |
| F7. Billing | 2 | 3 | 2 | 2 |
| F8. Audit & Opt-out | 1 | 2 | 1 | 2 |
| **TOTAL** | **13** | **21** | **17** | **14** |

**Grand total: 65 scenarios**

---

## F1. Authentication

### F1.1: User Registration

```gherkin
Feature: User Registration
  As a prospective user
  I want to create an account with email and password
  So that I can use Apollo (RU)

  # Happy path

  Scenario: Successful registration with strong password
    Given пользователь на странице /register
    When заполняет email "marina.smirnova@example.com" и password "Strong1234!"
      And отмечает галочку "Согласен на обработку ПДн"
      And нажимает "Зарегистрироваться"
    Then создаётся пользователь со статусом "pending_verification"
      And отправляется email со ссылкой verify (TTL 24h)
      And редирект на /verify-prompt
      And в audit_log создаётся запись action="user_registered"

  Scenario: Email verification within TTL
    Given user "marina@..." с status "pending_verification"
      And ссылка verify сгенерирована 12 часов назад (внутри TTL=24h)
    When пользователь кликает по ссылке
    Then user.status переходит в "active"
      And редирект на /dashboard
      And создаётся welcome email с onboarding tips

  # Errors

  Scenario: Weak password rejected
    When password "12345"
    Then возвращается 400 "WEAK_PASSWORD"
      And UI показывает требования (8+ chars, 1 uppercase, 1 digit)

  Scenario: Duplicate email
    Given существует user с email "marina@example.com" status "active"
    When заполняется форма с тем же email
    Then возвращается 409 "EMAIL_EXISTS"
      And UI: «Email уже зарегистрирован. <Войти>»

  Scenario: Missing PDN consent
    When галочка "Согласен на ПДн" не отмечена
    Then кнопка "Зарегистрироваться" disabled
      And tooltip: «Согласие обязательно по 152-ФЗ»

  # Edge cases

  Scenario: Email with plus alias
    When email "marina+test@gmail.com"
    Then принято (RFC 5322 valid)
      And создаётся user

  Scenario: Email verification link expired
    Given user status "pending_verification"
      And verify link сгенерирован 25 часов назад (TTL exceeded)
    When user кликает по ссылке
    Then возвращается 410 "VERIFICATION_EXPIRED"
      And UI: «Ссылка устарела, отправить новую?»

  # Security

  Scenario: Brute force registration blocked
    When IP делает 5 попыток регистрации за 1 час
    Then на 6-ю попытку возвращается 429 "RATE_LIMIT"
      And IP блокируется на 1 час

  Scenario: SQL injection attempt
    When email = "test' OR 1=1--"
    Then возвращается 400 "INVALID_EMAIL"
      And в audit_log security event "injection_attempt"

  Scenario: XSS attempt in email
    When email = "<script>alert(1)</script>@x.com"
    Then возвращается 400 "INVALID_EMAIL"
      And значение не сохраняется
```

### F1.2: Login & Session

```gherkin
Feature: Login

  # Happy path
  Scenario: Successful login
    Given user "marina@..." активный
    When отправляется POST /auth/login { email, password }
    Then 200 OK
      And устанавливается access_token cookie (HttpOnly, Secure, SameSite=Lax, TTL=15min)
      And устанавливается refresh_token cookie (HttpOnly, Secure, SameSite=Strict, Path=/api/v1/auth/refresh, TTL=7d)
      And в response: { user: {...}, subscription: {...} }

  Scenario: Token refresh
    Given access_token истёк, refresh_token валиден
    When POST /auth/refresh с refresh_token cookie
    Then новый access_token issued
      And refresh_token rotated (старый invalidated)

  # Errors
  Scenario: Wrong password
    When password неверный
    Then 401 "INVALID_CREDENTIALS"
      And не разглашается, существует ли email

  Scenario: 5 failed attempts → captcha
    Given user сделал 5 failed login для одного email
    When 6-я попытка
    Then требуется captcha challenge

  Scenario: Refresh token reuse (token theft)
    Given refresh_token A1 был использован для refresh, выдан A2
    When снова используется A1 (старый)
    Then 401, вся session family invalidated
      And user должен залогиниться заново
```

---

## F2. Company Search

```gherkin
Feature: Company Search

  Background:
    Given в БД 1000 компаний разного ОКВЭД и регионов
      And user "Marina" logged in with active Pro plan

  # Happy path
  Scenario: Filter by industry and region
    When user открывает /search
      And выбирает ОКВЭД "62.01" (Разработка ПО)
      And выбирает Region "Москва"
    Then показывается список компаний
      And все companies имеют okved_main starting with "62.01"
      And все companies имеют region == "Москва"
      And отображается total count "Найдено N компаний"
      And response p99 < 500ms (n=1000 parallel)

  Scenario: Search by ИНН
    When в строке поиска "7707083893"
    Then 1 company с inn == "7707083893"
      And подсвечивается совпадение

  # Errors
  Scenario: Invalid ИНН format
    When query "12345" (5 digits)
    Then не fired как ИНН search; обрабатывается как substring
      And если нет matches → empty state

  Scenario: Filter combination returns 0
    Given нет компаний с ОКВЭД 62.01 в регионе Якутия
    When user filters this combination
    Then возвращается 200 + total: 0
      And UI: "Ничего не найдено. <Расширить фильтры>"

  # Edge cases
  Scenario: Page beyond total
    Given 100 results, page_size=20
    When request page=999
    Then 200 + results: []
      And total: 100 (без error)

  Scenario: Cyrillic substring search
    When query "Сбер"
    Then matches "ПАО Сбербанк", "ПАО Сбер", "Сбер Капитал" via pg_trgm

  # Security
  Scenario: SQL injection in filter
    When query parameter region = "Москва'); DROP TABLE companies--"
    Then 200 OK (parameterized query)
      And companies table intact
      And в logs запись о подозрительном запросе (если matches pattern)
```

---

## F3. Contact Reveal

```gherkin
Feature: Contact Reveal

  Background:
    Given user "Marina" logged in with Pro plan, remaining_reveals=100
      And company "7707083893" имеет 3 контакта (none opted_out)

  # Happy path
  Scenario: Successful reveal with credits
    When Marina нажимает "Reveal contacts" на карточке компании
    Then показываются 3 контакта (email, phone, telegram)
      And remaining_credits становится 99
      And создаётся reveal_event (user_id=marina, company_inn=7707083893, credit_cost=1)
      And в audit_log: action=reveal_contact, entity_id=company:7707083893, metadata={credits_used:1}
      And response p95 < 2s

  Scenario: Repeat reveal (no double-charge)
    Given Marina уже revealed company "7707083893" 5 минут назад
    When нажимает "Reveal contacts" повторно
    Then показываются те же 3 контакта (cached)
      And remaining_credits НЕ списывается
      And новая запись в reveal_events НЕ создаётся

  # Errors
  Scenario: Reveal без credits
    Given Marina с remaining_credits == 0
    When нажимает "Reveal contacts"
    Then 402 "QUOTA_EXCEEDED"
      And UI modal: "Лимит исчерпан. <Upgrade plan>"
      And reveal_event НЕ создаётся

  Scenario: Reveal невалидного ИНН
    When POST /reveals { company_inn: "9999999999" }
    Then 404 "COMPANY_NOT_FOUND"
      And remaining_credits НЕ списывается

  Scenario: Reveal company с opted-out контактами
    Given company "X" имеет 3 контакта, все opted_out=true
    When Marina нажимает "Reveal"
    Then 200 [] (empty array)
      And remaining_credits НЕ списывается
      And UI: "Все контакты отозваны"

  # Edge cases — Concurrency

  Scenario: Two concurrent reveals at remaining=1
    Given Marina remaining_credits=1
    When 2 reveals fire concurrently for company X и Y
    Then ровно 1 succeeds (200), 1 fails (402)
      And remaining_credits=0
      And exactly 1 reveal_event записан

  Scenario: Subscription expired mid-action
    Given Marina subscription status="past_due"
    When нажимает "Reveal"
    Then 402 "SUBSCRIPTION_EXPIRED"
      And UI: "Платёж не прошёл. Обновите карту."

  Scenario: Cross-user same company (no shared cache)
    Given user A revealed company X, user B has not
    When user B нажимает "Reveal" for company X
    Then user B charged 1 credit (separate counter)
      And reveal_event создан для B

  # Security
  Scenario: Reveal без auth
    When POST /reveals без cookie
    Then 401 "AUTH_REQUIRED"

  Scenario: Reveal с modified user_id в JWT
    Given attacker имеет valid JWT для user A
      And подделывает user_id в JWT body
    When request с modified token
    Then 401 (signature mismatch)
      And в logs security event
```

---

## F4. CSV Export

```gherkin
Feature: CSV Export

  Background:
    Given Marina logged in with Starter plan

  # Happy path
  Scenario: Export filtered companies
    Given Marina selected filter "Москва, ОКВЭД 62" → 247 companies
    When нажимает "Экспорт CSV"
    Then скачивается "apollo-companies-2026-05-06.csv"
      And содержит 247 строк + header
      And UTF-8 with BOM (для Excel)
      And запятые в полях quoted

  # Errors
  Scenario: Export limit exceeded (Free tier)
    Given user на Free tier, в выборке 1500 companies
    When нажимает "Экспорт CSV"
    Then экспортируется первые 1000 строк
      And toast warning "Free tier limit. Upgrade to export more."

  Scenario: Export ничего
    Given filter не дал результатов
    When нажимает "Экспорт"
    Then кнопка disabled
      And tooltip: "Сначала выберите хотя бы одну компанию"

  # Edge cases
  Scenario: Cyrillic in CSV opens correctly in Excel
    Given в выборке "ПАО Сбербанк" (Cyrillic)
    When экспорт → открыть в Excel 2019+
    Then русский текст отображается корректно (BOM работает)

  Scenario: Special chars in fields
    Given company name содержит запятую: "Газпром, ПАО"
    When экспорт CSV
    Then field в выводе обёрнут в кавычки: `"Газпром, ПАО"`

  # Security
  Scenario: Export не утекает чужие данные
    Given Marina selected 100 companies
    When она инициирует экспорт
    Then в выводе только companies из её current selection
      And её revealed contacts (не чужие revealed)
```

---

## F5. AI ICP Analyzer

```gherkin
Feature: AI ICP Analysis

  Background:
    Given user "Дмитрий" logged in with Pro plan

  # Happy path
  Scenario: Analyze customer base of 50 companies
    Given Дмитрий загружает CSV с 50 ИНН своих клиентов
      And 45 ИНН найдены в Apollo DB (match rate 90%)
    When нажимает "Analyze ICP"
    Then в течение 30s выводится:
      | section | content |
      | Industry mix | distribution dict с top-3 ОКВЭД и percentage |
      | Size distribution | bucket counts по employee ranges |
      | Region | distribution по регионам |
      | LLM summary | 200-500 word текст про ICP |
      | Look-alikes | top-100 ranked companies |
      And остаются в его аккаунте под именем "ICP Profile #1"

  # Errors
  Scenario: Insufficient data
    Given Дмитрий загружает 10 ИНН (< 20 minimum)
    Then 400 "INSUFFICIENT_ICP_DATA"
      And UI: "Минимум 20 компаний для надёжного ICP анализа"

  Scenario: Low match rate
    Given Дмитрий загрузил 50 ИНН, но 40 не найдены в Apollo (match 20%)
    Then 400 "LOW_MATCH_RATE"
      And UI: "Только 20% компаний найдено. <Загрузить больше?>"

  Scenario: Free tier user пытается ICP
    Given user на Free plan
    When uploads CSV
    Then 403 "PLAN_UPGRADE_REQUIRED"
      And UI: "ICP Analyzer доступен на Pro+. <Upgrade>"

  # Edge cases
  Scenario: LLM fallback when YandexGPT fails
    Given YandexGPT API возвращает 5xx
    When ICP analysis запущен
    Then fallback на OpenAI gpt-4o-mini
      And в metadata profile: llm_provider="openai_fallback"

  Scenario: CSV with duplicates
    Given upload CSV с 50 строк, 30 unique ИНН
    Then используются только 30 unique
      And UI warning: "Обнаружены дубликаты, использовано 30 уникальных"

  # Security
  Scenario: Upload non-CSV file
    When uploaded файл типа application/pdf
    Then 400 "INVALID_FILE_TYPE"
      And файл удалён из MinIO
```

---

## F6. Telegram Outreach

```gherkin
Feature: Telegram Outreach

  Background:
    Given Marina на Pro plan, remaining_outreach=1000
      And bot @ApolloRuOutreachBot активен

  # Happy path
  Scenario: Create and launch campaign without AI personalize
    Given Marina выбрала 50 контактов с telegram username
    When создаёт campaign "IT Q4"
      And template "Здравствуйте, {company_name}! Мы помогаем..."
      And ai_personalize=false
      And нажимает "Отправить сейчас"
    Then создаётся campaign status="scheduled"
      And в течение 15s запускается worker.send_campaign
      And для каждого получателя:
        | step | check |
        | render | template применён с {company_name} substitution |
        | throttle | максимум 5 msg/sec |
        | send | telegram.send_message called |
        | record | campaign_messages.status = 'sent' if 200 от TG |
      And campaign.status = 'completed' когда все обработаны

  Scenario: Campaign with AI personalize
    Given Marina с Pro plan
    When создаёт campaign с ai_personalize=true
      And 100 recipients
    Then для каждого:
      | step | check |
      | LLM call | с template + company context |
      | timeout | < 5s per message (or fallback to template) |
      | send | personalized text via telegram |
      And total time < 5 minutes

  # Errors
  Scenario: Recipient opted out
    Given контакт @ivanov ответил "стоп" в предыдущей кампании
      And создан opt_outs запись
    When Marina включает @ivanov в новую кампанию
    Then этому получателю не отправляется
      And campaign_messages.status='skipped', error_code='OPTED_OUT'
      And UI campaign view: "1 пропущен (opt-out)"
      And remaining_outreach НЕ списан

  Scenario: Per-recipient lifetime limit (30-day)
    Given @ivanov получил сообщение от Marina 10 дней назад (status='sent')
    When Marina включает @ivanov в новую кампанию
    Then status='skipped', error_code='RECENTLY_CONTACTED'
      And remaining_outreach НЕ списан
      And UI: "1 пропущен (recently contacted, retry after 20 days)"

  Scenario: Telegram USER_BLOCKED_BOT
    Given @petrov заблокировал нашего bot
    When sending message @petrov
    Then telegram.send_message returns ERR
      And status='errored', error_code='USER_BLOCKED_BOT'
      And remaining_outreach НЕ списан (нет реального send)

  # Edge cases
  Scenario: Quota exhausted mid-campaign
    Given Marina remaining_outreach=200, audience=300
    When campaign launches
    Then первые 200 sent
      And остальные 100 status='skipped', error_code='QUOTA_EXCEEDED'
      And campaign.status='completed'
      And user notified via in-app

  Scenario: User cancels campaign mid-run
    Given campaign running, 50/300 sent
    When Marina нажимает "Cancel"
    Then worker checks status каждые 50 messages → break
      And campaign.status='canceled'
      And остальные status='skipped', error_code='CANCELED_BY_USER'

  Scenario: Telegram API rate limit
    Given TG API возвращает FLOOD_WAIT 60s
    When sending hits flood
    Then worker sleeps 60s
      And resumes
      And retry counter incremented (max 5)

  # Security
  Scenario: Campaign attempts to use API key from request body
    Given attacker sends POST /campaigns с поддельным telegram_token в body
    When backend получает request
    Then telegram_token поле игнорируется (не в Pydantic schema)
      And используется наш bot token из env

  Scenario: Opt-out link не enumerable
    Given attacker tries /optout?email=victim@x.com&token=guessed
    Then HMAC проверка fails
      And 400 "INVALID_TOKEN"
      And victim НЕ helpful не помечается opted_out
```

---

## F7. Billing & Subscription

```gherkin
Feature: Subscription Billing

  Background:
    Given Marina на Free tier

  # Happy path
  Scenario: Upgrade Free → Pro via ЮKassa
    When Marina нажимает "Upgrade to Pro"
      And выбирает payment method "Карта"
      And оплачивает через ЮKassa hosted page
    Then ЮKassa возвращает payment.succeeded webhook
      And subscription становится status="active", plan="pro"
      And remaining_reveals=2000, remaining_outreach=1000
      And payment_method_id сохранён для авто-продления
      And в audit_log: subscription_upgraded
      And user получает welcome-pro email

  Scenario: Quota reset on monthly cycle
    Given Marina на Pro, period: 2026-04-01 .. 2026-05-01
      And remaining_reveals=547
    When наступает 2026-05-01 00:00 МСК (Celery Beat trigger)
    Then ЮKassa charge auto-renewal
      And remaining_reveals=2000, remaining_outreach=1000
      And period_end = 2026-06-01

  # Errors
  Scenario: Failed payment
    Given у Marina истекла карта при auto-renewal
    When ЮKassa отдаёт payment.failed webhook
    Then subscription.status="past_due"
      And email "Платёж не прошёл, обновите карту"
      And через 7 дней без оплаты → downgrade to Free

  Scenario: Webhook без подписи
    When POST /yookassa-webhook без X-Yookassa-Signature
    Then 401 "MISSING_SIGNATURE"
      And в logs security event
      And subscription state не меняется

  Scenario: Webhook с неверной подписью
    When POST с поддельной подписью
    Then 401 "INVALID_SIGNATURE"
      And subscription state не меняется

  # Edge cases
  Scenario: Pro-rated upgrade Pro → Team mid-month
    Given Marina на Pro, current period 2026-04-01..2026-05-01
      And сегодня 2026-04-15 (50% месяца)
    When upgrade to Team (₽29 990)
    Then prorated charge = (29990 - 9990) * 50% = ₽10 000 за остаток
      And plan="team" с этого момента
      And remaining_reveals = текущий + (Team_quota - Pro_quota) * 50% pro-rated

  Scenario: Downgrade Pro → Starter
    When user requests downgrade
    Then UI message: "Plan changes effective from 2026-05-01 (next billing cycle)"
      And subscription.scheduled_plan_change="starter"
      And в начале нового периода — переход на Starter

  # Security
  Scenario: Webhook idempotency
    Given ЮKassa отправил event_id "abc123" дважды
    When backend получает 2-й payload
    Then dedup by event_id
      And операция выполняется только один раз

  Scenario: Payment method belongs to другому user
    Given attacker пытается использовать payment_method_id user A для своего checkout
    When request POST /checkout
    Then validate ownership → 403 "FORBIDDEN"
```

---

## F8. Audit & Opt-out

```gherkin
Feature: Audit Log & Opt-out (152-ФЗ Compliance)

  # Happy path
  Scenario: Reveal logged in audit_log
    When Marina выполняет reveal
    Then в audit_log запись:
      | column | value |
      | user_id | uuid-marina |
      | action | reveal_contact |
      | entity_type | company |
      | entity_id | 7707083893 |
      | metadata | {"credits_used":1} |
      | created_at | now() |
      | ip | request IP |

  # Errors
  Scenario: Audit log unavailable
    Given БД временно недоступна для INSERT в audit_log
    When critical action (например, reveal) выполняется
    Then всё равно успешно завершается (audit_log не блокирует)
      And событие fallback в Loki / structured log
      And alert триггерится для ops

  Scenario: Audit log retention
    Given audit_log записи старше 3 лет
    When ежемесячный cron archive_audit_log
    Then партиции старше 3 лет удаляются
      And предварительно архивируются в MinIO (compressed)

  # Edge cases
  Scenario: Audit search by admin
    Given admin role
    When admin запрашивает /admin/audit?user_id=marina&action=reveal_contact
    Then возвращаются all reveal_contact actions Marina за period
      And admin action also logged (action=audit_search)

  # Security: Opt-out flow
  Scenario: Email opt-out via signed link
    Given в outreach footer ссылка /optout?email=ivanov@x.com&token=hmac_signed
    When Иванов кликает
    Then HMAC проверяется (matches?)
      And insert opt_outs (identifier=ivanov@x.com, type=email)
      And ivanov@x.com больше не показывается в reveals
      And page: "Вы отписаны"

  Scenario: Opt-out URL enumeration attempt
    Given attacker пытается /optout?email=victim@x.com&token=GUESSED
    When request
    Then HMAC mismatch → 400 "INVALID_TOKEN"
      And victim НЕ помечается opted_out
      And в logs: security event (multiple attempts от same IP → block IP)
```

---

## Performance Test Scenarios

### P1: Search Throughput

```gherkin
Feature: Search Performance

  Scenario: 100 RPS sustained for 1 minute
    Given БД с 100K companies
      And 100 users делают filter+search queries
    When 6000 requests за 60 sec (average 100 RPS)
    Then p99 latency < 500ms
      And error rate < 0.1%
      And no DB connection pool exhaustion
```

### P2: Reveal Throughput

```gherkin
Feature: Reveal Performance

  Scenario: 50 RPS sustained for 1 minute
    Given 50 users каждый имеет remaining_credits >= 60
    When каждый делает 60 reveals за минуту (50 RPS combined)
    Then p95 latency < 2s
      And no concurrency issues (no over-deduction of quotas)
```

### P3: Outreach Campaign

```gherkin
Feature: Outreach Throughput

  Scenario: Campaign 5000 messages
    Given Pro+ user, audience=5000, ai_personalize=true
    When campaign launches
    Then completes within 30 minutes
      And LLM API errors < 5%
      And telegram errors < 10%
```

---

## Security Test Scenarios (additional)

```gherkin
Feature: Security Hardening

  # OWASP Top 10 spot-checks

  Scenario: Authorization bypass attempt
    Given user A logged in
    When user A пытается GET /api/v1/users/B/profile
    Then 403 "FORBIDDEN"
      And в logs security event

  Scenario: CSRF protection
    Given Marina logged in via cookie auth
    When evil.com делает POST /reveals со cookies (cross-origin)
    Then 403 (CSRF token mismatch)
      And в logs security event

  Scenario: Rate limiting per endpoint
    When user делает 31 reveal request за минуту
    Then 31-я возвращает 429 "RATE_LIMIT"
      And Retry-After header

  Scenario: Sensitive data masking in logs
    When log line содержит { user_email: "marina@..." }
    Then log output: { user_email: "m***@..." }
      And full email хранится только в audit_log (restricted access)

  Scenario: Session fixation prevention
    Given attacker предоставил victim ссылку с pre-set session ID
    When victim логинится
    Then новый session ID генерируется (старый отброшен)
```

---

## Test Implementation Roadmap

### Sprint 1 (Auth + Search)
- F1: 10 scenarios (auth)
- F2: 6 scenarios (search)
- + Security scenarios

### Sprint 2 (Reveal + Export)
- F3: 10 scenarios
- F4: 6 scenarios
- + Concurrency tests

### Sprint 3 (Billing)
- F7: 9 scenarios
- + Webhook idempotency tests

### Sprint 4 (Outreach)
- F6: 10 scenarios
- + Performance test for campaign

### Sprint 5 (ICP)
- F5: 7 scenarios
- + LLM mock setup

### Sprint 6 (Polish)
- F8: 6 scenarios
- + Full E2E user journey tests

## Tooling

| Tool | Purpose |
|------|---------|
| **pytest + pytest-bdd** | Backend BDD scenarios |
| **playwright** | E2E browser tests (TypeScript) |
| **k6** | Performance/load tests |
| **respx (httpx mock)** | LLM/Telegram/ЮKassa mocking |
| **testcontainers-python** | Real Postgres/Redis в тестах |
| **OWASP ZAP** | Dynamic security scan in CI staging |
| **bandit** | Python static security scan |
| **eslint-plugin-security** | JS security linting |

## Coverage Targets

| Layer | Target |
|-------|--------|
| Backend unit | ≥ 80% |
| Backend critical paths (reveal, billing, audit) | 100% |
| Frontend component | ≥ 60% |
| E2E happy paths | 100% covered |
| BDD scenarios from this doc | 100% implemented by sprint 6 |
