# 大模型后端：单一职责 = 文本生成
# 作者: 晨星
from __future__ import annotations

import re
from typing import Protocol, runtime_checkable


@runtime_checkable
class LLM(Protocol):
    """大模型契约：传入 prompt（及可选上下文），返回生成文本。"""

    def generate(self, prompt: str, **kwargs) -> str: ...


def _extractive_answer(query: str, contexts: list[str], max_sentences: int = 4) -> str:
    """抽取式回答：从上下文中挑选与查询词重叠最高的句子。"""
    q_toks = set(re.findall(r"[a-z0-9]+", query.lower())) | set(
        re.findall(r"[\u4e00-\u9fff]", query)
    )
    q_toks = {t for t in q_toks if len(t) > 1 or re.match(r"[\u4e00-\u9fff]", t)}
    sentences: list[tuple[str, int]] = []
    seen: set[str] = set()
    for ctx in contexts:
        for s in re.split(r"(?<=[。.!?！？])", ctx):
            s = s.strip()
            if len(s) < 8:
                continue
            toks = set(re.findall(r"[a-z0-9]+", s.lower())) | set(
                re.findall(r"[\u4e00-\u9fff]", s)
            )
            overlap = len(toks & q_toks)
            if overlap == 0:
                continue
            key = s[:40]
            if key in seen:
                continue
            seen.add(key)
            sentences.append((s, overlap))
    sentences.sort(key=lambda x: x[1], reverse=True)
    picked = [s for s, _ in sentences[:max_sentences]]
    if picked:
        return "\n".join(picked)
    return "根据已有资料，暂未检索到与问题直接相关的明确表述。"


class DeterministicLLM:
    """默认零依赖生成器：抽取式 + 模板，离线确定性可验证。"""

    def generate(self, prompt: str, contexts: list[str] | None = None, query: str | None = None, **kwargs) -> str:
        if contexts:
            return _extractive_answer(query or prompt, contexts)
        q = (query or prompt).strip().split("\n")[-1][:200]
        return "[deterministic] 已接收指令：" + q


class LlamaCppLLM:
    """生产后端：复用 llama-cpp-python 本地推理 GGUF 模型。"""

    def __init__(self, model_path: str, n_ctx: int = 4096, n_threads: int = 4) -> None:
        try:
            from llama_cpp import Llama
        except ImportError as exc:
            raise RuntimeError("LlamaCppLLM 需要 llama-cpp-python") from exc
        if not model_path:
            raise ValueError("LlamaCppLLM 需要 model_path")
        self._model = Llama(model_path=model_path, n_ctx=n_ctx, n_threads=n_threads)

    def generate(self, prompt: str, **kwargs) -> str:
        out = self._model.create_completion(prompt, max_tokens=512, temperature=0.1)
        return out["choices"][0]["text"].strip()


class OpenAICompatibleLLM:
    """生产后端：兼容 OpenAI / Ollama / vLLM 的 /chat/completions 接口。"""

    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        import httpx

        self._httpx = httpx
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str, **kwargs) -> str:
        # 指向 localhost 的服务必须关闭代理信任，避免流量被送进系统 SOCKS
        with self._httpx.Client(
            base_url=self.base_url, timeout=60, trust_env=False
        ) as client:
            resp = client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                },
                headers={"Authorization": "Bearer " + self.api_key},
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
