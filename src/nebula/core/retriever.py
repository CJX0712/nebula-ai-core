# 检索器：单一职责 = 融合稠密与稀疏召回
# 作者: 晨星
from __future__ import annotations

from typing import Protocol, runtime_checkable

from .lexical import LexicalIndex
from .types import Chunk, RetrievedChunk
from .vectorstore import VectorStore


@runtime_checkable
class Retriever(Protocol):
    """检索器契约：传入查询文本与查询向量，返回排序后的片段。"""

    def retrieve(
        self, query: str, query_vector: list[float], top_k: int
    ) -> list[RetrievedChunk]: ...


def _rrf(rank: int, k: int = 60) -> float:
    """Reciprocal Rank Fusion 分数。"""
    return 1.0 / (k + rank + 1)


class HybridRetriever:
    """混合检索：稠密向量 + 稀疏 BM25，经 RRF 融合排序。"""

    def __init__(self, vector_store: VectorStore, lexical: LexicalIndex | None) -> None:
        self.vs = vector_store
        self.lex = lexical

    def retrieve(
        self, query: str, query_vector: list[float], top_k: int
    ) -> list[RetrievedChunk]:
        vec_res = self.vs.search(query_vector, top_k * 3) if self.vs else []
        lex_res = self.lex.search(query, top_k * 3) if self.lex else []

        fused: dict[str, float] = {}
        chunk_map: dict[str, Chunk] = {}
        for rank, (chunk, _score) in enumerate(vec_res):
            fused[chunk.chunk_id] = fused.get(chunk.chunk_id, 0.0) + _rrf(rank)
            chunk_map[chunk.chunk_id] = chunk
        for rank, (chunk, _score) in enumerate(lex_res):
            fused[chunk.chunk_id] = fused.get(chunk.chunk_id, 0.0) + _rrf(rank)
            chunk_map[chunk.chunk_id] = chunk

        ordered = sorted(fused.items(), key=lambda x: x[1], reverse=True)[:top_k]
        out = []
        for rank, (cid, score) in enumerate(ordered):
            out.append(
                RetrievedChunk(chunk=chunk_map[cid], score=float(score), rank=rank + 1)
            )
        return out
