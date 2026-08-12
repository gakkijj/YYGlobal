from datetime import date, timedelta
from typing import List, Optional

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.entities import (
    ApplicantProfile,
    ApplicationPackage,
    Document,
    Experience,
    MaterialArtifact,
    MaterialDraft,
    MaterialPlan,
    Program,
    ProgramRequirement,
    Shortlist,
    ShortlistItem,
    Task,
)
from app.schemas.api import ProfileUpdate, TaskCreate

DEFAULT_MATERIALS = ["CV", "PS", "成绩单", "推荐信", "语言成绩"]

MATERIAL_ALIASES = {
    "cv": ("CV", "Resume", "Curriculum Vitae", "简历"),
    "ps": ("PS", "Statement of Purpose", "Personal Statement", "Essay", "个人陈述", "文书"),
    "transcript": ("Transcript", "成绩单"),
    "recommendation": ("Recommendation", "Reference", "推荐信"),
    "language": ("TOEFL", "IELTS", "Language", "语言成绩"),
    "writing_sample": ("Writing Sample", "写作样本"),
    "portfolio": ("Portfolio", "作品集"),
    "video_essay": ("Video Essay", "视频文书"),
}


def material_key(name: str) -> str:
    lowered = name.lower()
    for key, aliases in MATERIAL_ALIASES.items():
        if any(alias.lower() in lowered for alias in aliases):
            return key
    return "other_" + "_".join(name.lower().split())[:60]


def material_label(key: str, original: str = "") -> str:
    labels = {
        "cv": "CV / Resume", "ps": "PS / Essays", "transcript": "成绩单",
        "recommendation": "推荐信", "language": "语言成绩",
        "writing_sample": "Writing Sample", "portfolio": "作品集",
        "video_essay": "Video Essay",
    }
    return labels.get(key, original or key)

FIELD_ALIASES = {
    "computer science": {"computer science", "computer engineering", "software engineering", "计算机", "软件工程", "人工智能", "ai"},
    "business": {"business", "management", "商科", "管理"},
    "business analytics": {"business analytics", "商业分析"},
    "finance": {"finance", "financial engineering", "金融", "金融工程"},
    "accounting": {"accounting", "会计"},
    "public policy": {"public policy", "public administration", "公共政策", "公共管理"},
}


def canonical_fields(values: List[str]) -> List[str]:
    matches = []
    for value in values:
        lowered = value.strip().lower()
        for canonical, aliases in FIELD_ALIASES.items():
            if any(alias in lowered or lowered in alias for alias in aliases):
                matches.append(canonical)
    matches = list(dict.fromkeys(matches))
    # “Business Analytics”等具体方向也包含 business 字样；具体方向存在时不能再扩展为
    # 整个商科目录，否则精确搜索会混入金融、会计项目。
    if "business" in matches and any(
        item in matches for item in ("business analytics", "finance", "accounting")
    ):
        matches.remove("business")
    return matches


def program_matches_fields(program: Program, values: List[str]) -> bool:
    requested = canonical_fields(values)
    if not requested:
        return True
    if "business" in requested and program.field in {"Business Analytics", "Finance", "Accounting"}:
        return True
    program_fields = set(canonical_fields([program.field]))
    return bool(set(requested) & program_fields)


async def get_or_create_profile(session: AsyncSession) -> ApplicantProfile:
    profile = await session.scalar(
        select(ApplicantProfile).where(ApplicantProfile.owner_id == settings.local_owner_id)
    )
    if profile is None:
        profile = ApplicantProfile(owner_id=settings.local_owner_id)
        session.add(profile)
        await session.commit()
        await session.refresh(profile)
    return profile


async def profile_with_experiences(session: AsyncSession) -> tuple:
    profile = await get_or_create_profile(session)
    experiences = list(
        (
            await session.scalars(
                select(Experience)
                .where(Experience.profile_id == profile.id)
                .order_by(Experience.start_date.desc())
            )
        ).all()
    )
    return profile, experiences


async def update_profile(session: AsyncSession, payload: ProfileUpdate) -> tuple:
    profile = await get_or_create_profile(session)
    fields = payload.model_dump(exclude={"experiences"})
    for key, value in fields.items():
        setattr(profile, key, value)
    await session.execute(delete(Experience).where(Experience.profile_id == profile.id))
    for item in payload.experiences:
        values = item.model_dump(exclude={"id"})
        session.add(
            Experience(
                profile_id=profile.id,
                owner_id=settings.local_owner_id,
                **values,
            )
        )
    await session.commit()
    return await profile_with_experiences(session)


