from typing import Any, Dict, List

from app.agent.skills import Skill

SKILL_STEPS = {
    "applicant-profile": ["读取现有画像", "识别已知与缺失信息", "提出下一步或保存候选事实"],
    "program-research": ["拆解检索条件", "搜索候选项目", "核对官网证据", "汇总结果与待确认项"],
    "program-compare": ["确定比较维度", "读取项目与要求", "校验硬性条件", "输出差异与风险"],
    "shortlist-builder": ["读取画像与约束", "筛选候选项目", "评分并分层", "验证理由和风险"],
    "cv-planner": ["读取项目要求", "检索已确认经历", "选择并排序经历", "检查真实性与缺口"],
    "ps-planner": ["解析项目与题目", "检索已确认经历", "匹配真实素材", "生成提纲并检查贴题"],
    "application-timeline": ["读取截止日期", "拆解申请里程碑", "计算任务日期", "检查依赖与风险"],
}


def build_plan(skill: Skill, goal: str) -> List[Dict[str, Any]]:
    steps = SKILL_STEPS.get(skill.name, ["分析目标", "执行任务", "验证输出"])
    return [
        {
            "id": f"step-{index + 1}",
            "name": name,
            "status": "pending",
            "dependencies": [] if index == 0 else [f"step-{index}"],
            "expected_output": f"{name}的可验证结果",
        }
        for index, name in enumerate(steps)
    ]


def should_replan(error_type: str) -> bool:
    return error_type in {
        "no_result",
        "source_conflict",
        "goal_changed",
        "hard_constraint_failed",
        "tool_timeout",
        "tool_error",
        "invalid_arguments",
        "permission_denied",
    }


def replan_after_failure(
    plan: List[Dict[str, Any]], error_type: str, tool_name: str
) -> List[Dict[str, Any]]:
    """Preserve verified work and annotate the remaining plan with a bounded recovery step."""
    updated = [dict(item) for item in plan]
    recovery = {
        "id": f"recovery-{sum(1 for item in updated if str(item['id']).startswith('recovery-')) + 1}",
        "name": f"处理 {tool_name} 的 {error_type}",
        "status": "pending",
        "dependencies": [
            item["id"] for item in updated if item.get("status") == "completed"
        ],
        "expected_output": "改用更安全的参数、替代工具，或明确返回待确认项",
        "recovery": True,
    }
    updated.append(recovery)
    return updated
