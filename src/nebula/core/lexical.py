# 稀疏索引：单一职责 = 关键词（BM25）检索
# 作者: 晨星
from __future__ import annotations

import math
import re
from typing import Protocol, runtime_checkable

from .types import Chunk


@runtime_checkable
class LexicalIndex(Protocol):
    """稀疏索引契约：upsert 建索引，search 返回 (Chunk, 得分)。"""

    def upsert(self, chunk: Chunk) -> None: ...
    def search(self, query: str, top_k: int) -> list[tuple[Chunk, float]]: ...


def _tokenize(text: str) -> list[str]:
    toks = [t.lower() for t in re.findall(r"[a-z0-9]+", text.lower())]
    toks += list(re.findall(r"[\u4e00-\u9fff]", text))
    return toks


class BM25Index:
    """默认零依赖 BM25：Robertson idf 恒非负，规避小语料 idf 为负陷阱。"""

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self._docs: list[list[str]] = []
        self._chunks: list[Chunk] = []
        self._df: dict[str, int] = {}
        self._idf: dict[str, float] = {}
        self._avgdl: float = 0.0
        self._built = False

    def upsert(self, chunk: Chunk) -> None:
        toks = _tokenize(chunk.text)
        self._docs.append(toks)
        self._chunks.append(chunk)
        for t in set(toks):
            self._df[t] = self._df.get(t, 0) + 1
        self._built = False

    def _ensure(self) -> None:
        if self._built:
            return
        n = len(self._docs)
        self._avgdl = sum(len(d) for d in self._docs) / n if n else 0.0
        for t, df in self._df.items():
            # Robertson idf，恒非负
            self._idf[t] = math.log(1 + (n - df + 0.5) / (df + 0.5))
        self._built = True

    def search(self, query: str, top_k: int) -> list[tuple[Chunk, float]]:
        self._ensure()
        q_toks = _tokenize(query)
        scored = []
        for i, doc in enumerate(self._docs):
            dl = len(doc)
            freq: dict[str, int] = {}
            for t in doc:
                freq[t] = freq.get(t, 0) + 1
            score = 0.0
            norm_dl = dl / self._avgdl if self._avgdl else 1.0
            for qt in set(q_toks):
                if qt not in freq:
                    continue
                idf = self._idf.get(qt, 0.0)
                f = freq[qt]
                denom = f + self.k1 * (1 - self.b + self.b * norm_dl)
                score += idf * (f * (self.k1 + 1)) / denom
            if score > 0:
                scored.append((self._chunks[i], float(score)))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
