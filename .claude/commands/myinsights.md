---
description: Capture and manage development insights (gotchas, workarounds, discoveries) into knowledge base.
---

# /myinsights $ARGUMENTS

## Purpose

Захватить «грабли» в knowledge base, чтобы повторно на них не наступать. Используется при:
- Обнаружении workaround для external API quirk
- Counter-intuitive performance fix
- Configuration gotcha
- Поведение, отличающееся от документации
- Solution занявшее >20 минут debugging

## Subcommands

| Usage | Action |
|-------|--------|
| `/myinsights <description>` | Create new insight |
| `/myinsights status` | Show all insights with status |
| `/myinsights archive INS-NNN` | Mark insight as Obsolete |
| `/myinsights hit INS-NNN` | Increment hit counter (when reused) |
| `/myinsights search <keyword>` | Grep all insights |

## Step 0: Duplicate Detection

```bash
# Search index for similar
grep -i "<keywords from description>" myinsights/1nsights.md
```

If match found:
- Show existing insight
- Ask: "Это та же проблема? Update existing OR создать новый?"

## Step 1: Information Collection

Prompt user (или extract from context):

| Field | Description |
|-------|-------------|
| **Title** | Короткое название (≤80 chars) |
| **Tags** | Comma-separated (см. список в `.claude/rules/insights-capture.md`) |
| **Problem** | Что произошло, какая ошибка/поведение |
| **Root cause** | Почему происходит (если understood) |
| **Solution** | Working код или steps |
| **Status** | Active / Workaround / Obsolete |
| **Related** | Issue #, docs section, other insights |

## Step 2: Create Detail File

Auto-number: highest existing INS-NNN + 1.

File: `myinsights/INS-{NNN}-{slug}.md`

Template:
```markdown
# INS-{NNN}: {Title}

**Status:** {Status}
**Created:** {YYYY-MM-DD}
**Tags:** {tags}
**Hits:** 0

## Problem

{description}

```error
{stack trace или error verbatim}
```

## Root Cause

{technical explanation}

## Solution

{steps or code snippet}

```{language}
{working code}
```

## Related

- Issue: #{xxx}
- Docs: {file_path}
- Other insights: INS-NNN
```

## Step 3: Update Index

File: `myinsights/1nsights.md`

Append row to table:
```markdown
| INS-{NNN} | {Title} | {Status} | 0 | {tags} |
```

## Step 4: Auto-commit (via Stop hook)

Stop hook в `.claude/settings.json` автоматически commit'ит изменения в `myinsights/`:

```bash
git add myinsights/ && git commit -m "docs(insights): INS-{NNN} {short_title}"
```

## Subcommand: `/myinsights status`

Output:
```
═══════════════════════════════════════════════════════════════
📚 INSIGHTS STATUS

Total: 12
  • Active:    8
  • Workaround: 3
  • Obsolete:  1

Top hits (most reused):
  INS-002 (7 hits) — Telegram FLOOD_WAIT requires sleep, not retry
  INS-005 (5 hits) — pgvector ivfflat probes parameter
  INS-008 (4 hits) — ЮKassa webhook idempotency by event.id

By tag:
  billing: 3, outreach: 4, search: 2, llm: 3
═══════════════════════════════════════════════════════════════
```

## Subcommand: `/myinsights archive INS-NNN`

1. Update file `myinsights/INS-NNN-*.md`:
   - Change status: `Obsolete`
   - Add section:
     ```markdown
     ## Obsolete (YYYY-MM-DD)
     
     {reason — например: "Resolved by upgrading SQLAlchemy to 2.0.30"}
     ```
2. Update index: change status column to `Obsolete`
3. Commit

## Subcommand: `/myinsights hit INS-NNN`

1. Increment Hits counter в file и index
2. Commit (silent, no message в chat — чтобы не отвлекать)

Используется автоматически когда insight применён для решения проблемы. Высокие hits → кандидат для:
- Включения в основную доку (`docs/Refinement.md`)
- Создания automation/test
- Promotion в `.claude/rules/`

## Search

```bash
/myinsights search webhook
```

Greps по всем файлам insights:
```bash
grep -ri "webhook" myinsights/
```

Возвращает matched lines с context.

## Apollo-Specific Examples

### Example 1: Telegram throttling

```
/myinsights "Telegram FLOOD_WAIT 60s requires sleep, не retry. Retry без sleep усугубляет."
Tags: outreach, telegram
```

### Example 2: pg_trgm gotcha

```
/myinsights "pg_trgm ILIKE не использует GIN index. Нужно % operator с similarity threshold."
Tags: search, db, performance
```

### Example 3: ЮKassa webhook

```
/myinsights "ЮKassa отправляет webhook 5 раз с одним event.id. Нужна idempotency."
Tags: billing, webhook
```

## Architecture

```
myinsights/
├── 1nsights.md              # Index (sorted alphabetically by '1' prefix)
├── INS-001-yookassa-webhook-no-trailing-newline.md
├── INS-002-telegram-flood-wait.md
├── INS-003-pg-trgm-similarity-threshold.md
└── ...
```

См. `.claude/rules/insights-capture.md` для полного протокола.

## Error-First Lookup Reminder

**Before debugging an error, ALWAYS:**
```bash
grep -i "<error_substring>" myinsights/1nsights.md
```

Это сэкономит 30-60 минут на already-solved проблемах.
