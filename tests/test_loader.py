# 加载器测试
# 作者: 晨星
from __future__ import annotations

import builtins
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

from nebula.core.loader import (  # noqa: E402
    MarkdownLoader,
    PDFLoader,
    TextLoader,
    select_loader,
)


def test_text_loader(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("hello world 你好世界", encoding="utf-8")
    doc = TextLoader().load(str(f))
    assert doc.title == "a.txt"
    assert "你好世界" in doc.text
    assert doc.doc_id.startswith("doc_")


def test_markdown_title(tmp_path):
    f = tmp_path / "b.md"
    f.write_text("# 我的标题\n正文内容。", encoding="utf-8")
    doc = MarkdownLoader().load(str(f))
    assert doc.title == "我的标题"


def test_select_loader_dispatch():
    assert isinstance(select_loader("x.pdf"), PDFLoader)
    assert isinstance(select_loader("x.md"), MarkdownLoader)
    assert isinstance(select_loader("x.txt"), TextLoader)


def test_pdf_loader_missing_dep(monkeypatch):
    real = builtins.__import__

    def fake(name, *a, **k):
        if name == "pypdf":
            raise ImportError("no pypdf")
        return real(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", fake)
    try:
        PDFLoader().load(str(ROOT / "samples" / "sample.md"))
    except RuntimeError as exc:
        assert "pypdf" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")
