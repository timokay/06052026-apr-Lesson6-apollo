# C4 Diagrams: Apollo (RU)

> System Context, Container, Component diagrams.

## Level 1: System Context

```mermaid
graph TB
  subgraph Users
    SDR[B2B Sales SDR/AE<br/>Marina]
    MKT[B2B Marketer<br/>Дмитрий]
    MA[M&A Analyst<br/>Анна]
    ADMIN[Admin/Founder]
  end

  APOLLO[Apollo RU<br/>B2B Sales Intelligence Platform]

  subgraph "External Systems"
    YK[ЮKassa<br/>Payment Acquiring]
    TG[Telegram Bot API<br/>Outreach Channel]
    YG[YandexGPT<br/>LLM Primary]
    OAI[OpenAI API<br/>LLM Fallback]
    EGRUL[ЕГРЮЛ Open Data<br/>ФНС РФ]
    SPARK[СПАРК API<br/>P2 Data Source]
    TGUSER[Telegram Users<br/>Recipients]
    EMAIL[Email Provider<br/>Unisender Go - P1]
  end

  SDR -->|search, reveal,<br/>outreach| APOLLO
  MKT -->|ICP analysis,<br/>look-alike| APOLLO
  MA -->|company research| APOLLO
  ADMIN -->|operations,<br/>monitoring| APOLLO

  APOLLO -->|payments| YK
  APOLLO -->|send messages| TG
  APOLLO -->|generate text,<br/>analyze ICP| YG
  APOLLO -->|fallback if YG down| OAI
  APOLLO <-->|weekly bulk import| EGRUL
  APOLLO <-->|incremental sync<br/>P2 only| SPARK
  TG -->|deliver messages| TGUSER
  TGUSER -.->|opt-out replies| TG
  APOLLO -->|transactional<br/>P1| EMAIL
```

## Level 2: Container Diagram

```mermaid
graph TB
  subgraph "User Browser"
    UI[Web UI<br/>Next.js + React<br/>Encrypted IndexedDB<br/>for user API keys]
  end

  subgraph "Apollo RU - HOSTKEY VPS"
    direction TB
    NX[Reverse Proxy<br/>Nginx + Let's Encrypt<br/>TLS, rate-limit, HSTS]

    subgraph "Application Tier"
      FE[Frontend<br/>Next.js 14 SSR/SPA<br/>Port: 3000]
      API[Backend Core API<br/>FastAPI + Python 3.12<br/>Port: 8000]
      WORK[Worker<br/>Celery + Redis broker<br/>Outreach + ICP + ETL jobs]
      BEAT[Scheduler<br/>Celery Beat<br/>Cron: quota_reset, etl]
    end

    subgraph "Data Tier"
      PG[(PostgreSQL 16<br/>+ pg_trgm + pg_vector<br/>Primary database)]
      RD[(Redis 7<br/>Cache + Celery broker<br/>Sessions)]
      MN[(MinIO<br/>S3-compatible<br/>CSV uploads, exports)]
    end

    subgraph "Observability"
      PR[Prometheus<br/>Metrics scraper]
      GR[Grafana<br/>Dashboards]
      LK[Loki + Promtail<br/>Logs]
      AM[Alertmanager<br/>PagerDuty + TG]
    end
  end

  subgraph "External"
    YK[ЮKassa]
    TG[Telegram Bot API]
    LLM[LLM Providers]
    OPEN[Open Data Sources]
  end

  UI -->|HTTPS| NX
  NX --> FE
  NX -->|/api/*| API
  FE -.->|API calls| API
  API <--> PG
  API <--> RD
  API --> MN
  API -->|enqueue jobs| RD
  WORK <-->|consume jobs| RD
  WORK <--> PG
  WORK -->|HTTPS| TG
  WORK -->|HTTPS| LLM
  BEAT -->|schedule| RD
  API -->|webhook callback| YK
  YK -->|payment events| API
  WORK -->|metrics| PR
  API -->|metrics| PR
  API -->|logs| LK
  WORK -->|logs| LK
  PR --> GR
  LK --> GR
  PR --> AM
  WORK <-->|HTTPS| OPEN
```

## Level 3: Component Diagram — Backend Core API

