---
name: security-patterns
description: Apollo (RU) security patterns — Encrypted IndexedDB (AES-GCM 256 + PBKDF2), JWT rotation, HMAC webhook verification, OWASP Top 10. Auto-loaded при работе с auth, secrets, billing webhooks, user-side keys.
version: "1.0"
maturity: production
---

# Apollo (RU) Security Patterns

> See also: `.claude/rules/security.md`, `.claude/rules/secrets-management.md`.

## Pattern 1: User-Side Encrypted Storage (IndexedDB)

For storing user-provided API keys (LLM, Telegram bot tokens) entirely client-side.

### Encryption (`frontend/lib/crypto/index.ts`)

```typescript
const SALT_BYTES = 16
const IV_BYTES = 12
const PBKDF2_ITERATIONS = 100_000

export async function deriveMasterKey(password: string, salt: Uint8Array): Promise<CryptoKey> {
  const passwordKey = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(password),
    "PBKDF2",
    false,
    ["deriveKey"]
  )
  return crypto.subtle.deriveKey(
    { name: "PBKDF2", salt, iterations: PBKDF2_ITERATIONS, hash: "SHA-256" },
    passwordKey,
    { name: "AES-GCM", length: 256 },
    false,  // not extractable
    ["encrypt", "decrypt"]
  )
}

export async function encryptSecret(plaintext: string, masterKey: CryptoKey): Promise<EncryptedBlob> {
  const iv = crypto.getRandomValues(new Uint8Array(IV_BYTES))
  const ciphertext = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv },
    masterKey,
    new TextEncoder().encode(plaintext)
  )
  return { iv: arrayBufferToBase64(iv), ciphertext: arrayBufferToBase64(ciphertext) }
}

export async function decryptSecret(blob: EncryptedBlob, masterKey: CryptoKey): Promise<string> {
  const plaintext = await crypto.subtle.decrypt(
    { name: "AES-GCM", iv: base64ToArrayBuffer(blob.iv) },
    masterKey,
    base64ToArrayBuffer(blob.ciphertext)
  )
  return new TextDecoder().decode(plaintext)
}
```

### Storage (IndexedDB)

```typescript
import { openDB } from "idb"

const DB_NAME = "apollo_user_secrets"
const STORE = "secrets"

async function getDB() {
  return openDB(DB_NAME, 1, {
    upgrade(db) {
      if (!db.objectStoreNames.contains(STORE)) {
        db.createObjectStore(STORE, { keyPath: "id" })
      }
    },
  })
}

export async function saveUserKey(id: string, plainKey: string, masterKey: CryptoKey) {
  const blob = await encryptSecret(plainKey, masterKey)
  const db = await getDB()
  await db.put(STORE, { id, ...blob, updatedAt: new Date() })
}

export async function loadUserKey(id: string, masterKey: CryptoKey): Promise<string | null> {
  const db = await getDB()
  const stored = await db.get(STORE, id)
  if (!stored) return null
  return decryptSecret({ iv: stored.iv, ciphertext: stored.ciphertext }, masterKey)
}
```

### Master Key Lifecycle

```typescript
import { atom } from "jotai"

const masterKeyAtom = atom<CryptoKey | null>(null)
const lastActivityAtom = atom<number>(Date.now())

const IDLE_TIMEOUT = 30 * 60 * 1000  // 30 min

// Re-derive on user input
export async function unlock(password: string) {
  const salt = await getSaltFromIDB()  // stored once on first registration
  const key = await deriveMasterKey(password, salt)
  setMasterKey(key)
  resetActivityTimer()
}

// Auto-lock
setInterval(() => {
  if (Date.now() - getLastActivity() > IDLE_TIMEOUT) {
    setMasterKey(null)
    showLockedModal()
  }
}, 60_000)

// Reset on user activity
document.addEventListener("click", () => updateActivity())
document.addEventListener("keypress", () => updateActivity())
```

### Constraints

