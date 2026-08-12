import base64
import hashlib
import re
from pathlib import Path
from typing import Any, Dict, Tuple

import fitz
from docx import Document as DocxDocument

SUPPORTED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "text/markdown",
    "image/png",
    "image/jpeg",
}


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def extract_text(path: Path, mime_type: str) -> Tuple[str, str]:
    if mime_type == "application/pdf":
        with fitz.open(path) as pdf:
            return "\n".join(page.get_text() for page in pdf), "parsed"
    if mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = DocxDocument(path)
        return "\n".join(paragraph.text for paragraph in doc.paragraphs), "parsed"
    if mime_type in {"text/plain", "text/markdown"}:
        return path.read_text(encoding="utf-8", errors="replace"), "parsed"
    if mime_type.startswith("image/"):
        return "", "needs_multimodal_review"
    return "", "unsupported"


def infer_document_data(text: str, kind: str) -> Dict[str, Any]:
    cleaned = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    emails = re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", cleaned)
    gpa_match = re.search(
        r"(?:GPA|绩点)\s*[:：]?\s*(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)", cleaned, re.I
    )
    sections = []
    for label in [
        "Education",
        "Experience",
        "Research",
        "Projects",
        "Awards",
        "教育",
        "实习",
        "科研",
        "项目",
    ]:
        if re.search(rf"\b{re.escape(label)}\b", cleaned, re.I):
            sections.append(label)
    data: Dict[str, Any] = {
        "kind": kind,
        "emails": emails[:3],
        "sections": sections,
        "text_preview": cleaned[:1200],
        "candidate_facts": [],
        "education": [],
        "experiences": [],
        "language_scores": {},
        "skills": [],
        "awards": [],
        "requires_confirmation": True,
    }
    if gpa_match:
        data["candidate_facts"].append(
            {"field": "gpa", "value": float(gpa_match.group(1)), "scale": float(gpa_match.group(2))}
        )
    return data


def build_image_inputs(path: Path, mime_type: str, max_pdf_pages: int = 3) -> list:
    if mime_type.startswith("image/"):
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return [f"data:{mime_type};base64,{encoded}"]
    if mime_type == "application/pdf":
        images = []
        with fitz.open(path) as pdf:
            for page in list(pdf)[:max_pdf_pages]:
                pixmap = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
                encoded = base64.b64encode(pixmap.tobytes("png")).decode("ascii")
                images.append(f"data:image/png;base64,{encoded}")
        return images
    return []
