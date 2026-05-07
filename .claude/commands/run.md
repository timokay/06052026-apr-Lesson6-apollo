---
description: Autonomous build loop. /run for MVP scope, /run all for everything in roadmap. Bootstrap → /next → /go → repeat.
---

# /run $ARGUMENTS

## Subcommands

| Usage | Action |
|-------|--------|
| `/run` или `/run mvp` | Build all MVP features (P0 only) until done или blocked |
| `/run all` | Build all features (P0 + P1 + P2) |
| `/run sprint [N]` | Build только Sprint N features |
| `/run feature [id]` | Build single feature (≈ /go [id]) |
| `/run pause` | Pause current run (saves state) |
| `/run resume` | Resume paused run |

## Process

### Step 1: Bootstrap (if needed)

```python
if not Path(".apollo-initialized").exists():
    print("Project not initialized. Running /start first...")
    invoke /start
    if /start failed:
        ABORT
```

### Step 2: Determine Scope

- `/run` или `/run mvp` → filter `priority=='P0'`
- `/run all` → all features (P0+P1+P2)
- `/run sprint N` → filter `sprint == N`
- `/run feature ID` → single feature

### Step 3: Loop

```python
while True:
    # Find next eligible feature
    candidates = roadmap.filter(
        status="next",
        deps_satisfied=True,
        in_scope=scope,
    )
    if not candidates:
        # Try `planned` features that are now ready
        candidates = roadmap.filter(
            status="planned",
            deps_satisfied=True,
            in_scope=scope,
        )
    
    if not candidates:
        break  # All done или all blocked
    
    feature = sort_by_priority_then_sprint(candidates)[0]
    
    # Run /go (auto-pick pipeline)
    print(f"🚀 Building {feature.id}...")
    result = invoke /go feature.id
    
    if result.success:
        # /go already marked done, cascaded unblocking
        print(f"✅ {feature.id} done")
        commit_and_push()
    else:
        # Halt on failure
        print(f"❌ {feature.id} failed: {result.error}")
        roadmap.set_status(feature.id, "blocked")
        roadmap.add_note(feature.id, f"Auto-halted: {result.error}")
        break  # don't continue if one fails
    
    # Check budget
    if elapsed_time > MAX_RUN_DURATION:
        print("⏱ Max run duration reached, pausing")
        save_run_state()
        break
```

### Step 4: Summary

```
═══════════════════════════════════════════════════════════════
🏁 /run COMPLETE

Scope: MVP (P0 features)
Duration: 18h 42m

Features built:
  ✅ user-auth                    (4h 12m, /feature)
  ✅ company-search               (3h 05m, /feature)
  ✅ company-card                 (2h 18m, /feature)
  ✅ csv-export-basic             (1h 33m, /plan)
  ✅ reveal-with-quota            (3h 27m, /feature)
  ✅ audit-log                    (2h 11m, /feature)
  ❌ telegram-outreach-mvp        FAILED — TG bot token missing

Roadmap status: 12/18 done (67%)

Tests added: 245
Coverage: 82% (backend), 64% (frontend)

🚧 Blocked features (need attention):
  • telegram-outreach-mvp — set TELEGRAM_BOT_TOKEN in .env
  • billing-yookassa — depends on telegram-outreach-mvp? (no, depends on user-auth — done)

🚀 Next:
  Resolve blockers, then /run resume
  Or /run all to continue с P1/P2
═══════════════════════════════════════════════════════════════
```

## Pause / Resume

State saved to `.claude/.run-state.json`:
```json
{
  "scope": "mvp",
  "started_at": "2026-05-06T10:00:00Z",
  "paused_at": "2026-05-06T11:30:00Z",
  "completed": ["user-auth", "company-search"],
  "in_progress": "company-card",
  "remaining_in_scope": ["csv-export-basic", "reveal-with-quota", ...]
}
```

`/run pause`:
- Save state
- If feature in_progress — finish current Phase, then pause
- Don't block waiting on confirmation

`/run resume`:
- Load state
- Continue from in_progress (или next)

## Safety Limits

| Limit | Default | Reason |
|-------|---------|--------|
| Max run duration | 8 hours | Prevent runaway sessions |
| Max consecutive failures | 2 | Stop if pipeline broken |
| Max API cost (estimated) | $20 | Prevent surprise bills |
| Required: clean git tree | yes | Don't mix manual + automated changes |
| Required: tests pass | yes | Don't proceed if previous broke things |

## Auto-commit Strategy

После каждой successful feature:
1. Roadmap update committed (auto via Stop hook)
2. Implementation commits (per logical unit, made в /feature Phase 3)
3. Push к origin при end of feature (graceful если network fails — retry next iteration)

## Failure Handling

| Failure | Action |
|---------|--------|
| Validation score < 70 после 3 iterations | Mark feature `blocked`, halt run, prompt user |
| Test failure после implementation | Halt feature, mark `blocked`, halt run |
| External API down (LLM/TG/YK) | Retry с backoff, if 3 fails — pause |
| Disk full | Halt immediately, alert |
| Out of LLM credits | Halt, alert |
| Lost network | Pause, save state |

## Hierarchy

```
/run (autonomous loop)
  ├─ checks /start done
  ├─ loop:
  │   ├─ /next (find feature)
  │   └─ /go (pick pipeline)
  │       ├─ /plan (simple)
  │       └─ /feature (complex)
  └─ summary
```

## Related

- `.claude/commands/next.md`
- `.claude/commands/go.md`
- `.claude/commands/start.md` (bootstrap)
- `.claude/skills/feature-navigator/SKILL.md` (roadmap logic)
- `.claude/feature-roadmap.json` (data)
