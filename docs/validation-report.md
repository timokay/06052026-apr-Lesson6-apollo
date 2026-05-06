# Validation Report: Apollo (RU)

> SPARC Phase 2 output. Swarm of 5 validators (INVEST + SMART + Architecture + Pseudocode + Coherence).
> Date: 2026-05-06. Iteration: 1/3.

## Executive Summary

**Verdict:** 🟢 **READY (with caveats)**
**Average Score:** 78/100
**Iterations:** 1/3
**Blocked items:** 0
**Warnings:** 7

| Validator | Avg Score | Verdict |
|-----------|-----------|---------|
| Stories (INVEST) | 81/100 | ✅ READY |
| Acceptance Criteria (SMART) | 76/100 | ✅ READY |
| Architecture | 82/100 | ✅ READY |
| Pseudocode | 79/100 | ✅ READY |
| Cross-document Coherence | 73/100 | 🟡 CAVEATS |

---

## Validator 1: Stories (INVEST) — 81/100

### Stories Analyzed: 14 (from PRD.md)

| ID | Title | Score | INVEST | Status |
|----|-------|-------|--------|--------|
| US-1.1 | Filter companies by ОКВЭД, region, employees, revenue | 92 | 6/6 ✓ | READY |
| US-1.2 | Search by ИНН → company card | 90 | 6/6 ✓ | READY |
| US-1.3 | Upload CSV → AI look-alike | 78 | 5/6 (E) | READY |
| US-2.1 | Reveal contacts | 88 | 6/6 ✓ | READY |
| US-2.2 | Credit-based quota | 85 | 6/6 ✓ | READY |
| US-2.3 | CSV export | 90 | 6/6 ✓ | READY |
| US-3.1 | Create Telegram campaign | 80 | 5/6 (S) | READY |
| US-3.2 | AI personalize per company | 75 | 5/6 (E) | READY |
| US-3.3 | Campaign open/reply stats | 70 | 4/6 (V,T) | READY (warning) |
| US-4.1 | Subscribe to Pro via ЮKassa | 92 | 6/6 ✓ | READY |
| US-4.2 | Quota dashboard | 85 | 6/6 ✓ | READY |
| US-4.3 | Invite team members | 75 | 5/6 (S) | READY |
| US-5.1 | Upload customer CSV | 78 | 5/6 (E) | READY |
| US-5.2 | Look-alike suggestions | 72 | 4/6 (E,T) | READY (warning) |

### Detailed Issues & Fixes

#### ⚠️ US-3.3 — Campaign open/reply stats (score 70)
- **V (Valuable):** OK ("iterate on copy") но мог быть точнее: "уменьшить cost per reply"
- **T (Testable):** "see stats" слишком расплывчато
- **FIX:** Уточнить в Specification: список метрик stats явно (Sent / Delivered / Read / Replied / Errored), с тестируемыми пороговыми значениями для UI

#### ⚠️ US-5.2 — Look-alike suggestions (score 72)
- **E (Estimable):** Неопределена сложность similarity-алгоритма (rule-based vs vector)
- **T (Testable):** «Похожих» — субъективный критерий
- **FIX:** В Pseudocode уже задан scoring formula (0.4×industry + 0.3×size + 0.2×region + 0.1×revenue) — добавить ссылку из user story; критерий приёмки: top-100 ranked by score, minimum match score >0.4

#### ⚠️ US-1.3, US-3.2, US-5.1 — общая проблема Estimable (score 75-78)
- LLM-related stories имеют переменную сложность (зависит от качества промптов)
- **FIX:** В Refinement.md добавить раздел "LLM Quality Benchmarks" с перечнем проверочных промптов и target accuracy

### Recommendations
1. Добавить **explicit success metric** к каждой US (не только в overall PRD success metrics)
2. Для LLM-stories — добавить fallback behavior (что если LLM недоступен)
3. US-4.3 (Team invite) — разбить на 3 sub-stories (invite, accept, revoke)

---

## Validator 2: Acceptance Criteria (SMART) — 76/100

### AC Analyzed: 23 Gherkin scenarios (Specification.md)

#### High-quality scenarios (≥85):

| Feature | Scenario | SMART | Score |
|---------|----------|-------|-------|
| Search | Filter by industry and region | ✓✓✓✓✓ | 95 |
| Search | Search by ИНН | ✓✓✓✓✓ | 92 |
| Reveal | Successful reveal with credits | ✓✓✓✓✓ | 95 |
| Reveal | Reveal без credits | ✓✓✓✓✓ | 95 |
| Reveal | Repeat reveal (no double-charge) | ✓✓✓✓✓ | 90 |
| Outreach | Per-recipient lifetime limit | ✓✓✓✓✓ | 90 |
| Billing | Upgrade to Pro | ✓✓✓✓✓ | 92 |
| Billing | Quota reset on monthly cycle | ✓✓✓✓✓ | 92 |
| Compliance | Reveal logged in audit | ✓✓✓✓✓ | 90 |

