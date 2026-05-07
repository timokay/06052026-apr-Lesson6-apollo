---
description: Lightweight implementation plan for simple tasks (≤3 files). Saves to docs/plans/. Faster than /feature (5x).
---

# /plan $ARGUMENTS

## Purpose

Создать лёгкий implementation plan для простых задач без full SPARC lifecycle.

**Когда:** task touches ≤3 files, no architectural impact, no security implications.
**Когда нет:** complex feature → use `/feature`. Architectural decision → use `@architect` agent.

## Process

### Step 1: Understand task

Read $ARGUMENTS. If unclear → ask 2-3 clarification questions.

Quick context loading:
- Read relevant existing code (1-3 files)
- Check `.claude/skills/project-context/SKILL.md` для domain knowledge
- Check `.claude/rules/coding-style.md` для patterns

### Step 2: Plan

Output `docs/plans/<slug>.md`:

```markdown
# Plan: $ARGUMENTS

**Created:** YYYY-MM-DD
**Estimated:** N hours
**Files affected:** [list]

## Goal

<one-line>

## Approach

<2-4 sentences how to solve>

## Steps

1. [ ] Step 1 (file: path/to/file.py)
2. [ ] Step 2 (file: path/to/other.tsx)
3. [ ] Tests for ...
4. [ ] Manual verification: ...

## Acceptance

- [ ] <criterion 1>
- [ ] <criterion 2>

## Risks

- <risk 1 + mitigation>

## Notes

<any context, links к docs, related ADRs>
```

### Step 3: Execute (interactive)

If user wants — start executing immediately:
1. Take first unchecked step
2. Implement
3. Update plan checkbox
4. Commit per logical step
5. Repeat

### Step 4: Auto-commit plan

Stop hook auto-commits `docs/plans/` changes:
```
docs(plans): auto-capture from session
```

## Example

```
/plan add favicon to landing page

→ Creates docs/plans/2026-05-06-add-favicon.md
→ 2 steps: add favicon.ico, update next.config.js
→ Estimated: 0.5h
```

vs `/feature`:
```
/feature user-authentication
→ Creates docs/features/user-authentication/sparc/ (5+ docs)
→ Phases: Plan → Validate → Implement → Review
→ Estimated: 8h+ planning, 16h+ implementation
```

## When to Promote to /feature

If during planning you realize:
- Touches >3 files
- Affects security (auth, billing)
- New API endpoint
- Database schema change
- Architectural decision needed

→ Stop, suggest user run `/feature <name>` instead.

## Output

Plan saved + summary:
```
═══════════════════════════════════════════════════════════════
📋 PLAN CREATED: <task>

📁 docs/plans/<date>-<slug>.md
⏱️ Estimated: N hours
📂 Files: <list>

🚀 Start implementing? (y/n)
═══════════════════════════════════════════════════════════════
```
