# 重排器测试
# 作者: 晨星
from __future__ import annotations

from nebula.core.reranker import ScoreReranker
from nebula.core.types import Chunk, RetrievedChunk


def test_rerank_boost_overlap():
    r = ScoreReranker()
    chunks = [
        RetrievedChunk(
            chunk=Chunk(chunk_id="c1", doc_id="d", text="完全不相关的内容关于足球比赛"),
            score=0.4,
            rank=1,
        ),
        RetrievedChunk(
            chunk=Chunk(chunk_id="c2", doc_id="d", text="向量数据库用于存储嵌入向量"),
            score=0.4,
            rank=2,
        ),
    ]
    out = r.rerank("向量数据库", chunks)
    assert out[0].chunk.chunk_id == "c2"
