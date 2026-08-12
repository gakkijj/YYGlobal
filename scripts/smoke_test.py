"""HTTP-level P0 smoke test against running web and API services."""

import json
import sys
import urllib.error
import urllib.request
import uuid

API = "http://127.0.0.1:8000/api"
WEB = "http://127.0.0.1:3000"


def request(path: str, method: str = "GET", payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        f"{API}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        body = response.read().decode()
        return response.status, json.loads(body) if body else None


def upload_markdown(filename: str, kind: str, text: str):
    boundary = f"----YYGlobal{uuid.uuid4().hex}"
    body = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"kind\"\r\n\r\n{kind}\r\n"
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\n"
        f"Content-Type: text/markdown\r\n\r\n{text}\r\n--{boundary}--\r\n"
    ).encode()
    req = urllib.request.Request(
        f"{API}/documents",
        data=body,
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.loads(response.read().decode())


def check(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"PASS: {label}")


def main() -> int:
    try:
        status, health = request("/health")
        check(status == 200 and health["database"] == "ok", "API and database health")

        with urllib.request.urlopen(WEB, timeout=15) as response:
            homepage = response.read().decode()
        check(
            response.status == 200 and "YYGlobal" in homepage, "production web homepage"
        )

        _, profile = request(
            "/profile",
            "PUT",
            {
                "full_name": "P0 验收学生",
                "current_school": "YY Test University",
                "current_major": "Computer Science",
                "degree": "Bachelor",
                "gpa": 3.7,
                "gpa_scale": 4.0,
                "language_scores": {"TOEFL": 105},
                "target_countries": ["United States"],
                "target_fields": ["Computer Science"],
                "intake": "2027 Fall",
                "budget": 65000,
                "preferences": {},
                "confirmed": True,
                "experiences": [
                    {
                        "kind": "project",
                        "title": "Grounded RAG Project",
                        "organization": "YY Lab",
                        "description": "Implemented retrieval and citation verification.",
                        "tags": ["RAG", "AI"],
                        "confirmed": True,
                    }
                ],
            },
        )
        check(
            profile["confirmed"] and len(profile["experiences"]) == 1,
            "confirmed profile and experience",
        )
        _, exported = request("/profile/export")
        check(
            exported["profile"]["full_name"] == "P0 验收学生" and exported["memories"],
            "profile and memory data export",
        )

        _, programs = request("/programs")
        check(
            len(programs) >= 20
            and {program["field"] for program in programs} == {"Computer Science"}
            and programs[0]["sources"],
            "profile-driven Computer Science programs with official sources",
        )
        _, business_programs = request("/programs?q=Business%20Analytics")
        check(
            business_programs
            and all(program["field"] == "Business Analytics" for program in business_programs)
            and all("master" in program["name"].lower() for program in business_programs),
            "cross-discipline business master catalog and direct program URLs",
        )
        ids = [program["id"] for program in programs[:3]]

        _, shortlist = request(
            "/shortlists", "POST", {"name": "P0 HTTP 验收", "program_ids": ids}
        )
        check(len(shortlist["items"]) == 3, "shortlist scoring, tiers and risks")

        _, materials = request("/material-plans", "POST", {"program_id": ids[0]})
        check(
            materials["cv_plan"]["grounded"]
            and materials["ps_plan"]["grounded"]
            and materials["cv_plan"] != materials["ps_plan"],
            "separate grounded CV and PS plans",
        )

        document = upload_markdown("p0-school-cv.md", "cv", "Grounded RAG Project")
        _, artifact = request(
            "/material-artifacts",
            "POST",
            {
                "document_id": document["id"],
                "program_id": ids[0],
                "kind": "cv",
                "scope": "program",
                "version_name": "P0 school CV",
                "status": "ready",
            },
        )
        _, preflight = request(
            "/material-artifacts/preflight",
            "POST",
            {"artifact_id": artifact["id"], "program_id": ids[0]},
        )
        check(
            preflight["ready_to_upload"] and all(item["passed"] for item in preflight["checks"]),
            "material versions and upload preflight",
        )

        try:
            request("/tasks/timeline", "POST", {"program_id": ids[0]})
            raise AssertionError("unverified timeline must be rejected")
        except urllib.error.HTTPError as exc:
            check(
                exc.code == 400 and "官网核验" in exc.read().decode(),
                "unverified timeline safety gate",
            )
        _, existing_applications = request("/applications")
        application = next(
            (item for item in existing_applications if item["program_id"] == ids[0]), None
        )
        if application is None:
            _, application = request("/applications", "POST", {"program_id": ids[0]})
        _, application = request(
            f"/applications/{application['id']}", "PATCH", {"status": "submitted"}
        )
        check(application["status"] == "submitted", "per-program application status")

        _, skills = request("/skills")
        check(len(skills) == 7, "seven loadable Skills")

        _, mcp = request(
            "/mcp/demo/call",
            "POST",
            {"name": "catalog.search_programs", "arguments": {"query": "Stanford"}},
        )
        check(
            mcp["result"][0]["university"] == "Stanford University"
            and mcp["registry_tool"] == "mcp_catalog_search",
            "read-only MCP through unified Tool Registry",
        )
        _, mcp_trace = request(f"/agent-runs/{mcp['run_id']}/trace")
        check(
            mcp_trace["tool_calls"][0]["tool_name"] == "mcp_catalog_search",
            "MCP ToolCall trace",
        )

        req = urllib.request.Request(
            f"{API}/chat/stream",
            data=json.dumps({"message": "帮我规划 CV"}).encode(),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            stream = response.read().decode()
        check(
            "event: plan.created" in stream and "event: run.completed" in stream,
            "Agent SSE plan and completion",
        )
        run_id = None
        for line in stream.splitlines():
            if line.startswith("data: "):
                payload = json.loads(line[6:])
                if payload.get("run_id"):
                    run_id = payload["run_id"]
                    break
        _, trace = request(f"/agent-runs/{run_id}/trace")
        check(
            trace["run"]["skill_name"] == "cv-planner"
            and len(trace["steps"]) == 4
            and trace["run"]["structured_output"]
            and all(item["status"] == "completed" for item in trace["run"]["plan"]),
            "Agent structured output, synchronized plan and trace replay data",
        )
        print("PASS: complete P0 HTTP smoke test")
        return 0
    except (AssertionError, urllib.error.URLError, KeyError, IndexError) as exc:
        print(f"FAIL: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
