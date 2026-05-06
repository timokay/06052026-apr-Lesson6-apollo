# Insights Capture — Apollo (RU)

> Knowledge base protocol. Capture gotchas, workarounds, and discoveries to prevent re-stepping on the same rakes.

## Architecture

```
myinsights/
├── 1nsights.md             # Index (alphabetic prefix '1' to sort first)
├── INS-001-<slug>.md       # Individual insight detail file
├── INS-002-<slug>.md
└── ...
```

Index format:

```markdown
# Insights Index

| ID | Title | Status | Hits | Tags |
|----|-------|--------|------|------|
| INS-001 | YooKassa webhook signature without trailing newline | Active | 3 | billing, webhook |
| INS-002 | Telegram FLOOD_WAIT requires sleep, not retry | Active | 7 | outreach |
| INS-003 | pg_trgm similarity threshold tuning | Workaround | 1 | search |
```

## Error-First Lookup Protocol

**Before debugging an error, ALWAYS:**

1. `grep -i "<error_message_substring>" myinsights/1nsights.md`
2. If match found → read that INS file → apply solution
3. If no match → debug normally → after fix → consider `/myinsights` to capture

This prevents 30-60 minutes of re-debugging known issues.

## When TO Suggest Capturing

Trigger conditions for `/myinsights`:

1. **Workaround for external API quirk** — vendor bug, undocumented behavior
   *Example:* ЮKassa webhook не возвращает `event.id` если payment_method = "embedded"

2. **Counter-intuitive performance fix** — something that wouldn't be obvious from code
   *Example:* `EXPLAIN ANALYZE` показал, что pg_trgm index не используется при `ILIKE` — нужен `%`

3. **Configuration gotcha** — env var, Docker setting, library config
   *Example:* uvicorn `--workers 4` ломает Celery beat, нужно `--workers 1` для beat container

4. **Behavior surprise** — что-то ведёт себя не так, как написано в документации
   *Example:* SQLAlchemy 2.0 `.scalars().all()` иногда возвращает None при пустом результате — лучше явно `.first()`

5. **Repeated debugging session** — если решение заняло >20 минут и можно повторить

## When NOT to Suggest

Don't trigger for:

1. **Trivial mistakes** — typos, missing imports
2. **Standard errors with obvious fixes** — "permission denied" → chmod
3. **One-off issues** — environment-specific (e.g., dev machine setup)
4. **Knowledge gap** — учиться newest framework feature, не "грабли"

## Insight File Format

```markdown
# INS-NNN: <Short Title>

**Status:** Active | Workaround | Obsolete
**Created:** YYYY-MM-DD
**Tags:** comma, separated

## Problem

<What error/behavior you encountered>

```error
Stack trace or error message verbatim
```

## Root Cause

<Why it happens, technical explanation>

## Solution

<Code snippet or steps>

```python
# Working approach
```

## Related

- Issue: #XXX (if any)
- Docs: docs/Refinement.md section Y
- Other insights: INS-NNN
```

## Lifecycle Status

| Status | Meaning |
|--------|---------|
| **Active** | Currently relevant, useful workaround |
| **Workaround** | Temporary fix, awaiting upstream resolution |
| **Obsolete** | Issue resolved by upstream/refactor — kept for history |

When marking Obsolete: add `## Obsolete` section с datestamp + reason.

## Hit Counter

Каждый раз, когда insight помог решить проблему — `/myinsights hit INS-NNN` инкрементирует counter.
Высокие hits → кандидаты для:
- Включения в основную документацию (Refinement.md)
- Добавления в `.claude/rules/` если это паттерн
- Создания automation/test чтобы предотвратить regression

## Index Maintenance

- Auto-numbering: highest INS-NNN + 1
- Tags: free-form, common ones tracked в индексе
- Sort: index сортируется alphabetically (поэтому prefix '1nsights')
- Search: `grep -i` по всем файлам или по индексу

## Auto-Commit

Stop hook в `.claude/settings.json` автоматически commit'ит изменения в `myinsights/` после каждой сессии:

```bash
git add myinsights/ && git commit -m "docs(insights): auto-capture from session"
```

Этот коммит делается Claude автоматически. Reviewer проверяет в PR.

## Apollo-Specific Tags (suggested)

- `billing` — ЮKassa, subscriptions, quotas
- `outreach` — Telegram bot, throttling, opt-out
- `search` — pg_trgm, FTS performance
- `llm` — YandexGPT/OpenAI quirks, prompt engineering
- `etl` — ЕГРЮЛ open data parsing, СПАРК API
- `auth` — JWT, OAuth, refresh rotation
- `compliance` — 152-ФЗ, opt-out, audit
- `db` — PostgreSQL, migrations, locking
- `infra` — Docker, nginx, deployment
- `frontend` — Next.js, React, Tailwind specific
