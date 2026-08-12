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
