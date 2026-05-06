# Security Rules — Apollo (RU)

> Mandatory security practices. Source: `docs/Specification.md` NFR-2, `docs/Architecture.md` Section 6, `docs/ADR.md` ADR-007.

## 1. Authentication & Authorization

- Passwords hashed with `bcrypt(cost=12)`. Never plaintext, MD5, SHA1.
- JWT in `httpOnly` cookies (`Secure`, `SameSite=Lax` access / `Strict` refresh).
- Access token TTL 15 min, refresh 7 days, refresh token rotation.
- Refresh token reuse detection → invalidate entire session family.
- All resources scoped by `user_id` in queries (no shared data leaks).
- For Team plans: RBAC roles `owner` / `admin` / `member`.

## 2. Data Encryption

| Data | At Rest | In Transit |
|------|---------|------------|
| Passwords | bcrypt(12) | TLS 1.3 |
| User PII (email, phone) | PostgreSQL TDE | TLS 1.3 |
| Audit log | Same | Same |
| User-side API keys (LLM, TG bot tokens) | Encrypted IndexedDB AES-GCM 256 + PBKDF2 from user password | **NEVER sent to backend** |
| Backups | Encrypted dump | TLS to MinIO/S3 |

## 3. User-Side Secrets Pattern

When a user provides an API key (e.g., own LLM key for cost-control, own Telegram bot token):

1. **Input** in UI Settings → Integrations
2. **Encrypt** via Web Crypto API (AES-GCM 256-bit)
3. **Key derivation:** PBKDF2 from user password (100K+ iterations)
4. **Store** in IndexedDB only (master key in memory)
5. **Auto-lock** after 30 min idle
6. **Never:** transmit to backend, log, store in plaintext

This pattern is **mandatory** for any user-provided credentials. See `docs/ADR.md` ADR-007.

## 4. Input Validation

- All endpoints have **Pydantic schemas**. Reject unknown fields.
- ИНН regex: `^\d{10}$|^\d{12}$`
- ОКВЭД regex: `^\d{2}\.\d{1,3}(\.\d{1,2})?$`
- Email: RFC 5322 strict
- File uploads: max 10 MB, MIME whitelist (text/csv only for CSV)
- Never trust client-side validation alone.

## 5. SQL & NoSQL Injection

- **Only parametrized queries** (SQLAlchemy default). Never f-strings with user input.
- For JSONB queries: use SQLAlchemy operators, not raw text.
- Forbidden: `text(f"SELECT * WHERE col = '{user_input}'")`
- Required: `text("SELECT * WHERE col = :val").bindparams(val=user_input)`

## 6. XSS Prevention

- React auto-escapes by default (jsx).
- For user-input HTML rendering: **DOMPurify** sanitize before `dangerouslySetInnerHTML`.
- Markdown rendering: use `react-markdown` with `disallowedElements=['script','iframe']`.
- HTTP headers: `X-Content-Type-Options: nosniff`.

## 7. CSRF Protection

- Cookies have `SameSite=Lax` (sufficient для basic CSRF).
- Mutating endpoints check `Origin` header against allow-list.
- For sensitive mutations (delete account, change billing): add CSRF token (double-submit pattern).

## 8. Rate Limiting

| Endpoint | Limit | Why |
|----------|-------|-----|
| `POST /auth/login` | 5/min/IP, 10/min/email | Brute force |
| `POST /auth/register` | 3/hour/IP | Spam |
| `GET /companies` | 60/min/user | Abuse |
| `POST /reveals` | 30/min/user | Quota abuse |
| `POST /icp/analyze` | 5/hour/user | LLM cost |
| `POST /campaigns/:id/launch` | 10/day/user | Spam |
| Global per IP | 100/min | DDoS basic |

Implement at: Nginx (basic IP) + FastAPI middleware (per-user, Redis backend).

## 9. Webhook Security

- ЮKassa webhook: verify HMAC signature **before** processing payload.
- Reject `POST /yookassa-webhook` without `X-Yookassa-Signature` header → 401.
- Idempotency: dedupe by `event.id` in audit_log.

```python
# Pattern
def verify_yookassa_signature(payload: bytes, signature: str) -> bool:
    expected = hmac.new(YOOKASSA_SECRET, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
```

## 10. Opt-Out & Public Endpoints

- Opt-out URL contains HMAC-signed token (prevents email enumeration).
- Token format: `{email}:{expiry}:{hmac(SECRET, email + expiry)}`
- Never accept opt-out without HMAC verification.

## 11. Logging Discipline

**NEVER log:**
- Passwords (in any form, including hashes)
- JWTs (full tokens)
- ЮKassa secrets, API keys
- User-side encrypted blobs

**Mask in logs:**
- Email → `m***@example.com`
- Phone → `+7***1234`
- ИНН → `770708****`

**Log structure:** JSON with `request_id`, `user_id` (optional), `level`, `event`.

## 12. Secrets Management (server-side)

- Production secrets in `.env` (chmod 600, never in git).
- `.env.example` committed (no values, only keys).
- Rotate JWT signing key каждые 90 дней (поддержка 2 ключей одновременно).
- ЮKassa secret rotation: при компрометации, иначе годовая.
- Never hardcode fallback secrets ("if no env, use 'dev-secret'") in production code.

## 13. CORS

- Whitelist origins: `https://apollo-ru.example.com` (prod), `http://localhost:3000` (dev).
- `credentials: true` (для cookies).
- Methods: только нужные (`GET, POST, PUT, DELETE`, не `*`).

## 14. Content Security Policy

```
default-src 'self';
script-src 'self' 'sha256-<hash>';
style-src 'self' 'unsafe-inline';  # Tailwind requires inline; use 'sha256' if possible
img-src 'self' data: https:;
connect-src 'self' https://api.yookassa.ru https://api.telegram.org;
frame-ancestors 'none';
form-action 'self';
```

## 15. 152-ФЗ Compliance

- Реестр операторов ПДн (регистрация в Роскомнадзоре).
- Хранение ПДн только на серверах в РФ (HOSTKEY VPS).
- Privacy Policy на `/privacy`, Terms of Service на `/terms`.
- Согласие на обработку ПДн (чекбокс) при регистрации.
- Право на удаление аккаунта: soft delete + hard delete через 30 дней.
- Audit log retention 3 года.
- Только публичные данные о компаниях.
- Opt-out flow для outreach получателей.

## 16. OWASP Top 10 Compliance

Run `bandit -r backend-api/` and `npm audit` in CI. Critical/high — block merge.
Quarterly OWASP ZAP dynamic scan на staging.

## Code Review Security Checklist

Перед merge PR:

- [ ] Нет hardcoded secrets
- [ ] Все user input validated (Pydantic schema)
- [ ] SQL только parametrized
- [ ] XSS-safe rendering (если есть user HTML)
- [ ] Auth check на endpoint (если не публичный)
- [ ] Rate limit configured (если новый endpoint)
- [ ] Audit log для critical actions
- [ ] Логи не содержат PII / secrets
- [ ] CORS не expanded без причины
- [ ] Tests покрывают auth/auth scenarios
