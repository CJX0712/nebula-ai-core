# FastAPI 服务：入口只负责装配与路由，零业务逻辑
# 作者: 晨星
from __future__ import annotations

from fastapi import FastAPI

from ..core.config import Settings
from ..core.factory import build_system
from .schemas import (
    AgentRequest,
    AgentResponse,
    ChunkOut,
    IngestRequest,
    QueryRequest,
    QueryResponse,
)


def create_app(settings: Settings | None = None) -> FastAPI:
    app = FastAPI(title="Nebula AI Core", version="1.0.0")
    state: dict = {"sys": build_system(settings)}

    @app.get("/health")
    def health() -> dict:
        sys = state["sys"]
        return {
            "status": "ok",
            "version": "1.0.0",
            "llm": sys["settings"].llm,
            "embedder": sys["settings"].embedder,
            "vector_store": sys["settings"].vector_store,
            "indexed_chunks": sys["repository"].count(),
        }

    @app.post("/ingest", response_model=dict)
    def ingest(req: IngestRequest) -> dict:
        return state["sys"]["pipeline"].ingest(req.source)

    @app.post("/query", response_model=QueryResponse)
    def query(req: QueryRequest) -> QueryResponse:
        res = state["sys"]["pipeline"].query(req.question, req.top_k)
        return QueryResponse(
            answer=res.answer,
            query=res.query,
            contexts=[
                ChunkOut(
                    chunk_id=c.chunk.chunk_id,
                    doc_id=c.chunk.doc_id,
                    text=c.chunk.text,
                    score=c.score,
                )
                for c in res.contexts
            ],
            meta=res.meta,
        )

    @app.post("/agent", response_model=AgentResponse)
    def agent(req: AgentRequest) -> AgentResponse:
        res = state["sys"]["agent"].run(req.query)
        return AgentResponse(
            answer=res.answer,
            query=res.query,
            steps=[
                {"thought": s.thought, "action": s.action, "observation": s.observation}
                for s in res.steps
            ],
            meta=res.meta,
        )

    return app


# 供 uvicorn 直接加载：uvicorn nebula.api.server:app
app = create_app()
