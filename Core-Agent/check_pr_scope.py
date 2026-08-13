"""Verify that a proposed YYGlobal pull request only changes Core-Agent files.

The check compares the current branch with a base ref and also inspects staged,
unstaged, and untracked files. It only uses the Python standard library.

Usage:
    python Core-Agent/check_pr_scope.py
    python Core-Agent/check_pr_scope.py --base upstream/main
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path, PurePosixPath

ALLOWED_ROOT = "Core-Agent"
DEFAULT_BASE_REFS = ("upstream/main", "origin/main", "main")


class GitError(RuntimeError):
    """Raised when a required Git command cannot be completed."""


def run_git(repo_root: Path, *args: str, allow_failure: bool = False) -> bytes:
    """Run Git and return stdout without relying on the user's shell."""
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode and not allow_failure:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise GitError(message or f"git {' '.join(args)} failed")
    return result.stdout


def find_repo_root(start: Path) -> Path:
    output = run_git(start, "rev-parse", "--show-toplevel")
    return Path(output.decode("utf-8", errors="surrogateescape").strip())


def ref_exists(repo_root: Path, ref: str) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
        cwd=repo_root,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def resolve_base_ref(repo_root: Path, requested: str | None) -> str:
    if requested:
        if not ref_exists(repo_root, requested):
            raise GitError(f"base ref does not exist: {requested}")
        return requested

    for candidate in DEFAULT_BASE_REFS:
        if ref_exists(repo_root, candidate):
            return candidate
    raise GitError("no base ref found; pass one explicitly with --base")


def decode_paths(output: bytes) -> set[str]:
    return {
        item.decode("utf-8", errors="surrogateescape")
        for item in output.split(b"\0")
        if item
    }


def collect_changed_paths(repo_root: Path, base_ref: str) -> set[str]:
    """Collect committed and local paths, preserving both sides of renames."""
    common_args = ("--name-only", "-z", "--no-renames", "--diff-filter=ACDMRTUXB")
    outputs = (
        run_git(repo_root, "diff", *common_args, f"{base_ref}...HEAD"),
        run_git(repo_root, "diff", *common_args),
        run_git(repo_root, "diff", "--cached", *common_args),
        run_git(repo_root, "ls-files", "--others", "--exclude-standard", "-z"),
    )
    paths: set[str] = set()
    for output in outputs:
        paths.update(decode_paths(output))
    return paths


def is_allowed_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    parsed = PurePosixPath(normalized)
    return (
        not parsed.is_absolute()
        and ".." not in parsed.parts
        and len(parsed.parts) > 1
        and parsed.parts[0] == ALLOWED_ROOT
    )


def find_out_of_scope(paths: set[str]) -> list[str]:
    return sorted(path for path in paths if not is_allowed_path(path))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check that every PR file is located under Core-Agent/."
    )
    parser.add_argument(
        "--base",
        help="base branch or commit (auto-detects upstream/main, origin/main, then main)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        repo_root = find_repo_root(Path.cwd())
        base_ref = resolve_base_ref(repo_root, args.base)
        changed_paths = collect_changed_paths(repo_root, base_ref)
    except (GitError, OSError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    if not changed_paths:
        print(f"[ERROR] no changes found relative to {base_ref}", file=sys.stderr)
        return 2

    invalid_paths = find_out_of_scope(changed_paths)
    if invalid_paths:
        print(f"[FAIL] {len(invalid_paths)} path(s) are outside {ALLOWED_ROOT}/:")
        for path in invalid_paths:
            print(f"  - {path}")
        return 1

    print(
        f"[PASS] {len(changed_paths)} changed path(s) are contained in "
        f"{ALLOWED_ROOT}/ (base: {base_ref})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
