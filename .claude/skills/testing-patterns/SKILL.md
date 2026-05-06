---
name: testing-patterns
description: Testing patterns для Apollo (RU) — pytest + pytest-asyncio (backend), pytest-bdd (Gherkin), Vitest (frontend), Playwright (E2E), k6 (load), respx (mocks), testcontainers. Auto-loaded при написании тестов.
version: "1.0"
maturity: production
---

# Apollo (RU) Testing Patterns

## Coverage Targets

| Layer | Target | Critical paths |
|-------|--------|----------------|
| Backend unit | ≥80% | auth, billing, reveal, audit — 100% |
| Backend integration | ≥60% | All API endpoints |
| Frontend component | ≥60% | Forms, critical flows |
| E2E | Happy paths covered | Register → upgrade → reveal → export |
| Performance | All endpoints с NFR | Search 100 RPS, Reveal 50 RPS |
| Security | OWASP Top 10 | Quarterly OWASP ZAP |

## Backend Testing Stack

```
pytest                  # Test runner
pytest-asyncio          # async support
pytest-bdd              # Gherkin scenarios
pytest-cov              # Coverage
testcontainers-python   # Real Postgres/Redis в integration tests
respx                   # httpx mocking (LLM/Telegram/YK)
factory-boy             # Test data factories
freezegun               # Time freezing
```

## Test Organization

```
backend-api/tests/
├── conftest.py             # Top-level fixtures
├── unit/
│   ├── test_auth_service.py
│   ├── test_reveal_service.py
│   └── ...
├── integration/
│   ├── conftest.py         # Test DB fixtures
│   ├── test_api_auth.py    # Real HTTP via TestClient
│   ├── test_api_reveals.py
│   └── ...
├── bdd/
│   ├── conftest.py
│   ├── features/           # .feature files (Gherkin)
│   │   ├── reveal.feature
│   │   ├── outreach.feature
│   │   └── billing.feature
│   └── step_defs/
│       ├── test_reveal.py
│       └── ...
├── performance/
│   ├── locustfile.py
│   └── k6_scripts/
└── mocks/
    ├── yandexgpt.py
    ├── telegram.py
    └── yookassa.py
```

## Patterns

### 1. conftest.py (top-level fixtures)

```python
# backend-api/tests/conftest.py
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from testcontainers.postgres import PostgresContainer
from app.database import Base
from app.models import *  # noqa

@pytest.fixture(scope="session")
def event_loop():
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def postgres_container():
    with PostgresContainer("pgvector/pgvector:pg16") as pg:
        yield pg

@pytest_asyncio.fixture(scope="session")
async def engine(postgres_container):
    url = postgres_container.get_connection_url().replace(
        "postgresql://", "postgresql+asyncpg://"
    )
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def session(engine):
    async with AsyncSession(engine) as s:
        yield s
        await s.rollback()
```

### 2. Unit Test (Service)

```python
# backend-api/tests/unit/test_reveal_service.py
import pytest
from unittest.mock import AsyncMock
from app.services.reveal import RevealService
from app.exceptions import QuotaExceeded

@pytest.mark.asyncio
async def test_reveal_with_quota():
    user_repo = AsyncMock()
    sub_repo = AsyncMock()
    contact_repo = AsyncMock()

    sub_repo.get_active.return_value = AsyncMock(
        remaining_reveals=10, plan_code="pro"
    )
    contact_repo.get_for_company.return_value = [
        AsyncMock(id=1, email="x@y.z"),
    ]

    service = RevealService(sub_repo=sub_repo, contact_repo=contact_repo, ...)
    contacts = await service.reveal(user_id="u1", company_inn="7707083893")

    assert len(contacts) == 1
    sub_repo.decrement_quota.assert_called_once()

@pytest.mark.asyncio
async def test_reveal_quota_exceeded():
    sub_repo = AsyncMock()
    sub_repo.get_active.return_value = AsyncMock(remaining_reveals=0, plan_code="free")
    contact_repo = AsyncMock()
    
    service = RevealService(sub_repo=sub_repo, contact_repo=contact_repo, ...)
    with pytest.raises(QuotaExceeded) as exc:
        await service.reveal(user_id="u1", company_inn="7707083893")
    assert exc.value.code == "QUOTA_EXCEEDED"
```

### 3. Integration Test (API)

