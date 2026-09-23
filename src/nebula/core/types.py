# 共享数据类型定义
# 作者: 晨星
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Document:
    """一篇被加载的原始文档。"""

    doc_id: str
    title: str
    text: str
    source: str = ""
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class Chunk:
    """文档分块后的最小检索单元。"""

    chunk_id: str
    doc_id: str
    text: str
    index: int = 0
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievedChunk:
    """检索返回的带评分片段。"""

    chunk: Chunk
    score: float
    rank: int = 0


@dataclass
class QueryResult:
    """RAG 查询的最终结果。"""

    answer: str
    contexts: list[RetrievedChunk]
    query: str
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentStep:
    """Agent 单步思考-行动-观察记录。"""

    thought: str
    action: str
    observation: str


@dataclass
class AgentResult:
    """Agent 推理最终结果。"""

    answer: str
    steps: list[AgentStep]
    query: str
    meta: dict[str, Any] = field(default_factory=dict)
