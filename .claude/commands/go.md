---
description: Smart pipeline selector. Analyzes feature complexity, picks /plan or /feature automatically.
---

# /go $ARGUMENTS

## Purpose

Auto-pick implementation pipeline (`/plan` или `/feature`) на основе complexity scoring.

## Usage

```
/go user-auth        # explicit feature ID from roadmap
/go "add favicon"    # ad-hoc task description
/go                  # use /next to find feature, then go
```

## Step 1: Determine Target

If $ARGUMENTS:
- Matches roadmap feature ID → use that feature
- Otherwise → treat as ad-hoc task description

If empty:
- Run `/next` logic → use returned feature
- If no `next` feature → pick first `planned` (с deps satisfied)
- If nothing → exit с message "Roadmap empty или all blocked"

## Step 2: Complexity Scoring

| Signal | Weight |
|--------|--------|
| Feature touches > 3 files | +2 |
| New API endpoint | +2 |
| Database schema change (migration needed) | +3 |
| External integration (LLM, TG, YK, СПАРК) | +3 |
| Auth / authz changes | +3 |
| Billing / quota changes | +3 |
| Frontend page (new) | +1 |
| Frontend component (new) | +0.5 |
| Bug fix | -1 |
| Config change only | -2 |
| Documentation only | -2 |
| Has DDD bounded context | +2 (toward /feature-ent if available) |

### Scoring Buckets

| Score | Pipeline | Why |
|-------|----------|-----|
| ≤ -2 | `/plan` | Trivial, lightweight plan sufficient |
| -1 to +4 | `/feature` | Standard SPARC lifecycle |
| ≥ +5 | `/feature-ent` IF available, else `/feature` | Complex enterprise feature |

**Note:** `/feature-ent` not generated for Apollo (no DDD docs), so always use `/feature` для complex.

## Step 3: Confirm

Show analysis to user:
```
═══════════════════════════════════════════════════════════════
🤔 PIPELINE SELECTION

Feature: user-auth
Complexity score: +7
  +3 auth changes
  +2 new endpoints (4)
  +2 files affected (8 estimated)

Selected pipeline: /feature
  (would be /feature-ent at +5+ but DDD not available)

Reasoning: Auth involves security, multiple files, и new endpoints — needs full SPARC lifecycle с validation + brutal-honesty review.

Proceed? (y/n)
═══════════════════════════════════════════════════════════════
```

## Step 4: Execute

Based on selection:

### `/plan` selected

```bash
/plan <feature-id-or-description>
```

For roadmap features:
- Update status: `next` → `in_progress`
- Run `/plan` который creates `docs/plans/<slug>.md`
- After plan execution → `/next mark-done <feature-id>`

### `/feature` selected

```bash
/feature <feature-id>
```

For roadmap features:
- Update status: `next` → `in_progress`
- Run `/feature` (4 phases)
- After Phase 4 complete → `/next mark-done <feature-id>` cascade unblocking

### `/feature-ent` selected (NOT available для Apollo)

```
⚠️ Complex feature (score: +6) but /feature-ent not available в этом проекте
   (no DDD documentation in docs/ddd/).
   
Falling back to /feature with extra attention to architecture.

Recommendation: Create manual ADR в docs/ADR.md если architectural decision made.
```

## Step 5: Post-Implementation

After pipeline completes:

1. Update `.claude/feature-roadmap.json`:
   - status → `done`
   - completed_at → now()
   - files → actual files touched
2. Commit roadmap (auto via Stop hook)
3. Show next suggestion:

```
═══════════════════════════════════════════════════════════════
✅ /go user-auth COMPLETE

Pipeline: /feature
Duration: 4h 23m
Files: 12 modified
Tests: 47 added (95% coverage)

🔓 Unblocked features:
  • company-search (P0, ready)
  • billing-plans (P1, ready)
  • audit-log (P0, ready)

🎯 Next suggested: company-search (P0, no further deps)

🚀 Continue?
  /go              — auto-pick next
  /run             — autonomous loop (until blocked)
  /next status     — see roadmap overview
═══════════════════════════════════════════════════════════════
```

## Anti-patterns

❌ `/go` для tasks NOT in roadmap (use `/plan` или `/feature` directly)
❌ Skipping confirmation на complex score
❌ Using `/go` для bug fixes (use `/plan` directly)
❌ Running `/go` без `/start` first (project not initialized)

## Forbidden

- Launching raw `Task` tool без going через `/plan`/`/feature` pipelines
- Bypassing complexity check ("just use /plan для everything")

## Hierarchy

```
/run (autonomous loop)
  └─ /next (find feature)
      └─ /go (auto-pick pipeline)
          ├─ /plan (simple)
          └─ /feature (complex)
              └─ Phase 1-4 + agents + skills
```

## Related

- `.claude/commands/next.md` — feature selection
- `.claude/commands/plan.md` — lightweight pipeline
- `.claude/commands/feature.md` — full SPARC lifecycle
- `.claude/commands/run.md` — autonomous loop
- `.claude/skills/feature-navigator/SKILL.md` — roadmap logic
