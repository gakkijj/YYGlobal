"""Deadline countdown Skill：根据申请截止日期计算剩余天数。

零第三方依赖，可单独运行：

    python Core-Agent/deadline_countdown.py 2026-12-01
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from typing import Any


class DeadlineCountdownSkill:
    """留学申请场景下的轻量 Skill：判断截止日期有多紧急。"""

    name = "deadline_countdown"
    description = "根据 ISO 日期计算距申请截止日期的剩余天数和紧急程度"

    def run(self, deadline: str, today: str | None = None) -> dict[str, Any]:
        due = _parse_iso_date(deadline, "deadline")
        current = _parse_iso_date(today, "today") if today else date.today()
        remaining = (due - current).days
        return {
            "deadline": due.isoformat(),
            "today": current.isoformat(),
            "days_remaining": remaining,
            "urgency": _urgency(remaining),
        }


def _parse_iso_date(value: str, field: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"{field} 必须是 YYYY-MM-DD，收到 {value!r}") from exc


def _urgency(days_remaining: int) -> str:
    if days_remaining < 0:
        return "overdue"
    if days_remaining <= 7:
        return "critical"
    if days_remaining <= 30:
        return "soon"
    return "planned"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=DeadlineCountdownSkill.description)
    parser.add_argument("deadline", help="截止日期，格式 YYYY-MM-DD")
    parser.add_argument("--today", help="可选对照日期，默认使用今天")
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    try:
        result = DeadlineCountdownSkill().run(deadline=args.deadline, today=args.today)
    except ValueError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