#### Medium-quality scenarios (60-84):

| Feature | Scenario | Issues | Score |
|---------|----------|--------|-------|
| Registration | Successful registration | 'pending_verification' state — не описан timeout | 78 |
| ICP Analysis | Analyze customer base | "В течение 30s" — нет упоминания what-if LLM медленнее | 72 |
| Outreach | Create and launch campaign | "throttle 5 msg/sec" есть, но retry policy не в AC | 70 |
| ICP Analysis | Insufficient data | "≥ 20 компаний" hardcoded — где конфиг? | 75 |

#### Issues found:

**M (Measurable) gaps:**
- "ответ возвращается < 500ms" — указан p99, но какой sample size для validation? → добавить "при 1000 параллельных запросах"
- "Marina нажимает 'Reveal'" — не указано в каком state (logged-in, has subscription)

**T (Time-bound) gaps:**
- ICP analysis "< 30s" — для скольких компаний именно? Уточнить в Specification

**A (Achievable) warnings:**
- "Marina выбрала filter 'Москва, ОКВЭД 62.01' → 247 компаний" — конкретное число только для seed dataset; нужна оговорка "при загруженном dataset"

**Vague terms flagged (0 found):**
- ✅ Нет употребления "fast", "easy", "user-friendly", "secure", "scalable" — все требования квантифицированы

### Recommendations
1. **Все perf-требования квантифицировать с sample size** (n=1000 parallel users for p99 latency)
2. **LLM operation latency** — указать также fallback timeout (например, "30s with YandexGPT, 60s if fallback to OpenAI")
3. **State preconditions** во всех Gherkin: `Given Marina logged in AND has active Pro subscription`

---

## Validator 3: Architecture — 82/100

### Checks Applied

| Check | Status | Notes |
|-------|--------|-------|
| ✅ Pattern matches constraint (Distributed Monolith) | PASS | ADR-001 |
| ✅ Container choice matches (Docker Compose) | PASS | section 8 |
| ✅ Infrastructure matches (VPS HOSTKEY) | PASS | ADR-008 |
| ✅ Deploy method matches (Docker Compose direct) | PASS | section 8.1 |
| ✅ AI integration via MCP servers | PASS | section 8.2 |
| ✅ Tech stack components specified | PASS | section 4 |
| ✅ Component responsibilities defined | PASS | section 3 |
| ✅ Data model complete | PASS | section 5.1 (10 tables) |
| ✅ Security architecture detailed | PASS | section 6 |
| ⚠️ Scalability strategy with thresholds | WARN | sections 7, но без конкретных RPS thresholds для horizontal scaling triggers |
| ✅ All endpoints have DB design | PASS | tables map to API contracts |
| ✅ Diagrams included | PASS | C4_Diagrams.md (full set) |
| ⚠️ Disaster recovery plan | WARN | DR mentioned in Completion.md, но cross-region failover не детализирован |
| ⚠️ Rate limiting design | PARTIAL | per-endpoint в Refinement, но не в Architecture |
| ✅ Logging strategy | PASS | Completion.md section "Logging Strategy" |
| ✅ Compliance (152-ФЗ) | PASS | ADR + Architecture section 6.5 |

### Issues

**WARN-A1: Horizontal scaling triggers не quantified**
- Architecture описывает что делать при scale (replicas, DB read replica), но **не когда** — нет конкретных RPS/latency thresholds
- **FIX:** Добавить таблицу в Architecture.md section 7:
  ```
  | Trigger | Action |
  |---------|--------|
  | API p95 > 800ms for 1h | scale FastAPI 1→2 replicas |
  | DB connections > 80% pool | add read replica |
  | Celery queue > 5K | scale workers 2→4 |
  ```

**WARN-A2: DR cross-region не детализирован**
- Single-region (Москва, HOSTKEY) — single point of failure
- **FIX:** ADR-016 нужен: cross-region replica strategy (HOSTKEY MSK + secondary VPS in СПб?)

**WARN-A3: Rate limiting в Architecture отсутствует**
- В Refinement.md есть детальная таблица, но в Architecture только упоминание "Nginx rate limit"
- **FIX:** Cross-reference Refinement.md из Architecture.md section 6.4

### Recommendations (non-blocking)
1. Cross-region DR plan для P2
2. Quantified horizontal scaling triggers
3. Cross-references между Architecture / Refinement / Completion для security/perf topics

---

## Validator 4: Pseudocode — 79/100

### Checks Applied

