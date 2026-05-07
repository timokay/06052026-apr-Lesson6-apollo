# Git Workflow — Apollo (RU)

## Branch Strategy

- `main` — production. Auto-deploy via GitHub Actions.
- `develop` — staging integration. Manual deploy для smoke tests.
- `feature/<name>` — feature branches от `develop`.
- `fix/<issue>` — bug fixes.
- `claude/<task-id>` — Claude Code automated branches.

PR target: feature/fix → `develop` → squash merge. `develop` → `main` через release PR.

## Commit Format

```
type(scope): short description

Optional longer body explaining the why.

Refs: #123 (если есть issue)
```

### Types

| Type | When |
|------|------|
| `feat` | New feature, новый user-facing capability |
| `fix` | Bug fix |
| `refactor` | Code restructuring, NO behavior change |
| `perf` | Performance improvement |
| `test` | Adding/updating tests only |
| `docs` | Documentation changes (markdown, comments) |
| `chore` | Build, CI, config, dependency updates |
| `style` | Formatting, whitespace (no logic change) |
| `revert` | Revert previous commit |

### Scope (optional)

Используй имя package или domain:
- `auth`, `companies`, `reveals`, `icp`, `campaigns`, `billing`, `etl`, `worker`
- `frontend`, `backend-api`
- `nginx`, `docker`, `ci`

### Examples

```
feat(reveals): add concurrent reveal protection via SELECT FOR UPDATE
fix(campaigns): handle USER_BLOCKED_BOT without charging credit
refactor(billing): extract YooKassa client into separate module
test(icp): add LLM fallback scenarios
docs(architecture): clarify data partitioning strategy
chore(deps): bump fastapi to 0.115.0
perf(search): add composite index on (region, okved_main)
```

## Rules

1. **Commit after each logical change.** Не комбинируй несвязанные изменения в одном коммите.
2. **Imperative mood:** "add feature" not "added feature" / "adds feature".
3. **Краткое описание ≤ 72 chars.** Длиннее — в body.
4. **Не пушь сломанный main.** Если merge сломан — фиксни в течение 1 часа или revert.
5. **No `WIP:` commits в `main`/`develop`.** OK в feature branches.

## Pre-commit Hooks

Установи:
```bash
pip install pre-commit
pre-commit install
```

Hooks:
- ruff format + lint (Python)
- prettier (TS/JS/CSS/MD)
- mypy --strict (Python)
- detect-secrets (no API keys committed)
- trailing-whitespace, end-of-file-fixer

## Pull Requests

### PR Description Template

```markdown
## What
<Brief summary>

## Why
<Context, links to docs/issue>

## How
<Implementation approach>

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing на staging

## Checklist
- [ ] Соответствует coding-style.md
- [ ] Соответствует security.md
- [ ] Audit log запись для critical actions
- [ ] No new secrets committed
- [ ] Documentation updated (если applicable)
```

### Review Requirements

- ≥1 reviewer approval (для develop)
- ≥2 reviewer approval (для main)
- All CI checks green
- No conversations unresolved

## Forbidden Operations

- ❌ `git push --force` в `main` или `develop`
- ❌ `git commit --no-verify` (skip pre-commit hooks)
- ❌ `git commit --amend` для already-pushed commits
- ❌ Direct push в `main` без PR
- ❌ Merge с unresolved conflicts (rebase first)

## Recovery

| Scenario | Solution |
|----------|----------|
| Случайно committed secret | Rotate secret + `git revert` + `git filter-repo` для history |
| Need to undo last commit (local only) | `git reset --soft HEAD~1` |
| Need to undo last commit (already pushed) | `git revert <sha>` (новый коммит, не rewrite) |
| Wrong branch | `git stash` → `git checkout correct` → `git stash pop` |
| Sync with develop | `git fetch && git rebase origin/develop` |

## Tagging Releases

```bash
# Semver tag
git tag -a v1.2.3 -m "Release v1.2.3: <highlights>"
git push origin v1.2.3

# Version bumps
# Major: breaking API changes
# Minor: new features (backwards-compatible)
# Patch: bug fixes only
```

## Hooks Auto-Commit (via Stop hook)

Apollo's `.claude/settings.json` has `Stop` hooks that auto-commit:

1. `myinsights/` — knowledge base updates
2. `.claude/feature-roadmap.json` — roadmap status changes
3. `docs/plans/` — implementation plans

These commits are made by Claude Code automatically. Human commits должны следовать правилам выше.
