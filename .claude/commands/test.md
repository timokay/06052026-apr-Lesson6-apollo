---
description: Run or generate tests. /test [scope] runs subset; /test all runs everything; /test generate [feature] generates tests from BDD scenarios.
---

# /test $ARGUMENTS

## Subcommands

| Usage | Action |
|-------|--------|
| `/test` | Run all tests (unit + integration + bdd) |
| `/test backend` | Backend only (pytest) |
| `/test frontend` | Frontend only (vitest) |
| `/test e2e` | Playwright E2E (требует staging environment) |
| `/test bdd` | BDD scenarios via pytest-bdd |
| `/test perf` | Performance tests via k6 |
| `/test security` | Security tests + bandit + npm audit |
| `/test coverage` | Coverage report |
| `/test generate <feature>` | Generate test stubs from `docs/features/<f>/test-scenarios.md` |
| `/test [path]` | Run specific test file/dir |

## Backend Tests (pytest)

```bash
cd backend-api

# All
pytest

# Specific
pytest tests/unit/test_reveal_service.py
pytest -k "reveal_concurrent"

# Coverage
pytest --cov=app --cov-report=html --cov-fail-under=80

# Excluding slow
pytest -m "not slow"
```

## Frontend Tests (vitest)

```bash
cd frontend

# All
npm test

# Watch mode
npm test -- --watch

# Coverage
npm test -- --coverage

# Specific file
npm test components/RevealButton.test.tsx
```

## BDD (pytest-bdd)

```bash
cd backend-api
pytest tests/bdd/
```

Features в `tests/bdd/features/`, step definitions в `tests/bdd/step_defs/`.

## E2E (Playwright)

```bash
cd e2e
npx playwright install --with-deps  # one-time
npx playwright test
npx playwright test --ui  # interactive mode
npx playwright test --debug  # debug single test
```

Requires staging environment running. Set `BASE_URL` env var.

## Performance (k6)

```bash
cd performance

# Local
k6 run search.k6.js

# Against staging (с auth token)
TEST_TOKEN=<jwt> k6 run --env BASE_URL=https://staging.apollo-ru.example.com search.k6.js
```

Thresholds defined in script (e.g., p99 < 500ms).

## Security

```bash
# Backend
cd backend-api
bandit -r app/                # Static security scan
pip-audit                     # Dependency vulnerabilities

# Frontend
cd frontend
npm audit --audit-level=high

# Dynamic (staging only)
docker run -t owasp/zap2docker-stable zap-baseline.py -t https://staging.apollo-ru.example.com
```

## Coverage Targets

| Layer | Min |
|-------|-----|
| Backend overall | 80% |
| Backend critical paths (auth, billing, reveal) | 100% |
| Frontend component | 60% |
| E2E happy paths | 100% covered |

CI will block merge если coverage пробивает threshold.

## Generate Tests From BDD

`/test generate <feature>` generates test stubs from BDD scenarios:

```
/test generate user-authentication

→ Reads docs/features/user-authentication/test-scenarios.md
→ Parses Gherkin scenarios
→ Generates:
   backend-api/tests/bdd/features/user-authentication.feature  (copy)
   backend-api/tests/bdd/step_defs/test_user_authentication.py (stubs)
   frontend/__tests__/user-authentication.test.tsx              (stubs)
```

Stubs have:
- All step functions defined с `@given`, `@when`, `@then` decorators
- TODO comments showing what to implement
- Imports already correct

## Output

```
═══════════════════════════════════════════════════════════════
🧪 TEST RUN — backend (pytest)

✅ Passed: 142
❌ Failed: 3
⏭️ Skipped: 5
📊 Coverage: 78% (target 80%)

Failures:
  tests/unit/test_reveal.py::test_concurrent — race condition
  tests/integration/test_billing.py::test_webhook_idempotency — flaky?
  tests/bdd/step_defs/test_reveal.py::test_recently_contacted — date arithmetic

Coverage gaps:
  app/services/icp.py: 45% (target 80%)
  app/integrations/yandexgpt.py: 32% (target 80%)

Next: /test backend tests/unit/test_reveal.py -v
═══════════════════════════════════════════════════════════════
```

## CI Integration

Tests run автоматически в `.github/workflows/ci.yml`:
- On PR: backend + frontend + bdd
- On push to develop: + e2e (staging deployment)
- Nightly: + perf + security