- Master key **only in memory** (never persisted)
- Salt persisted in IndexedDB (16 bytes, generated once)
- IV unique per encryption (12 bytes, fresh each time)
- Lost password = lost keys (no recovery, no escrow)
- Backup: user can export encrypted blob (still encrypted; user keeps password separately)

## Pattern 2: JWT with Rotation

### Generation

```python
# backend-api/app/utils/jwt.py
import jwt
from datetime import datetime, timedelta, timezone

ACCESS_TTL = timedelta(minutes=15)
REFRESH_TTL = timedelta(days=7)

def create_access_token(user_id: UUID) -> str:
    return jwt.encode(
        {
            "sub": str(user_id),
            "exp": datetime.now(timezone.utc) + ACCESS_TTL,
            "iat": datetime.now(timezone.utc),
            "type": "access",
        },
        settings.JWT_SECRET_CURRENT,
        algorithm="HS256",
    )

def verify_token(token: str) -> dict:
    """Try current key first, fall back to previous (during 90-day rotation overlap)."""
    for key in [settings.JWT_SECRET_CURRENT, settings.JWT_SECRET_PREVIOUS]:
        if not key:
            continue
        try:
            payload = jwt.decode(token, key, algorithms=["HS256"])
            return payload
        except jwt.InvalidSignatureError:
            continue
    raise jwt.InvalidTokenError("No valid signing key matched")
```

### Cookie Setting

```python
# backend-api/app/routers/auth.py
@router.post("/login")
async def login(payload: LoginRequest, response: Response, ...):
    user = await auth_service.authenticate(payload.email, payload.password)
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    
    response.set_cookie(
        "access_token",
        access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=int(ACCESS_TTL.total_seconds()),
    )
    response.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        path="/api/v1/auth/refresh",
        max_age=int(REFRESH_TTL.total_seconds()),
    )
    return {"user": user.to_dict()}
```

### Refresh Token Rotation

```python
@router.post("/refresh")
async def refresh(refresh_token: str = Cookie(...)):
    payload = verify_token(refresh_token)
    if payload["type"] != "refresh":
        raise HTTPException(401, "Wrong token type")
    
    # Detect token reuse
    family = await session_repo.get_session_family(payload["jti"])
    if family.last_used_jti != payload["jti"]:
        # Token was already rotated — likely theft
        await session_repo.invalidate_family(family.id)
        raise HTTPException(401, "Token reuse detected")
    
    # Issue new tokens, mark old as used
    new_access = create_access_token(payload["sub"])
    new_refresh = create_refresh_token(payload["sub"], family_id=family.id)
    await session_repo.rotate(family.id, new_jti=new_refresh.jti)
    
    return Response(...)  # set new cookies
```

## Pattern 3: HMAC Webhook Verification (ЮKassa)

```python
# backend-api/app/integrations/yookassa.py
import hmac
import hashlib

def verify_webhook(payload: bytes, signature: str) -> bool:
    expected = hmac.new(
        settings.YOOKASSA_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

@router.post("/yookassa-webhook")
async def yookassa_webhook(
    request: Request,
    x_yookassa_signature: str = Header(...),
):
    payload = await request.body()
    if not verify_webhook(payload, x_yookassa_signature):
        # Log security event
        logger.warning("YooKassa webhook signature mismatch", extra={"ip": request.client.host})
        raise HTTPException(401, "Invalid signature")
    
    event = json.loads(payload)
    
    # Idempotency check
    if await audit_repo.event_processed(event["id"]):
        return {}  # Already handled
    
    # Process
    await billing_service.handle_yookassa_event(event)
    await audit_repo.mark_event_processed(event["id"])
    return {}
```

## Pattern 4: Opt-out HMAC Token (Public)

For unsubscribe links — must prevent enumeration of other users' emails.

