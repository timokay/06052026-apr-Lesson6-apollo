# Testing Rules — Apollo (RU)

> Mandatory test discipline. Source: `docs/Refinement.md` Section "Testing Strategy", `docs/test-scenarios.md` (65 BDD scenarios).

## Coverage Gates (CI blocks merge if below)

| Layer | Min |
|-------|-----|
| Backend overall | 80% |
| Backend critical paths (auth, billing, reveal, audit, opt-out) | **100%** |
| Frontend component | 60% |
| E2E happy paths covered | 100% |

## Mandatory Tests for Every Feature

When `/feature` Phase 3 (IMPLEMENT) writes code, tests must include:

- [ ] **Happy path** — feature works as designed
- [ ] **Validation errors** — invalid input → 4xx с правильным error code
- [ ] **Auth check** — endpoint требует valid auth (если не публичный)
- [ ] **Authorization** — user A не может access resource user B
- [ ] **Quota check** — если billing-related, exhausted quota → 402
- [ ] **Idempotency** — повторный запрос не дублирует side effects
- [ ] **Concurrent** — race conditions на shared resource (см. reveal pattern)
- [ ] **External API failure** — LLM/TG/YK down → graceful degradation
- [ ] **Audit log** — critical action записан в audit_log

## Test Style

- pytest fixtures для shared setup (см. `.claude/skills/testing-patterns/SKILL.md`)
- testcontainers-python для integration tests (real Postgres/Redis)
- respx для mocking external APIs (LLM, TG, YK)
- Factories (`factory-boy`) для test data — не hardcoded dicts
- freezegun для time-dependent tests (quota reset, cooldown)
- `@pytest.mark.slow` для tests > 1s (skip в default CI)
- `@pytest.mark.security` для security tests (отдельный CI job)

## Forbidden in Tests

- ❌ Real external API calls (use respx mocks)
- ❌ `time.sleep()` — use freezegun
- ❌ Tests without rollback (must be independent)
- ❌ Hardcoded UUIDs / dates (use factories or `freeze_time`)
- ❌ Tests dependent on order (sort/randomize)

## CI Test Stages

```yaml
stages:
  - lint              # ruff + mypy + eslint
  - unit              # pytest -m "not slow" + vitest
  - integration       # pytest tests/integration/
  - bdd               # pytest tests/bdd/
  - security          # bandit + npm audit + pytest -m security
  - e2e               # playwright (только develop branch)
  - perf              # k6 (nightly)
```

Каждый stage блокирует следующий при failure.

## Pre-commit Local Tests

Минимум перед commit:
```bash
# Backend
cd backend-api && pytest -m "not slow" -x

# Frontend (если изменения)
cd frontend && npm test -- --run --bail
```

При hot fix urgent — допустимо commit без local tests, **но CI должен пройти** до push в main.

## Test Data Discipline

- **Real ИНН в tests:** разрешено для seed dataset (25 публичных компаний). Не использовать персональные ИНН в публичных fixtures.
- **Email в tests:** только `*@test.example.com` или `*@example.local` (RFC 6761 reserved)
- **Phone в tests:** `+1-555-0100` диапазон (NANP test numbers)
- **Telegram в tests:** `@test_*` префикс

## Performance Test Thresholds

| Endpoint | p99 target | Sample |
|----------|-----------|--------|
| GET /companies (search) | < 500ms | 100 RPS, 1 min |
| POST /reveals | < 2s | 50 RPS, 1 min |
| POST /icp/analyze | < 30s | 5 RPS, 5 min |

CI запускает k6 еженедельно. Regression > 20% blocks deploy в production.

## Security Test Mandatory

Each `/feature` Phase 4 (REVIEW) включает security-reviewer agent. He проверяет:
- Auth bypass attempts
- SQL injection
- XSS (если есть user-input HTML)
- CSRF
- Rate limit bypass
- Sensitive data в logs

См. `docs/test-scenarios.md` Section "Security Test Scenarios".

## Critical Path Coverage Matrix

| Path | Tests required (min) |
|------|---------------------|
| **Auth (FR-1)** | 10 (register, login, token refresh, password reset, verify, brute force, token theft, weak pass, duplicate email, missing PDN) |
| **Reveal (FR-3)** | 9 (happy, no credits, repeat, opted-out, no contacts, expired sub, race condition, concurrent, audit logged) |
| **Billing (FR-7)** | 9 (upgrade, quota reset, failed payment, webhook missing sig, webhook invalid sig, prorated, downgrade, idempotency, refund) |
| **Outreach (FR-6)** | 10 (happy, AI personalize, opt-out skip, cooldown skip, blocked-bot, FLOOD_WAIT, quota mid-campaign, cancel, cyrillic, unicode emoji) |
| **Audit (FR-8)** | 6 (reveal logged, login logged, retention, mask PII, archive, partition rotation) |

Эти tests **должны быть** в каждом релизе. Если coverage пробит — release halt.

## Reference

- `.claude/skills/testing-patterns/SKILL.md` — patterns + code examples
- `docs/test-scenarios.md` — 65 BDD scenarios
- `docs/Refinement.md` — edge cases + testing strategy
