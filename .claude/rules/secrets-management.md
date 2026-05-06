# Secrets Management — Apollo (RU)

> External APIs detected: ЮKassa, Telegram Bot, YandexGPT, OpenAI, ЕГРЮЛ open data, СПАРК (P2).
> Mandatory секрет-management practices.

## Server-Side Secrets

### Storage

- **Production:** `.env` file at `/opt/apollo/.env`, chmod 600, owner = deploy user
- **Staging:** Same pattern, separate keys
- **Development:** `.env.local` (gitignored)
- **Never:** в git, в Docker images, в logs, в frontend bundle

### Required ENV variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://apollo:***@postgres:5432/apollo

# JWT
JWT_SECRET_CURRENT=<random 64 chars>
JWT_SECRET_PREVIOUS=<previous, для rotation overlap>

# YooKassa
YOOKASSA_SHOP_ID=<id>
YOOKASSA_SECRET_KEY=<secret>
YOOKASSA_WEBHOOK_SECRET=<HMAC verification key>

# LLM
LLM_PROVIDER=yandexgpt  # primary
YANDEXGPT_API_KEY=<key>
YANDEXGPT_FOLDER_ID=<id>
OPENAI_API_KEY=<key for fallback>

# Telegram (Apollo's outreach bot)
TELEGRAM_BOT_TOKEN=<from @BotFather>

# Email transactional (P1)
UNISENDER_GO_API_KEY=<key>

# Object storage
MINIO_ROOT_USER=<user>
MINIO_ROOT_PASSWORD=<password>
MINIO_ENDPOINT=http://minio:9000

# Observability
GRAFANA_ADMIN_PASSWORD=<password>
PROMETHEUS_BASIC_AUTH=<user:hash>

# CSRF / Cookies
COOKIE_DOMAIN=apollo-ru.example.com

# Email SMTP (registration, notifications)
SMTP_HOST=<host>
SMTP_USER=<user>
SMTP_PASSWORD=<password>
```

### `.env.example` (committed)

```bash
DATABASE_URL=postgresql+asyncpg://apollo:CHANGEME@postgres:5432/apollo
JWT_SECRET_CURRENT=CHANGEME_GENERATE_RANDOM_64_CHARS
YOOKASSA_SHOP_ID=
YOOKASSA_SECRET_KEY=
YANDEXGPT_API_KEY=
TELEGRAM_BOT_TOKEN=
# ...
```

## Secret Rotation

| Secret | Frequency | Procedure |
|--------|-----------|-----------|
| JWT signing key | 90 дней | Set `JWT_SECRET_PREVIOUS` = old, `JWT_SECRET_CURRENT` = new. Поддерживай оба 1 неделю. |
| Database password | 1 год | Стандартная rotation: alter user → update env → restart services |
| YooKassa secret | По compromise | Coordinate с ЮKassa support |
| Telegram bot token | По compromise | `/revoke` в @BotFather → regenerate → update env |
| LLM API keys | 6 мес | Generate new в vendor portal → update env |

### Rotation playbook (JWT example)

```bash
# 1. Generate new key
NEW_KEY=$(openssl rand -hex 32)

# 2. Update env (move current → previous, new → current)
ssh deploy@vps
cd /opt/apollo
sed -i "s/^JWT_SECRET_PREVIOUS=.*/JWT_SECRET_PREVIOUS=$(grep JWT_SECRET_CURRENT .env | cut -d= -f2)/" .env
sed -i "s/^JWT_SECRET_CURRENT=.*/JWT_SECRET_CURRENT=$NEW_KEY/" .env

# 3. Restart API (graceful, no downtime)
docker compose up -d --no-deps backend-api

# 4. After 1 week (all old tokens expired) → remove PREVIOUS
sed -i "s/^JWT_SECRET_PREVIOUS=.*/JWT_SECRET_PREVIOUS=/" .env
docker compose restart backend-api
```

## Forbidden Patterns

❌ **Hardcoded secrets** в коде:
```python
# BAD
YOOKASSA_KEY = "live_..."  # never
```

❌ **Fallback dummy secrets:**
```python
# BAD
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")  # dangerous
```

```python
# GOOD
JWT_SECRET = os.environ["JWT_SECRET"]  # crash on startup if missing
```

❌ **Logging secrets:**
```python
logger.info(f"Token: {token}")  # BAD
logger.info(f"Token: {token[:8]}***")  # BETTER, но и так не нужно
```

❌ **Secrets в Docker build args** (попадут в image history)

❌ **Secrets в frontend env vars** (`NEXT_PUBLIC_*` видны в browser)

✅ **Frontend получает** keys через authenticated API calls — никогда напрямую из env.

## User-Side Secrets (Bring Your Own Key)

Если пользователь предоставляет собственные API keys (например, свой OpenAI key для cost-control, свой Telegram bot token):

### Pattern: Encrypted IndexedDB (АЕС-GCM 256 + PBKDF2)

```typescript
// frontend pattern
import { encryptUserKey, decryptUserKey } from '@/lib/crypto';

// On user input (e.g., in /settings/api-keys):
const masterKey = await deriveMasterKey(userPassword, userSalt);  // PBKDF2 100k iter
const encrypted = await encryptUserKey(plainKey, masterKey);
await idb.put('user_keys', { id: 'openai', value: encrypted });

// On usage (client-side LLM call only):
const masterKey = await getMasterKeyFromMemory();  // user re-entered password
const stored = await idb.get('user_keys', 'openai');
const plainKey = await decryptUserKey(stored.value, masterKey);
// ... use plainKey for direct API call from browser
```

### Constraints

- Master key **only in memory**, never persisted
- Auto-lock after 30 min idle (clear master key)
- **Never sent to backend** — даже зашифрованный
- Backup: user responsibility (export encrypted blob)
- Recovery: lost password = lost keys (no escrow)

См. ADR-007 для решения о scope (MVP vs P1).

## Secrets Detection

Pre-commit hook:

```yaml
# .pre-commit-config.yaml
- repo: https://github.com/Yelp/detect-secrets
  rev: v1.5.0
  hooks:
    - id: detect-secrets
      args: ['--baseline', '.secrets.baseline']
```

CI scan:

```yaml
# .github/workflows/ci.yml
- name: Secrets scan
  uses: gitleaks/gitleaks-action@v2
```

## Incident Response: Compromised Secret

1. **Immediately rotate** affected secret (см. rotation playbooks выше)
2. **Audit log analysis** — какие requests использовали скомпрометированный секрет?
3. **Notify affected users** если PII под угрозой (152-ФЗ требование)
4. **Post-mortem** в течение 7 дней
5. **Update procedures** чтобы prevent recurrence

## Webhook Secrets

ЮKassa webhook secret — **отдельный** от API secret. Используется для HMAC verification incoming events.

```python
# Pattern
def verify_yookassa_webhook(payload: bytes, signature: str) -> bool:
    expected = hmac.new(
        YOOKASSA_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

Если verification fail → 401 + log security event + НЕ обрабатывать payload.

## Rate-Limited APIs

Внешние API имеют rate limits. Храним current quota usage в Redis:

```
yandexgpt:requests:today = 450 (limit 1000/day)
openai:tokens:hour = 50000 (limit 200000/hour)
telegram:bot:send_per_sec = 5 (limit 30/sec, but we use 5)
```

Если quota close to limit → log warning, throttle.

## Secrets in Tests

- Use mock LLM/TG/YK clients (`respx`)
- Test fixtures use dummy secrets (`test_secret_123`)
- Integration tests против test sandbox accounts (separate from prod)
