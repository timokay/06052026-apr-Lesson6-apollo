---
name: feature-navigator
description: Navigate Apollo (RU) feature roadmap. Reads .claude/feature-roadmap.json, suggests next feature based on status/priority/dependencies. Used by /next command.
version: "1.0"
maturity: production
---

# Feature Navigator — Apollo (RU)

## Purpose

Помогает определять, какую фичу делать следующей, по roadmap'у с учётом:
- Статусов (`done`, `in_progress`, `next`, `planned`, `blocked`)
- Приоритетов (P0 / P1 / P2)
- Зависимостей (depends_on)
- Sprint назначения (Sprint 1-6 для MVP)

## How It Works

### Read roadmap

```python
with open(".claude/feature-roadmap.json") as f:
    roadmap = json.load(f)
```

### Find next candidate

Algorithm (используется `/next` без аргументов):

```
1. Filter features where status == 'next'
2. Sort by priority (P0 first), then sprint (lower first), then depends_on satisfied
3. Return top 1
4. If no 'next' → find highest-priority 'planned' с dependencies satisfied
5. If none → return roadmap summary "all features done или blocked"
```

### Mark feature done

`/next mark-done <feature-id>`:
1. Update status: `done`
2. Add `completed_at` timestamp
3. Cascade: для каждого feature, что depends_on этой → unblock (если все depends done):
   - status: `blocked` → `next` (если всё satisfied)
   - status: `planned` остаётся, но logged "now ready"

### Status summary

`/next status`:
```
═══════════════════════════════════════════════════════════════
📊 ROADMAP STATUS

Sprint 1 (Auth + Search):           4/4 done   ✅
Sprint 2 (Reveal + Export):         2/3 done   🟡 в работе: csv-export
Sprint 3 (Billing):                 0/3 next   ⏳
Sprint 4 (Outreach):                0/3 planned ⏳
Sprint 5 (ICP):                     0/2 planned ⏳
Sprint 6 (Polish):                  0/3 planned ⏳

Overall MVP: 6/18 (33%)
Estimated remaining: ~80 hours

🎯 Suggested next: csv-export (P0, Sprint 2, blocked nothing else)
═══════════════════════════════════════════════════════════════
```

## Roadmap JSON Schema

`.claude/feature-roadmap.json`:

```json
{
  "version": "1.0",
  "project": "apollo-ru",
  "features": [
    {
      "id": "user-auth",
      "title": "User authentication (register, login, JWT, verify)",
      "priority": "P0",
      "sprint": 1,
      "status": "next",
      "estimated_hours": 8,
      "depends_on": [],
      "blocks": ["company-search", "billing"],
      "files_touched": [
        "backend-api/app/routers/auth.py",
        "backend-api/app/services/auth.py",
        "frontend/app/(auth)/**"
      ],
      "completed_at": null
    },
    ...
  ]
}
```

### Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | kebab-case unique identifier |
| `title` | string | Human-readable name |
| `priority` | enum | P0 (must), P1 (should), P2 (nice) |
| `sprint` | integer | Target sprint (1-6 для MVP) |
| `status` | enum | done / in_progress / next / planned / blocked |
| `estimated_hours` | number | Effort estimate |
| `depends_on` | string[] | Feature IDs that must be done before this |
| `blocks` | string[] | Feature IDs that need this done first |
| `files_touched` | string[] | Expected file paths |
| `completed_at` | datetime | Set when status='done' |

## Status Transitions

```
planned → next       (когда все depends_on в 'done')
planned → blocked    (когда depends_on не в 'done' и есть hard dependency)
next → in_progress   (когда /feature или /go запущена)
in_progress → done   (когда /feature Phase 4 complete)
in_progress → blocked (если обнаружен внешний blocker)
blocked → next       (когда blocker resolved)
done → done          (immutable; recreate feature как новая если нужны changes)
```

## Auto-detect Status from Code

`/next update` сканирует codebase и suggests status updates:

```python
def detect_status(feature):
    # Check files exist + non-empty
    files = [Path(f) for f in feature["files_touched"]]
    if all(f.exists() and f.stat().st_size > 100 for f in files):
        # Check tests exist для feature
        test_files = find_tests_for(feature["id"])
        if test_files:
            return "candidate_for_done"
    elif any(f.exists() for f in files):
        return "in_progress"
    return "no_change"
```

Output:
```
Status update suggestions:
  ⬆️ user-auth: next → in_progress  (auth.py exists, ~80 lines)
  ✅ user-auth: in_progress → done   (tests exist, 95% coverage)
  ⏳ company-search: still 'next' (no files yet)

Apply? (y/n)
```

## Apollo MVP Roadmap (target)

| Sprint | Features | Focus |
|--------|----------|-------|
| **1** | user-auth, company-search, company-card, csv-export-basic | Foundation |
| **2** | reveal-with-quota, csv-export-pro, audit-log | Reveal flow |
| **3** | billing-plans, billing-yookassa, quota-reset | Monetization |
| **4** | telegram-outreach-mvp, outreach-personalize, opt-out-flow | Outreach |
| **5** | icp-analyzer, icp-look-alike | AI features |
| **6** | team-seats, monitoring-dashboards, e2e-tests | Polish |

## Failure Modes

| Situation | Resolution |
|-----------|------------|
| `feature-roadmap.json` missing | Generate default from PRD MVP Feature Matrix |
| Two features в `in_progress` | Warning — focus on one. /next покажет both. |
| Circular dependencies | Validate on save — block circular |
| Feature status inconsistent с code | `/next update` для re-sync |

## Related

- `.claude/commands/next.md` — uses this skill
- `.claude/commands/go.md` — uses this skill для feature selection
- `.claude/commands/run.md` — uses этот skill для loop
- `docs/PRD.md` — MVP Feature Matrix (source of truth для initial roadmap)
