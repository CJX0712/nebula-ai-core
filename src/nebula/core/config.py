# 运行时配置（环境变量驱动，零额外依赖）
# 作者: 晨星
from __future__ import annotations

import os
from dataclasses import dataclass


def _env(name: str, default: str) -> str:
    v = os.environ.get(name)
    return v if v is not None else default


@dataclass(frozen=True)
class Settings:
    """系统配置，全部可通过 NEBULA_ 前缀环境变量覆盖。

    后端选型字段决定工厂注入哪套实现：
      embedder:     hash(默认零依赖) | fastembed(ONNX 生产)
      vector_store: memory(默认零依赖) | faiss(生产)
      lexical:      bm25(默认纯Python) | none
      llm:          deterministic(默认) | llamacpp | openai
      reranker:     score(默认RRF) | none
    """

    embedder: str = "hash"
    vector_store: str = "memory"
    lexical: str = "bm25"
    llm: str = "deterministic"
    reranker: str = "score"

    chunk_size: int = 400
    chunk_overlap: int = 80
    top_k: int = 5
    embed_dim: int = 256

    fastembed_model: str = "BAAI/bge-small-en-v1.5"
    llamacpp_model_path: str = ""
    openai_base_url: str = "http://localhost:11434/v1"
    openai_api_key: str = "sk-no-key"
    openai_model: str = "gpt-3.5-turbo"
    log_level: str = "INFO"

    @staticmethod
    def from_env() -> "Settings":
        def i(name: str, default: int) -> int:
            try:
                return int(_env("NEBULA_" + name, str(default)))
            except ValueError:
                return default

        return Settings(
            embedder=_env("NEBULA_EMBEDDER", "hash"),
            vector_store=_env("NEBULA_VECTOR_STORE", "memory"),
            lexical=_env("NEBULA_LEXICAL", "bm25"),
            llm=_env("NEBULA_LLM", "deterministic"),
            reranker=_env("NEBULA_RERANKER", "score"),
            chunk_size=i("CHUNK_SIZE", 400),
            chunk_overlap=i("CHUNK_OVERLAP", 80),
            top_k=i("TOP_K", 5),
            embed_dim=i("EMBED_DIM", 256),
            fastembed_model=_env("NEBULA_FASTEMBED_MODEL", "BAAI/bge-small-en-v1.5"),
            llamacpp_model_path=_env("NEBULA_LLAMACPP_MODEL_PATH", ""),
            openai_base_url=_env("NEBULA_OPENAI_BASE_URL", "http://localhost:11434/v1"),
            openai_api_key=_env("NEBULA_OPENAI_API_KEY", "sk-no-key"),
            openai_model=_env("NEBULA_OPENAI_MODEL", "gpt-3.5-turbo"),
            log_level=_env("NEBULA_LOG_LEVEL", "INFO"),
        )
