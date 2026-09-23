# RAG 管线：单一职责 = 编排 ingest / query 端到端链路
# 作者: 晨星
from __future__ import annotations

from .chunker import RecursiveChunker
from .embedder import Embedder
from .lexical import LexicalIndex
from .loader import DocumentLoader, select_loader
from .llm import LLM
from .reranker import Reranker
from .repository import DocRepository
from .retriever import Retriever
from .types import Chunk, QueryResult
from .vectorstore import VectorStore


class RAGPipeline:
    """把加载、分块、嵌入、索引、检索、重排、生成串成可运行链路。

    每个依赖都是 Protocol，运行时由工厂注入；ingest/query 是其唯一对外入口。
    """

    def __init__(
        self,
        loader: DocumentLoader,
        chunker: RecursiveChunker,
        embedder: Embedder,
        vector_store: VectorStore,
        lexical: LexicalIndex | None,
        retriever: Retriever,
        reranker: Reranker | None,
        llm: LLM,
        repository: DocRepository,
        top_k: int = 5,
    ) -> None:
        self.loader = loader
        self.chunker = chunker
        self.embedder = embedder
        self.vector_store = vector_store
        self.lexical = lexical
        self.retriever = retriever
        self.reranker = reranker
        self.llm = llm
        self.repository = repository
        self.top_k = top_k

    def ingest(self, source: str) -> dict:
        """加载并索引一篇文档，返回统计信息。"""
        loader = select_loader(source)
        doc = loader.load(source)
        chunks = self.chunker.chunk(doc)
        vectors = self.embedder.embed_batch([c.text for c in chunks])
        for chunk, vec in zip(chunks, vectors):
            self.vector_store.upsert(chunk, vec)
            if self.lexical is not None:
                self.lexical.upsert(chunk)
            self.repository.add_chunk(chunk)
        self.repository.add_doc(doc)
        return {
            "doc_id": doc.doc_id,
            "title": doc.title,
            "source": source,
            "chunks": len(chunks),
        }

    @staticmethod
    def _build_prompt(question: str, contexts: list[Chunk]) -> str:
        kb = "\n\n".join(
            f"[{i + 1}] {c.text}" for i, c in enumerate(contexts)
        )
        # 使用全局唯一分隔符，避免与上下文内容中的 <context> 撞名
        return (
            "你是一个严谨的助手。请仅依据以下资料回答问题，不要编造。\n"
            f"<kb-context>\n{kb}\n</kb-context>\n\n"
            f"问题：{question}\n回答："
        )

    def query(self, question: str, top_k: int | None = None) -> QueryResult:
        k = top_k or self.top_k
        qvec = self.embedder.embed(question)
        retrieved = self.retriever.retrieve(question, qvec, k)
        if self.reranker is not None:
            retrieved = self.reranker.rerank(question, retrieved)
        contexts = [rc.chunk for rc in retrieved]
        prompt = self._build_prompt(question, contexts)
        answer = self.llm.generate(prompt, contexts=[c.text for c in contexts], query=question)
        return QueryResult(
            answer=answer,
            contexts=retrieved,
            query=question,
            meta={"n_chunks": len(contexts)},
        )
