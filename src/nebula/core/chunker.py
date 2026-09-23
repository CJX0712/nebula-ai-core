# 文本分块器：单一职责 = 把 Document 切成可检索的 Chunk
# 作者: 晨星
from __future__ import annotations

import re

from .types import Chunk, Document


class RecursiveChunker:
    """按句边界递归拼接，超过阈值则切断并保留重叠区。

    默认实现零依赖，确定性可复现；chunk_overlap 必须 < chunk_size。
    """

    def __init__(self, chunk_size: int = 400, chunk_overlap: int = 80) -> None:
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap 必须小于 chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, doc: Document) -> list[Chunk]:
        sentences = [
            s.strip()
            for s in re.split(r"(?<=[。.!?！？\n])", doc.text)
            if s.strip()
        ]
        chunks: list[Chunk] = []
        buf = ""
        idx = 0

        def flush(text: str) -> None:
            nonlocal idx
            chunks.append(
                Chunk(
                    chunk_id=f"{doc.doc_id}_c{idx}",
                    doc_id=doc.doc_id,
                    text=text.strip(),
                    index=idx,
                )
            )
            idx += 1

        for s in sentences:
            if not buf:
                buf = s
            elif len(buf) + len(s) <= self.chunk_size:
                buf += s
            else:
                flush(buf)
                tail = buf[-self.chunk_overlap:] if self.chunk_overlap else ""
                buf = tail + s
        if buf.strip():
            flush(buf)
        if not chunks:
            flush(doc.text[: self.chunk_size])
        return chunks