```python
# backend-api/tests/integration/test_api_reveals.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_reveal_endpoint(session, seed_user, seed_company):
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Login
        login = await client.post("/auth/login", json={"email": "test@x.com", "password": "Pass1234"})
        access_token = login.cookies["access_token"]

        # Reveal
        resp = await client.post(
            "/reveals",
            json={"company_inn": "7707083893"},
            cookies={"access_token": access_token},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["company_inn"] == "7707083893"
        assert "contacts" in body
        assert body["remaining_credits"] < 100

@pytest.mark.asyncio
async def test_reveal_concurrent_quota(session, seed_user_remaining_1, seed_companies_2):
    """Concurrent reveals при remaining=1: только один проходит."""
    # ... use asyncio.gather to fire 2 reveals simultaneously
    # ... assert 1 succeeds with 200, 1 fails with 402
```

### 4. BDD Test (pytest-bdd)

`reveal.feature`:
```gherkin
Feature: Contact Reveal

  Scenario: Successful reveal with credits
    Given Marina has Pro plan with remaining_reveals = 100
    And company "7707083893" has 3 contacts
    When she clicks reveal
    Then she sees 3 contacts
    And remaining_reveals becomes 99
```

`step_defs/test_reveal.py`:
```python
from pytest_bdd import scenarios, given, when, then
from pytest_bdd.parsers import parse

scenarios("../features/reveal.feature")

@given(parse('Marina has Pro plan with remaining_reveals = {amount:d}'))
def setup_marina(session, amount):
    # ... create user, subscription
    return ...

@given(parse('company "{inn}" has {n:d} contacts'))
def setup_company(session, inn, n):
    # ... create company, contacts
    return ...

@when('she clicks reveal')
async def click_reveal(client, marina, company):
    response = await client.post("/reveals", json={"company_inn": company.inn})
    return response

@then(parse('she sees {n:d} contacts'))
def assert_contacts(response, n):
    assert response.status_code == 200
    assert len(response.json()["contacts"]) == n
```

### 5. Mocking External APIs (respx)

```python
# backend-api/tests/mocks/yookassa.py
import respx
from httpx import Response

@pytest.fixture
def mock_yookassa(respx_mock):
    respx_mock.post("https://api.yookassa.ru/v3/payments").mock(
        return_value=Response(200, json={
            "id": "test-payment-id",
            "status": "pending",
            "confirmation": {"confirmation_url": "https://yookassa.ru/checkout/..."},
        })
    )
    return respx_mock

# Usage
async def test_checkout(mock_yookassa, client):
    resp = await client.post("/billing/checkout", json={"plan_code": "pro"})
    assert resp.json()["checkout_url"].startswith("https://yookassa.ru")
```

### 6. Time Freezing

```python
from freezegun import freeze_time

@freeze_time("2026-05-01 00:00:00", tz_offset=3)  # MSK
async def test_quota_reset_on_monthly_cycle(session, subscription):
    await reset_quotas_task()
    await session.refresh(subscription)
    assert subscription.remaining_reveals == 2000  # Pro tier
```

## Frontend Testing

### Vitest Unit

```typescript
// frontend/components/companies/RevealButton.test.tsx
import { describe, it, expect, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { RevealButton } from "./RevealButton"

vi.mock("@/lib/api/client")

describe("RevealButton", () => {
  it("calls reveal API and shows contacts", async () => {
    const onReveal = vi.fn()
    const queryClient = new QueryClient()
    
    render(
      <QueryClientProvider client={queryClient}>
        <RevealButton companyInn="7707083893" onReveal={onReveal} />
      </QueryClientProvider>
    )
    
    fireEvent.click(screen.getByText("Reveal contacts"))
    // ... assert API called, onReveal triggered
  })
})
```

### Playwright E2E

```typescript
// e2e/tests/reveal-flow.spec.ts
import { test, expect } from "@playwright/test"

test("user registers, upgrades, reveals contact", async ({ page }) => {
  await page.goto("/register")
  await page.fill("[name=email]", `test-${Date.now()}@example.com`)
  await page.fill("[name=password]", "Strong1234!")
  await page.check("[name=pdnConsent]")
  await page.click("text=Зарегистрироваться")
  
  // Verify email link (use mock email service in test env)
  await page.goto(`/verify?token=${TEST_VERIFY_TOKEN}`)
  
  await page.goto("/dashboard")
  await page.fill("[name=search]", "Сбербанк")
  await page.click("text=ПАО Сбербанк")
  
  await page.click("text=Reveal contacts")
  await expect(page.locator(".contact-card")).toHaveCount(3)
})
```

