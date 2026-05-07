---
name: project-context
description: Apollo (RU) domain knowledge — terminology, business rules, российский B2B sales context, regulatory landscape (152-ФЗ), 25-row seed dataset. Auto-loaded when working с companies, contacts, reveals, outreach, ICP, billing.
version: "1.0"
maturity: production
---

# Apollo (RU) Project Context

## What This Skill Provides

Domain knowledge для разработчика и Claude Code, чтобы:
- Не спрашивать «что такое ОКВЭД?» каждый раз
- Понимать российский B2B sales context
- Соответствовать 152-ФЗ из коробки
- Использовать seed dataset правильно

## Core Domain Concepts

### Companies

**ИНН** (Идентификационный номер налогоплательщика):
- 10 цифр для юрлиц (LLC/АО/etc.)
- 12 цифр для ИП (individual entrepreneurs)
- **Уникальный** идентификатор в системе. Primary key для companies table.
- Validation regex: `^\d{10}$|^\d{12}$`
- **Никогда не number** — leading zeros важны (например, `0123456789`)

**ОКВЭД** (Общероссийский классификатор видов экономической деятельности):
- Формат: `XX.XX[.XX]` — например, `62.01` (Разработка ПО), `64.19` (Денежное посредничество)
- Иерархический: `62` — общий, `62.01` — конкретнее, `62.01.1` — ещё конкретнее
- Search via prefix-match: фильтр `62` matches `62.01`, `62.02.1`
- Reference: справочник ОКВЭД (статичный, обновляется редко) — храним в DB

**Юр.форма** (legal form):
- ПАО, АО, ООО, ИП, ГУП, ГК, etc.
- Часто в name: "ПАО Сбербанк", "ООО Яндекс"
- Не отдельное поле в MVP — извлекается из name при необходимости

**Регионы РФ:** 89 субъектов федерации (на 2026, включая ДНР, ЛНР, Херсон, Запорожье с 2022).

**Revenue ranges (enum):**
- `<10M` — до 10 млн ₽/год
- `10M-50M`
- `50M-100M`
- `100M-500M`
- `500M-1B`
- `1B-10B`
- `10B+` — топ компании

### Contacts

**Типы контактов:**
- `Пресс-служба` — публичный контакт, обычно generic email (press@, media@)
- `IR-Service` (Investor Relations) — для инвесторов, ir@
- `Департамент по связям с инвесторами` — то же
- Личный контакт ЛПР (Лицо Принимающее Решения) — самое ценное, но сложнее найти

**Telegram username:**
- Формат: `@username` или `username` (без @)
- Normalization: всегда strip leading `@`
- `@ivanov` и `ivanov` — одно и то же

**Confidence levels:**
- `high` — verified из 2+ публичных источников
- `medium` — 1 источник, но reputable
- `low` — есть, но требует verification

### Data Sources

| Source | URL | What it provides | Cost |
|--------|-----|------------------|------|
| **ЕГРЮЛ open data** | https://egrul.nalog.ru | Все юрлица: ИНН, name, address, директор, ОКВЭД | Free, weekly bulk |
| **rusprofile.ru** | https://rusprofile.ru | Карточка компании, контакты | Free, scraping (grey area) |
| **e-disclosure.ru** | https://www.e-disclosure.ru | Отчётность ПАО (annual reports, IR) | Free |
| **СПАРК-Интерфакс** | spark-interfax.ru | Полная база, кредитные риски, связи | ₽30-100K+/мес |
| **Контур.Фокус** | kontur.ru/focus | Карточки компаний | ₽15-40K/мес |
| **Контур.Компас** | kontur.ru/compass | Lead-gen, контакты ЛПР | ₽20-50K/мес |
| **Smart-lab.ru** | smart-lab.ru | Финданные публичных компаний | Free |

### Regulatory Landscape

**152-ФЗ** (О персональных данных):
- Обязательная регистрация в Реестре операторов ПДн (Роскомнадзор)
- Хранение ПДн на серверах в РФ (наш HOSTKEY VPS)
- Согласие на обработку ПДн (явное, отзываемое)
- Право на удаление аккаунта (30 дней)
- Audit log retention 3 года
- **Только публичные данные о компаниях** в Apollo — никаких personal records

**Реклама и outreach:**
- 38-ФЗ «О рекламе» — для cold outreach к юрлицам менее строго чем для физ.лиц
- Telegram outreach — серая зона, нужна юр-консультация
- Email outreach без предварительного согласия — риск спам-жалоб → бан IP

