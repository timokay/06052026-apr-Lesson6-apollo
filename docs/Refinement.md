# Refinement: Apollo (RU)

> SPARC Phase 6 output. Edge cases, testing strategy, optimizations.

## Edge Cases Matrix

### Authentication

| Scenario | Input | Expected | Handling |
|----------|-------|----------|----------|
| Empty email | `""` | 400 INVALID_EMAIL | Pydantic validation |
| Email с `+` алиасом | `marina+test@gmail.com` | 201 success | Allowed by RFC 5322 |
| Кириллический email | `маша@мейл.рф` | 400 INVALID_EMAIL (MVP) | Только ASCII в MVP |
| 100 попыток login за минуту | brute force | 429 RATE_LIMIT | IP-based throttle, captcha after 5 fails |
| JWT истёк во время длинной операции | refresh token call | 200 new access token | Auto-refresh в frontend interceptor |
| Refresh token reuse (token theft) | старый refresh token | 401 + invalidate session family | Token rotation pattern |

### Search

| Scenario | Input | Expected | Handling |
|----------|-------|----------|----------|
| Empty filter set | no params | 400 FILTER_REQUIRED OR full list (paginated) | Default to top-100 by updated_at |
| Слишком общие фильтры (>10K results) | okved=64 only | 200 + warning "Уточните фильтры" | Soft limit message |
| Невалидный ИНН формат | `"123"` | 400 INVALID_INN | Regex validation `^\d{10,12}$` |
| ИНН с ведущими нулями | `"0123456789"` | 200 / 404 | Сохраняем как string, не number |
| Unicode в name search | `"Сбер"` | 200 partial matches | pg_trgm работает с UTF-8 |
| SQL injection попытка | `"'; DROP TABLE--"` | 200 (safely escaped) | Parametrized queries |
| Page > total/page_size | page=999 | 200 [] empty | Return empty array, not error |

### Reveal

| Scenario | Input | Expected | Handling |
|----------|-------|----------|----------|
| Concurrent reveals (race condition) | 5 parallel reveals at remaining=1 | Only 1 succeeds, 4 get 402 | SELECT FOR UPDATE |
| Reveal company с 0 контактов | company_inn без contacts | 200 [] + НЕ списывать credit | Check before deduction |
| Reveal company с opted_out контактами | все контакты opted_out | 200 [] + НЕ списывать credit | Filter opted_out, check empty |
| Reveal несуществующего company_inn | unknown ИНН | 404 COMPANY_NOT_FOUND | Validate before TX |
| Reveal с просроченной подпиской | sub.status='past_due' | 402 SUBSCRIPTION_EXPIRED | Check status='active' |

### ICP Analysis

| Scenario | Input | Expected | Handling |
|----------|-------|----------|----------|
| CSV с дубликатами ИНН | 50 rows, 30 unique | Use unique only, warning | dedup before analysis |
| CSV с >5000 ИНН | 10K rows | 400 TOO_MANY_INNS | Limit to 5000 per profile |
| CSV malformed | broken structure | 400 INVALID_CSV | Pre-parse validation |
| LLM API timeout | YandexGPT down | Fallback to OpenAI; if both fail → use rule-based summary template | Circuit breaker pattern |
| LLM hallucinates non-Russian content | inappropriate output | Sanitize + flag for review | Output filter, monitoring |
| Match rate < 30% | most ИНН не в БД | 400 LOW_MATCH_RATE с CTA "Загрузить больше" | Warn user |

### Outreach

| Scenario | Input | Expected | Handling |
|----------|-------|----------|----------|
| Telegram username с @ | `@ivanov` vs `ivanov` | normalize, accept оба | Strip leading @ |
| Контакт без telegram | telegram=null | skip + status='skipped' | filter at send time |
| Telegram USER_BLOCKED_BOT | recipient blocked us | mark errored, NOT charge credit | revert quota |
| Telegram CHAT_NOT_FOUND | username invalid | mark errored, NOT charge | check before send |
| Telegram FLOOD_WAIT | API rate limit | exponential backoff 1s/4s/16s/60s | Celery retry |
| Кампания на 5000 контактов с AI personalize | LLM 5000 calls | Throttle LLM 10/sec, ETA shown to user | Progress indicator |
| Quota исчерпался mid-campaign | remaining=200, audience=300 | Send first 200, mark остальные skipped, status=completed | Atomic deduction |
| User отменил campaign mid-run | UI cancel button | Worker checks status каждые 50 messages → break | Cooperative cancellation |
| Дубликат отправки (повторный contact) | sent 25 days ago | Skip with code RECENTLY_CONTACTED | 30-day cooldown |
| AI personalize fail на 1 message | LLM returns error | Fallback to template render | per-message error handling |

### Billing

