# workspace_audit_agent.py

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any


class WorkspaceAuditAgent:
    """只读核查指定工作区，并生成结构化报告。"""

    IGNORED_DIRECTORIES = {
        ".git",
        ".idea",
        ".vscode",
        "__pycache__",
        "node_modules",
        ".venv",
        "venv",
        "dist",
        "build",
    }

    KEY_FILES = {
        "README": ("README.md", "README.rst", "README.txt"),
        "Git Ignore": (".gitignore",),
        "Python Config": ("pyproject.toml", "requirements.txt", "setup.py"),
        "Node Config": ("package.json",),
        "Agent Guide": ("AGENTS.md",),
    }

    def __init__(self, workspace: str | Path, max_files: int = 5_000):
        self.workspace = Path(workspace).expanduser().resolve()
        self.max_files = max_files

    def run(self) -> dict[str, Any]:
        """执行全部只读检查。"""
        report: dict[str, Any] = {
            "agent": "WorkspaceAuditAgent",
            "workspace": str(self.workspace),
            "checks": {},
            "findings": [],
        }

        if not self.workspace.exists():
            report["status"] = "error"
            report["findings"].append("工作区不存在。")
            return report

        if not self.workspace.is_dir():
            report["status"] = "error"
            report["findings"].append("指定路径不是目录。")
            return report

        report["checks"]["directory"] = self._check_directory()
        report["checks"]["key_files"] = self._check_key_files()
        report["checks"]["git"] = self._check_git()
        report["status"] = self._decide_status(report)

        return report

    def _check_directory(self) -> dict[str, Any]:
        """统计文件数量，并限制大型工作区的扫描范围。"""
        file_count = 0
        directory_count = 0
        scan_limited = False

        try:
            for root, directories, files in os.walk(self.workspace):
                directories[:] = [
                    name
                    for name in directories
                    if name not in self.IGNORED_DIRECTORIES
                ]

                directory_count += len(directories)
                file_count += len(files)

                if file_count >= self.max_files:
                    scan_limited = True
                    break

            return {
                "readable": True,
                "file_count": min(file_count, self.max_files),
                "directory_count": directory_count,
                "scan_limited": scan_limited,
                "ignored_directories": sorted(self.IGNORED_DIRECTORIES),
            }
        except OSError as error:
            return {
                "readable": False,
                "error": str(error),
            }

    def _check_key_files(self) -> dict[str, Any]:
        """检查常见项目入口文件是否存在。"""
        result: dict[str, Any] = {}

        for category, candidates in self.KEY_FILES.items():
            found = [
                filename
                for filename in candidates
                if (self.workspace / filename).is_file()
            ]

            result[category] = {
                "found": bool(found),
                "files": found,
            }

        return result

    def _check_git(self) -> dict[str, Any]:
        """核查 Git 仓库、分支和未提交改动。"""
        inside_repo = self._run_git(
            "rev-parse",
            "--is-inside-work-tree",
        )

        if not inside_repo["success"]:
            return {
                "is_repository": False,
                "message": "该工作区不是 Git 仓库，或 Git 不可用。",
            }

        branch = self._run_git("branch", "--show-current")
        root = self._run_git("rev-parse", "--show-toplevel")
        status = self._run_git("status", "--short")
        remote = self._run_git("remote", "-v")

        changed_files = (
            status["stdout"].splitlines()
            if status["success"] and status["stdout"]
            else []
        )

        return {
            "is_repository": True,
            "repository_root": root["stdout"] or None,
            "branch": branch["stdout"] or "detached HEAD",
            "working_tree_clean": not changed_files,
            "changed_file_count": len(changed_files),
            "changed_files": changed_files,
            "remotes": (
                remote["stdout"].splitlines()
                if remote["success"] and remote["stdout"]
                else []
            ),
        }

    def _run_git(self, *arguments: str) -> dict[str, Any]:
        """安全执行只读 Git 命令。"""
        try:
            completed = subprocess.run(
                ["git", *arguments],
                cwd=self.workspace,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                check=False,
            )

            return {
                "success": completed.returncode == 0,
                "stdout": completed.stdout.strip(),
                "stderr": completed.stderr.strip(),
            }
        except FileNotFoundError:
            return {
                "success": False,
                "stdout": "",
                "stderr": "系统中没有找到 Git。",
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Git 命令执行超时。",
            }

    @staticmethod
    def _decide_status(report: dict[str, Any]) -> str:
        """根据检查结果给出 Agent 判断。"""
        directory = report["checks"]["directory"]
        git = report["checks"]["git"]

        if not directory.get("readable"):
            report["findings"].append("工作区无法完整读取。")
            return "error"

        if directory.get("scan_limited"):
            report["findings"].append("文件较多，扫描已达到数量上限。")

        if not git.get("is_repository"):
            report["findings"].append("工作区尚未初始化为 Git 仓库。")
            return "warning"

        if not git.get("working_tree_clean"):
            count = git["changed_file_count"]
            report["findings"].append(f"发现 {count} 个未提交的文件改动。")
            return "warning"

        report["findings"].append("工作区存在、Git 仓库有效且工作区干净。")
        return "ok"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="只读核查一个 Agent 工作区。"
    )
    parser.add_argument(
        "workspace",
        nargs="?",
        default=".",
        help="需要核查的工作区路径，默认为当前目录。",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=5_000,
        help="最多扫描的文件数量，默认为 5000。",
    )
    args = parser.parse_args()

    agent = WorkspaceAuditAgent(
        workspace=args.workspace,
        max_files=args.max_files,
    )
    report = agent.run()

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()