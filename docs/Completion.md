# Completion: Apollo (RU)

> SPARC Phase 7 output. Deployment, CI/CD, monitoring, runbooks.

## Pre-Deployment Checklist

### Code & Tests
- [ ] All unit tests passing (CI green)
- [ ] Integration tests passing
- [ ] E2E smoke tests passing on staging
- [ ] Code review approved (≥1 reviewer)
- [ ] No `TODO`/`FIXME`/`HACK` без issue ссылки
- [ ] Bandit / npm audit / OWASP ZAP — no high/critical issues

### Documentation
- [ ] CHANGELOG.md updated
- [ ] API docs (OpenAPI) regenerated
- [ ] Runbook updated for new components
- [ ] Privacy Policy / Terms reviewed by юрист (для major releases)

### Configuration
- [ ] All `.env` variables в production secrets manager
- [ ] Database migration tested на staging
- [ ] Feature flags configured (если используются)
- [ ] Rate limit thresholds reviewed

### Infrastructure
- [ ] DB backup completed within last 24h
- [ ] Disk usage < 80%
- [ ] Monitoring/alerting verified
- [ ] Rollback plan documented and tested

## Deployment Architecture (production)

```
GitHub Actions (CI/CD)
       │
       │ on push main:
       │  1. lint + test + type-check
       │  2. build Docker images (multi-stage)
       │  3. push to ghcr.io with tag (commit SHA + 'latest')
       │  4. SSH deploy to VPS
       │
       ▼
HOSTKEY VPS (Russia)
├── docker compose pull
├── docker compose up -d --no-deps backend-api worker frontend
├── docker compose exec backend-api alembic upgrade head
└── healthcheck loop (max 60s) → если fail → rollback
```

## Deployment Sequence

### Initial (Day 0)

```bash
# 1. Provision VPS (HOSTKEY)
ssh root@<vps-ip>

# 2. Install Docker + docker-compose
curl -fsSL https://get.docker.com | sh
apt install docker-compose-plugin

# 3. Set up directory structure
mkdir -p /opt/apollo/{config,data,logs,backups}
cd /opt/apollo

# 4. Pull repository (read-only deploy key)
git clone --branch main git@github.com:timokay/06052026-apr-Lesson6-apollo.git .

# 5. Configure environment
cp .env.example .env
# Edit .env with production secrets (DB password, JWT secret, API keys)

# 6. Initial database setup
docker compose pull
docker compose up -d postgres redis
docker compose exec postgres psql -U apollo -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
docker compose exec postgres psql -U apollo -c "CREATE EXTENSION IF NOT EXISTS vector;"
docker compose run --rm backend-api alembic upgrade head

# 7. Seed initial data (companies + plans + admin user)
docker compose run --rm backend-api python -m app.scripts.seed_plans
docker compose run --rm backend-api python -m app.scripts.seed_companies docs/uploads/.../companies.csv
docker compose run --rm backend-api python -m app.scripts.create_admin --email admin@apollo-ru.example.com

# 8. Start all services
docker compose up -d

# 9. Get SSL certificate
docker compose run --rm certbot certonly --webroot -w /var/www/certbot \
  -d apollo-ru.example.com --email ops@apollo-ru.example.com --agree-tos

# 10. Reload nginx
docker compose exec nginx nginx -s reload

# 11. Verify
curl -k https://apollo-ru.example.com/api/v1/health
# Expected: {"status":"ok","version":"x.y.z"}
```

### Routine (per release)

```bash
# CI/CD автоматически выполняет:

# 1. Build & push images
docker buildx build --platform linux/amd64 -t ghcr.io/.../apollo-api:$SHA ./backend-api
docker push ghcr.io/.../apollo-api:$SHA

# 2. SSH deploy
ssh deploy@<vps-ip> << 'EOF'
  cd /opt/apollo
  git fetch && git checkout $SHA
  docker compose pull
  
  # Run migrations (zero-downtime: only forward-compatible)
  docker compose run --rm backend-api alembic upgrade head
  
  # Rolling restart
  docker compose up -d --no-deps backend-api worker
  
  # Wait for healthy
  for i in {1..60}; do
    curl -sf http://localhost:8000/health && break
    sleep 1
  done
  
  # Frontend (Next.js — restart needed for new bundle)
  docker compose up -d --no-deps frontend
EOF

# 3. Smoke tests (from CI runner)
curl -f https://apollo-ru.example.com/health
curl -f https://apollo-ru.example.com/api/v1/health
# (more critical endpoints...)

# 4. Notify Slack/TG channel
```

