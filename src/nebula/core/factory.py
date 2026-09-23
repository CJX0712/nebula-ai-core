# 依赖注入工厂：唯一装配点，按 Settings 选择并注入实现
# 作者: 晨星
from __future__ import annotations

from .agent import ReActAgent
from .chunker import RecursiveChunker
from .config import Settings
from .embedder import FastEmbedEmbedder, HashBigramEmbedder
from .lexical import BM25Index
from .llm import DeterministicLLM, LlamaCppLLM, OpenAICompatibleLLM
from .loader import TextLoader
from .rag import RAGPipeline
from .reranker import ScoreReranker
from .repository import DocRepository
from .retriever import HybridRetriever
from .vectorstore import FaissVectorStore, MemoryVectorStore


def build_system(settings: Settings | None = None) -> dict:
    """构建完整系统，返回各模块实例字典（供 API / CLI / 测试使用）。"""
    s = settings or Settings.from_env()

    # 嵌入器
    if s.embedder == "fastembed":
        embedder: object = FastEmbedEmbedder(s.fastembed_model)
    else:
        embedder = HashBigramEmbedder(s.embed_dim)

    # 向量库
    vector_store = FaissVectorStore() if s.vector_store == "faiss" else MemoryVectorStore()

    # 稀疏索引
    lexical = BM25Index() if s.lexical == "bm25" else None

    # 大模型
    if s.llm == "llamacpp":
        llm = LlamaCppLLM(s.llamacpp_model_path)
    elif s.llm == "openai":
        llm = OpenAICompatibleLLM(s.openai_base_url, s.openai_api_key, s.openai_model)
    else:
        llm = DeterministicLLM()

    chunker = RecursiveChunker(s.chunk_size, s.chunk_overlap)
    retriever = HybridRetriever(vector_store, lexical)
    reranker = ScoreReranker() if s.reranker == "score" else None
    repository = DocRepository()

    pipeline = RAGPipeline(
        loader=TextLoader(),
        chunker=chunker,
        embedder=embedder,  # type: ignore[arg-type]
        vector_store=vector_store,  # type: ignore[arg-type]
        lexical=lexical,  # type: ignore[arg-type]
        retriever=retriever,  # type: ignore[arg-type]
        reranker=reranker,  # type: ignore[arg-type]
        llm=llm,  # type: ignore[arg-type]
        repository=repository,
        top_k=s.top_k,
    )
    agent = ReActAgent(pipeline)

    return {
        "settings": s,
        "pipeline": pipeline,
        "agent": agent,
        "embedder": embedder,
        "vector_store": vector_store,
        "lexical": lexical,
        "llm": llm,
        "repository": repository,
    }