```python
# Generate (when sending campaign)
def make_optout_token(email: str, ttl_days: int = 365) -> str:
    expiry = int((datetime.now() + timedelta(days=ttl_days)).timestamp())
    payload = f"{email}:{expiry}"
    sig = hmac.new(
        settings.OPTOUT_SECRET.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"{payload}:{sig}"

def make_optout_url(email: str) -> str:
    token = make_optout_token(email)
    return f"https://apollo-ru.example.com/optout?email={quote(email)}&token={token}"

# Verify (on opt-out endpoint)
def verify_optout_token(email: str, token: str) -> bool:
    try:
        token_email, expiry, sig = token.rsplit(":", 2)
    except ValueError:
        return False
    if token_email != email:
        return False
    if int(expiry) < int(datetime.now().timestamp()):
        return False
    expected = hmac.new(
        settings.OPTOUT_SECRET.encode(),
        f"{token_email}:{expiry}".encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, sig)

@app.get("/optout")  # public, no auth
async def optout(email: str, token: str):
    if not verify_optout_token(email, token):
        # Log security event for monitoring
        logger.warning("Invalid opt-out token", extra={"email_attempted": email})
        return HTMLResponse("Invalid token", status_code=400)
    
    await opt_out_repo.add(email=email, source="user_link")
    await audit_log_repo.add(action="optout", entity_id=email)
    return HTMLResponse("Вы отписаны от outreach Apollo")
```

## Pattern 5: bcrypt Password Hashing

```python
import bcrypt

BCRYPT_ROUNDS = 12

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode()

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except ValueError:
        return False  # Malformed hash
```

## Pattern 6: Rate Limiting (Redis-backed)

```python
# backend-api/app/middleware/rate_limit.py
from fastapi import Request, HTTPException
import time

async def rate_limit(
    request: Request,
    redis: Redis,
    key: str,
    limit: int,
    window_sec: int,
):
    bucket = f"ratelimit:{key}:{int(time.time() // window_sec)}"
    count = await redis.incr(bucket)
    if count == 1:
        await redis.expire(bucket, window_sec)
    if count > limit:
        ttl = await redis.ttl(bucket)
        raise HTTPException(
            status_code=429,
            detail={"code": "RATE_LIMIT", "retry_after": ttl},
            headers={"Retry-After": str(ttl)},
        )

# Usage in router
@router.post("/reveals", dependencies=[Depends(rate_limit_per_user(30, 60))])
async def reveal(...):
    ...
```

## Pattern 7: Input Sanitization для HTML rendering

Frontend (если приходится render user-input HTML):

```typescript
import DOMPurify from "isomorphic-dompurify"

function SafeHTMLBlock({ html }: { html: string }) {
  const sanitized = DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ["b", "i", "em", "strong", "a", "p", "br", "ul", "ol", "li"],
    ALLOWED_ATTR: ["href", "target"],
  })
  return <div dangerouslySetInnerHTML={{ __html: sanitized }} />
}
```

## Pattern 8: Sensitive Data Masking в Logs

```python
# backend-api/app/utils/logging.py
import re

def mask_email(email: str) -> str:
    if "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    return f"{local[0]}***@{domain}"

def mask_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 4:
        return "***"
    return f"+{digits[0]}***{digits[-4:]}"

def mask_inn(inn: str) -> str:
    if len(inn) < 6:
        return "***"
    return f"{inn[:6]}****"

# Logger filter
class SensitiveDataFilter(logging.Filter):
    def filter(self, record):
        if hasattr(record, "user_email"):
            record.user_email = mask_email(record.user_email)
        if hasattr(record, "phone"):
            record.phone = mask_phone(record.phone)
        return True
```

## Common Mistakes (CI catches)

| Mistake | Catch |
|---------|-------|
| Plaintext password в logs | bandit + custom regex check |
| Hardcoded API key | detect-secrets pre-commit |
| SQL injection (f-string в text()) | bandit B608 |
| `eval()` / `exec()` | bandit B102/B307 |
| Missing CSRF token | manual review checklist |
| Expired TLS cert | monitoring alert |
| Public endpoint без rate limit | manual review |
| Missing webhook HMAC verification | code-reviewer agent |

## Related

- `.claude/rules/security.md` — overall security policy
- `.claude/rules/secrets-management.md` — secret rotation, env vars
- `docs/Architecture.md` Section 6 — security architecture
- `docs/ADR.md` ADR-007 — encrypted IndexedDB decision