## Rollback Procedure

```bash
# Method 1: Image tag rollback (preferred)
ssh deploy@<vps-ip>
cd /opt/apollo
docker compose pull # pulls 'latest' OR specific previous SHA
git checkout <previous-sha>
docker compose up -d --no-deps backend-api worker frontend

# Method 2: Database rollback (если миграция вызвала issues)
docker compose exec backend-api alembic downgrade -1
# WARNING: only if migration was reversible

# Method 3: Full DB restore (worst case)
docker compose stop postgres
docker run --rm -v apollo_postgres_data:/var/lib/postgresql/data \
  -v /opt/apollo/backups:/backups \
  postgres:16 bash -c "rm -rf /var/lib/postgresql/data/* && pg_restore -d apollo -U apollo /backups/<latest>.dump"
docker compose start postgres
```

## CI/CD Configuration

### `.github/workflows/ci.yml` (PR checks)

```yaml
name: CI

on:
  pull_request:
    branches: [main]

jobs:
  backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env: { POSTGRES_PASSWORD: test }
        ports: ['5432:5432']
      redis:
        image: redis:7
        ports: ['6379:6379']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - name: Install dependencies
        run: cd backend-api && pip install -r requirements-dev.txt
      - name: Lint
        run: cd backend-api && ruff check . && black --check .
      - name: Type check
        run: cd backend-api && mypy app/
      - name: Test
        run: cd backend-api && pytest --cov=app --cov-fail-under=80
      - name: Security scan
        run: cd backend-api && bandit -r app/

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '22' }
      - run: cd frontend && npm ci
      - run: cd frontend && npm run lint
      - run: cd frontend && npm run typecheck
      - run: cd frontend && npm test -- --run
      - run: cd frontend && npm audit --audit-level=high

  e2e:
    needs: [backend, frontend]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker compose -f docker-compose.test.yml up -d
      - run: cd e2e && npx playwright install --with-deps && npm test
```

### `.github/workflows/deploy-prod.yml`

```yaml
name: Deploy Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions: { contents: read, packages: write }
    steps:
      - uses: actions/checkout@v4
      
      - name: Login to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Build & push images
        run: |
          for svc in backend-api worker frontend etl; do
            docker buildx build --platform linux/amd64 \
              -t ghcr.io/${{ github.repository }}/$svc:${{ github.sha }} \
              -t ghcr.io/${{ github.repository }}/$svc:latest \
              --push ./$svc
          done
      
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.PROD_HOST }}
          username: deploy
          key: ${{ secrets.PROD_SSH_KEY }}
          script: |
            cd /opt/apollo
            git fetch && git checkout ${{ github.sha }}
            docker compose pull
            docker compose run --rm backend-api alembic upgrade head
            docker compose up -d --no-deps backend-api worker frontend
            
            # Health check
            for i in {1..60}; do
              if curl -sf http://localhost:8000/health > /dev/null; then exit 0; fi
              sleep 1
            done
            echo "Health check failed, rolling back"
            git checkout HEAD~1
            docker compose pull
            docker compose up -d --no-deps backend-api worker frontend
            exit 1
      
      - name: Notify
        if: always()
        run: |
          curl -X POST ${{ secrets.SLACK_WEBHOOK }} \
            -d '{"text":"Deploy ${{ github.sha }}: ${{ job.status }}"}'
```

### `.github/workflows/nightly.yml`

```yaml
name: Nightly Jobs

on:
  schedule:
    - cron: '0 2 * * *'  # 02:00 UTC = 05:00 MSK

jobs:
  etl:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger ETL
        run: |
          ssh deploy@${{ secrets.PROD_HOST }} \
            "docker compose exec -T worker celery -A app.celery call etl.refresh_companies"
  
  backup:
    runs-on: ubuntu-latest
    steps:
      - name: PG Dump to S3
        run: |
          ssh deploy@${{ secrets.PROD_HOST }} \
            "docker compose exec -T postgres pg_dump -Fc apollo > /opt/apollo/backups/apollo-$(date +%F).dump"
          # Sync to remote backup (HOSTKEY S3 / Yandex Object Storage)
```

## Database Migrations

