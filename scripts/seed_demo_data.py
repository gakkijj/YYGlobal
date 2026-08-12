"""Load an idempotent P0 demo workspace through the public HTTP API.

The script intentionally leaves official program requirements unverified. It creates
enough grounded applicant and material data to exercise the UI without pretending
that seed catalog facts have been checked against live university pages.
"""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
import uuid
from typing import Any


DEMO_SHORTLIST_NAME = "2027 Fall CS 演示选校"
DEMO_CV_FILENAME = "demo-general-cv.md"
DEMO_PS_FILENAME = "demo-program-ps.md"


class ApiClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def request(self, path: str, method: str = "GET", payload: Any = None) -> Any:
        data = json.dumps(payload, ensure_ascii=False).encode() if payload is not None else None
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=data,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                body = response.read().decode()
                return json.loads(body) if body else None
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            raise RuntimeError(f"{method} {path} failed ({exc.code}): {detail}") from exc

    def upload_markdown(self, filename: str, kind: str, content: str) -> Any:
        boundary = f"----YYGlobalDemo{uuid.uuid4().hex}"
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="kind"\r\n\r\n{kind}\r\n'
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            "Content-Type: text/markdown\r\n\r\n"
            f"{content}\r\n--{boundary}--\r\n"
        ).encode()
        request = urllib.request.Request(
            f"{self.base_url}/documents",
            data=body,
            method="POST",
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            raise RuntimeError(f"upload {filename} failed ({exc.code}): {detail}") from exc


def confirmed_profile() -> dict[str, Any]:
    return {
        "full_name": "林晨（演示学生）",
        "current_school": "华南理工大学",
        "current_major": "软件工程",
        "degree": "Bachelor",
        "gpa": 3.72,
        "gpa_scale": 4.0,
        "language_scores": {"TOEFL": 105, "GRE": 326},
        "target_countries": ["United States"],
        "target_fields": ["Computer Science"],
        "intake": "2027 Fall",
        "budget": 70000,
        "preferences": {
            "career_goal": "毕业后从事 AI 应用工程与检索系统研发",
            "location": "优先科技公司和实习机会较多的城市",
            "program_style": "偏好课程与实践并重的项目",
        },
        "confirmed": True,
        "experiences": [
            {
                "kind": "research",
                "title": "面向课程问答的可溯源 RAG 研究",
                "organization": "学校自然语言处理实验室",
                "start_date": "2025-03",
                "end_date": "2026-01",
                "description": "设计混合检索与引用核验流程，在自建测试集上将答案引用命中率从 71% 提升到 86%。",
                "tags": ["RAG", "NLP", "Evaluation"],
                "confirmed": True,
            },
            {
                "kind": "internship",
                "title": "后端开发实习生",
                "organization": "某科技公司（演示）",
                "start_date": "2025-07",
                "end_date": "2025-10",
                "description": "参与 Python API 与异步任务服务开发，为内部知识检索接口补充缓存和监控。",
                "tags": ["Python", "FastAPI", "Backend"],
                "confirmed": True,
            },
            {
                "kind": "project",
                "title": "留学项目证据核验助手",
                "organization": "课程项目",
                "start_date": "2025-11",
                "end_date": "2026-02",
                "description": "实现项目检索、官网来源记录和结构化材料清单原型，负责 Agent 工具调用与数据模型。",
                "tags": ["Agent", "Tool Calling", "PostgreSQL"],
                "confirmed": True,
            },
            {
                "kind": "award",
                "title": "校级程序设计竞赛二等奖",
                "organization": "华南理工大学",
                "start_date": "2024-12",
                "end_date": "2024-12",
                "description": "三人团队完成算法与工程综合赛题。",
                "tags": ["Algorithms", "Teamwork"],
                "confirmed": True,
            },
        ],
    }


def ensure_uploaded_artifact(
    api: ApiClient,
    *,
    filename: str,
    kind: str,
    scope: str,
    version_name: str,
    content: str,
    program_id: str | None = None,
) -> dict[str, Any]:
    artifacts = api.request(f"/material-artifacts?kind={kind}")
    existing = next((item for item in artifacts if item["filename"] == filename), None)
    if existing:
        return existing
    document = api.upload_markdown(filename, kind, content)
    return api.request(
        "/material-artifacts",
        "POST",
        {
            "document_id": document["id"],
            "program_id": program_id,
            "kind": kind,
            "scope": scope,
            "version_name": version_name,
            "language": "English",
            "status": "ready",
            "notes": "P0 演示上传材料；内容仅来自演示学生已确认经历。",
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/api")
    parser.add_argument(
        "--generate-with-llm",
        action="store_true",
        help="另外调用当前配置的大模型生成通用 CV 和项目 PS，并保存版本历史。",
    )
    args = parser.parse_args()
    api = ApiClient(args.base_url)

    health = api.request("/health")
    print(f"API: {health['status']} | database={health['database']} | llm={health['llm_mode']}")

    profile = api.request("/profile")
    if not (
        profile.get("full_name") == confirmed_profile()["full_name"]
        and profile.get("confirmed")
        and len(profile.get("experiences", [])) == len(confirmed_profile()["experiences"])
    ):
        profile = api.request("/profile", "PUT", confirmed_profile())
    print(f"Profile: {profile['full_name']} | experiences={len(profile['experiences'])}")

    programs = api.request("/programs")
    if len(programs) < 3:
        raise RuntimeError("画像保存后可推荐的 Computer Science 项目不足 3 个")
    selected = programs[:3]
    selected_ids = [item["id"] for item in selected]
    print("Programs: " + " | ".join(f"{item['university']} - {item['name']}" for item in selected))

    shortlists = api.request("/shortlists")
    shortlist = next((item for item in shortlists if item["name"] == DEMO_SHORTLIST_NAME), None)
    if shortlist is None:
        shortlist = api.request(
            "/shortlists", "POST", {"name": DEMO_SHORTLIST_NAME, "program_ids": selected_ids}
        )
    print(f"Shortlist: {shortlist['name']} | items={len(shortlist['items'])}")

    plans = api.request("/material-plans")
    existing_plan_ids = {item["program_id"] for item in plans}
    for program in selected:
        if program["id"] not in existing_plan_ids:
            api.request("/material-plans", "POST", {"program_id": program["id"]})
    print("Material plans: ready for 3 selected programs")

    cv_content = """# Lin Chen\n\n## Education\nSouth China University of Technology — B.Eng. in Software Engineering, GPA 3.72/4.0\n\n## Research Experience\n**Grounded RAG for Course Question Answering** — Designed hybrid retrieval and citation verification; improved citation hit rate from 71% to 86% on a self-built evaluation set.\n\n## Internship Experience\n**Backend Engineering Intern** — Contributed to Python APIs and asynchronous task services; added caching and monitoring for an internal retrieval interface.\n\n## Projects\n**Study-abroad Program Evidence Assistant** — Implemented program search, official-source tracking, structured material checklists, and Agent tool calling.\n\n## Skills\nPython, FastAPI, PostgreSQL, RAG, LLM Agent Tool Calling\n"""
    ps_content = f"""# Initial PS Material for {selected[0]['name']}\n\nThis uploaded draft records the applicant's initial motivation and evidence before project-specific rewriting. The applicant studied software engineering, researched grounded RAG, completed a backend internship, and built an Agent tool-calling prototype.\n\nThe final statement must be checked against the official prompt, word limit, and curriculum of {selected[0]['university']} before use.\n"""
    ensure_uploaded_artifact(
        api,
        filename=DEMO_CV_FILENAME,
        kind="cv",
        scope="general",
        version_name="通用 CV 初始上传版",
        content=cv_content,
    )
    ensure_uploaded_artifact(
        api,
        filename=DEMO_PS_FILENAME,
        kind="ps",
        scope="program",
        program_id=selected[0]["id"],
        version_name=f"{selected[0]['university']} PS 初始上传版",
        content=ps_content,
    )
    print("Uploaded materials: general CV + first-program PS")

    drafts = api.request("/material-drafts")
    if args.generate_with_llm:
        cv = next(
            (item for item in drafts if item["kind"] == "cv" and item["program_id"] is None),
            None,
        )
        if cv is None:
            cv = api.request(
                "/material-drafts/generate",
                "POST",
                {
                    "kind": "cv",
                    "language": "English",
                    "prompt": "Generate a concise one-page general CV using only confirmed experiences.",
                },
            )
        ps = next(
            (
                item
                for item in drafts
                if item["kind"] == "ps" and item["program_id"] == selected[0]["id"]
            ),
            None,
        )
        if ps is None:
            ps = api.request(
                "/material-drafts/generate",
                "POST",
                {
                    "kind": "ps",
                    "program_id": selected[0]["id"],
                    "language": "English",
                    "prompt": "Generate a project-specific first draft using only confirmed experiences.",
                },
            )
        print(f"LLM drafts: CV v{cv['version_number']} + PS v{ps['version_number']}")

    tasks = api.request("/tasks")
    demo_titles = {item["title"] for item in tasks}
    for payload in [
        {
            "title": "确认三所候选项目的官网材料要求",
            "category": "research",
            "status": "todo",
            "priority": "high",
            "details": "演示任务：按需核验官网，不把种子目录当作已核验事实。",
        },
        {
            "title": "检查通用 CV 的量化证据",
            "category": "cv",
            "status": "todo",
            "priority": "medium",
            "details": "确认 71% 到 86% 的指标有可追溯依据。",
        },
    ]:
        if payload["title"] not in demo_titles:
            api.request("/tasks", "POST", payload)
    print("Tasks: demo research and CV review tasks available")

    packages = api.request("/application-packages")
    if len(packages) < 3:
        raise RuntimeError("选校后没有建立对应的项目申请包")
    if any(item["official_verified"] for item in packages if item["program"]["id"] in selected_ids):
        raise RuntimeError("演示种子不应把项目官网状态标记为已核验")
    print("Safety gate: application packages correctly remain pending official verification")
    print("DONE: P0 demo data is ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