```mermaid
graph TB
  subgraph "Backend Core API - FastAPI"
    direction TB

    subgraph "Routers (HTTP layer)"
      AUTH_R[auth.router<br/>register, login, refresh, verify]
      COMP_R[companies.router<br/>search, by_inn]
      REV_R[reveals.router<br/>POST /reveals]
      ICP_R[icp.router<br/>analyze, jobs]
      CAMP_R[campaigns.router<br/>CRUD, launch]
      BILL_R[billing.router<br/>checkout, webhook]
      OPT_R[optout.public<br/>HMAC-secured]
      AUDIT_R[audit.router<br/>admin only]
    end

    subgraph "Services (business logic)"
      AUTH_S[AuthService<br/>JWT, bcrypt]
      COMP_S[CompanyService<br/>filter compose,<br/>search, ranking]
      REV_S[RevealService<br/>atomic quota deduct]
      ICP_S[ICPService<br/>distributions,<br/>look-alike scoring]
      CAMP_S[CampaignService<br/>audience builder,<br/>scheduler]
      BILL_S[BillingService<br/>YK integration,<br/>plan upgrades]
      LLM_S[LLMService<br/>provider abstraction<br/>YG → OpenAI fallback]
      AUDIT_S[AuditService<br/>append-only writer]
    end

    subgraph "Repositories (data access)"
      USER_REPO[UserRepository]
      COMP_REPO[CompanyRepository<br/>+ pg_trgm queries]
      CONT_REPO[ContactRepository]
      REV_REPO[RevealEventRepository]
      SUB_REPO[SubscriptionRepository<br/>SELECT FOR UPDATE]
      CAMP_REPO[CampaignRepository]
      AUDIT_REPO[AuditLogRepository]
      OPT_REPO[OptOutRepository]
    end

    subgraph "Infrastructure"
      DB[SQLAlchemy 2.0<br/>async session]
      RED[Redis client]
      S3[MinIO client]
      CEL[Celery sender<br/>API → Worker]
      YKC[ЮKassa client<br/>HTTPS]
    end
  end

  AUTH_R --> AUTH_S --> USER_REPO --> DB
  COMP_R --> COMP_S --> COMP_REPO --> DB
  REV_R --> REV_S
  REV_S --> SUB_REPO --> DB
  REV_S --> REV_REPO --> DB
  REV_S --> CONT_REPO --> DB
  REV_S --> AUDIT_S --> AUDIT_REPO --> DB
  ICP_R --> ICP_S
  ICP_S --> S3
  ICP_S --> CEL
  CAMP_R --> CAMP_S --> CAMP_REPO --> DB
  CAMP_S --> CEL
  BILL_R --> BILL_S
  BILL_S --> YKC
  BILL_S --> SUB_REPO --> DB
  BILL_S --> AUDIT_S
  OPT_R --> OPT_REPO --> DB
  AUDIT_R --> AUDIT_REPO --> DB
  COMP_S -.->|cache lookup| RED
```

## Level 3: Component Diagram — Worker Service

```mermaid
graph TB
  subgraph "Celery Worker Service"
    direction TB

    subgraph "Task Queues"
      Q_OUT[outreach queue<br/>5 msg/sec throttle]
      Q_ICP[icp queue<br/>concurrent 5]
      Q_ETL[etl queue<br/>singleton]
      Q_BIL[billing queue<br/>concurrent 3]
      Q_NOT[notifications queue<br/>concurrent 10]
    end

    subgraph "Tasks"
      T_SEND[outreach.send_campaign<br/>per-campaign]
      T_ICP[icp.analyze<br/>per-job]
      T_ETL_RU[etl.refresh_companies<br/>weekly cron]
      T_QR[billing.reset_quotas<br/>monthly cron]
      T_REN[billing.charge_renewal<br/>per-subscription]
      T_EMAIL[notifications.send_email<br/>per-message]
    end

    subgraph "Helpers"
      TG_C[Telegram Client<br/>bot API wrapper<br/>retry, backoff]
      LLM_C[LLM Client<br/>YG / OpenAI<br/>cache, fallback]
      EGRUL_C[ЕГРЮЛ Parser<br/>JSONLines streaming]
      YK_C[ЮKassa Client<br/>idempotency keys]
      EMAIL_C[Email Client<br/>SMTP / Unisender]
      CACHE[LLM Prompt Cache<br/>Redis]
    end

    subgraph "Repos"
      W_REPOS[Same as API<br/>shared codebase]
    end
  end

  Q_OUT --> T_SEND --> TG_C
  T_SEND --> LLM_C
  LLM_C --> CACHE
  T_SEND --> W_REPOS
  Q_ICP --> T_ICP --> LLM_C
  T_ICP --> W_REPOS
  Q_ETL --> T_ETL_RU --> EGRUL_C
  T_ETL_RU --> W_REPOS
  Q_BIL --> T_QR --> W_REPOS
  Q_BIL --> T_REN --> YK_C
  Q_NOT --> T_EMAIL --> EMAIL_C
```

## Sequence Diagram: Reveal Flow

```mermaid
sequenceDiagram
    participant U as User Browser
    participant N as Nginx
    participant API as FastAPI
    participant DB as PostgreSQL
    participant R as Redis

    U->>N: POST /api/v1/reveals { company_inn }
    N->>API: forward
    API->>API: JWT validate (cookie)
    API->>R: cache lookup (subscription)
    R-->>API: hit/miss
    
    alt cache miss
      API->>DB: BEGIN TX
      API->>DB: SELECT subscription FOR UPDATE
      DB-->>API: { remaining=100 }
    end
    
    alt remaining == 0
      API-->>U: 402 QUOTA_EXCEEDED
    else
      API->>DB: SELECT existing reveal_event
      alt already revealed
        API->>DB: SELECT contacts (no charge)
        DB-->>API: contacts[]
        API-->>U: 200 contacts
      else first reveal
        API->>DB: SELECT contacts WHERE not opted_out
        API->>DB: UPDATE remaining_reveals -= 1
        API->>DB: INSERT reveal_event
        API->>DB: INSERT audit_log
        API->>DB: COMMIT
        API->>R: invalidate subscription cache
        API-->>U: 200 contacts
      end
    end
```

