# PRD: Apollo (RU)

> Product Requirements Document. SPARC Phase 3.
> Source: `docs/product-discovery-brief.md` (Phase 0 output)

## 1. Vision

**Apollo (RU)** — B2B Sales Intelligence платформа для российского рынка. Аналог Apollo.io / ZoomInfo, но с фокусом на:
- Российские регистры (ЕГРЮЛ, ОКВЭД, e-disclosure)
- Поиск по ИНН и российским юрлицам
- Telegram-first outreach (под РФ-реальность)
- AI ICP look-alike на YandexGPT/OpenAI
- Соответствие 152-ФЗ

## 2. Personas

### P1: Marina — SDR в B2B SaaS компании (Primary, P0)
- 27 лет, Москва, 3 года в продажах
- KPI: 150 lead'ов в неделю, 30 встреч в месяц
- Pain: тратит 2-3 часа в день на ручной поиск контактов
- Цитата: «Гуглю по ИНН → СПАРК → корпоративный сайт → press@... — это не email ЛПР»

### P2: Дмитрий — Head of Marketing в IT-агентстве (P1)
- 35 лет, Санкт-Петербург, отвечает за лидген
- KPI: 50 SQL/мес, CAC <₽30K
- Pain: нужен ICP-анализ (look-alike по существующим клиентам)
- Цитата: «У меня 200 клиентов в amoCRM — хочу найти похожих в РФ. Нет инструмента»

### P3: Анна — M&A аналитик в инвест-фонде (P2)
- 31 год, Москва, скрин компаний для сделок
- Pain: ручная сборка списков по выручке/отрасли через 3-4 источника

## 3. Core User Stories (MVP)

### Epic 1: Search & Discovery

**US-1.1** — As Marina, I want to filter companies by ОКВЭД, region, employee_count, and revenue_range, so that I can build a target list in 5 minutes instead of 2 hours.

**US-1.2** — As Marina, I want to search by ИНН to instantly get full company card, so that I can verify a lead from CRM.

**US-1.3** — As Дмитрий, I want to upload a CSV of ИНН (existing customers) and get a look-alike list of similar companies via AI, so that I can find new prospects.

### Epic 2: Contact Reveal

**US-2.1** — As Marina, I want to click "Reveal" on a company and see contacts (email, phone, telegram) of decision makers (or relevant departments), so that I can reach out.

**US-2.2** — As Marina, I want my reveals to consume credits from my plan quota, so that I track my usage and stay within budget.

**US-2.3** — As Marina, I want to export selected companies + contacts to CSV, so that I can import them to my CRM (amoCRM/Bitrix24).

### Epic 3: Outreach (Telegram MVP)

**US-3.1** — As Marina, I want to create a Telegram outreach campaign with a template, so that I can send personalized messages to 50-200 contacts.

**US-3.2** — As Marina, I want AI to personalize each Telegram message based on the company's industry/size, so that messages don't look generic.

**US-3.3** — As Marina, I want to see open/reply stats per campaign, so that I can iterate on copy.

### Epic 4: Account & Billing

**US-4.1** — As Marina, I want to subscribe to Pro plan via ЮKassa/CloudPayments (₽9 990/мес), so that I get 2 000 reveals/month.

**US-4.2** — As Marina, I want to see my quota usage in dashboard, so that I know when I need to upgrade.

**US-4.3** — As Дмитрий (admin), I want to invite team members to Team plan, so that we share the seat pool.

### Epic 5: AI ICP Analyzer

**US-5.1** — As Дмитрий, I want to upload my customer CSV (≥20 ИНН), so that the system analyzes patterns (industry mix, size, region) and produces ICP profile.

**US-5.2** — As Дмитрий, I want to see suggested look-alike companies based on my ICP, so that I can target prospects most likely to convert.

## 4. MVP Feature Matrix

| Feature | Priority | Effort | Sprint |
|---------|----------|--------|--------|
| Auth (email + password) | P0 | S | 1 |
| Company search with filters | P0 | M | 1-2 |
| Company card view | P0 | S | 2 |
| Contact reveal + credits | P0 | M | 2-3 |
| CSV export | P0 | S | 3 |
| Billing (ЮKassa) | P0 | M | 3 |
| Tier-based quotas | P0 | S | 3 |
| Telegram outreach (templates) | P0 | M | 4 |
| LLM personalization | P0 | M | 4 |
| AI ICP analyzer | P0 | L | 5 |
| Look-alike suggestions | P0 | M | 5 |
| Team seats (Team tier) | P1 | M | 6 |
| Email outreach | P1 | M | 7+ |
| amoCRM/Bitrix24 export | P1 | L | 7+ |
| SSO/SAML | P2 | L | post-MVP |
| Mobile app | P2 | XL | post-MVP |

