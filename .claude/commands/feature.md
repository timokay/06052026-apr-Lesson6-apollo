---
description: Full SPARC feature lifecycle — Plan -> Validate -> Implement -> Review with quality gates.
---

# /feature $ARGUMENTS

## Purpose

Запустить полный 4-фазный lifecycle для feature разработки: SPARC documentation → swarm validation → parallel implementation → brutal-honesty review.

**Использование:**
```
/feature user-authentication
/feature reveal-with-quota
/feature telegram-outreach
```

## Pre-flight Checks

ABORT if missing:
- `.claude/skills/sparc-prd-mini/SKILL.md`
- `.claude/skills/requirements-validator/SKILL.md`
- `.claude/skills/brutal-honesty-review/SKILL.md`

WARN if missing:
- `.claude/skills/explore/SKILL.md`
- `.claude/skills/goap-research-ed25519/SKILL.md`
- `.claude/skills/problem-solver-enhanced/SKILL.md`

Verify:
- `docs/features/<name>/` does not already exist (если exists — ASK перезаписать или resume)

## Phase 1: PLAN (sparc-prd-mini)

### Setup
```bash
mkdir -p docs/features/$ARGUMENTS/sparc
```

### Run sparc-prd-mini
1. Read `.claude/skills/sparc-prd-mini/SKILL.md`
2. **Gate Assessment:** is feature scope clear from $ARGUMENTS + project context?
   - Clear → AUTO mode
   - Ambiguous → run explore skill для clarification
3. **Pre-fill context** from project docs:
   - PRD personas → use as feature target users
   - Architecture constraints → enforce (Distributed Monolith, Docker, etc.)
   - Security pattern → apply (encrypted IndexedDB if user-side keys)
4. Generate documents в `docs/features/$ARGUMENTS/sparc/`:
   - `Specification.md` — Gherkin AC + NFR
   - `Pseudocode.md` — algorithms, API contracts
   - `Architecture.md` — only if has architectural impact
   - `Refinement.md` — edge cases, tests
   - `Completion.md` — deployment notes (если applicable)

### Commit
```bash
git add docs/features/$ARGUMENTS/sparc/
git commit -m "docs($ARGUMENTS): SPARC planning"
```

## Phase 2: VALIDATE (requirements-validator swarm)

### Run 5 validators in parallel

Spawn `Task` tool with 5 parallel agents:

```
Task: validator-stories
  Read: docs/features/$ARGUMENTS/sparc/Specification.md
  Apply: INVEST criteria to user stories
  Output: stories validation portion

Task: validator-acceptance
  Read: same Specification.md (Gherkin AC sections)
  Apply: SMART criteria
  Output: AC validation portion

Task: validator-architecture
  Read: docs/features/$ARGUMENTS/sparc/Architecture.md (if exists)
        + docs/Architecture.md (project-wide)
  Check: alignment with constraints, completeness
  Output: architecture validation portion

Task: validator-pseudocode
  Read: docs/features/$ARGUMENTS/sparc/Pseudocode.md
  Check: story coverage, algorithm correctness, edge cases
  Output: pseudocode validation portion

Task: validator-coherence
  Read: ALL files в docs/features/$ARGUMENTS/sparc/
        + docs/PRD.md, docs/Architecture.md, docs/ADR.md
  Check: cross-document consistency, no contradictions
  Output: coherence validation portion
```

### Aggregate
Combine 5 validator outputs into `docs/features/$ARGUMENTS/validation-report.md`.

### Iteration loop (max 3 iterations)
```
WHILE (avg_score < 70 OR has_blocked_items) AND iteration < 3:
  Identify gaps from validation report
  Auto-fix clear gaps в Specification/Pseudocode (если простые)
  Re-run validators on changed sections
  iteration++

IF still failing after 3 iterations:
  HALT, ask user для manual fix
```

### Pass criteria
- ✅ All scores ≥50 (no BLOCKED)
- ✅ Average ≥70
- ✅ No cross-document contradictions

### Generate BDD scenarios
Create `docs/features/$ARGUMENTS/test-scenarios.md` с:
- Happy path (1-2)
- Errors (2-3)
- Edge cases (1-2)
- Security (если auth/PII touched)

### Commit
```bash
git add docs/features/$ARGUMENTS/validation-report.md
git add docs/features/$ARGUMENTS/test-scenarios.md
git commit -m "docs($ARGUMENTS): validation complete (score: $AVG/100)"
```

## Phase 3: IMPLEMENT (parallel agents)

### Read validated docs as source of truth
- `docs/features/$ARGUMENTS/sparc/Specification.md`
- `docs/features/$ARGUMENTS/sparc/Pseudocode.md`
- `docs/features/$ARGUMENTS/test-scenarios.md`
- `docs/features/$ARGUMENTS/sparc/Architecture.md` (если есть)

