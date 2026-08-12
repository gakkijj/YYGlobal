from typing import Any, Dict, List

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.entities import (
    EvidenceChunk,
    MCPConnection,
    Program,
    ProgramRequirement,
    ProgramSource,
    SkillVersion,
    Workspace,
)

PROGRAMS: List[Dict[str, Any]] = [
    {
        "university": "Carnegie Mellon University",
        "name": "Master of Science in Computer Science",
        "city": "Pittsburgh",
        "url": "https://csd.cs.cmu.edu/academics/masters/ms-in-computer-science",
    },
    {
        "university": "Stanford University",
        "name": "MS in Computer Science",
        "city": "Stanford",
        "url": "https://www.cs.stanford.edu/masters-program",
    },
    {
        "university": "University of Illinois Urbana-Champaign",
        "name": "Master of Computer Science",
        "city": "Champaign",
        "url": "https://cs.illinois.edu/academics/graduate/professional-mcs",
    },
    {
        "university": "Georgia Institute of Technology",
        "name": "MS in Computer Science",
        "city": "Atlanta",
        "url": "https://www.cc.gatech.edu/degree-programs/master-science-computer-science",
    },
    {
        "university": "University of Washington",
        "name": "Professional Master's Program in Computer Science",
        "city": "Seattle",
        "url": "https://www.cs.washington.edu/academics/graduate/pmp",
    },
    {
        "university": "Columbia University",
        "name": "MS in Computer Science",
        "city": "New York",
        "url": "https://www.cs.columbia.edu/education/ms/",
    },
    {
        "university": "University of Southern California",
        "name": "MS in Computer Science",
        "city": "Los Angeles",
        "url": "https://www.cs.usc.edu/academic-programs/masters/computer-science-general/",
    },
    {
        "university": "University of Michigan",
        "name": "CSE Master's Program",
        "city": "Ann Arbor",
        "url": "https://cse.engin.umich.edu/academics/graduate/masters-programs/",
    },
    {
        "university": "University of California, San Diego",
        "name": "MS in Computer Science and Engineering",
        "city": "San Diego",
        "url": "https://cse.ucsd.edu/graduate/degree-programs/ms-program",
    },
    {
        "university": "New York University",
        "name": "MS in Computer Science",
        "city": "New York",
        "url": "https://cs.nyu.edu/home/master/prospective_overview.html",
    },
    {
        "university": "Northeastern University",
        "name": "MS in Computer Science",
        "city": "Boston",
        "url": "https://graduate.northeastern.edu/programs/mscs-computer-science/master-of-science-in-computer-science-boston/",
    },
    {
        "university": "University of Massachusetts Amherst",
        "name": "MS in Computer Science",
        "city": "Amherst",
        "url": "https://www.cics.umass.edu/academics/ms-computer-science",
    },
    {
        "university": "University of Wisconsin-Madison",
        "name": "Professional Master's Program in Computer Sciences",
        "city": "Madison",
        "url": "https://www.cs.wisc.edu/graduate/pmp-program/",
    },
    {
        "university": "University of Maryland",
        "name": "MS in Computer Science",
        "city": "College Park",
        "url": "https://www.cs.umd.edu/grad/catalog",
    },
    {
        "university": "Purdue University",
        "name": "MS in Computer Science",
        "city": "West Lafayette",
        "url": "https://www.cs.purdue.edu/graduate/index.html",
    },
    {
        "university": "Texas A&M University",
        "name": "Master of Computer Science",
        "city": "College Station",
        "url": "https://engineering.tamu.edu/cse/academics/degrees/graduate/mcs.html",
    },
    {
        "university": "Rice University",
        "name": "Master of Computer Science",
        "city": "Houston",
        "url": "https://csweb.rice.edu/academics/graduate-programs/professional-masters-program",
    },
    {
        "university": "University of California, Irvine",
        "name": "Master of Computer Science",
        "city": "Irvine",
        "url": "https://mcs.ics.uci.edu/",
    },
    {
        "university": "Pennsylvania State University",
        "name": "Master of Science in Computer Science and Engineering",
        "city": "University Park",
        "url": "https://www.eecs.psu.edu/students/graduate/Graduate-Degree-Programs-CSE.aspx",
    },
    {
        "university": "University at Buffalo",
        "name": "MS in Computer Science and Engineering",
        "city": "Buffalo",
        "url": "https://engineering.buffalo.edu/computer-science-engineering/graduate/degrees-and-programs/ms-in-computer-science-and-engineering.html",
    },
    {
        "university": "Massachusetts Institute of Technology",
        "name": "Master of Business Analytics",
        "field": "Business Analytics",
        "city": "Cambridge",
        "duration_months": 12,
        "url": "https://mitsloan.mit.edu/master-of-business-analytics/admissions",
    },
    {
        "university": "University of California, Los Angeles",
        "name": "Master of Science in Business Analytics",
        "field": "Business Analytics",
        "city": "Los Angeles",
        "duration_months": 15,
        "url": "https://www.anderson.ucla.edu/degrees/master-of-science-in-business-analytics-msba",
    },
    {
        "university": "Duke University",
        "name": "Master of Quantitative Management: Business Analytics",
        "field": "Business Analytics",
        "city": "Durham",
        "duration_months": 10,
        "url": "https://www.fuqua.duke.edu/programs/mqm-business-analytics",
    },
    {
        "university": "University of Texas at Austin",
        "name": "Master of Science in Business Analytics",
        "field": "Business Analytics",
        "city": "Austin",
        "duration_months": 10,
        "url": "https://www.mccombs.utexas.edu/graduate/specialized-masters/ms-business-analytics/ms-business-analytics-on-campus/",
    },
    {
        "university": "University of Southern California",
        "name": "Master of Science in Business Analytics",
        "field": "Business Analytics",
        "city": "Los Angeles",
        "duration_months": 18,
        "url": "https://www.marshall.usc.edu/programs/graduate-programs/specialized-masters/ms-business-analytics",
    },
    {
        "university": "New York University",
        "name": "Master of Science in Accounting",
        "field": "Accounting",
        "city": "New York",
        "duration_months": 12,
        "url": "https://www.stern.nyu.edu/programs-admissions/masters-programs/ms-accounting",
    },
    {
        "university": "University of California, Berkeley",
        "name": "Master of Financial Engineering",
        "field": "Finance",
        "city": "Berkeley",
        "duration_months": 12,
        "url": "https://mfe.haas.berkeley.edu/",
    },
    {
        "university": "Vanderbilt University",
        "name": "Master of Science in Finance",
        "field": "Finance",
        "city": "Nashville",
        "duration_months": 9,
        "url": "https://business.vanderbilt.edu/masters-in-finance/",
    },
    {
        "university": "Carnegie Mellon University",
        "name": "Master of Science in Public Policy and Management",
        "field": "Public Policy",
        "city": "Pittsburgh",
        "duration_months": 24,
        "url": "https://www.heinz.cmu.edu/programs/public-policy-management-master/",
    },
    {
        "university": "University of Michigan",
        "name": "Master of Public Policy",
        "field": "Public Policy",
        "city": "Ann Arbor",
        "duration_months": 24,
        "url": "https://fordschool.umich.edu/mpp-mpa/mpp",
    },
]


