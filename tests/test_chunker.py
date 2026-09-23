# 分块器测试
# 作者: 晨星
from __future__ import annotations

from nebula.core.chunker import RecursiveChunker
from nebula.core.types import Document


def _doc(text: str) -> Document:
    return Document(doc_id="d1", title="t", text=text)


def test_chunk_basic():
    c = RecursiveChunker(80, 10)
    text = "这是第一句。这是第二句。" + "用于测试分块逻辑是否正确工作的小段落。" * 6
    chunks = c.chunk(_doc(text))
    assert len(chunks) >= 2
    assert all(ch.text for ch in chunks)
    ids = {ch.chunk_id for ch in chunks}
    assert len(ids) == len(chunks)


def test_overlap_must_be_smaller():
    try:
        RecursiveChunker(100, 100)
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_empty_doc():
    chunks = RecursiveChunker(200, 40).chunk(_doc(""))
    assert len(chunks) == 1