### Decompose into tasks (use @planner agent)
```
Task: planner agent
  Input: validated docs
  Output: implementation-plan.md с задачами:
    - File path
    - Module/function
    - Dependencies (other tasks)
    - Estimated complexity (XS/S/M/L)
    - Test requirements
```

Save plan: `docs/features/$ARGUMENTS/implementation-plan.md`

### Execute tasks in parallel (где возможно)

Group by independence:

**Group 1 (parallel):** Independent units
- Backend models + migrations (Alembic)
- Frontend components (UI only, no API yet)
- Tests stubs

**Group 2 (after Group 1):** Dependent units
- Backend services + repositories (uses models)
- Frontend API hooks (uses components)
- Integration tests

**Group 3:** Wire-up
- Backend routers (uses services)
- Frontend pages (uses hooks)
- E2E tests

### Implementation rules
- **Read docs, never hallucinate** — каждая function основана на Pseudocode
- **Modular design** — extract reusable utilities
- **TDD-leaning** — test parallel с code
- **Frequent commits** — per logical unit, not giant commits
- **Run tests локально** перед commit

### Commit format
```
feat($ARGUMENTS): <what specifically>
```

Examples:
```
feat(reveals): add atomic reveal with SELECT FOR UPDATE
feat(reveals): add quota deduction logic
feat(reveals): add API endpoint POST /reveals
test(reveals): add concurrent reveal scenarios
```

## Phase 4: REVIEW (brutal-honesty-review swarm)

### Run 5 review agents in parallel

```
Task: code-quality-reviewer
  Check: style violations, dead code, complexity, naming, dry/wet balance
  Severity: critical (blocks) / major / minor

Task: architecture-reviewer
  Check: alignment с ADRs, service boundaries, dependency direction
  
Task: security-reviewer
  Check: OWASP Top 10, auth/authz, secrets, audit log, 152-ФЗ compliance

Task: performance-reviewer
  Check: N+1 queries, missing indexes, caching opportunities, frontend bundle

Task: testing-reviewer
  Check: coverage critical paths, edge cases tested, mocks proper
```

### Aggregate
Combine into `docs/features/$ARGUMENTS/review-report.md` с severity ratings.

### Fix loop
```
FOR each critical issue:
  Fix in code
  Re-run relevant review agent on changed files
  
FOR each major issue:
  Fix or add to debt log с justification
  
FOR each minor issue:
  Defer (note в review-report)
```

### Final pass criteria
- ✅ 0 critical issues remaining
- ✅ Major issues addressed или explicitly deferred (с notes)
- ✅ Test coverage ≥80% (backend), ≥60% (frontend) для new code
- ✅ Critical paths 100% covered (auth, billing, reveal — если касаются)

### Commit
```bash
git add docs/features/$ARGUMENTS/review-report.md
git commit -m "docs($ARGUMENTS): review complete"
```

## Phase 5: Roadmap Update

```bash
# Mark feature as 'done' in roadmap
python3 -c "
import json
with open('.claude/feature-roadmap.json', 'r') as f:
    rm = json.load(f)
for f_obj in rm['features']:
    if f_obj['id'] == '$ARGUMENTS':
        f_obj['status'] = 'done'
        f_obj['completed_at'] = '$(date -Iseconds)'
        break
with open('.claude/feature-roadmap.json', 'w') as f:
    json.dump(rm, f, indent=2, ensure_ascii=False)
"
git add .claude/feature-roadmap.json
git commit -m "docs(roadmap): mark $ARGUMENTS as done"
```

## Final Summary

```
═══════════════════════════════════════════════════════════════
✅ /feature $ARGUMENTS COMPLETE

📊 Phase scores:
  Phase 1 PLAN:     SPARC docs created (X files)
  Phase 2 VALIDATE: avg XX/100, N iterations
  Phase 3 IMPLEMENT: M files modified, K commits
  Phase 4 REVIEW:   Y critical fixed, Z majors addressed

📁 Artifacts:
  docs/features/$ARGUMENTS/
  ├── sparc/           # SPARC docs
  ├── validation-report.md
  ├── test-scenarios.md
  ├── implementation-plan.md
  └── review-report.md

🚀 Next:
  /next        — see next feature to build
  /run         — continue MVP loop
═══════════════════════════════════════════════════════════════
```

## Failure Modes

| Phase | Failure | Action |
|-------|---------|--------|
| 1 | sparc-prd-mini не может generate | ABORT, show error, ask user clarify |
| 2 | Validation < 70 после 3 iterations | HALT, ask user manual fix |
| 3 | Implementation breaks tests | Halt, fix immediately, не proceed |
| 3 | Migration не reversible | Halt, refactor migration |
| 4 | Critical security issue | HALT, fix mandatory before commit |

## Notes

- Phase 1 → 4 — strict order, не skip
- Phase 1 + 2 — могут retry если результаты не устраивают
- Phase 3 — naturally parallel; используй Task tool aggressively
- Phase 4 — самый важный для quality; не cut corners