| Check | Status | Notes |
|-------|--------|-------|
| ✅ Story coverage | PASS | 14 stories → 5 core algorithms cover all critical paths |
| ✅ Data structures defined | PASS | TypeScript types for 10 entities |
| ✅ API contracts complete | PASS | All endpoints with request/response examples |
| ✅ State machines | PASS | Mermaid diagrams for 3 entities |
| ✅ Error handling strategy | PASS | Categories table + standard format |
| ⚠️ Algorithm complexity stated | PARTIAL | 4/5 algorithms have BIG-O; ICP missing exact bound |
| ✅ Concurrency considerations | PASS | SELECT FOR UPDATE pattern, idempotency |
| ✅ Retry policies | PASS | Per-operation retry strategy |
| ⚠️ Edge case handling in code | PARTIAL | Algorithms describe happy path well, edge cases в Refinement, но cross-ref слабый |
| ✅ Idempotency design | PASS | Per-endpoint idempotency mechanism table |
| ⚠️ Test stubs / examples | MISSING | Нет примеров test data для each algorithm |

### Issues

**WARN-P1: ICP algorithm complexity**
- Описано как "O(N + 500*4)" — рекомендую сделать explicit с подсчётом N
- **FIX:** "O(N + K), where N = filtered candidates ≤ 500K, K = uploaded_inns ≤ 5000"

**WARN-P2: Edge cases vs algorithms — cross-reference**
- Algorithms в Pseudocode не ссылаются на edge cases в Refinement
- **FIX:** В каждом algorithm добавить "EDGE CASES: see Refinement.md section X.Y"

**WARN-P3: Test data examples**
- Алгоритмы хороши для разработки, но недостаточно для test stubs
- **FIX:** Создать `docs/test-data-examples.md` с input/output JSON для каждого алгоритма (или отдельная секция в Refinement)

### Recommendations
1. Cross-link algorithms → edge cases → tests
2. Test stubs (input/expected output samples) для core algorithms
3. ICP algorithm: явно обозначить, что MVP rule-based, P2 vector-based — это есть в Pseudocode, но стоит выделить

---

## Validator 5: Cross-document Coherence — 73/100 🟡

### Cross-checks Applied

| Check | Status |
|-------|--------|
| ✅ PRD personas referenced consistently | PASS — Marina/Дмитрий/Анна везде где нужно |
| ✅ Tech stack identical в Architecture vs Completion | PASS |
| ✅ Plans (Free/Starter/Pro/Team) identical в PRD vs Specification | PASS |
| ⚠️ Pricing — некоторые расхождения | WARN |
| ⚠️ MVP scope vs P1/P2 inconsistency | WARN |
| ⚠️ Outreach quota numbers | WARN |
| ✅ Constraints (Distributed Monolith etc.) везде | PASS |
| ⚠️ Security pattern usage | WARN |
| ✅ ADRs cover decisions referenced elsewhere | PASS |

### Found Inconsistencies

**WARN-C1: Pricing recommendation conflict**
- PRD section 8: ARPU Pro = ₽9 990
- Phase 0 Open Question 4: «Pro ₽9 990 vs ₽4 990 для тяги» — undecided
- Solution_Strategy ADR-decision matrix: Pro ₽9 990
- **FIX:** Зафиксировать в ADR-016: «Pro tier launch price ₽9 990 with Founder offer ₽4 990 first 100 customers»

**WARN-C2: MVP scope vs P1**
- PRD MVP Feature Matrix shows AI ICP analyzer as P0 (Sprint 5)
- Solution_Strategy "Phase 1 MVP": "Core search + reveal + Telegram outreach + AI ICP" — consistent
- НО в product-discovery-brief.md (Phase 0) MVP_scope ставит AI ICP под "must_have" — consistent
- ✅ Consistency found на пересмотре (initial false positive)

**WARN-C3: Outreach quota numbers**
- Specification FR-7.1 plans table: Pro = 1 000 outreach msgs/мес
- PRD Section 8 (constraints): не указано
- Pseudocode FR-6.2 audience limits: Pro = 1000 per campaign — ОК
- НО в Specification FR-6.2: "Лимит per campaign: ... 1000 (Pro), 5000 (Team+)"
- **Conflict:** Pro plan total quota 1000/мес, но per-campaign limit 1000 — значит можно сделать только 1 campaign на 1000 в месяц? Или quota измеряется в messages, и можно несколько campaigns суммарно до 1000?
- **FIX:** Specification FR-6.2 уточнить: "per-campaign limit + total monthly outreach limit per plan"

