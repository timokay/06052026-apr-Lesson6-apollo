# Feature Lifecycle — Apollo (RU)

> Mandatory protocol for feature development via `/feature` command.

## Protocol: 4 Phases

```
Phase 1: PLAN     → /feature triggers sparc-prd-mini → docs/features/<name>/sparc/
Phase 2: VALIDATE → 5 validators swarm → score ≥70 → BDD scenarios
Phase 3: IMPLEMENT → parallel agents read validated docs → code + tests
Phase 4: REVIEW   → brutal-honesty-review swarm → fix criticals
```

## Feature Directory Structure

```
docs/features/<feature-name>/
├── sparc/
│   ├── PRD.md
│   ├── Specification.md
│   ├── Pseudocode.md
│   ├── Architecture.md (if architectural impact)
│   ├── Refinement.md
│   └── Completion.md
├── validation-report.md
├── test-scenarios.md
├── implementation-plan.md
└── review-report.md
```

## Phase 1: PLAN

**Tool:** `sparc-prd-mini` skill
**Mode:** AUTO if context clear, MANUAL if ambiguous (Gate assessment)

**Required outputs:**
- Specification.md with Gherkin acceptance criteria
- Pseudocode.md with algorithms
- Architecture impact noted (если изменяет global architecture — нужно обновлять `docs/Architecture.md`)
- Edge cases identified

**Skip conditions:**
- Trivial change (1-2 lines, e.g., copy update) → use `/plan` instead

**Commit:** `docs(feature): SPARC planning for <name>`

## Phase 2: VALIDATE

**Tool:** `requirements-validator` skill (5-agent swarm)

**Validators:**
1. validator-stories (INVEST, score ≥70)
2. validator-acceptance (SMART, testability)
3. validator-architecture (constraints, completeness)
4. validator-pseudocode (story coverage, edge cases)
5. validator-coherence (cross-doc consistency)

**Iterative loop:** max 3 iterations.

**Pass criteria:**
- All scores ≥50 (no BLOCKED)
- Average ≥70
- No contradictions across docs

**Output:** `validation-report.md` + `test-scenarios.md` (BDD)

**Commit:** `docs(feature): validation complete for <name>`

## Phase 3: IMPLEMENT

**Approach:** Parallel agents read validated SPARC docs.

**Agent assignments:**
- `@architect` — system design decisions (если new patterns)
- `@planner` — task breakdown, dependency analysis
- Implementation tasks via `Task` tool (parallel where possible)
- Tests written **alongside** implementation (TDD-leaning)

**Rules:**
- Read docs as source of truth, **never hallucinate** code
- Modular design — extract reusable units
- Frequent commits (per logical unit)
- Run tests локально перед commit

**Commit:** `feat(<scope>): <what>` per logical unit

## Phase 4: REVIEW

**Tool:** `brutal-honesty-review` skill (5-agent swarm)

**Reviewers:**
1. code-quality (style, complexity, dead code)
2. architecture (alignment с decisions, ADRs)
3. security (OWASP, auth, secrets, audit log)
4. performance (N+1, caching, indexes)
5. testing (coverage, scenarios, edge cases)

**Pass criteria:**
- No critical issues
- Major issues addressed (или explicit defer to debt log)
- Test coverage on critical paths ≥80%

**Output:** `review-report.md`

**Fix:** все critical, обсудить majors

**Commit:** `docs(feature): review complete for <name>`

## Skip Rules Table

| Phase | Skip if |
|-------|---------|
| Phase 1 (PLAN) | NEVER skip — даже trivial features нуждаются в Specification |
| Phase 2 (VALIDATE) | NEVER skip — toolkit зависит от validated docs |
| Phase 3 (IMPLEMENT) | If feature is documentation-only (no code) |
| Phase 4 (REVIEW) | If single-line config change (still recommend) |

## When to Use `/plan` Instead of `/feature`

`/plan` для:
- Bug fix touching ≤3 files
- Config changes
- Documentation updates
- Trivial UI tweaks

`/feature` для:
- Anything user-facing
- Database schema changes
- New API endpoints
- Cross-package changes
- Anything с security implications

`/go` автоматически выбирает между ними.

## /feature-ent (NOT available)

Apollo проект **не использует DDD strategic docs**, поэтому `/feature-ent` не сгенерирован. Все features идут через `/feature` (standard).

Если бизнес домен расширится и потребуется DDD моделирование — добавить документы в `docs/ddd/` и регенерировать toolkit.

## Pre-flight Checks

`/feature` команда выполняет:

1. ✅ Verify required skills exist:
   - `.claude/skills/sparc-prd-mini/SKILL.md`
   - `.claude/skills/requirements-validator/SKILL.md`
   - `.claude/skills/brutal-honesty-review/SKILL.md`
   ABORT если отсутствуют.

2. ⚠️ Warn if optional skills missing:
   - `.claude/skills/explore/SKILL.md`
   - `.claude/skills/goap-research-ed25519/SKILL.md`
   - `.claude/skills/problem-solver-enhanced/SKILL.md`

3. ✅ Verify `docs/features/` directory exists.

4. ✅ Verify не conflict с existing feature directory.

## Apollo-Specific Notes

### When Phase 3 IMPLEMENT touches:

- **Database** → требуется migration (Alembic), forward-compatible (см. ADR-012)
- **External API** (LLM, Telegram, ЮKassa) → required: retry policy, timeout, fallback
- **User-facing** → required: 152-ФЗ check (нет ли утечки PII), opt-out где applicable
- **Billing-related** → required: idempotency, audit log, тесты на race conditions

### Architecture Impact

Если фича меняет:
- Service boundaries → новый ADR
- Tech stack → ADR + update Architecture.md section 4
- Security pattern → review ADR-007, security.md
- Performance characteristics → update NFR в Specification

### Performance Targets

Все новые endpoints должны соответствовать NFR-1 в Specification:
- p99 < 500ms для read endpoints
- p95 < 2s для action endpoints (reveal, etc.)
- LLM operations < 5s per call (с fallback timeout)

## Quality Gates

| Gate | Threshold | Blocks |
|------|-----------|--------|
| Validation score | ≥70 avg | Phase 3 |
| Critical review issues | 0 | Phase 4 commit |
| Test coverage critical paths | 100% | Phase 4 commit |
| Test coverage overall | ≥80% backend, ≥60% frontend | Warning, not block |
| Migration reversibility | Required | Phase 3 commit |
| 152-ФЗ check (если PII touched) | Pass | Phase 4 commit |
