# 文档加载器：单一职责 = 把外部文件变成 Document
# 作者: 晨星
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Protocol, runtime_checkable

from .types import Document


@runtime_checkable
class DocumentLoader(Protocol):
    """加载器契约：给定来源路径，返回标准化 Document。"""

    def load(self, source: str) -> Document: ...


def _stable_id(source: str, text: str) -> str:
    h = hashlib.sha1((source + "|" + text[:200]).encode("utf-8")).hexdigest()[:12]
    return "doc_" + h


def select_loader(source: str) -> DocumentLoader:
    """按扩展名选择加载器（工厂辅助）。"""
    p = source.lower()
    if p.endswith(".pdf"):
        return PDFLoader()
    if p.endswith((".md", ".markdown")):
        return MarkdownLoader()
    return TextLoader()


class TextLoader:
    def load(self, source: str) -> Document:
        p = Path(source)
        text = p.read_text(encoding="utf-8")
        return Document(
            doc_id=_stable_id(source, text),
            title=p.name,
            text=text,
            source=source,
        )


class MarkdownLoader(TextLoader):
    def load(self, source: str) -> Document:
        doc = super().load(source)
        m = re.search(r"^#\s+(.+)$", doc.text, re.MULTILINE)
        if m:
            doc.title = m.group(1).strip()
        return doc


class PDFLoader:
    """生产后端：复用 pypdf 解析 PDF（需 pip install pypdf）。"""

    def load(self, source: str) -> Document:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("PDFLoader 需要 pypdf，请执行 pip install pypdf") from exc
        p = Path(source)
        reader = PdfReader(str(p))
        parts = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(parts)
        return Document(
            doc_id=_stable_id(source, text),
            title=p.name,
            text=text,
            source=source,
        )
