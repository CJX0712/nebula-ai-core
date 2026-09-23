# 稀疏索引测试
# 作者: 晨星
from __future__ import annotations

from nebula.core.lexical import BM25Index
from nebula.core.types import Chunk


def _chunk(text: str, cid: str) -> Chunk:
    return Chunk(chunk_id=cid, doc_id="d", text=text)


def test_bm25_returns_match():
    idx = BM25Index()
    idx.upsert(_chunk("向量数据库用于存储嵌入向量并支持相似度检索", "c1"))
    idx.upsert(_chunk("今天天气晴朗适合户外运动", "c2"))
    idx.upsert(_chunk("机器学习模型需要大量训练数据", "c3"))
    res = idx.search("向量数据库 相似度", 2)
    assert res
    assert res[0][0].chunk_id == "c1"


def test_idf_non_negative():
    idx = BM25Index()
    for i in range(5):
        idx.upsert(_chunk(f"文档 {i} 关于不同主题的内容说明", f"c{i}"))
    idx._ensure()
    assert all(v >= 0 for v in idx._idf.values())
