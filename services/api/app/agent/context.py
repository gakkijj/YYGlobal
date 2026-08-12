from typing import Any, Dict

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.entities import Memory, Program, Task
from app.services.business import profile_with_experiences


async def build_context(session: AsyncSession, skill_name: str, goal: str) -> Dict[str, Any]:
    profile, experiences = await profile_with_experiences(session)
    memories = list(
        (
            await session.scalars(
                select(Memory)
                .where(Memory.owner_id == settings.local_owner_id, Memory.active.is_(True))
                .order_by(Memory.updated_at.desc())
                .limit(20)
            )
        ).all()
    )
    program_count = await session.scalar(select(func.count()).select_from(Program))
    open_tasks = await session.scalar(
        select(func.count())
        .select_from(Task)
        .where(Task.owner_id == settings.local_owner_id, Task.status != "done")
    )
    return {
        "goal": goal,
        "skill": skill_name,
        "profile": {
            "full_name": profile.full_name,
            "school": profile.current_school,
            "major": profile.current_major,
            "degree": profile.degree,
            "gpa": profile.gpa,
            "gpa_scale": profile.gpa_scale,
            "language_scores": profile.language_scores,
            "target_countries": profile.target_countries,
            "target_fields": profile.target_fields,
            "intake": profile.intake,
            "budget": profile.budget,
            "preferences": profile.preferences,
            "confirmed": profile.confirmed,
        },
        "experiences": [
            {
                "id": item.id,
                "kind": item.kind,
                "title": item.title,
                "organization": item.organization,
                "description": item.description,
                "confirmed": item.confirmed,
            }
            for item in experiences[:20]
        ],
        "memories": [
            {
                "type": item.memory_type,
                "key": item.key,
                "value": item.value,
                "source": item.source_type,
            }
            for item in memories
        ],
        "catalog": {"program_count": program_count or 0},
        "tasks": {"open_count": open_tasks or 0},
        "context_policy": {
            "facts_only": True,
            "unconfirmed_values_are_not_facts": True,
            "token_budget": settings.agent_context_token_budget,
        },
    }
