# 嵌入器测试
# 作者: 晨星
from __future__ import annotations

import builtins
import math

from nebula.core.embedder import FastEmbedEmbedder, HashBigramEmbedder


def test_dim_and_determinism():
    e = HashBigramEmbedder(128)
    v1 = e.embed("向量数据库")
    v2 = e.embed("向量数据库")
    assert e.dim == 128
    assert v1 == v2
    norm = math.sqrt(sum(x * x for x in v1))
    assert abs(norm - 1.0) < 1e-9


def test_batch():
    e = HashBigramEmbedder(64)
    out = e.embed_batch(["a", "b"])
    assert len(out) == 2 and len(out[0]) == 64


def test_fastembed_import_error(monkeypatch):
    real = builtins.__import__

    def fake(name, *a, **k):
        if name == "fastembed":
            raise ImportError("no")
        return real(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", fake)
    try:
        FastEmbedEmbedder()
    except RuntimeError as exc:
        assert "fastembed" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")
