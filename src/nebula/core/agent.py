# 智能体：单一职责 = 推理编排与工具路由
# 作者: 晨星
from __future__ import annotations

import re

from .rag import RAGPipeline
from .types import AgentResult, AgentStep


class CalculatorTool:
    """确定性计算器：仅允许四则运算，eval 沙箱化。"""

    name = "calculator"

    def run(self, expr: str) -> str:
        allowed = set("0123456789+-*/().% ")
        if not all(c in allowed for c in expr):
            return "表达式包含非法字符"
        try:
            return str(eval(expr, {"__builtins__": {}}, {}))  # noqa: S307
        except Exception as exc:  # noqa: BLE001
            return "计算错误：" + str(exc)


class RAGTool:
    """知识检索工具：委托 RAG 管线回答问题。"""

    name = "rag"

    def __init__(self, pipeline: RAGPipeline) -> None:
        self.pipeline = pipeline

    def run(self, query: str) -> str:
        return self.pipeline.query(query).answer


class ReActAgent:
    """确定性前置路由的智能体。

    先识别算术表达式 -> 调用 calculator（避免小模型重算出错）；
    否则 -> 调用 rag 检索知识库。每步记录 thought/action/observation。
    """

    def __init__(self, pipeline: RAGPipeline) -> None:
        self.pipeline = pipeline
        self.calc = CalculatorTool()
        self.rag = RAGTool(pipeline)

    @staticmethod
    def _has_arithmetic(query: str) -> bool:
        return bool(re.search(r"\d+\s*[\+\-\*/]\s*\d+", query))

    def run(self, query: str) -> AgentResult:
        steps: list[AgentStep] = []
        if self._has_arithmetic(query):
            expr = re.sub(r"[^0-9\+\-\*/\(\)\.\%\s]", "", query)
            obs = self.calc.run(expr)
            steps.append(
                AgentStep(
                    thought="检测到算术表达式，确定性前置路由到 calculator 工具",
                    action="calculator(" + expr + ")",
                    observation=obs,
                )
            )
            return AgentResult(
                answer="计算结果：" + obs,
                steps=steps,
                query=query,
                meta={"route": "calculator"},
            )
        # 知识路由
        res = self.pipeline.query(query)
        steps.append(
            AgentStep(
                thought="调用 RAG 工具检索知识库并生成回答",
                action="rag(query)",
                observation=res.answer[:200],
            )
        )
        return AgentResult(
            answer=res.answer,
            steps=steps,
            query=query,
            meta={"route": "rag", "n_contexts": len(res.contexts)},
        )
