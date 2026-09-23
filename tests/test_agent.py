# 智能体测试
# 作者: 晨星
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "samples" / "sample.md"


def test_agent_arithmetic(system):
    res = system["agent"].run("计算 12 * (3 + 4) = ?")
    assert "84" in res.answer
    assert res.meta["route"] == "calculator"
    assert res.steps


def test_agent_rag(system):
    system["pipeline"].ingest(str(SAMPLE))
    res = system["agent"].run("Nebula 系统由哪些模块组成？")
    assert res.answer
    assert res.meta["route"] == "rag"
