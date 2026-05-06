---
name: coding-standards
description: Apollo (RU) code style — Python (FastAPI/SQLAlchemy/async), TypeScript (Next.js/React), SQL, общие правила. Auto-loaded при работе с кодом.
version: "1.0"
maturity: production
---

# Apollo (RU) Coding Standards

> See also: `.claude/rules/coding-style.md` (high-level rules).

## Python — Apollo Patterns

### Async-first

Все service / repository / router functions — `async`:

```python
# GOOD
async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

# BAD — sync вызов в async context
def get_user_by_email_sync(...):  # blocks event loop
    ...
```

### Repository Pattern

Каждая entity → один Repository class:

```python
# backend-api/app/repositories/user.py
class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        return (await self.session.execute(
            select(User).where(User.id == user_id)
        )).scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        return (await self.session.execute(
            select(User).where(User.email == email)
        )).scalar_one_or_none()

    async def create(self, *, email: str, password_hash: str, pdn_consent_at: datetime) -> User:
        user = User(email=email, password_hash=password_hash, pdn_consent_at=pdn_consent_at)
        self.session.add(user)
        await self.session.flush()  # get id
        return user
```

### Service Pattern

Business logic в Services. **Никогда не SQLAlchemy в Services** — только через Repository.

```python
# backend-api/app/services/auth.py
class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register(
        self,
        email: str,
        password: str,
        pdn_consent: bool,
    ) -> User:
        if not pdn_consent:
            raise BusinessError("PDN_CONSENT_REQUIRED")
        if await self.user_repo.get_by_email(email):
            raise BusinessError("EMAIL_EXISTS")
        password_hash = bcrypt_hash(password)
        return await self.user_repo.create(
            email=email,
            password_hash=password_hash,
            pdn_consent_at=utc_now(),
        )
```

### FastAPI Router

Routers — thin: dependency injection, валидация, делегирование service:

```python
# backend-api/app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserCreatedResponse, status_code=201)
async def register(
    payload: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        user = await auth_service.register(
            email=payload.email,
            password=payload.password,
            pdn_consent=payload.pdn_consent,
        )
    except BusinessError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"code": e.code, "message": str(e)},
        )
    return UserCreatedResponse.from_orm(user)
```

### Pydantic Schemas

В `backend-api/app/schemas/<domain>.py`:

```python
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")  # reject unknown fields

    email: EmailStr
    password: str = Field(min_length=8)
    pdn_consent: bool
    marketing_consent: bool = False

class UserCreatedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    email: str
    status: str
```

### Custom Exceptions

```python
# backend-api/app/exceptions.py
class BusinessError(Exception):
    """Domain-level error с error code."""
    code: str = "INTERNAL"
    status_code: int = 400

    def __init__(self, code: str, message: str | None = None, status_code: int = 400):
        self.code = code
        self.status_code = status_code
        super().__init__(message or code)

class QuotaExceeded(BusinessError):
    def __init__(self, plan: str, remaining: int, quota: int):
        super().__init__(
            code="QUOTA_EXCEEDED",
            message=f"Лимит исчерпан. Plan: {plan}, used: {quota}/{quota}",
            status_code=402,
        )
        self.details = {"plan": plan, "remaining": remaining, "quota": quota}
```

### SQLAlchemy 2.0 Models

```python
# backend-api/app/models/user.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, CheckConstraint
from app.database import Base
import uuid
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    pdn_consent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending_verification','active','suspended','deleted')",
            name="users_status_check",
        ),
    )
```

### Atomic Operations (Reveal Pattern)

```python
async def reveal_contact(
    session: AsyncSession,
    user_id: UUID,
    company_inn: str,
) -> list[Contact]:
    async with session.begin():  # transaction
        # Check existing
        existing = await session.execute(
            select(RevealEvent)
            .where(RevealEvent.user_id == user_id)
            .where(RevealEvent.company_inn == company_inn)
        )
        if existing.scalar_one_or_none():
            return await get_contacts(session, company_inn)

        # Lock subscription row
        sub = (await session.execute(
            select(Subscription)
            .where(Subscription.user_id == user_id)
            .where(Subscription.status == "active")
            .with_for_update()
        )).scalar_one()

        if sub.remaining_reveals <= 0:
            raise QuotaExceeded(plan=sub.plan_code, remaining=0, quota=...)

        # Decrement, log, return
        sub.remaining_reveals -= 1
        session.add(RevealEvent(user_id=user_id, company_inn=company_inn))
        await audit_log(session, user_id, "reveal_contact", "company", company_inn)
        return await get_contacts(session, company_inn)
```

## TypeScript / React — Apollo Patterns

### React Query Hook