FIELD_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "Computer Science": {
        "prerequisites": ["Programming", "Data Structures", "Algorithms"],
        "materials": ["CV", "PS", "成绩单", "3 封推荐信", "语言成绩"],
    },
    "Business Analytics": {
        "prerequisites": ["Calculus", "Statistics", "Programming"],
        "materials": ["CV", "Essays / PS", "成绩单", "推荐信", "语言成绩", "GMAT / GRE（如要求）"],
    },
    "Accounting": {
        "prerequisites": ["Accounting", "General Business"],
        "materials": ["CV", "Essays", "成绩单", "推荐信", "语言成绩", "GMAT / GRE（如要求）"],
    },
    "Finance": {
        "prerequisites": ["Calculus", "Statistics", "Finance / Economics"],
        "materials": ["CV", "Essays / PS", "成绩单", "推荐信", "语言成绩", "GMAT / GRE"],
    },
    "Public Policy": {
        "prerequisites": ["Quantitative preparation"],
        "materials": ["CV", "Essays / PS", "成绩单", "推荐信", "语言成绩", "GRE / GMAT（如要求）"],
    },
}


async def seed_database(session: AsyncSession) -> None:
    if await session.get(Workspace, settings.local_owner_id) is None:
        session.add(Workspace(id=settings.local_owner_id))

    for item in PROGRAMS:
        existing = await session.scalar(select(Program).where(Program.official_url == item["url"]))
        if existing is None:
            existing = await session.scalar(
                select(Program).where(
                    Program.university == item["university"], Program.name == item["name"]
                )
            )
            if existing is not None:
                existing.official_url = item["url"]
        field = item.get("field", "Computer Science")
        defaults = FIELD_DEFAULTS[field]
        if existing is None:
            existing = Program(
                university=item["university"],
                name=item["name"],
                degree="Master",
                country="United States",
                city=item["city"],
                field=field,
                duration_months=item.get("duration_months", 24),
                tuition=None,
                currency="USD",
                official_url=item["url"],
                summary="项目目录来自院校官方项目页；具体费用和申请要求需逐字段核验官网证据。",
            )
            session.add(existing)
            await session.flush()
            source = ProgramSource(
                program_id=existing.id,
                url=item["url"],
                title=f"{item['university']} official program page",
                source_type="official",
                content="",
                status="seed_unverified",
            )
            session.add(source)
            await session.flush()
            session.add(
                ProgramRequirement(
                    program_id=existing.id,
                    deadline_raw="",
                    deadline=None,
                    deadlines=[],
                    min_gpa=None,
                    language={},
                    prerequisites=defaults["prerequisites"],
                    materials=defaults["materials"],
                    fees={},
                    source_ids=[source.id],
                    verified=False,
                )
            )
        else:
            existing.field = field
            existing.degree = "Master"
            existing.duration_months = item.get("duration_months", existing.duration_months)
            existing.summary = (
                "项目目录来自院校官方项目页；具体费用和申请要求需逐字段核验官网证据。"
            )
            requirement = await session.scalar(
                select(ProgramRequirement).where(ProgramRequirement.program_id == existing.id)
            )
            if requirement is not None and not requirement.verified:
                # 旧版 P0 曾写入演示日期、费用和门槛。未附官网证据的数据必须回收为未知，
                # 避免在 UI、时间线或 Agent 上下文中被误当成真实招生信息。
                evidence_count = await session.scalar(
                    select(func.count()).select_from(EvidenceChunk).where(
                        EvidenceChunk.program_id == existing.id
                    )
                )
                if not evidence_count:
                    existing.tuition = None
                    requirement.deadline_raw = ""
                    requirement.deadline = None
                    requirement.deadlines = []
                    requirement.min_gpa = None
                    requirement.language = {}
                    requirement.fees = {}
            seed_source = await session.scalar(
                select(ProgramSource).where(
                    ProgramSource.program_id == existing.id,
                    ProgramSource.status == "seed_unverified",
                )
            )
            if seed_source is not None:
                seed_source.url = item["url"]

    skill_count = await session.scalar(select(func.count()).select_from(SkillVersion))
    if not skill_count:
        for name in settings.enabled_skills:
            session.add(
                SkillVersion(
                    name=name,
                    version="0.1.0",
                    manifest={"source": f"app/skills/{name}/SKILL.md"},
                )
            )

    mcp_count = await session.scalar(select(func.count()).select_from(MCPConnection))
    if not mcp_count:
        session.add(
            MCPConnection(
                name="yyglobal-demo-catalog",
                transport="in-process-demo-adapter",
                endpoint="in-process://program-catalog",
                read_only=True,
                status="available",
                tools=["catalog.search_programs", "catalog.get_program"],
            )
        )
    await session.commit()
