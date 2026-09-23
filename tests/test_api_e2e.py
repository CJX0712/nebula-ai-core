# API 端到端测试（TestClient，无需网络）
# 作者: 晨星
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
SAMPLE = ROOT / "samples" / "sample.md"

from fastapi.testclient import TestClient  # noqa: E402

from nebula.api.server import create_app  # noqa: E402


def test_health():
    c = TestClient(create_app())
    assert c.get("/health").json()["status"] == "ok"


def test_ingest_query_agent():
    c = TestClient(create_app())
    r = c.post("/ingest", json={"source": str(SAMPLE)})
    assert r.status_code == 200
    assert r.json()["chunks"] >= 2

    q = c.post("/query", json={"question": "什么是向量数据库？"})
    assert q.status_code == 200
    assert q.json()["answer"]

    a = c.post("/agent", json={"query": "计算 12 * (3 + 4) = ?"})
    assert a.status_code == 200
    assert "84" in a.json()["answer"]

    a2 = c.post("/agent", json={"query": "Nebula 系统由哪些模块组成？"})
    assert a2.status_code == 200
    assert a2.json()["answer"]