```typescript
// frontend/lib/api/companies.ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiClient } from "@/lib/api/client"

interface SearchParams {
  okved?: string[]
  region?: string[]
  query?: string
  page?: number
  pageSize?: number
}

interface SearchResult {
  total: number
  page: number
  companies: Company[]
}

export function useCompaniesSearch(params: SearchParams) {
  return useQuery({
    queryKey: ["companies", params],
    queryFn: async () => {
      const { data } = await apiClient.get<SearchResult>("/companies", {
        params: {
          okved: params.okved?.join(","),
          region: params.region?.join(","),
          query: params.query,
          page: params.page ?? 1,
          page_size: params.pageSize ?? 20,
        },
      })
      return data
    },
    staleTime: 5 * 60_000,
  })
}

export function useReveal() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (companyInn: string) => {
      const { data } = await apiClient.post("/reveals", { company_inn: companyInn })
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["subscription"] })
    },
  })
}
```

### Component Pattern

```typescript
// frontend/components/companies/RevealButton.tsx
"use client"

import { useReveal } from "@/lib/api/companies"
import { Button } from "@/components/ui/button"
import { toast } from "sonner"

interface Props {
  companyInn: string
  onReveal?: (contacts: Contact[]) => void
}

export function RevealButton({ companyInn, onReveal }: Props) {
  const reveal = useReveal()

  const handleClick = async () => {
    try {
      const result = await reveal.mutateAsync(companyInn)
      onReveal?.(result.contacts)
      toast.success(`Раскрыто ${result.contacts.length} контактов`)
    } catch (error: any) {
      if (error.response?.data?.error?.code === "QUOTA_EXCEEDED") {
        toast.error("Лимит исчерпан", { action: { label: "Upgrade", onClick: () => router.push("/billing") } })
      } else {
        toast.error("Ошибка раскрытия")
      }
    }
  }

  return (
    <Button onClick={handleClick} disabled={reveal.isPending}>
      {reveal.isPending ? "Раскрываем..." : "Reveal contacts"}
    </Button>
  )
}
```

### Form Pattern (react-hook-form + zod)

```typescript
"use client"

import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"

const schema = z.object({
  email: z.string().email("Неверный email"),
  password: z.string().min(8, "Минимум 8 символов"),
  pdnConsent: z.boolean().refine(v => v === true, "Согласие обязательно"),
})

type FormData = z.infer<typeof schema>

export function RegisterForm() {
  const form = useForm<FormData>({ resolver: zodResolver(schema) })

  const onSubmit = async (data: FormData) => {
    // ...
  }

  return (
    <form onSubmit={form.handleSubmit(onSubmit)}>
      {/* ... */}
    </form>
  )
}
```

## SQL — Apollo Patterns

### Forward-Compatible Migration

```python
# alembic/versions/XXX_add_users_pdn_consent.py
"""Add pdn_consent column to users

Forward-compatible: NULLABLE for existing rows, code сохраняет new rows
с этой колонкой populated.
"""

def upgrade():
    op.add_column(
        "users",
        sa.Column("pdn_consent_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Backfill existing rows (если safe) — separate migration или одноразовый script

def downgrade():
    op.drop_column("users", "pdn_consent_at")
```

### Composite Index для Common Filters

```sql
-- Для частых search queries: filter by region + okved + revenue
CREATE INDEX idx_companies_search ON companies(region, okved_main, revenue_range)
WHERE deleted_at IS NULL;
```

### Partial Index для opt-out filtering

```sql
-- Большинство contacts — not opted_out, индекс по active only
CREATE INDEX idx_contacts_company_active ON contacts(company_inn)
WHERE opted_out = false;
```

## Common Anti-Patterns to Avoid

### Python

```python
# BAD
def authenticate(email, password):                  # missing types
    user = db.query(User).filter(...).first()      # sync ORM в async context
    return user.password == password               # plaintext comparison + no type hint

# GOOD
async def authenticate(
    session: AsyncSession,
    email: str,
    password: str,
) -> User | None:
    user = await user_repo.get_by_email(session, email)
    if not user or not bcrypt_verify(password, user.password_hash):
        return None
    return user
```

### TypeScript

```typescript
// BAD
function getCompanies(filter: any): any {           // no types
  return fetch("/api/companies?" + filter)          // string concatenation
    .then(r => r.json())                            // no error handling
}

// GOOD
async function getCompanies(filter: SearchParams): Promise<SearchResult> {
  const { data } = await apiClient.get<SearchResult>("/companies", { params: filter })
  return data
}
```

## Project Structure

См. `.claude/commands/start.md` для полной структуры созданной `/start` командой.

## When in Doubt

- Read existing code в same domain (consistency)
- Check `docs/Pseudocode.md` для algorithm contracts
- Check `.claude/rules/` для policies
- Ask `@architect` agent для significant decisions