| Scenario | Input | Expected | Handling |
|----------|-------|----------|----------|
| ЮKassa webhook задержка/повтор | same event_id 5 раз | Process once, idempotent | Dedup by event.id |
| ЮKassa webhook без подписи | missing signature | 401 + log | HMAC verification |
| Upgrade с Pro на Team mid-month | period_end ещё не наступил | Pro-rated charge for remaining days | Compute prorated amount |
| Downgrade Pro→Starter | user requests | Schedule for period_end (не immediate) | UI shows "Will downgrade on YYYY-MM-DD" |
| Card expired | renewal_charge fails | status='past_due' + email | 7 days grace, then auto-downgrade |
| Refund request | user disputes | Manual ops process via ЮKassa dashboard | Out of automated flow |

### CSV Export

| Scenario | Input | Expected | Handling |
|----------|-------|----------|----------|
| Export 10000 строк (Pro) | quota allows | Stream as chunked response | use StreamingResponse |
| Excel UTF-8 BOM | export для Excel | Add BOM `\xef\xbb\xbf` | Add at file start |
| Запятые в адресе | `"117312, Москва..."` | Quoted CSV field | Use csv.QUOTE_MINIMAL |
| Telegram username `@user` | export contacts | Quote correctly | Standard CSV quoting |

## Concurrency / Race Conditions

| Race | Risk | Mitigation |
|------|------|------------|
| Two reveals exhaust last credit | both succeed → quota = -1 | `SELECT FOR UPDATE` + check before decrement |
| Webhook arrives before campaign created | order issue | Persist campaign first, return 201 with id, THEN enqueue worker |
| Two ETL pipelines update same company | last write wins, data loss | UPSERT with `ON CONFLICT DO UPDATE WHERE updated_at > existing.updated_at` |
| Concurrent ICP uploads from same user | duplicate jobs | Idempotency by file hash + user_id |
| Quota reset cron + active reveal at midnight | reveal at 23:59:58 charges old quota | accept (rare; user benefits) |

## Testing Strategy

### Unit Tests
- **Coverage target:** 80% for `backend-api/`, 70% for `worker/`, 60% for `frontend/`
- **Critical paths (100% required):**
  - reveal_contact (all 5 scenarios + race)
  - quota_reset
  - yookassa_webhook handler
  - jwt token generation/validation
  - opt_out token verification
- **Tools:** pytest + pytest-asyncio + pytest-cov; vitest for frontend

### Integration Tests
- **Database:** testcontainers-python (Postgres + Redis), fixtures with realistic data
- **External APIs:** mock с respx (httpx mock)
- **Coverage:**
  - Auth flow (register → verify → login → access)
  - Reveal flow (search → reveal → CSV export)
  - Campaign flow (create → launch → status)
  - Billing flow (checkout → webhook → activate)
  - ETL flow (download → parse → upsert)

### E2E Tests
- **Tool:** Playwright
- **Critical journeys:**
  - User registers → upgrades to Pro → does reveal → exports CSV
  - User uploads ICP CSV → analyzes → creates campaign on look-alikes
  - User receives campaign → opt-out flow

### Performance Tests
- **Tool:** k6 / Locust
- **Scenarios:**
  - Search throughput: 100 RPS, p99 < 500ms
  - Reveal throughput: 50 RPS, p95 < 2s
  - Campaign send 5000 messages: complete < 30 min
- **Run:** weekly + before each release

### Security Tests
- **Static:** Bandit (Python), npm audit, eslint-plugin-security
- **Dynamic:** OWASP ZAP scan in CI on staging
- **Pen-test:** quarterly external (P1)

## Test Cases (Gherkin selection)

### Feature: Reveal with race protection

```gherkin
Feature: Concurrent reveal does not exceed quota

  Background:
    Given Marina has Pro plan with remaining_reveals = 1
      And company "7707083893" has 3 contacts

  Scenario: Two concurrent reveals on different companies
    When 2 reveals fire concurrently for inn "7707083893" and "7706107510"
    Then exactly 1 succeeds with 200
      And 1 fails with 402 QUOTA_EXCEEDED
      And remaining_reveals = 0
```

### Feature: Outreach quota mid-campaign exhaustion

```gherkin
Feature: Outreach quota exhaustion mid-campaign

  Background:
    Given Marina has Pro plan with remaining_outreach = 200
      And campaign "spring-launch" with audience of 300 contacts

  Scenario: Send first 200, skip remaining
    When campaign launches
    Then 200 messages sent
      And 100 messages marked status='skipped' error_code='QUOTA_EXCEEDED'
      And campaign.status = 'completed'
      And remaining_outreach = 0
      And user notified via in-app alert
```

### Feature: 30-day per-recipient cooldown

```gherkin
Feature: 30-day cooldown on Telegram contact

  Background:
    Given Marina sent message to @ivanov on 2026-04-01

  Scenario: Send to same recipient before cooldown
    Given today is 2026-04-25
    When Marina launches new campaign including @ivanov
    Then message to @ivanov has status='skipped' error_code='RECENTLY_CONTACTED'

  Scenario: Send to same recipient after cooldown
    Given today is 2026-05-15
    When Marina launches new campaign including @ivanov
    Then message to @ivanov is sent successfully
```

## Performance Optimizations

