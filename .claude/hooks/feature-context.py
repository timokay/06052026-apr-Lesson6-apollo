#!/usr/bin/env python3
"""
SessionStart hook for Apollo (RU).

Outputs context snapshot to inject into Claude Code session:
- Sprint progress
- Current/next features from roadmap
- Recent commits
- Insights since last session
- Blockers

Reads .claude/feature-roadmap.json + git log + myinsights/.
Timeout: 10s. If anything fails — prints minimal fallback.
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone


def safe_run(cmd: list[str], timeout: int = 5) -> str:
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ""


def load_roadmap() -> dict | None:
    path = Path(".claude/feature-roadmap.json")
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def render_status(roadmap: dict) -> str:
    features = roadmap.get("features", [])
    if not features:
        return ""

    by_status = {"done": 0, "in_progress": 0, "next": 0, "planned": 0, "blocked": 0}
    by_sprint: dict[int, dict[str, int]] = {}

    for f in features:
        status = f.get("status", "planned")
        by_status[status] = by_status.get(status, 0) + 1
        sprint = f.get("sprint", 0)
        by_sprint.setdefault(sprint, {"total": 0, "done": 0})
        by_sprint[sprint]["total"] += 1
        if status == "done":
            by_sprint[sprint]["done"] += 1

    total = len(features)
    done = by_status.get("done", 0)
    pct = (done * 100 // total) if total else 0

    lines = [f"Roadmap: {done}/{total} ({pct}%)"]

    in_progress = [f for f in features if f.get("status") == "in_progress"]
    if in_progress:
        names = ", ".join(f["id"] for f in in_progress)
        lines.append(f"Active: {names}")

    next_candidates = [f for f in features if f.get("status") == "next"]
    if next_candidates:
        next_candidates.sort(key=lambda f: (f.get("priority", "P2"), f.get("sprint", 99)))
        top = next_candidates[0]
        lines.append(f"Suggested next: {top['id']} ({top.get('priority', '?')}, "
                     f"~{top.get('estimated_hours', '?')}h)")

    blocked = [f for f in features if f.get("status") == "blocked"]
    if blocked:
        names = ", ".join(f["id"] for f in blocked[:3])
        lines.append(f"Blocked ({len(blocked)}): {names}")

    return "\n".join(lines)


def render_recent_commits() -> str:
    log = safe_run(["git", "log", "--oneline", "-5", "--no-decorate"])
    if not log:
        return ""
    return "Recent commits:\n" + "\n".join(f"  {line}" for line in log.split("\n"))


def render_recent_insights() -> str:
    index = Path("myinsights/1nsights.md")
    if not index.exists():
        return ""

    try:
        recent = safe_run(["git", "log", "--since=7.days", "--name-only",
                          "--pretty=format:", "--diff-filter=A", "myinsights/"])
        if not recent:
            return ""
        added = [f for f in recent.split("\n")
                 if f.startswith("myinsights/INS-") and f.endswith(".md")]
        if not added:
            return ""
        return f"New insights last 7d: {len(added)} (см. /myinsights status)"
    except Exception:
        return ""


def render_uncommitted() -> str:
    status = safe_run(["git", "status", "--porcelain"])
    if not status:
        return ""
    lines = status.split("\n")
    return f"⚠️ Uncommitted: {len(lines)} files (review before /run)"


def main() -> int:
    if not Path(".git").exists():
        return 0

    parts = ["🎯 Apollo (RU) — Session start\n"]

    roadmap = load_roadmap()
    if roadmap:
        status = render_status(roadmap)
        if status:
            parts.append(status)

    commits = render_recent_commits()
    if commits:
        parts.append(commits)

    insights = render_recent_insights()
    if insights:
        parts.append(insights)

    uncommitted = render_uncommitted()
    if uncommitted:
        parts.append(uncommitted)

    parts.append("Commands: /next, /go, /run, /feature, /plan, /test, /deploy, /myinsights, /docs")

    print("\n\n".join(parts))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"feature-context hook failed: {e}", file=sys.stderr)
        sys.exit(0)
