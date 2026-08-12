import re
from typing import Dict, List
from urllib.parse import urlparse

PROMPT_INJECTION_PATTERNS = [
    r"ignore (all|any|the) previous instructions",
    r"system prompt",
    r"忽略.{0,8}(之前|以上|系统).{0,8}(指令|提示)",
    r"泄露.{0,8}(密钥|提示词|系统指令)",
]


def check_user_input(text: str) -> List[Dict[str, str]]:
    findings = []
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, text, re.I):
            findings.append({"type": "prompt_injection", "message": "检测到试图覆盖系统边界的内容"})
            break
    return findings


def is_official_looking_url(url: str) -> bool:
    hostname = (urlparse(url).hostname or "").lower()
    return bool(hostname) and not hostname.endswith(("medium.com", "reddit.com", "zhihu.com"))


def verify_output(text: str) -> List[Dict[str, str]]:
    findings = []
    banned_claims = ["保证录取", "一定录取", "100%录取", "已经替你提交", "已经完成付款"]
    for claim in banned_claims:
        if claim in text:
            findings.append(
                {"type": "unsafe_claim", "message": f"输出包含不允许的保证或操作声明：{claim}"}
            )
    return findings