## 5. Non-Functional Requirements

### Performance
- Search response < 500ms (p99) for filter queries against ≤100K companies
- Contact reveal < 2s (p95)
- LLM personalization < 5s per message
- AI ICP analysis < 30s for 100 companies

### Scalability
- Database: 1M+ companies, 5M+ contacts (Phase 2 target)
- Concurrent users: 500 (MVP), 5 000 (post-MVP)

### Security
- 152-ФЗ compliance: только публичные данные, opt-out flow, audit log
- Encrypted secrets in IndexedDB (AES-GCM 256, PBKDF2)
- Никаких API-ключей пользователя на бэкенде
- TLS 1.3, HSTS
- Rate limiting (100 req/min per user)

### Availability
- Uptime 99.5% (MVP), 99.9% (Post-MVP)
- Backup: daily snapshots, point-in-time recovery

### Legal/Compliance
- Регистрация в Реестре операторов ПДн (Роскомнадзор)
- Privacy Policy, Terms of Service на русском
- Согласие пользователя на обработку ПДн при регистрации
- Opt-out для контактов в outreach campaigns

## 6. Success Metrics

| Metric | Target Y1 Q4 | How to measure |
|--------|--------------|----------------|
| Paying customers | 300 | Stripe/ЮKassa dashboard |
| ARR | ₽25M | sum(active subscriptions) |
| Activation rate (Free → reveal first contact) | ≥40% | event tracking |
| Free → Paid conversion | ≥8% | cohort analysis |
| Monthly churn | ≤7% | Stripe data |
| NPS | ≥40 | quarterly survey |
| Contact reveal accuracy | ≥85% | manual sampling |

## 7. Out of Scope (v1)

- ❌ Mobile native apps (web responsive only)
- ❌ SSO/SAML (Email+password + OAuth Google в P1)
- ❌ Госконтракты, арбитражные дела (Phase 3)
- ❌ Email outreach (Phase 2 — Telegram first)
- ❌ Звонки/Power Dialer
- ❌ English UI (RU only до подтверждения PMF)
- ❌ White-label

## 8. Constraints

```yaml
architecture:
  pattern: Distributed Monolith (Monorepo)
  containers: Docker + Docker Compose
  infrastructure: VPS (AdminVPS / HOSTKEY)
  deploy: Docker Compose direct deploy via SSH/CI

tech_constraints:
  - Российский хостинг (закон о хранении ПДн на территории РФ)
  - LLM провайдер: предпочтительно YandexGPT (рос. compliance), fallback OpenAI
  - Telegram: Bot API (не MTProto, чтобы избежать проблем с TG API limits)
  - Платежи: ЮKassa или CloudPayments (российский эквайринг)

team:
  size_mvp: 4-6 человек (1 PM, 2 BE, 2 FE, 1 ML/Data)
  duration_mvp: 4-5 месяцев (5 спринтов по 2 недели + 1 sprint stabilization)
  budget_mvp: ~₽15-20M (включая инфру + LLM API)
```

## 9. Risks (Top 5)

| # | Risk | Probability | Impact | Mitigation |
|---|------|-------------|--------|------------|
| 1 | 152-ФЗ ужесточение запретит outreach | M | H | Pivot на enrichment-only, юр-аудит на старте |
| 2 | Telegram заблокирует bot за массовую рассылку | H | H | Rate-limit per recipient, opt-in flow, fallback на email |
| 3 | СПАРК/Контур запустят свой outreach | M | H | Скорость + AI ICP моат + community |
| 4 | СПАРК API дорогой, open data неполные | H | M | Hybrid: ЕГРЮЛ open data + парсинг + user-uploaded |
| 5 | LLM цены вырастут / OpenAI заблокируют | L | M | YandexGPT primary, локальные модели в перспективе |

## 10. Open Questions (для Phase 2 валидации)

1. ✋ Юридическая возможность Telegram-outreach по 152-ФЗ — нужна консультация
2. ✋ Pricing: ₽9 990 vs ₽4 990 за Pro — A/B на лендинге
3. ✋ Free tier: открыть reveals (рискованно для unit economics) или search-only
4. ✋ Source data: starter contract со СПАРК (₽1-3M/год) или начать с rusprofile парсинга

## 11. References

- Phase 0 brief: `docs/product-discovery-brief.md`
- Seed data: `docs/uploads/.../companies.csv`, `contacts.csv` (25 строк)
- Inspiration: https://apollo.io, https://zoominfo.com
- Russian competitors: rusprofile.ru, kontur.ru/focus, kontur.ru/compass