### Strategy
- **Forward-compatible only:** новые миграции должны быть совместимы со старым кодом (rolling deploy)
- **Adding column:** ALWAYS NULLABLE or with DEFAULT (no schema lock)
- **Removing column:** 2-phase: (1) deploy code, который не использует, (2) migration drop column
- **Renaming:** 3-phase: add new + dual-write + drop old
- **Adding index:** CREATE INDEX CONCURRENTLY на больших таблицах

### Tools
- **Alembic** для версионирования миграций
- Migration runs автоматически в deploy script
- Lock timeout 5 sec для DDL (если timeout — fail deploy)

### Rollback
- Каждая миграция должна быть **reversible** (downgrade)
- Тестируется на staging perед merge в main

## Monitoring & Alerting

### Key Metrics

| Metric | Source | Threshold | Alert channel |
|--------|--------|-----------|---------------|
| API request rate | FastAPI middleware → Prometheus | baseline ±50% | Grafana |
| API latency p99 | Prometheus histogram | > 1s for 5 min | PagerDuty + TG |
| API error rate (5xx) | Prometheus counter | > 1% for 5 min | PagerDuty + TG |
| DB connection pool usage | SQLAlchemy stats → Prometheus | > 90% | Slack |
| Celery queue depth | Celery exporter | > 10K | Slack |
| Celery task failure rate | Celery events | > 5% | Slack |
| Disk usage | node_exporter | > 80% | Slack |
| RAM usage | node_exporter | > 90% | Slack |
| YandexGPT API errors | App-level metric | > 10% in 10 min | Slack + auto-fallback |
| Telegram bot errors | App-level metric | > 50 errors/h | Slack |
| ЮKassa webhook signature fails | App-level metric | any | Security alert |
| Reveal accuracy (manual sample) | Quarterly review | < 80% | Slack |

### Dashboards (Grafana)

1. **Overview** — request rate, error rate, latency p50/95/99
2. **Business** — DAU, signups, paid conversions, ARR, churn
3. **Quality** — search/reveal/outreach success rates
4. **Infrastructure** — CPU, RAM, disk, network per container
5. **Database** — connections, slow queries, table sizes, vacuum stats
6. **External APIs** — YandexGPT, OpenAI, Telegram, ЮKassa response times и errors

### Alerting Rules (Alertmanager)

```yaml
groups:
  - name: critical
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.01
        for: 5m
        labels: { severity: critical }
        annotations: { summary: "Error rate > 1%" }
      
      - alert: APILatencyHigh
        expr: histogram_quantile(0.99, http_request_duration_seconds_bucket) > 1
        for: 5m
        labels: { severity: warning }
      
      - alert: DBPoolExhausted
        expr: db_pool_used / db_pool_size > 0.9
        for: 2m
        labels: { severity: critical }
```

## Logging Strategy

### Levels
- `DEBUG` — Disabled in production
- `INFO` — Request/response, key events (login, reveal, campaign launch)
- `WARN` — Recoverable issues (LLM fallback, rate limit hit)
- `ERROR` — Unrecoverable for current request, retry triggered
- `CRITICAL` — System-level (DB unavailable, OOM)

### Format (structured JSON)

```json
{
  "timestamp": "2026-05-06T16:00:00.123Z",
  "level": "INFO",
  "service": "backend-api",
  "request_id": "uuid",
  "user_id": "uuid",
  "method": "POST",
  "path": "/api/v1/reveals",
  "status": 200,
  "duration_ms": 145,
  "extra": { "company_inn": "7707083893", "credits_used": 1 }
}
```

### Retention

| Log type | Retention | Storage |
|----------|-----------|---------|
| Application logs | 30 days hot, 1 year cold | Loki + MinIO archive |
| Audit log | 3 years | PostgreSQL partitioned + MinIO (>6 mo) |
| Access logs (Nginx) | 90 days | Loki |

### Sensitive Data

- **NEVER log:** passwords, JWTs, ЮKassa secrets, user-API keys
- **Mask:** email (m***@example.com), phone (+7***1234), ИНН (770708****)
- **PII handling:** access logs for ПДн → restricted role for ops

## Handoff Checklists

### For Development Team
- [ ] Repository access granted (write to `develop`, read to `main`)
- [ ] Development environment setup guide tested (`README.md` + `DEVELOPMENT_GUIDE.md`)
- [ ] Local docker-compose comes up clean
- [ ] Sample data seeded
- [ ] Code review guidelines reviewed
- [ ] Branching strategy: `main` (prod), `develop` (staging), feature branches
- [ ] Pre-commit hooks installed (lint, format, secrets scan)