### Outreach Norms

**Telegram-first в РФ:**
- LinkedIn заблокирован → освободилась ниша B2B контактов
- Telegram — де-факто канал B2B-коммуникации
- Norm: ≤ 1 message / recipient / 30 дней (Apollo enforces)

**Email outreach (P1):**
- Требует opt-in или legitimate interest
- Footer обязательно: opt-out link с HMAC token

## Business Rules

### Reveal Logic

1. User clicks "Reveal contacts" на company card
2. Atomic check: `remaining_credits > 0`?
3. Already revealed by this user? → return cached, no charge
4. Check: contacts non-empty (исключая opted_out)? Empty → no charge, return []
5. Decrement credit, log audit, return contacts

### Quota Reset

- 1-го числа каждого месяца, 00:00 МСК
- Celery Beat triggers `billing.reset_quotas`
- ЮKassa auto-charge для активных подписок
- Failed payment → status="past_due" → 7 дней grace → downgrade to Free

### Outreach Cooldown

- 30 дней per recipient, **across all user's campaigns**
- Calculated from `sent_at` of last successful (status='sent') message
- Skipped messages не блокируют (можно retry)

### ICP Look-alike Algorithm (MVP rule-based)

```
score(candidate) = 
  0.4 * industry_overlap(candidate.okved, ICP.industry_distribution) +
  0.3 * size_overlap(candidate.employee_count, ICP.size_distribution) +
  0.2 * region_overlap(candidate.region, ICP.region_distribution) +
  0.1 * revenue_overlap(candidate.revenue_range, ICP.revenue_distribution)

return top-100 by score, filtered: candidate.inn NOT IN ICP.uploaded_inns
```

P2: vector embeddings via pg_vector ANN search.

## Personas (см. PRD.md для детали)

- **Marina** (P0) — SDR в B2B SaaS компании. Делает 150 leads/неделю.
- **Дмитрий** (P1) — Head of Marketing, demand gen. ICP analysis.
- **Анна** (P2) — M&A аналитик. Скрин компаний для сделок.

## Tier Pricing (см. Specification FR-7.1)

| Tier | Price/мес | Reveals | Outreach | Seats |
|------|-----------|---------|----------|-------|
| Free | 0 | 25 | 0 | 1 |
| Starter | ₽2 990 | 500 | 200 | 1 |
| Pro | ₽9 990 | 2 000 | 1 000 | 3 |
| Team | ₽29 990 | 10 000 | 5 000 | 10 |
| Enterprise | from ₽99K | unlimited | unlimited | unlimited |

## Seed Dataset

`docs/uploads/.../companies.csv` (25 rows) и `contacts.csv` (25 rows):

**25 топ российских ПАО:**
Сбербанк, Газпром, Роснефть, Лукойл, Норникель, Новатэк, Татнефть, Сургутнефтегаз, Алроса, НЛМК, Северсталь, ММК, РУСАЛ, Ростелеком, МТС, МегаФон, Яндекс, VK, Магнит, Ozon (Интернет Решения), РЖД, Аэрофлот, Интер РАО, Россети, Росатом.

Все confidence=high, источники в `Источники и ограничения датасета.md`.

Используется для:
- Initial DB seed (`/start` Phase 3.4)
- Demo для investors
- E2E test fixtures

## Common Gotchas

- **ИНН с leading zeros** — никогда не trim (some valid ИНН start with 0)
- **Кириллический name search** — pg_trgm работает, но ILIKE не использует index. Use `%` operator с similarity.
- **ОКВЭД prefix match** — LIKE `62%` matches `62.01`, `62.02.1` — но также `620.x` (если есть). Use regex `^62(\.|$)`.
- **Пробелы в username Telegram** — normalize to handle: strip whitespace, lowercase
- **Пустые контакты** — некоторые компании имеют только generic press@ — это OK, но reveal accuracy будет ниже

## Linked Documents

- `docs/PRD.md` — product requirements
- `docs/Architecture.md` — system design
- `docs/Specification.md` — detailed requirements
- `docs/ADR.md` — architecture decisions
- `.claude/rules/security.md` — security policies
- `.claude/rules/secrets-management.md` — secrets management
- `.claude/skills/coding-standards/SKILL.md` — code style
- `.claude/skills/testing-patterns/SKILL.md` — test patterns
