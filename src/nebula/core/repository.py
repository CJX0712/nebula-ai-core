# 仓储：单一职责 = 文档与分块的持久化元数据
# 作者: 晨星
from __future__ import annotations

from .types import Chunk, Document


class DocRepository:
    """默认内存仓储：进程内保存文档与分块索引，支持后续替换为 SQLite。"""

    def __init__(self) -> None:
        self._docs: dict[str, Document] = {}
        self._chunks: dict[str, Chunk] = {}

    def add_doc(self, doc: Document) -> None:
        self._docs[doc.doc_id] = doc

    def add_chunk(self, chunk: Chunk) -> None:
        self._chunks[chunk.chunk_id] = chunk

    def get_doc(self, doc_id: str) -> Document | None:
        return self._docs.get(doc_id)

    def list_docs(self) -> list[Document]:
        return list(self._docs.values())

    def count(self) -> int:
        """已索引的分块数量。"""
        return len(self._chunks)
