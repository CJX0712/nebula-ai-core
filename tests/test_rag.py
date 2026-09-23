# RAG 管线端到端测试
# 作者: 晨星
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "samples" / "sample.md"


def test_ingest_and_query(system):
    info = system["pipeline"].ingest(str(SAMPLE))
    assert info["chunks"] > 0
    # 样本较长，必须覆盖多分块路径
    assert info["chunks"] >= 2
    res = system["pipeline"].query("什么是向量数据库？")
    assert res.answer
    assert len(res.contexts) > 0


def test_empty_query_still_returns(system):
    system["pipeline"].ingest(str(SAMPLE))
    res = system["pipeline"].query("无关问题测试？")
    assert isinstance(res.answer, str)