### Database
1. **Indexes:** composite (region, okved_main, revenue_range) for common filter combo
2. **Materialized views:** top-1000 viewed companies refreshed nightly
3. **Connection pool:** asyncpg pool_size=20, max_overflow=10
4. **Query optimization:** EXPLAIN ANALYZE on slow queries; partial indexes для opted_out=false
5. **VACUUM:** auto-vacuum tuned per table; manual VACUUM FULL раз в квартал

### Caching (Redis)
1. **Search results:** cache top-1000 popular query hashes (TTL 5 min)
2. **Company cards:** cache by inn (TTL 1 hour)
3. **User subscription:** cache by user_id (TTL 1 min, invalidate on update)
4. **OKVED reference:** static data, cache forever

### LLM
1. **Prompt caching:** identical (template + company context) → cache result (TTL 1 day)
2. **Batching:** для AI personalize в кампании 100+ — батчить по 5-10 в один LLM call
3. **Streaming:** для ICP summary — stream к UI для perceived speed

### Frontend
1. **React Query:** stale-while-revalidate, 5-min staleTime
2. **Code splitting:** dynamic import для /icp, /campaigns (heavy charts)
3. **Image optimization:** Next.js Image component, AVIF/WebP
4. **Bundle:** target < 200KB initial, < 1MB total
5. **CDN:** Cloudflare для статики (если доступно для РФ юрисдикции)

## Security Hardening

### Input Validation
- All endpoints have Pydantic schemas
- File uploads: max 10MB, MIME type whitelist (text/csv only для CSV)
- ИНН regex: `^\d{10,12}$`
- ОКВЭД regex: `^\d{2}\.\d{1,3}(\.\d{1,2})?$`

### Rate Limiting
- Global: 100 req/min per IP (Nginx)
- Per-endpoint: см. таблицу

| Endpoint | Limit |
|----------|-------|
| POST /auth/login | 5/min per IP, 10/min per email |
| POST /auth/register | 3/hour per IP |
| GET /companies | 60/min per user |
| POST /reveals | 30/min per user |
| POST /icp/analyze | 5/hour per user |
| POST /campaigns/:id/launch | 10/day per user |

### Audit Trail
- Все state-changing actions → audit_log
- Retention 3 года (закон 152-ФЗ + финразведка для billing)
- Партиции по месяцу, archive в MinIO после 6 мес

### Encryption
- TLS 1.3 only (disable 1.0/1.1/1.2)
- HSTS preload (max-age=63072000; includeSubDomains; preload)
- bcrypt(12) для паролей
- JWT signing key — rotate каждые 90 дней (поддержка 2 ключей одновременно)
- User API keys (LLM, TG bot tokens) — клиент-сайд only, AES-GCM-256 в IndexedDB

### CORS
- Whitelist: только `https://apollo-ru.example.com` и localhost для dev
- Credentials: include (для cookies)

### Content Security Policy
```
default-src 'self';
script-src 'self' 'sha256-...';
style-src 'self' 'unsafe-inline';
img-src 'self' data: https:;
connect-src 'self' https://api.yookassa.ru https://api.telegram.org;
frame-ancestors 'none';
```

## Accessibility (a11y)

- WCAG 2.1 AA target
- Semantic HTML (article, section, nav)
- ARIA labels на icons-only buttons
- Keyboard navigation: tab order, focus states
- Color contrast ≥ 4.5:1 для текста, 3:1 для UI
- Reduce motion: respect `prefers-reduced-motion`
- Screen reader test: NVDA + VoiceOver
- Forms: labels + error messages с aria-describedby

## Internationalization (P1)

- MVP: только русский UI
- Архитектура готова к i18n: `next-intl`, message catalogs
- API responses: errors human-readable in Russian by default; English on `?lang=en` (P1)

## Technical Debt Items (planned)

| Item | Why now (debt) | Future fix |
|------|----------------|------------|
| Search via PG FTS | сложит до 200K rows | Migrate to Elasticsearch when company count > 500K |
| Look-alike rule-based | не используем embeddings в MVP | Add pgvector ivfflat ANN index |
| Single VPS (no HA) | MVP cost-savings | Multi-region replica + automated failover |
| Manual ETL trigger | nightly cron | Stream-based ETL (CDC from open data sources) |
| In-memory rate limiter | работает per-instance | Redis-based для multi-replica |
| Single bot token для outreach | TG rate-limit единичная | Bot pool с round-robin |
| Sync LLM calls в request | плохой UX при медленном LLM | Move к async job + WebSocket update |

## Monitoring & Alerting Triggers

| Trigger | Severity | Action |
|---------|----------|--------|
| API p99 latency > 1s for 5 min | warning | Slack alert ops |
| Error rate > 1% for 5 min | critical | PagerDuty + Telegram alert |
| DB connection pool exhausted | critical | Page on-call, auto-restart API |
| Celery queue depth > 10K | warning | Slack |
| YandexGPT API errors > 10% | warning | Auto-fallback to OpenAI |
| Telegram bot blocked (>50 errors/h) | critical | Disable outreach + investigate |
| ЮKassa webhook signature fail | security | Block IP + alert |
| Disk usage > 80% | warning | Auto-archive audit_log to MinIO |
