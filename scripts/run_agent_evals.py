"""Validate all P0 Skill packages and their deterministic eval contracts."""

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "services" / "api" / "app" / "skills"
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.agent.provider import OpenAIResponsesProvider
from app.agent.skills import skill_registry

REQUIRED = {
    "SKILL.md",
    "prompt.md",
    "input.schema.json",
    "output.schema.json",
    "tool-policy.yaml",
    "evals.yaml",
}


def main() -> int:
    failures = []
    packages = [path for path in SKILLS.iterdir() if path.is_dir()]
    for package in packages:
        missing = REQUIRED - {path.name for path in package.iterdir()}
        if missing:
            failures.append(f"{package.name}: missing {sorted(missing)}")
            continue
        for schema_name in ["input.schema.json", "output.schema.json"]:
            schema = json.loads((package / schema_name).read_text(encoding="utf-8"))
            if schema.get("type") != "object":
                failures.append(
                    f"{package.name}/{schema_name}: root type must be object"
                )
        policy = yaml.safe_load(
            (package / "tool-policy.yaml").read_text(encoding="utf-8")
        )
        evals = yaml.safe_load((package / "evals.yaml").read_text(encoding="utf-8"))
        if "tools" not in policy:
            failures.append(f"{package.name}: tool policy missing tools")
        if not evals.get("cases"):
            failures.append(f"{package.name}: no eval cases")
            continue
        skill = skill_registry.get(package.name)
        if skill.version != "0.1.0":
            failures.append(
                f"{package.name}: expected metadata.version 0.1.0, found {skill.version!r}"
            )
        if package.name == "cv-planner":
            try:
                skill_registry.validate_input(skill, {})
            except ValueError as exc:
                failures.append(
                    f"cv-planner: general CV input without program_id must be valid: {exc}"
                )
        context = {
            "profile": {
                "school": "Test University",
                "major": "Computer Science",
                "gpa": None,
                "target_countries": [],
                "target_fields": [],
                "intake": "",
            },
            "catalog": {"program_count": 20},
        }
        for case in evals["cases"]:
            output = OpenAIResponsesProvider._local_response(case["input"], context, skill)
            for phrase in case.get("must_not_contain", []):
                if phrase in output:
                    failures.append(
                        f"{package.name}/{case['name']}: forbidden phrase {phrase!r}"
                    )
            for concept in case.get("expected_concepts", []):
                if concept not in output:
                    failures.append(
                        f"{package.name}/{case['name']}: missing concept {concept!r}"
                    )
    if len(packages) != 7:
        failures.append(f"expected 7 skills, found {len(packages)}")
    if failures:
        print("\n".join(failures))
        return 1
    print(
        f"PASS: {len(packages)} Skill packages and {sum(len(yaml.safe_load((p / 'evals.yaml').read_text(encoding='utf-8'))['cases']) for p in packages)} deterministic eval cases validated"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