async def search_programs(
    session: AsyncSession,
    query: str = "",
    country: str = "",
    field: str = "",
) -> List[Program]:
    statement = select(Program).where(Program.active.is_(True))
    if query:
        pattern = f"%{query}%"
        statement = statement.where(
            or_(
                Program.name.ilike(pattern),
                Program.university.ilike(pattern),
                Program.field.ilike(pattern),
            )
        )
    if country:
        statement = statement.where(Program.country == country)
    if field:
        statement = statement.where(Program.field.ilike(f"%{field}%"))
    return list((await session.scalars(statement.order_by(Program.university))).all())


async def search_programs_for_profile(
    session: AsyncSession,
    query: str = "",
    country: str = "",
    field: str = "",
    use_profile: bool = True,
) -> List[Program]:
    profile = await get_or_create_profile(session)
    if (
        use_profile
        and not query
        and not field
        and not country
        and (
            not profile.confirmed
            or not profile.target_fields
            or not profile.target_countries
        )
    ):
        return []
    query_fields = canonical_fields([query]) if query else []
    requested_fields = [field] if field else (query_fields or (
        (profile.target_fields or ([profile.current_major] if profile.current_major else []))
        if use_profile and not query else []
    ))
    requested_countries = [country] if country else (profile.target_countries if use_profile and not query else [])
    # “master computer science” 这类自然语言不是项目名，先识别专业语义再筛选；
    # 没识别出专业时才按学校、项目名和字段做普通关键词搜索。
    items = await search_programs(
        session, query="" if query_fields else query, country="", field=""
    )
    if requested_countries:
        items = [item for item in items if item.country in requested_countries]
    if requested_fields:
        items = [item for item in items if program_matches_fields(item, requested_fields)]
    return items


async def get_program(session: AsyncSession, program_id: str) -> Optional[Program]:
    return await session.get(Program, program_id)


async def get_requirement(session: AsyncSession, program_id: str) -> Optional[ProgramRequirement]:
    return await session.scalar(
        select(ProgramRequirement).where(ProgramRequirement.program_id == program_id)
    )


async def score_program(
    profile: ApplicantProfile, program: Program, requirement: Optional[ProgramRequirement]
) -> tuple:
    score = 68.0
    reasons = []
    risks = []
    if profile.target_countries and program.country in profile.target_countries:
        score += 8
        reasons.append("符合目标国家")
    if profile.target_fields and any(
        target.lower() in program.field.lower() or program.field.lower() in target.lower()
        for target in profile.target_fields
    ):
        score += 10
        reasons.append("专业方向匹配")
    if profile.budget and program.tuition:
        if program.tuition <= profile.budget:
            score += 5
            reasons.append("学费在预算范围内")
        else:
            score -= 8
            risks.append("学费可能超过当前预算")
    if requirement and requirement.min_gpa is not None:
        if profile.gpa is None:
            risks.append("尚未填写 GPA，无法判断硬性门槛")
        elif profile.gpa >= requirement.min_gpa:
            score += 5
            reasons.append("达到公开 GPA 门槛")
        else:
            score -= 30
            risks.append(f"当前 GPA 低于公开门槛 {requirement.min_gpa}")
    if requirement and not requirement.verified:
        risks.append("项目要求尚未完成官网重新核验")
    score = max(0, min(100, score))
    tier = "reach" if score < 70 else "target" if score < 85 else "safer"
    return score, tier, reasons or ["与当前申请方向存在基础匹配"], risks


