# 向量库：单一职责 = 稠密向量存取与近邻检索
# 作者: 晨星
from __future__ import annotations

import math
from typing import Protocol, runtime_checkable

from .types import Chunk


@runtime_checkable
class VectorStore(Protocol):
    """向量库契约：upsert 写入，search 返回 (Chunk, 相似度)。"""

    def upsert(self, chunk: Chunk, vector: list[float]) -> None: ...
    def search(self, vector: list[float], top_k: int) -> list[tuple[Chunk, float]]: ...


class MemoryVectorStore:
    """默认零依赖向量库：numpy 余弦相似度，进程内存储。"""

    def __init__(self) -> None:
        self._vecs: list[list[float]] = []
        self._chunks: list[Chunk] = []
        self._norm: list[float] = []

    def upsert(self, chunk: Chunk, vector: list[float]) -> None:
        n = math.sqrt(sum(v * v for v in vector))
        self._norm.append(n if n > 0 else 1.0)
        self._vecs.append(vector)
        self._chunks.append(chunk)

    def search(self, vector: list[float], top_k: int) -> list[tuple[Chunk, float]]:
        qn = math.sqrt(sum(v * v for v in vector)) or 1.0
        scored = []
        for i, v in enumerate(self._vecs):
            dot = sum(a * b for a, b in zip(v, vector))
            sim = dot / (self._norm[i] * qn) if self._norm[i] > 0 else 0.0
            scored.append((self._chunks[i], float(sim)))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]


class FaissVectorStore:
    """生产后端：复用 faiss-cpu 的 IndexFlatIP（L2 归一后等价余弦）。

    需要 pip install faiss-cpu；维度由首个向量自动推断。
    """

    def __init__(self) -> None:
        try:
            import faiss
        except ImportError as exc:
            raise RuntimeError("FaissVectorStore 需要 faiss-cpu，请执行 pip install faiss-cpu") from exc
        self._faiss = faiss
        self._index = None
        self._chunks: list[Chunk] = []
        self._dim: int | None = None

    def upsert(self, chunk: Chunk, vector: list[float]) -> None:
        import numpy as np

        arr = np.array(vector, dtype="float32").reshape(1, -1)
        if self._index is None:
            self._dim = arr.shape[1]
            self._index = self._faiss.IndexFlatIP(self._dim)
        self._index.add(arr)
        self._chunks.append(chunk)

    def search(self, vector: list[float], top_k: int) -> list[tuple[Chunk, float]]:
        import numpy as np

        if self._index is None:
            return []
        k = min(top_k, len(self._chunks))
        arr = np.array(vector, dtype="float32").reshape(1, -1)
        self._faiss.normalize_L2(arr)
        scores, idx = self._index.search(arr, k)
        out = []
        for s, i in zip(scores[0], idx[0]):
            if i == -1:
                continue
            out.append((self._chunks[i], float(s)))
        return out
