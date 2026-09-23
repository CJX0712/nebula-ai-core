# 大模型后端测试
# 作者: 晨星
from __future__ import annotations

import builtins

from nebula.core.llm import DeterministicLLM, LlamaCppLLM, OpenAICompatibleLLM


def test_extractive_picks_relevant():
    llm = DeterministicLLM()
    ctx = [
        "今天天气晴朗适合户外运动",
        "向量数据库是一种以向量方式存储和检索非结构化数据的数据库",
    ]
    ans = llm.generate("什么是向量数据库？", contexts=ctx, query="什么是向量数据库？")
    assert "向量" in ans


def test_llamacpp_import_error(monkeypatch):
    real = builtins.__import__

    def fake(name, *a, **k):
        if name == "llama_cpp":
            raise ImportError("no")
        return real(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", fake)
    try:
        LlamaCppLLM("m.gguf")
    except RuntimeError as exc:
        assert "llama-cpp" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")