async def create_shortlist(session: AsyncSession, name: str, program_ids: List[str]) -> Shortlist:
    profile = await get_or_create_profile(session)
    shortlist = Shortlist(name=name, owner_id=settings.local_owner_id)
    session.add(shortlist)
    await session.flush()
    rationales = []
    for program_id in dict.fromkeys(program_ids):
        program = await get_program(session, program_id)
        if not program:
            continue
        requirement = await get_requirement(session, program_id)
        score, tier, reasons, risks = await score_program(profile, program, requirement)
        rationale = "；".join(reasons)
        rationales.append(f"{program.university}：{rationale}")
        session.add(
            ShortlistItem(
                shortlist_id=shortlist.id,
                program_id=program.id,
                tier=tier,
                score=score,
                rationale=rationale,
                risks=risks,
                owner_id=settings.local_owner_id,
            )
        )
        await get_or_create_application_package(session, program.id, shortlist.id)
    shortlist.rationale = "基于目标国家、专业、预算和已核验硬性条件生成。"
    await session.commit()
    await session.refresh(shortlist)
    return shortlist


async def _initial_assets(session: AsyncSession, program_id: str) -> dict:
    documents = list(
        (await session.scalars(select(Document).where(
            Document.owner_id == settings.local_owner_id,
            Document.parse_status.notin_(["failed", "pending"]),
        ))).all()
    )
    artifacts = list(
        (await session.scalars(select(MaterialArtifact).where(
            MaterialArtifact.owner_id == settings.local_owner_id,
        ))).all()
    )
    drafts = list(
        (await session.scalars(select(MaterialDraft).where(
            MaterialDraft.owner_id == settings.local_owner_id,
            MaterialDraft.status == "reviewed",
        ))).all()
    )
    by_key = {key: [] for key in MATERIAL_ALIASES}
    for document in documents:
        key = material_key(document.kind)
        if key in by_key:
            by_key[key].append({"type": "document", "id": document.id, "label": document.filename})
    for artifact in artifacts:
        if artifact.kind in by_key and (
            artifact.scope == "general" or artifact.program_id == program_id
        ):
            by_key[artifact.kind].append({"type": "artifact", "id": artifact.id, "label": artifact.version_name})
    for draft in drafts:
        if draft.kind in by_key and (
            draft.program_id is None or draft.program_id == program_id
        ):
            by_key[draft.kind].append({"type": "draft", "id": draft.id, "label": f"{draft.title} v{draft.version_number}"})
    return by_key


async def refresh_application_package(
    session: AsyncSession, package: ApplicationPackage
) -> ApplicationPackage:
    requirement = await get_requirement(session, package.program_id)
    official_verified = bool(requirement and requirement.verified)
    names = list(requirement.materials) if requirement and requirement.materials else DEFAULT_MATERIALS
    unique = []
    for name in names:
        key = material_key(str(name))
        if not any(item["material_key"] == key for item in unique):
            unique.append({"material_key": key, "name": material_label(key, str(name))})
    assets = await _initial_assets(session, package.program_id)
    previous = {item.get("material_key"): item for item in (package.checklist or [])}
    checklist = []
    for base in unique:
        key = base["material_key"]
        old = previous.get(key, {})
        candidates = assets.get(key, [])
        status = old.get("status")
        if status not in {"ready", "needs_edit", "unverified", "missing", "manual_review"}:
            status = "unverified" if candidates else "missing"
        checklist.append({
            **base,
            "required": True,
            "status": status,
            "source_verified": official_verified,
            "candidate_assets": candidates,
            "selected_asset_type": old.get("selected_asset_type", ""),
            "selected_asset_id": old.get("selected_asset_id", ""),
            "note": old.get("note", ""),
        })
    gaps = []
    if not official_verified:
        gaps.append("项目官网材料要求尚未完成深度核验，当前清单仅为通用占位")
    for item in checklist:
        if item["status"] == "missing":
            gaps.append(f"缺少：{item['name']}")
        elif item["status"] in {"needs_edit", "unverified", "manual_review"}:
            gaps.append(f"待处理：{item['name']}")
    package.official_verified = official_verified
    package.checklist = checklist
    package.gaps = gaps
    package.ready = official_verified and bool(checklist) and all(
        item["status"] == "ready" and item.get("selected_asset_id") for item in checklist
    )
    package.status = "ready" if package.ready else (
        "materials_in_progress" if official_verified else "needs_official_verification"
    )
    await session.flush()
    return package


async def get_or_create_application_package(
    session: AsyncSession, program_id: str, shortlist_id: Optional[str] = None
) -> ApplicationPackage:
    package = await session.scalar(select(ApplicationPackage).where(
        ApplicationPackage.owner_id == settings.local_owner_id,
        ApplicationPackage.program_id == program_id,
    ))
    if package is None:
        package = ApplicationPackage(
            owner_id=settings.local_owner_id, program_id=program_id,
            shortlist_id=shortlist_id, checklist=[], gaps=[],
        )
        session.add(package)
        await session.flush()
    elif shortlist_id and not package.shortlist_id:
        package.shortlist_id = shortlist_id
    return await refresh_application_package(session, package)


