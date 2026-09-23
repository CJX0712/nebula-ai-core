# 向量库测试
# 作者: 晨星
from __future__ import annotations

import pytest

from nebula.core.types import Chunk
from nebula.core.vectorstore import FaissVectorStore, MemoryVectorStore


def _chunk(text: str, cid: str) -> Chunk:
    return Chunk(chunk_id=cid, doc_id="d", text=text)


def test_memory_search_sorted():
    vs = MemoryVectorStore()
    vs.upsert(_chunk("a", "c1"), [1.0, 0.0])
    vs.upsert(_chunk("b", "c2"), [0.9, 0.1])
    vs.upsert(_chunk("c", "c3"), [0.0, 1.0])
    res = vs.search([1.0, 0.0], 2)
    assert res[0][0].chunk_id == "c1"
    assert res[0][1] >= res[1][1]


def test_faiss_search():
    pytest.importorskip("faiss")
    vs = FaissVectorStore()
    vs.upsert(_chunk("a", "c1"), [1.0, 0.0, 0.0])
    vs.upsert(_chunk("b", "c2"), [0.0, 1.0, 0.0])
    res = vs.search([1.0, 0.0, 0.0], 1)
    assert res and res[0][0].chunk_id == "c1"