## Performance Testing

### k6 Script

```javascript
// performance/search.k6.js
import http from "k6/http"
import { check } from "k6"

export const options = {
  stages: [
    { duration: "30s", target: 50 },   // ramp-up
    { duration: "1m", target: 100 },   // sustain
    { duration: "30s", target: 0 },
  ],
  thresholds: {
    http_req_duration: ["p(99) < 500"],
    http_req_failed: ["rate < 0.01"],
  },
}

export default function () {
  const res = http.get(
    "https://staging.apollo-ru.example.com/api/v1/companies?okved=62&region=Москва",
    { headers: { Authorization: `Bearer ${__ENV.TEST_TOKEN}` } }
  )
  check(res, { "status is 200": (r) => r.status === 200 })
}
```

## Security Testing

### Auth bypass test

```python
@pytest.mark.security
async def test_reveal_requires_auth(client):
    """Endpoint должен возвращать 401 без auth."""
    resp = await client.post("/reveals", json={"company_inn": "7707083893"})
    assert resp.status_code == 401

@pytest.mark.security
async def test_user_cannot_access_other_user_subscription(client, user_a, user_b):
    """User A не может посмотреть subscription user B."""
    login_a = await client.post("/auth/login", json={"email": user_a.email, "password": "..."})
    
    resp = await client.get(
        f"/admin/users/{user_b.id}",
        cookies=login_a.cookies,
    )
    assert resp.status_code in (403, 404)
```

### SQL injection

```python
@pytest.mark.security
async def test_search_resists_sql_injection(client, auth_cookies):
    payload = "'; DROP TABLE companies; --"
    resp = await client.get(
        "/companies",
        params={"region": payload},
        cookies=auth_cookies,
    )
    # Should return 200 (parameterized) or 400 (validation), но НЕ 500
    assert resp.status_code in (200, 400)
    
    # Verify table still exists
    check_companies = await client.get("/companies?page=1", cookies=auth_cookies)
    assert check_companies.status_code == 200
```

## CI Integration

```yaml
# .github/workflows/ci.yml (excerpt)
- name: Backend tests
  run: |
    cd backend-api
    pytest --cov=app --cov-fail-under=80 \
      --cov-report=term --cov-report=xml \
      -m "not slow"

- name: BDD scenarios
  run: cd backend-api && pytest tests/bdd/

- name: Frontend tests
  run: cd frontend && npm test -- --run --coverage

- name: E2E (staging only)
  if: github.ref == 'refs/heads/develop'
  run: cd e2e && npx playwright test
```

## Test Data Factories

```python
# backend-api/tests/factories.py
import factory
from app.models import User, Subscription, Company

class UserFactory(factory.Factory):
    class Meta: model = User
    email = factory.Sequence(lambda n: f"user{n}@test.com")
    password_hash = "$2b$12$..."  # bcrypt of "Test1234"
    status = "active"
    pdn_consent_at = factory.LazyFunction(datetime.utcnow)

class SubscriptionFactory(factory.Factory):
    class Meta: model = Subscription
    plan_code = "free"
    status = "active"
    remaining_reveals = 25
```

## Common Anti-Patterns

❌ **Testing internals** — test behavior not implementation
❌ **Mocking too much** — integration tests should use real DB
❌ **Sleep в тестах** — use freezegun or proper async waits
❌ **Hardcoded test data** — use factories
❌ **No teardown** — tests должны быть independent (rollback transaction)
❌ **Testing happy path only** — нужны errors + edge cases (см. test-scenarios.md)

## Critical Path Coverage Requirements

| Path | Test must cover |
|------|-----------------|
| **Auth** | Register, login, token refresh, password reset, email verification, brute-force, token theft |
| **Reveal** | Happy, no-credits, repeat (no charge), concurrent (race), opted-out contacts, no contacts, expired sub |
| **Billing** | Upgrade, downgrade, failed payment, webhook idempotency, prorated calc, failed signature |
| **Outreach** | Send, opt-out skip, cooldown skip, blocked-bot, quota exhaust mid-campaign, cancel mid-run |
| **Audit** | Critical actions logged, retention, masked PII |

## Reference

- 65 BDD scenarios: `docs/test-scenarios.md`
- Edge cases matrix: `docs/Refinement.md` Section "Edge Cases Matrix"
- Performance NFR: `docs/Specification.md` NFR-1