**WARN-C4: Security pattern (encrypted IndexedDB)**
- ADR-007: "MVP scope: эта фича P1 — в MVP используются наши shared keys"
- Architecture section 6.3: "User-side secrets" — описано как готовая фича
- /replicate constraints: "Security pattern: ... If external integrations" — должно быть в MVP
- **Conflict:** P1 vs MVP
- **FIX:** Решить — либо реализуем encrypted IndexedDB для MVP (рекомендуется, т.к. security-critical), либо явно отделяем endpoints, где user-keys нужны (например, "Bring Your Own Key" only для Enterprise) — обновить ADR-007 + Architecture

**WARN-C5: ИНН format validation**
- Specification: "10/12 цифр" (10 для юрлиц, 12 для ИП)
- Pseudocode: "10-12 digits", regex `^\d{10,12}$`
- Architecture SQL: `CHECK (inn ~ '^[0-9]{10,12}$')` — но также допускает 11 цифр (хотя в природе нет 11-значных ИНН)
- **FIX:** SQL constraint уточнить: `CHECK (inn ~ '^[0-9]{10}$|^[0-9]{12}$')`

**WARN-C6: Telegram-as-default vs Email**
- PRD MVP: Telegram only
- Architecture: workers, queues и infrastructure для Email — упомянуты
- ADR-006: "MVP только Telegram, Email в P1"
- **FIX:** Architecture для MVP должна явно отметить Email modules как "P1 (stub в MVP)"

**WARN-C7: Russian regions count**
- Specification: "89 субъектов РФ"
- На 2026 — 89 регионов (Donetsk, Luhansk, Kherson, Zaporizhia включены с 2022)
- ✅ Корректно для текущей конституции

### Recommendations
1. **ADR-016: Pricing decision** — зафиксировать decision о launch price
2. **Quota model clarification** — total monthly vs per-campaign limit
3. **Security pattern decision** — encrypted IndexedDB в MVP или P1 (рекомендую MVP, т.к. это security-critical)
4. **Email infrastructure** — пометить как P1 stubs в Architecture

---

## Aggregate Gap Register

| ID | Source | Severity | Description | Action |
|----|--------|----------|-------------|--------|
| GAP-1 | Stories | LOW | US-3.3, US-5.2, US-1.3 — LLM stories требуют fallback | Add to Refinement |
| GAP-2 | AC | LOW | Latency requirements нужны sample sizes | Spec update |
| GAP-3 | Architecture | LOW | Quantified scale-out triggers | Architecture.md section 7 |
| GAP-4 | Architecture | MED | DR cross-region plan (P2 ADR) | New ADR-016 |
| GAP-5 | Pseudocode | LOW | Test data examples per algorithm | New file or section in Refinement |
| GAP-6 | Coherence | MED | Pricing decision (ADR-016) | Already noted |
| GAP-7 | Coherence | MED | Quota model clarification (per-campaign vs monthly) | Specification fix |
| GAP-8 | Coherence | MED | Security pattern: MVP or P1? | Update ADR-007 |
| GAP-9 | Coherence | LOW | Email infrastructure labeled P1 | Architecture annotation |

**Total gaps:** 9
**Blocking (severity HIGH):** 0
**Medium severity:** 4 (worth fixing before sprint planning)
**Low severity:** 5 (can fix in iteration during development)

---

## Verdict & Action Plan

### Verdict: 🟢 READY (with caveats)

- ✅ Avg score 78 ≥ 70 threshold
- ✅ No blocked stories (all ≥50)
- ✅ Constraints satisfied (Distributed Monolith, Docker, VPS, MCP, security)
- ⚠️ 4 medium-severity coherence gaps — рекомендуется фиксить до старта разработки

### Recommended Actions Before Phase 3

| Priority | Action | Effort |
|----------|--------|--------|
| P0 | Decide pricing (ADR-016) | 5 min |
| P0 | Fix quota model in Specification FR-6.2 | 10 min |
| P0 | Decide MVP scope of encrypted IndexedDB (update ADR-007) | 10 min |
| P1 | Add quantified scale-out triggers to Architecture | 15 min |
| P1 | Add test data examples to Refinement | 30 min |
| P2 | DR cross-region ADR | 30 min (можно отложить до P2 разработки) |
| P2 | LLM fallback behavior in user stories | 20 min |

### Decision: Proceed to Phase 3

Гэпы non-blocking. Можно идти в Phase 3 (Toolkit Generation), параллельно сейчас исправлять Medium-severity items в течение первых 2 спринтов разработки. Toolkit будет генерироваться на текущей документации — обновления документов после Toolkit генерации не повлияют на сам toolkit.

---

## Appendix: Iteration History

**Iteration 1 (2026-05-06):** Initial validation. Score 78/100. 0 blocked, 9 gaps identified.

(Будущие итерации — если потребуются доработки, повторный запуск /replicate Phase 2.)