## Sequence Diagram: Outreach Campaign Launch

```mermaid
sequenceDiagram
    participant U as User
    participant API as FastAPI
    participant DB as PostgreSQL
    participant CR as Celery (Redis)
    participant W as Worker
    participant LLM as YandexGPT
    participant TG as Telegram Bot API

    U->>API: POST /api/v1/campaigns/:id/launch
    API->>DB: SELECT campaign, audience
    API->>DB: INSERT campaign_messages (status=queued)
    API->>DB: UPDATE campaign.status = 'scheduled'
    API->>CR: enqueue outreach.send_campaign(id)
    API-->>U: 202 { campaign_id, status }

    Note over W: Worker picks up task
    W->>DB: UPDATE status = 'running'
    
    loop For each contact
      W->>DB: Check opt_out, recently_contacted
      alt skip
        W->>DB: UPDATE message.status = 'skipped'
      else send
        W->>DB: SELECT FOR UPDATE remaining_outreach
        alt quota exhausted
          W->>DB: UPDATE message.status = 'skipped' (QUOTA)
          W->>DB: UPDATE campaign.status = 'completed'
          break
        else has quota
          alt ai_personalize
            W->>LLM: generate(template, company_ctx)
            LLM-->>W: personalized text
          end
          W->>TG: sendMessage(@username, text)
          alt success
            TG-->>W: 200
            W->>DB: UPDATE message.status = 'sent'
          else error
            TG-->>W: error code
            W->>DB: UPDATE message.status = 'errored'
          end
          W->>W: sleep(0.2)  # throttle
        end
      end
    end
    
    W->>DB: UPDATE campaign.status = 'completed'
    
    Note over TG: Async events
    TG-->>W: webhook (delivered, read, replied)
    W->>DB: UPDATE message.status accordingly
```

## Deployment Diagram

```mermaid
graph TB
  subgraph "Dev"
    DEV[Developer<br/>localhost docker compose]
  end

  subgraph "GitHub"
    REPO[Repository<br/>main + develop branches]
    GHA[GitHub Actions<br/>CI/CD]
    GHCR[ghcr.io<br/>Docker registry]
  end

  subgraph "Staging - HOSTKEY VPS-1"
    SVPS[8 vCPU, 8GB RAM<br/>staging.apollo-ru.example.com]
  end

  subgraph "Production - HOSTKEY VPS-2"
    PVPS[16 vCPU, 32GB RAM<br/>apollo-ru.example.com<br/>+ separate DB instance]
  end

  subgraph "Backups"
    YOS[Yandex Object Storage<br/>or HOSTKEY S3<br/>encrypted snapshots]
  end

  DEV -->|push PR| REPO
  REPO -->|trigger CI| GHA
  GHA -->|build & test| GHA
  GHA -->|push images| GHCR
  GHA -->|deploy on push to develop| SVPS
  GHA -->|deploy on push to main| PVPS
  PVPS -->|nightly pg_dump| YOS
  SVPS -->|nightly pg_dump| YOS
```

## Network / Security Diagram

```mermaid
graph TB
  subgraph "Internet"
    USERS[Users]
    ATTACKER((Bad actors))
  end

  subgraph "DMZ"
    CF[Cloudflare DDoS<br/>P1, optional]
    NX[Nginx<br/>TLS 1.3, HSTS<br/>Rate limit: 100/min/IP<br/>WAF rules]
  end

  subgraph "Application Network - Docker bridge"
    FE[Frontend Container<br/>Port 3000 internal]
    API[API Container<br/>Port 8000 internal]
    WORK[Worker Container<br/>no exposed ports]
  end

  subgraph "Data Network - Docker bridge isolated"
    PG[(Postgres<br/>5432 only to API/Worker)]
    RD[(Redis<br/>6379 only to API/Worker)]
    MN[(MinIO<br/>9000 only to API/Worker)]
  end

  subgraph "Secrets"
    DOT[.env file<br/>chmod 600<br/>Never in git]
    DEPLOY_KEY[GH deploy key<br/>read-only]
  end

  USERS -->|HTTPS:443| CF
  ATTACKER -.->|blocked| CF
  CF --> NX
  NX --> FE
  NX --> API
  FE -.->|server-side| API
  API --> PG
  API --> RD
  API --> MN
  WORK --> PG
  WORK --> RD
  WORK --> MN
  API -.uses.-> DOT
  WORK -.uses.-> DOT
```

## Notes

- All диаграммы рендерятся mermaid
- Для C4 diagrams в Confluence/Notion — экспорт через mermaid-cli в SVG
- Обновлять диаграммы синхронно с major изменениями архитектуры (см. ADR.md)
