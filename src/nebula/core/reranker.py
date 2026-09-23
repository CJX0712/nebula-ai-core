# 重排器：单一职责 = 对召回结果二次排序
# 作者: 晨星
from __future__ import annotations

import re
from typing import Protocol, runtime_checkable

from .types import RetrievedChunk


@runtime_checkable
class Reranker(Protocol):
    """重排器契约：输入召回列表，返回重排后列表。"""

    def rerank(self, query: str, retrieved: list[RetrievedChunk]) -> list[RetrievedChunk]: ...


class ScoreReranker:
    """默认重排：在 RRF 融合分基础上，叠加查询词与片段的词面重叠奖励。

    确定性、零模型依赖；融合分已是高质量排序，此步做轻量精排。
    """

    @staticmethod
    def _q_tokens(query: str) -> set[str]:
        return set(re.findall(r"[a-z0-9]+", query.lower())) | set(
            re.findall(r"[\u4e00-\u9fff]", query)
        )

    def rerank(self, query: str, retrieved: list[RetrievedChunk]) -> list[RetrievedChunk]:
        q_toks = self._q_tokens(query)
        if not q_toks:
            return retrieved
        boosted = []
        for rc in retrieved:
            toks = set(re.findall(r"[a-z0-9]+", rc.chunk.text.lower())) | set(
                re.findall(r"[\u4e00-\u9fff]", rc.chunk.text)
            )
            overlap = len(toks & q_toks)
            new_score = rc.score + 0.001 * overlap
            boosted.append(RetrievedChunk(chunk=rc.chunk, score=new_score, rank=rc.rank))
        boosted.sort(key=lambda x: x.score, reverse=True)
        for i, rc in enumerate(boosted):
            rc.rank = i + 1
        return boosted
