# 命令行入口：serve / ingest / query / agent
# 作者: 晨星
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core.factory import build_system


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="nebula", description="Nebula AI Core 命令行")
    sub = p.add_subparsers(dest="cmd", required=True)

    serve = sub.add_parser("serve", help="启动 HTTP 服务")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)

    ingest = sub.add_parser("ingest", help="索引一篇文档")
    ingest.add_argument("source", help="文件路径（.txt/.md/.pdf）")

    query = sub.add_parser("query", help="RAG 问答")
    query.add_argument("question")
    query.add_argument("--top-k", type=int, default=None)

    agent = sub.add_parser("agent", help="智能体推理")
    agent.add_argument("query")

    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    system = build_system()

    if args.cmd == "serve":
        from .api.server import create_app
        import uvicorn

        uvicorn.run(create_app(), host=args.host, port=args.port)
        return 0

    if args.cmd == "ingest":
        result = system["pipeline"].ingest(args.source)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "query":
        res = system["pipeline"].query(args.question, args.top_k)
        print(
            json.dumps(
                {
                    "answer": res.answer,
                    "contexts": [c.chunk.text for c in res.contexts],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.cmd == "agent":
        res = system["agent"].run(args.query)
        print(
            json.dumps(
                {
                    "answer": res.answer,
                    "steps": [
                        {"thought": s.thought, "action": s.action, "observation": s.observation}
                        for s in res.steps
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
