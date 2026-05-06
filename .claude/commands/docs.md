---
description: Generate bilingual documentation (RU/EN) for Apollo. Creates user guide, admin guide, API reference, deployment guide, troubleshooting.
---

# /docs $ARGUMENTS

## Subcommands

| Usage | Action |
|-------|--------|
| `/docs` | Generate both RU + EN |
| `/docs rus` | Russian only |
| `/docs eng` | English only |
| `/docs update` | Update existing docs (incremental) |
| `/docs api` | Regenerate OpenAPI spec only |
| `/docs admin` | Admin guide only |
| `/docs user` | End-user guide only |

## Output Structure

```
README/
├── ru/
│   ├── README.md                 # Главная (продукт обзор)
│   ├── user-guide.md             # Руководство пользователя
│   ├── admin-guide.md            # Руководство администратора
│   ├── api-reference.md          # Из OpenAPI spec
│   ├── deployment-guide.md       # Деплой на VPS
│   ├── troubleshooting.md        # Распространённые проблемы
│   ├── faq.md                    # Часто задаваемые вопросы
│   └── changelog.md              # История изменений
├── en/
│   └── (mirror structure)
└── images/
    └── (screenshots, diagrams)
```

## Generation Process

### Step 1: Collect Source Material

```python
sources = {
    "PRD": "docs/PRD.md",
    "Architecture": "docs/Architecture.md",
    "Specification": "docs/Specification.md",
    "API contracts": "docs/Pseudocode.md (API section)",
    "Deployment": "docs/Completion.md",
    "Test scenarios": "docs/test-scenarios.md (для examples)",
    "OpenAPI": "backend-api/openapi.json (auto-generated)",
}
```

### Step 2: Generate User Guide

Sections:
1. **Welcome** — что такое Apollo, для кого
2. **Getting Started** — registration, first reveal, first campaign
3. **Search & Filters** — как использовать filters
4. **Reveal Contacts** — credit system, что значит quota
5. **CSV Export** — формат, ограничения
6. **AI ICP Analyzer** — upload CSV → look-alike (Pro+)
7. **Telegram Outreach** — campaign creation, opt-out, cooldown
8. **Billing & Plans** — tiers, upgrade, downgrade, cancel
9. **Settings** — profile, API keys (BYOK), team members (Team+)
10. **Privacy & Security** — 152-ФЗ, наша политика
11. **Best Practices** — outreach tips, ICP recommendations

### Step 3: Generate Admin Guide

Sections:
1. **System Requirements** — VPS specs, Docker version
2. **Installation** — `/start` command details
3. **Configuration** — `.env` variables explained
4. **User Management** — admin panel, suspend/delete users
5. **Subscription Management** — manual quota grants, refunds
6. **Monitoring** — Grafana dashboards, alert thresholds
7. **Backups** — backup strategy, restore procedure
8. **Security** — secret rotation, audit log access
9. **Compliance** — 152-ФЗ checklist, audit log retention
10. **Scaling** — when to scale, how (read replica, multi-replica API)
11. **Troubleshooting** — runbooks из `docs/Completion.md`

### Step 4: Generate API Reference

```bash
# Auto-generate from OpenAPI
docker compose exec backend-api python -c "
from app.main import app
import json
with open('openapi.json', 'w') as f:
    json.dump(app.openapi(), f, indent=2)
"

# Convert OpenAPI → Markdown
npx @redocly/cli build-docs openapi.json -o README/ru/api-reference.html
# или используем openapi-to-md tool
```

Sections (auto-generated):
- All endpoints с request/response schemas
- Authentication
- Error codes
- Rate limits
- Examples (Python, JavaScript, curl)
- Webhooks (ЮKassa)

### Step 5: Generate Deployment Guide

Из `docs/Completion.md` — extract sections:
- Pre-deployment checklist
- Initial deployment (Day 0)
- Routine deployment
- Rollback procedure
- Database migrations
- CI/CD configuration
- Monitoring setup

### Step 6: Generate Troubleshooting

Sources:
- `myinsights/` (если есть)
- Runbooks из `docs/Completion.md`
- Common error codes из `docs/Pseudocode.md`

Format:
```markdown
## Проблема: 402 QUOTA_EXCEEDED при reveal

**Симптомы:** "Лимит исчерпан" modal на UI.

**Причина:** Текущая subscription quota исчерпана для текущего billing period.

**Решение:**
1. Upgrade plan: Settings → Billing → выбрать tier
2. Дождаться нового billing period (1-го числа месяца)
3. Если admin: manual grant через `/admin/users/<id>/grant-credits`

**Связано:** [INS-005] Edge case: subscription mid-period upgrade
```

### Step 7: Translation (English)

Use LLM с our prompt:
```
Translate the following Russian Apollo (RU) documentation to English.
Preserve technical terms, code blocks, file paths verbatim.
Use professional B2B SaaS tone.
Keep markdown structure identical.
```

Manual review: каждая EN страница должна быть прочитана native-speaking reviewer.

## Update Mode (`/docs update`)

```
1. Detect changed source docs since last `/docs` run (git diff vs last docs commit)
2. Re-generate only affected pages
3. Update changelog
4. Mark "last updated" timestamp на каждой странице
```

## OpenAPI Auto-Refresh

Add to CI:
```yaml
- name: Update API docs
  if: contains(github.event.head_commit.modified, 'backend-api/app/routers/')
  run: |
    docker compose exec backend-api python -m app.scripts.export_openapi
    /docs api
```

## Output

```
═══════════════════════════════════════════════════════════════
📚 DOCS GENERATED

Russian (8 pages):
  ✅ README/ru/README.md             (1500 words)
  ✅ README/ru/user-guide.md         (4200 words)
  ✅ README/ru/admin-guide.md        (3800 words)
  ✅ README/ru/api-reference.md      (auto from OpenAPI, 156 endpoints)
  ✅ README/ru/deployment-guide.md   (2100 words)
  ✅ README/ru/troubleshooting.md    (1900 words, 23 issues covered)
  ✅ README/ru/faq.md                (800 words, 18 Qs)
  ✅ README/ru/changelog.md          (auto from git log)

English (mirror): 8 pages translated, ~14000 words total

🚀 Suggested next:
  • Review EN translations с native speaker
  • Add screenshots to README/images/
  • Publish: GitHub Pages / docs.apollo-ru.example.com
═══════════════════════════════════════════════════════════════
```

## Manual Review Required

LLM-translated EN docs **must** be reviewed by:
- Native English speaker (для tone)
- Technical reviewer (для accuracy)

Mark в frontmatter:
```yaml
---
last_updated: 2026-05-06
translation_status: machine | reviewed | native
reviewer: <name>
---
```

## Anti-patterns

❌ Auto-generate без human review для public-facing docs
❌ Outdated screenshots (verify все skrinshots при `/docs update`)
❌ Mixing English и Russian в same page
❌ Linking к internal `docs/` files (used internal references should not leak в user docs)

## Related

- `docs/PRD.md`, `docs/Specification.md` — source material
- `docs/Completion.md` — runbooks, deployment
- `myinsights/` — troubleshooting source
- `backend-api/openapi.json` — API spec source
