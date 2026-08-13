助力每一个梦想，PR 请提交到这里。

## Skill contract audit

`audit_skill_contracts.py` validates every package under
`services/api/app/skills` before the API imports it. The audit checks required
files, frontmatter metadata, JSON Schema structure, evaluation cases, registered
tool names, and approval-policy consistency.

```bash
python Core-Agent/audit_skill_contracts.py
python Core-Agent/audit_skill_contracts.py --json
python -m unittest discover -s Core-Agent -p "test_*.py" -v
```

The command exits with `0` when all contracts pass, `1` when contract issues are
found, and `2` when the repository cannot be inspected. JSON output is suitable
for CI or other automation.
=======
## 提交前检查

本目录提供一个仅依赖 Python 标准库的范围检查器，用于确认当前分支、暂存区、
工作区和未跟踪文件中的所有改动都位于 `Core-Agent/` 下：

```bash
python Core-Agent/check_pr_scope.py --base upstream/main
```

如果本地没有名为 `upstream` 的远端，可以省略 `--base`；脚本会依次尝试
`upstream/main`、`origin/main` 和 `main`。

运行单元测试：

```bash
python -m unittest discover -s Core-Agent -p "test_*.py"
```
