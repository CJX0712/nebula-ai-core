# 混合检索测试
# 作者: 晨星
from __future__ import annotations

from nebula.core.embedder import HashBigramEmbedder
from nebula.core.lexical import BM25Index
from nebula.core.retriever import HybridRetriever
from nebula.core.types import Chunk
from nebula.core.vectorstore import MemoryVectorStore


def _setup():
    embedder = HashBigramEmbedder(64)
    vs = MemoryVectorStore()
    lex = BM25Index()
    chunks = [
        Chunk(chunk_id="c1", doc_id="d", text="向量数据库存储嵌入向量"),
        Chunk(chunk_id="c2", doc_id="d", text="今天天气晴朗"),
        Chunk(chunk_id="c3", doc_id="d", text="机器学习需要训练数据"),
    ]
    for ch in chunks:
        vs.upsert(ch, embedder.embed(ch.text))
        lex.upsert(ch)
    return HybridRetriever(vs, lex), embedder


def test_fusion_ranks_relevant():
    r, embedder = _setup()
    res = r.retrieve("向量数据库", embedder.embed("向量数据库"), 2)
    assert res
    assert res[0].chunk.chunk_id == "c1"
    assert res[0].rank == 1
