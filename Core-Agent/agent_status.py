"""Simple agent health check for the Core-Agent workspace."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


def summarize_workspace(repo_root: Path) -> dict[str, object]:
    """Collect a tiny snapshot of the repository shape."""
    core_agent_dir = repo_root / "Core-Agent"
    files = sorted(p.name for p in core_agent_dir.glob("*")) if core_agent_dir.exists() else []
    return {
        "repo_root": str(repo_root),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "core_agent_files": files,
        "artifact_count": len(files),
        "status": "ready",
    }


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    snapshot = summarize_workspace(repo_root)

    print("YYGlobal Core-Agent status")
    print(f"Repository root: {snapshot['repo_root']}")
    print(f"Generated at: {snapshot['generated_at']}")
    print(f"Core-Agent files: {', '.join(snapshot['core_agent_files']) or 'none'}")
    print(f"Artifacts detected: {snapshot['artifact_count']}")
    print(f"Overall status: {snapshot['status']}")


if __name__ == "__main__":
    main()