### For QA Team
- [ ] Staging environment access (`staging.apollo-ru.example.com`)
- [ ] Test user accounts (Free, Starter, Pro, Team)
- [ ] Test data: 10K companies, 30K contacts in staging DB
- [ ] Test ЮKassa account in sandbox mode
- [ ] Test Telegram bot (separate token from prod)
- [ ] Test plan with regression scenarios
- [ ] Bug reporting: GitHub Issues with template

### For Operations Team
- [ ] Production VPS access (SSH key + 2FA)
- [ ] Grafana/Prometheus dashboards reviewed
- [ ] Runbook for common incidents (см. ниже)
- [ ] On-call rotation schedule (PagerDuty)
- [ ] Backup/restore procedure tested
- [ ] DR (disaster recovery) plan документирован
- [ ] Vendor escalation contacts: HOSTKEY (host), ЮKassa (билинг), Yandex (LLM)

### For Marketing/Sales Team
- [ ] Admin panel access (read-only Grafana business dashboard)
- [ ] Customer support tooling (доступ к user list, manual quota grant)
- [ ] Email templates (welcome, payment-failed, plan-renewed)
- [ ] FAQ / Knowledge base (см. /docs)

## Runbooks (top 5 incidents)

### R1: API down (5xx errors > 50%)

1. Check `https://status-page` (or Grafana Overview)
2. SSH to VPS: `docker compose ps` — все ли up?
3. Logs: `docker compose logs -f backend-api --tail=200`
4. Common причины:
   - DB unreachable → check postgres container
   - OOM → check `docker stats`, restart `backend-api`
   - Bad deploy → rollback (см. Rollback Procedure)
5. Acknowledge incident in PagerDuty
6. Post-mortem within 48h

### R2: ЮKassa webhook failures

1. Check audit_log: `SELECT * FROM audit_log WHERE action='yookassa_webhook' ORDER BY created_at DESC LIMIT 50`
2. Verify HMAC signature config (`.env` `YOOKASSA_SECRET_KEY`)
3. Check ЮKassa dashboard: any pending payments?
4. Manual reconciliation: запустить `python -m app.scripts.yookassa_reconcile --since 24h`

### R3: Telegram bot rate-limited

1. Check `campaign_messages` errored count
2. If FLOOD_WAIT: pause all running campaigns, wait timeout
3. Reduce throttle (5/sec → 2/sec) and resume
4. Long-term: provision second bot, round-robin

### R4: Database disk full

1. Free up immediately: `docker compose exec postgres psql -U apollo -c "VACUUM FULL audit_log;"`
2. Archive old partitions: `python -m app.scripts.archive_audit_log --before 6mo`
3. If still full: scale up VPS storage (HOSTKEY support, ~30 min downtime)

### R5: LLM API quota exceeded (YandexGPT)

1. Check Grafana: YandexGPT errors → quota
2. Auto-fallback to OpenAI should kick in (verify in logs)
3. If both unavailable: disable `ai_personalize` flag globally → templates only
4. Notify users via in-app banner

## Compliance Checklist (152-ФЗ)

- [x] Регистрация в Реестре операторов ПДн (Роскомнадзор)
- [x] Privacy Policy опубликована на /privacy
- [x] Terms of Service на /terms
- [x] Согласие на обработку ПДн при регистрации
- [x] Хранение ПДн на серверах в РФ (HOSTKEY)
- [x] Право на удаление аккаунта реализовано
- [x] Audit log retention 3 года
- [x] Opt-out flow для контактов в outreach
- [x] Только публичные данные о компаниях
- [x] Pen-test раз в год (post-MVP)
- [x] Назначен ответственный за обработку ПДн (DPO)

## Post-Launch Activities (Day 1-30)

- Day 1-3: Hyper-monitoring, daily standups, hotfix queue
- Day 7: Retro первой недели, top-3 issues prioritization
- Day 14: First customer interviews (5-10 calls)
- Day 30: First metrics review (DAU, conversion, NPS), pivot decisions

## Definition of "Done" for the Project

- [ ] All P0 features deployed to production
- [ ] Smoke + integration + E2E tests passing
- [ ] Monitoring dashboards green for 7 days straight
- [ ] First 10 paying customers onboarded
- [ ] Customer support workflow documented
- [ ] Founder/PM sign-off
