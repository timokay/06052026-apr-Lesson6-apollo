---
description: Show next feature to work on. Reads .claude/feature-roadmap.json. Subcommands: status, update, mark-done.
---

# /next $ARGUMENTS

## Subcommands

| Usage | Action |
|-------|--------|
| `/next` | Show recommended next feature |
| `/next status` | Roadmap overview (по sprints + progress) |
| `/next update` | Auto-detect status from codebase, suggest updates |
| `/next [feature-id]` | Mark feature as done, cascade unblocking |
| `/next blocked` | Show all blocked features + reasons |
| `/next sprint [N]` | Show features в Sprint N |

## /next (default — show what to do)

Process:
1. Read `.claude/feature-roadmap.json`
2. Filter `status == 'next'`
3. Sort by priority (P0 > P1 > P2), sprint (lower first)
4. Return top candidate

Output:
```
═══════════════════════════════════════════════════════════════
🎯 NEXT FEATURE: user-auth

Priority: P0 (Sprint 1)
Estimated: 8 hours
Depends on: nothing
Blocks: company-search, billing-plans, audit-log

Description: User registration (email + password), login (JWT in httpOnly cookie),
email verification, password reset, refresh token rotation.

Files affected:
  • backend-api/app/routers/auth.py
  • backend-api/app/services/auth.py
  • backend-api/app/repositories/user.py
  • backend-api/app/models/user.py
  • backend-api/alembic/versions/XXX_init_users.py
  • frontend/app/(auth)/register/page.tsx
  • frontend/app/(auth)/login/page.tsx
  • frontend/app/(auth)/verify/page.tsx

🚀 Suggested approach:
  /go user-auth        — auto-pick pipeline (will use /feature)
  /feature user-auth   — manual full SPARC lifecycle
  /plan user-auth      — NOT recommended (too complex for /plan)
═══════════════════════════════════════════════════════════════
```

## /next status

```
═══════════════════════════════════════════════════════════════
📊 ROADMAP OVERVIEW

Sprint 1: Foundation       [✅✅⏳⏳]   2/4 done
  ✅ user-auth                          (8h)
  ✅ company-search                     (6h)
  ⏳ company-card               in_progress
  ⏳ csv-export-basic           next

Sprint 2: Reveal           [⏳⏳⏳]    0/3 next
  ⏳ reveal-with-quota          next (P0)
  ⏳ csv-export-pro             planned (depends on csv-export-basic)
  ⏳ audit-log                  next (P0)

Sprint 3: Billing          [⏳⏳⏳]    0/3 planned (blocked: depends on user-auth)
Sprint 4: Outreach         [⏳⏳⏳]    0/3 planned
Sprint 5: ICP              [⏳⏳]      0/2 planned
Sprint 6: Polish           [⏳⏳⏳]    0/3 planned

OVERALL MVP: 2/18 (11%)  ~110 hours remaining

🎯 Active: company-card (in_progress)
🎯 Next:   csv-export-basic OR reveal-with-quota
═══════════════════════════════════════════════════════════════
```

## /next update

Scan codebase, suggest status updates:

```python
# Logic
for feature in roadmap['features']:
    expected_files = feature['files_touched']
    actual_state = analyze_files(expected_files)
    
    if actual_state.all_exist and actual_state.has_tests:
        suggest 'in_progress' → 'done'
    elif actual_state.any_exist:
        suggest 'next' → 'in_progress'
    elif actual_state.none_exist and feature['status'] == 'in_progress':
        suggest 'in_progress' → 'next'
```

Output:
```
═══════════════════════════════════════════════════════════════
🔄 STATUS UPDATE SUGGESTIONS

Feature                    Current        →   Suggested        Reason
user-auth                  in_progress    →   done            Tests exist (95% coverage), all files present
company-card               next           →   in_progress     auth.py has 80 lines, 3/4 files exist
csv-export-pro             planned        →   blocked         Depends on csv-export-basic (still next)

Apply all? (y / individual)
═══════════════════════════════════════════════════════════════
```

## /next [feature-id] — mark done

```
/next user-auth
```

1. Set `status: 'done'`, `completed_at: now()`
2. Cascade: для каждого feature что depends_on user-auth:
   - If all депс done → unblock (status: blocked → next или planned → next)
   - Log: "company-search now ready"
3. Commit roadmap changes (auto via Stop hook)
4. Show next recommendation

```
✅ user-auth marked DONE

🔓 Unblocked:
  • company-search   (status: next)
  • billing-plans    (now planned, depends on user-auth done)
  • audit-log        (status: next)

🎯 Suggested next: company-search (P0, no further deps)
```

## /next blocked

```
═══════════════════════════════════════════════════════════════
🚧 BLOCKED FEATURES (3)

billing-yookassa          blocked by:  user-auth (in_progress)
                                      billing-plans (planned)

team-seats                blocked by:  user-auth (in_progress)
                                      billing-plans (planned)

monitoring-dashboards     blocked by:  metrics-instrumentation (planned, P2)
═══════════════════════════════════════════════════════════════
```

## /next sprint [N]

```
/next sprint 2

═══════════════════════════════════════════════════════════════
📋 SPRINT 2 — Reveal

🎯 Focus: reveal flow с quota deduction + audit log

Features (3):
  ⏳ reveal-with-quota         next       P0   8h    No deps
  ⏳ csv-export-pro            planned    P1   4h    Depends: csv-export-basic
  ⏳ audit-log                 next       P0   6h    No deps

Total estimated: 18 hours

🚀 Recommended order:
  1. audit-log (foundational для compliance)
  2. reveal-with-quota (uses audit-log)
  3. csv-export-pro (after csv-export-basic done in Sprint 1)
═══════════════════════════════════════════════════════════════
```

## Hook Integration

`SessionStart` hook automatically shows brief context:

```
🎯 Apollo (RU) — Session start

Roadmap status: 6/18 done (33%)
Active: company-card (in_progress)
Suggested next: csv-export-basic

Recent activity:
  ✅ company-search committed 2 hours ago (a1b2c3d)
  ⏳ company-card в работе

Insights since last session:
  📚 INS-007 added: pgvector ivfflat probes parameter
```

## Forbidden

- ❌ Marking feature 'done' если код не существует
- ❌ Skipping dependencies (если depends_on не done — нельзя начать)
- ❌ Manual edit `feature-roadmap.json` без validation (use this command)

## Related

- `.claude/skills/feature-navigator/SKILL.md` — navigation logic
- `.claude/feature-roadmap.json` — data
- `.claude/hooks/feature-context.py` — SessionStart hook
- `.claude/commands/go.md` — auto-pick pipeline для feature
- `.claude/commands/run.md` — autonomous loop