async def create_material_plan(session: AsyncSession, program_id: str) -> MaterialPlan:
    program = await get_program(session, program_id)
    if not program:
        raise ValueError("项目不存在")
    requirement = await get_requirement(session, program_id)
    _, experiences = await profile_with_experiences(session)
    materials = (
        requirement.materials if requirement and requirement.materials else DEFAULT_MATERIALS
    )
    checklist = [
        {
            "name": item,
            "required": True,
            "status": "todo",
            "source_verified": bool(requirement and requirement.verified),
        }
        for item in materials
    ]
    confirmed = [item for item in experiences if item.confirmed]
    selected = [
        {
            "experience_id": item.id,
            "title": item.title,
            "kind": item.kind,
            "reason": f"可支持 {program.field} 方向的能力证明",
        }
        for item in confirmed[:5]
    ]
    gaps = []
    if not confirmed:
        gaps.append("经历库中没有已确认经历，请先补充科研、实习或项目经历")
    if not requirement or not requirement.verified:
        gaps.append("材料要求尚未完成官网核验")
    plan = MaterialPlan(
        owner_id=settings.local_owner_id,
        program_id=program_id,
        checklist=checklist,
        cv_plan={
            "selected_experiences": selected,
            "recommended_order": [item["title"] for item in selected],
            "focus": f"突出与 {program.field} 相关的技术深度、成果和量化影响",
            "grounded": True,
        },
        ps_plan={
            "prompt": "请以学校官网实际 PS 题目为准；当前为通用规划。",
            "selected_experiences": selected[:3],
            "outline": ["申请动机", "能力证据", "项目匹配", "学习与职业目标"],
            "customization": f"具体说明 {program.name} 的课程或研究资源如何支持目标",
            "grounded": True,
        },
        gaps=gaps,
    )
    session.add(plan)
    await session.commit()
    await session.refresh(plan)
    return plan


def parse_deadline(value: Optional[str]) -> date:
    if not value:
        raise ValueError("项目截止日期尚未通过官网证据核验，不能生成带日期的申请时间线")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("项目截止日期格式无效，请重新核验官网") from exc


async def create_timeline(session: AsyncSession, program_id: str) -> List[Task]:
    program = await get_program(session, program_id)
    if not program:
        raise ValueError("项目不存在")
    package = await session.scalar(select(ApplicationPackage).where(
        ApplicationPackage.owner_id == settings.local_owner_id,
        ApplicationPackage.program_id == program_id,
    ))
    if not package or not package.ready:
        raise ValueError("项目申请包材料尚未就绪，不能进入申请执行")
    requirement = await get_requirement(session, program_id)
    if not requirement or not requirement.verified:
        raise ValueError("项目截止日期和材料要求尚未完成官网核验，不能生成正式时间线")
    deadline = parse_deadline(requirement.deadline)
    milestones = [
        ("核验项目要求", "research", 100, "high"),
        ("确认 CV 经历与结构", "cv", 75, "high"),
        ("完成 PS 提纲与初稿", "ps", 60, "high"),
        ("确认推荐人并跟进推荐信", "recommendation", 50, "medium"),
        ("整理成绩单与语言成绩", "document", 35, "medium"),
        ("完成网申提交前检查", "application", 7, "high"),
    ]
    tasks = []
    for title, category, days_before, priority in milestones:
        item = Task(
            owner_id=settings.local_owner_id,
            program_id=program_id,
            title=f"{program.university}｜{title}",
            category=category,
            status="todo",
            due_date=(deadline - timedelta(days=days_before)).isoformat(),
            priority=priority,
            details=f"根据项目截止日期 {deadline.isoformat()} 自动生成。",
        )
        session.add(item)
        tasks.append(item)
    await session.commit()
    for item in tasks:
        await session.refresh(item)
    return tasks


async def create_task(session: AsyncSession, payload: TaskCreate) -> Task:
    item = Task(owner_id=settings.local_owner_id, **payload.model_dump())
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item
