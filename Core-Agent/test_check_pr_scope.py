"""Unit tests for the Core-Agent PR scope checker."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_pr_scope import decode_paths, find_out_of_scope, is_allowed_path


class DecodePathsTests(unittest.TestCase):
    def test_decodes_null_delimited_git_output(self) -> None:
        output = b"Core-Agent/README.md\0Core-Agent/tool.py\0"
        self.assertEqual(
            decode_paths(output),
            {"Core-Agent/README.md", "Core-Agent/tool.py"},
        )


class ScopeTests(unittest.TestCase):
    def test_accepts_nested_core_agent_files(self) -> None:
        self.assertTrue(is_allowed_path("Core-Agent/checks/source.py"))

    def test_accepts_windows_separators(self) -> None:
        self.assertTrue(is_allowed_path(r"Core-Agent\checks\source.py"))

    def test_rejects_other_directories(self) -> None:
        self.assertFalse(is_allowed_path("docs/README.md"))

    def test_rejects_similar_prefix(self) -> None:
        self.assertFalse(is_allowed_path("Core-Agent-old/tool.py"))

    def test_rejects_parent_traversal(self) -> None:
        self.assertFalse(is_allowed_path("Core-Agent/../README.md"))

    def test_finds_out_of_scope_paths_in_sorted_order(self) -> None:
        paths = {
            "services/api/app.py",
            "Core-Agent/check_pr_scope.py",
            "README.md",
        }
        self.assertEqual(
            find_out_of_scope(paths),
            ["README.md", "services/api/app.py"],
        )


if __name__ == "__main__":
    unittest.main()
