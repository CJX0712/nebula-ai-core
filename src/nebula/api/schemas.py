# API 请求/响应模型
# 作者: 晨星
from __future__ import annotations

from pydantic import BaseModel


class IngestRequest(BaseModel):
    source: str


class QueryRequest(BaseModel):
    question: str
    top_k: int | None = None


class AgentRequest(BaseModel):
    query: str


class ChunkOut(BaseModel):
    chunk_id: str
    doc_id: str
    text: str
    score: float


class QueryResponse(BaseModel):
    answer: str
    query: str
    contexts: list[ChunkOut]
    meta: dict


class AgentResponse(BaseModel):
    answer: str
    query: str
    steps: list[dict]
    meta: dict
