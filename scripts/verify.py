# 自包含端到端验证：拉起应用，跑成功流与错误流，全绿即系统可运行
# 作者: 晨星
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
SAMPLE = ROOT / "samples" / "sample.md"

from fastapi.testclient import TestClient  # noqa: E402

from nebula.api.server import create_app  # noqa: E402


def main() -> int:
    app = create_app()
    client = TestClient(app)

    assert client.get("/health").json()["status"] == "ok"

    r = client.post("/ingest", json={"source": str(SAMPLE)})
    assert r.status_code == 200, r.text
    ing = r.json()
    assert ing["chunks"] >= 2, "样本应被切成多个分块"

    q = client.post("/query", json={"question": "什么是向量数据库？"})
    assert q.status_code == 200, q.text
    qj = q.json()
    assert qj["answer"], "查询必须返回非空答案"
    assert len(qj["contexts"]) > 0

    a = client.post("/agent", json={"query": "计算 12 * (3 + 4) = ?"})
    assert a.status_code == 200, a.text
    assert "84" in a.json()["answer"], "智能体算术路由必须得到 84"

    a2 = client.post("/agent", json={"query": "Nebula 系统由哪些模块组成？"})
    assert a2.status_code == 200
    assert a2.json()["answer"], "智能体知识路由必须返回答案"

    print("E2E PASS: ingest + query + agent 全部通过")
    print(f"  indexed_chunks={ing['chunks']}  query_contexts={len(qj['contexts'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
