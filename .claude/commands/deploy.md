---
description: Deploy Apollo to staging or production. Handles pre-flight checks, image build, migration, smoke tests, rollback on failure.
---

# /deploy $ARGUMENTS

## Subcommands

| Usage | Action |
|-------|--------|
| `/deploy staging` | Deploy current branch к staging |
| `/deploy production` | Deploy `main` branch к production (требует confirmation) |
| `/deploy rollback staging` | Rollback staging к previous version |
| `/deploy status [env]` | Show current deployed version + health |

## Pre-flight Checklist

Auto-checked before deploy:
- [ ] Branch tests passing (CI green)
- [ ] No uncommitted local changes
- [ ] Tag/commit specified
- [ ] Required secrets present in `.env.<env>`
- [ ] Database backup completed within last 24h (production only)
- [ ] No production maintenance window blocking
- [ ] Disk usage < 80%

## Staging Deploy

```bash
# 1. Verify branch
git status
CURRENT_SHA=$(git rev-parse HEAD)

# 2. Build images (if not cached)
docker buildx build --platform linux/amd64 \
  -t ghcr.io/timokay/06052026-apr-lesson6-apollo/backend-api:$CURRENT_SHA \
  --push ./backend-api

# (parallel for all services: backend-api, worker, frontend, etl)

# 3. SSH deploy
ssh deploy@staging-vps << EOF
  cd /opt/apollo-staging
  git fetch && git checkout $CURRENT_SHA
  docker compose pull
  
  # Migrations
  docker compose run --rm backend-api alembic upgrade head
  
  # Rolling restart (preserve user sessions)
  docker compose up -d --no-deps backend-api worker
  sleep 10
  docker compose up -d --no-deps frontend
EOF

# 4. Smoke tests
curl -fsS https://staging.apollo-ru.example.com/api/v1/health
curl -fsS https://staging.apollo-ru.example.com/health

# 5. E2E tests against staging
cd e2e && BASE_URL=https://staging.apollo-ru.example.com npx playwright test --project=smoke

# 6. Notify Slack
curl -X POST $SLACK_WEBHOOK -d "{\"text\":\"✅ Deployed $CURRENT_SHA to staging\"}"
```

## Production Deploy

**Requires confirmation:**
```
⚠️ PRODUCTION DEPLOY

Current production: <SHA>  (deployed: 2 days ago)
Will deploy:        <NEW_SHA>  (commits since: 12)

Changes:
  feat(reveals): add concurrent reveal protection
  fix(billing): handle expired card in past_due flow
  ...

Database migrations:
  20260506_120000_add_indexes  (CREATE INDEX CONCURRENTLY — non-blocking)

Estimated downtime: 0s (rolling deploy)

Confirm? Type "DEPLOY PRODUCTION" to proceed.
```

After confirmation:

```bash
# 1. Set maintenance flag (info banner only — no actual downtime)
ssh deploy@prod-vps "touch /opt/apollo/maintenance.flag"

# 2. Backup BEFORE migration
ssh deploy@prod-vps << EOF
  cd /opt/apollo
  docker compose exec -T postgres pg_dump -Fc apollo > /opt/apollo/backups/pre-deploy-$(date +%F-%H%M).dump
EOF

# 3. Deploy
ssh deploy@prod-vps << EOF
  cd /opt/apollo
  git fetch && git checkout main
  docker compose pull
  
  # Migration в отдельном контейнере (не affects running)
  docker compose run --rm backend-api alembic upgrade head
  
  # Rolling
  docker compose up -d --no-deps backend-api worker
  
  # Health check loop (max 60s)
  for i in {1..60}; do
    if curl -sf http://localhost:8000/health > /dev/null; then
      echo "Healthy after \${i}s"
      break
    fi
    sleep 1
  done
  
  # Frontend
  docker compose up -d --no-deps frontend
EOF

# 4. Remove maintenance flag
ssh deploy@prod-vps "rm /opt/apollo/maintenance.flag"

# 5. Smoke tests
for endpoint in /api/v1/health /health /api/v1/companies?page=1; do
  curl -fsS "https://apollo-ru.example.com$endpoint" || ALERT
done

# 6. Notify
curl -X POST $SLACK_WEBHOOK -d "..."
```

## Rollback Procedure

```bash
/deploy rollback staging

# Internal:
ssh deploy@staging-vps << EOF
  cd /opt/apollo-staging
  PREV_SHA=$(git log --oneline -2 main | tail -1 | awk '{print $1}')
  git checkout $PREV_SHA
  docker compose pull
  
  # If migration was made — downgrade
  CURRENT_REV=$(docker compose exec backend-api alembic current --short)
  PREV_REV=<previous>  # from git history
  if [ "$CURRENT_REV" != "$PREV_REV" ]; then
    docker compose run --rm backend-api alembic downgrade $PREV_REV
  fi
  
  docker compose up -d --no-deps backend-api worker frontend
EOF
```

## Worst Case: Database Restore

```bash
# Only when DB corruption или non-reversible migration broke things
ssh deploy@prod-vps << EOF
  cd /opt/apollo
  docker compose stop backend-api worker
  docker compose exec postgres pg_restore -d apollo -U apollo --clean /opt/apollo/backups/pre-deploy-<timestamp>.dump
  docker compose start backend-api worker
EOF
```

⚠️ Это потеряет все данные после backup. Только в emergency.

## Status Command

```
/deploy status production

═══════════════════════════════════════════════════════════════
🚀 DEPLOY STATUS — production

Current SHA: abc123def (deployed: 2 days ago)
Build: ghcr.io/.../apollo-api:abc123def
Health: ✅ 200 OK (latency: 45ms)
Uptime: 2d 5h
Last migration: 20260504_113000

Services:
  ✅ nginx       (running, 3d uptime)
  ✅ frontend    (running)
  ✅ backend-api (running, 2 replicas healthy)
  ✅ worker      (running, queue depth: 23)
  ✅ postgres    (running, 156 connections)
  ✅ redis       (running, memory: 1.4GB / 2GB)

Recent metrics:
  RPS: 47 (avg)
  p99 latency: 287ms
  Error rate: 0.02%

Next deploy candidate: <SHA> (12 commits ahead)
═══════════════════════════════════════════════════════════════
```

## Forbidden

- `/deploy production` без CI green
- `/deploy production` без backup в last 24h
- `/deploy production` от feature branch (только main)
- Skip migration testing на staging до production
- `--force` flag — не существует, всегда есть rollback path

## Related

- `docs/Completion.md` — full deployment runbook
- `.github/workflows/deploy-prod.yml` — GitHub Actions automation
- `.claude/rules/git-workflow.md` — branching strategy
