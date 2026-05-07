# Development Guide — Apollo (RU)

> Step-by-step guide: setup → develop → test → deploy.

## Prerequisites

- **OS:** Linux / macOS / WSL2 (Windows native не поддерживается)
- **Docker:** 24+, Docker Compose v2
- **Python:** 3.12 (для local backend dev без Docker)
- **Node.js:** 22+ (для local frontend dev)
- **Git:** 2.40+
- **Claude Code:** установлен (CLI или web)

## First-Time Setup

### 1. Clone & branch

```bash
git clone https://github.com/timokay/06052026-apr-Lesson6-apollo.git
cd 06052026-apr-Lesson6-apollo
git checkout claude/init-p-replicator-23CcQ  # или main после merge
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — заполнить значения (см. .claude/rules/secrets-management.md)
```

Минимум для local dev:
- `DATABASE_URL` — local Postgres
- `JWT_SECRET_CURRENT` — `openssl rand -hex 32`
- `YOOKASSA_*`, `TELEGRAM_BOT_TOKEN`, `YANDEXGPT_API_KEY` — testkeys (или dummy для unit tests)

### 3. Bootstrap project

```bash
# Через Claude Code:
/start

# Or manually:
docker compose up -d postgres redis minio
docker compose run --rm backend-api alembic upgrade head
docker compose run --rm backend-api python -m app.scripts.seed_plans
docker compose run --rm backend-api python -m app.scripts.seed_companies docs/uploads/.../companies.csv
docker compose up -d
```

### 4. Verify

```bash
curl http://localhost:8000/health              # API
curl http://localhost:3000/                    # Frontend
docker compose ps                              # All services healthy
```

## Daily Development Workflow

### Start session

В Claude Code:
```
/next                    # See what's recommended
/next status             # See full roadmap
```

SessionStart hook автоматически inject'нет sprint progress + recent activity.

### Implement feature

**Recommended (autonomous):**
```
/go user-auth            # auto-pick /plan or /feature
```

**Manual (granular control):**
```
/feature user-auth       # full SPARC lifecycle (Plan → Validate → Implement → Review)
```

**Quick task (≤3 files):**
```
/plan add-favicon        # lightweight plan в docs/plans/
```

### Run tests

```
/test                    # Run all
/test backend            # Backend only
/test bdd                # BDD scenarios
/test coverage           # Coverage report
```

### Deploy

```
/deploy staging          # Deploy current branch к staging
/deploy production       # Deploy main к prod (требует confirmation)
```

### Capture learnings

При обнаружении grabель:
```
/myinsights "Telegram FLOOD_WAIT requires sleep, не retry"
```

Stop hook auto-commit'нет в `myinsights/`.

## Architecture Quick Reference

См. `CLAUDE.md` + `docs/Architecture.md`.

```
backend-api/    FastAPI + Python 3.12 (REST API)
worker/         Celery 5 (async tasks: outreach, ICP, ETL)
etl/            Python (data ingestion)
frontend/       Next.js 14 (App Router, TS)
nginx/          Reverse proxy + TLS
postgres/       PG 16 + pg_trgm + pg_vector
redis/          Cache + broker
minio/          S3-compatible object storage
monitoring/     Prometheus + Grafana + Loki
```

## Available Commands

| Command | Purpose |
|---------|---------|
| `/start` | Bootstrap project (DB, migrations, seed) |
| `/run` / `/run mvp` | Autonomous build loop (P0 features) |
| `/run all` | Build all features (P0+P1+P2) |
| `/next` | What feature to work on next |
| `/go [feature]` | Smart pipeline picker (/plan or /feature) |
| `/feature [name]` | Full SPARC lifecycle |
| `/plan [task]` | Lightweight plan |
| `/test [scope]` | Run tests |
| `/deploy [env]` | Deploy to staging/production |
| `/myinsights` | Capture insights |
| `/docs` | Generate user/admin docs |
| `/harvest` | Extract reusable knowledge |

## Available Agents (`.claude/agents/`)

- **planner** — feature decomposition, dependency analysis
- **architect** — system design, ADR drafting
- **code-reviewer** — brutal-honesty pre-merge review

Invoke via `Task` tool с `subagent_type` parameter.

## Available Skills (`.claude/skills/`)

Apollo-specific (auto-loaded):
- `project-context` — domain knowledge (ИНН, ОКВЭД, 152-ФЗ, etc.)
- `coding-standards` — Python/TS patterns
- `testing-patterns` — pytest/playwright/k6
- `feature-navigator` — roadmap navigation
- `security-patterns` — encrypted IndexedDB, JWT, HMAC

Generic (from p-replicator init):
- `sparc-prd-mini`, `requirements-validator`, `brutal-honesty-review`
- `explore`, `goap-research-ed25519`, `problem-solver-enhanced`
- `cc-toolkit-generator-enhanced`, `knowledge-extractor`, `pipeline-forge`
- `reverse-engineering-unicorn`

