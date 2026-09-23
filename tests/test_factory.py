# 工厂装配测试
# 作者: 晨星
from __future__ import annotations

import pytest

from nebula.core.config import Settings
from nebula.core.factory import build_system
from nebula.core.vectorstore import FaissVectorStore


def test_build_all_keys():
    sys = build_system(Settings())
    for k in [
        "settings",
        "pipeline",
        "agent",
        "embedder",
        "vector_store",
        "lexical",
        "llm",
        "repository",
    ]:
        assert k in sys


def test_faiss_selection():
    pytest.importorskip("faiss")
    sys = build_system(Settings(vector_store="faiss"))
    assert isinstance(sys["vector_store"], FaissVectorStore)


def test_no_lexical():
    sys = build_system(Settings(lexical="none"))
    assert sys["lexical"] is None
