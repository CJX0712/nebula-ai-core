# 嵌入器：单一职责 = 文本 -> 固定维向量
# 作者: 晨星
from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol, runtime_checkable

from .config import Settings


@runtime_checkable
class Embedder(Protocol):
    """嵌入器契约。dim 为输出向量维度。"""

    dim: int

    def embed(self, text: str) -> list[float]: ...
    def embed_batch(self, texts: list[str]) -> list[list[float]]: ...


class HashBigramEmbedder:
    """默认零依赖嵌入器。

    中英文混合 hashing trick：英文按词、中文按字 + 二字 bigram 取哈希桶，
    +/-1 符号累加后 L2 归一化。确定性、离线、无需模型，适合复现与单测。
    """

    def __init__(self, dim: int = 256) -> None:
        if dim <= 0:
            raise ValueError("dim 必须为正整数")
        self.dim = dim

    def _tokens(self, text: str) -> list[str]:
        toks = re.findall(r"[a-z0-9]+", text.lower())
        cjk = re.findall(r"[\u4e00-\u9fff]", text)
        for i in range(len(cjk) - 1):
            toks.append("bg:" + cjk[i] + cjk[i + 1])
        for c in cjk:
            toks.append("c1:" + c)
        return toks

    def _vec(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for t in self._tokens(text):
            h = int(hashlib.md5(t.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dim
            sign = 1.0 if (h >> 7) & 1 else -1.0
            vec[idx] += sign
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    def embed(self, text: str) -> list[float]:
        return self._vec(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self._vec(t) for t in texts]


class FastEmbedEmbedder:
    """生产后端：复用 Qdrant fastembed（ONNX，CPU 友好，无需 torch）。

    首次使用会下载模型权重，需要网络；dim 随模型固定为 384。
    """

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5") -> None:
        try:
            from fastembed import TextEmbedding
        except ImportError as exc:
            raise RuntimeError("FastEmbedEmbedder 需要 fastembed，请执行 pip install fastembed") from exc
        self._model = TextEmbedding(model_name=model_name)
        self.dim = 384

    def embed(self, text: str) -> list[float]:
        return list(self._model.embed([text]))[0].tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [v.tolist() for v in self._model.embed(texts)]