## Available Rules (`.claude/rules/`)

- `security.md` — auth, encryption, OWASP, 152-ФЗ
- `coding-style.md` — Python + TS + SQL patterns
- `secrets-management.md` — env vars, secret rotation
- `git-workflow.md` — commit format, branches, PRs
- `feature-lifecycle.md` — 4-phase /feature protocol
- `insights-capture.md` — knowledge base protocol
- `testing.md` — coverage gates, mandatory tests

## Database

### Migrations (Alembic)

```bash
# Create
docker compose run --rm backend-api alembic revision --autogenerate -m "description"

# Apply
docker compose run --rm backend-api alembic upgrade head

# Rollback (только если migration reversible)
docker compose run --rm backend-api alembic downgrade -1

# Show current
docker compose run --rm backend-api alembic current
```

**Forward-compatible migrations only** (см. ADR-012):
- New columns NULLABLE или с DEFAULT
- New indexes CONCURRENTLY
- 2-phase для column removal (deploy code → drop column)

### Schema

См. `docs/Architecture.md` Section 5.1 (10 tables).

## Testing

### Backend
```bash
cd backend-api
pytest                            # All
pytest -m "not slow"              # Skip slow
pytest --cov=app --cov-fail-under=80
pytest tests/unit/test_reveal.py -v
```

### Frontend
```bash
cd frontend
npm test
npm test -- --watch
npm test -- --coverage
```

### BDD
```bash
cd backend-api
pytest tests/bdd/                 # 65 scenarios from docs/test-scenarios.md
```

### E2E (staging)
```bash
cd e2e
BASE_URL=https://staging.apollo-ru.example.com npx playwright test
```

См. `.claude/skills/testing-patterns/SKILL.md` для patterns.

## Deployment

### Staging (auto on push to develop)

GitHub Actions → build images → push to ghcr.io → SSH deploy → smoke tests → notify Slack.

### Production (auto on push to main)

Same flow, но требует:
- Manual confirmation в `/deploy production`
- DB backup в last 24h
- Tag в semver: `git tag v1.2.3`

См. `docs/Completion.md` для full runbook.

## Troubleshooting

### Common Issues

| Error | Solution |
|-------|----------|
| `pg_trgm extension не доступен` | Verify `pgvector/pgvector:pg16` image (not plain postgres) |
| `alembic не находит models` | Check `alembic/env.py` import paths |
| `JWT_SECRET missing` | Generate: `openssl rand -hex 32` → add to `.env` |
| `Health check timeout в /start` | `docker compose logs backend-api` |
| `Migration FAIL` | Если safe: `alembic downgrade base` → fix migration → re-run |
| `Telegram bot не отвечает` | Verify `TELEGRAM_BOT_TOKEN` valid (`/getMe` API call) |
| `YooKassa webhook 401` | Verify `YOOKASSA_WEBHOOK_SECRET` matches dashboard config |

### Knowledge Base

Сначала grep в `myinsights/1nsights.md` — может уже решено:
```bash
grep -ri "<error keyword>" myinsights/
```

Если нет → debug → `/myinsights` для capture.

## Performance Targets

| Endpoint | p99 |
|----------|-----|
| Search | 500ms |
| Reveal | 2s |
| ICP analysis | 30s |

Если miss target — `/feature` Phase 4 review-performance agent flag'нет.

## Security Mandatory Checks

Перед merge:
- [ ] Нет hardcoded secrets (`detect-secrets` pre-commit)
- [ ] Все user input validated (Pydantic schemas)
- [ ] SQL parametrized only
- [ ] Auth check на endpoint
- [ ] Rate limit configured
- [ ] Audit log для critical actions
- [ ] Logs не содержат PII / secrets
- [ ] CORS не expanded без причины
- [ ] Tests cover auth/authz scenarios

См. `.claude/rules/security.md` Section "Code Review Security Checklist".

## Resources

| Resource | Path |
|----------|------|
| Project context | `CLAUDE.md` |
| Architecture | `docs/Architecture.md` |
| C4 diagrams | `docs/C4_Diagrams.md` |
| ADRs | `docs/ADR.md` |
| User stories + Gherkin AC | `docs/Specification.md` |
| Algorithms | `docs/Pseudocode.md` |
| Edge cases + testing | `docs/Refinement.md` |
| Deployment runbooks | `docs/Completion.md` |
| 65 BDD scenarios | `docs/test-scenarios.md` |
| Validation report | `docs/validation-report.md` |
| Roadmap | `.claude/feature-roadmap.json` |

## Getting Help

- Read `CLAUDE.md` first (project overview)
- Check `myinsights/` for known gotchas
- Use `@architect` agent для design decisions
- Use `/feature` для structured implementation
- Capture new learnings via `/myinsights`
