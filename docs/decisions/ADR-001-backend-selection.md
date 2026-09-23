# ADR-001: 默认零依赖实现 + 生产可插拔后端

- **状态**：Accepted（2026-09-24）
- **作者**：晨星

## Background

需要在干净环境中保证 AI 系统「一键复现、可运行、可验证」，同时又要复用业界领先的开源成果以获得真实语义能力。二者存在张力：强依赖（torch / 编译型原生库）会破坏离线复现。

## Decision

- 每个模块以 `typing.Protocol` 定义契约；
- 提供**零依赖默认实现**（哈希嵌入 / numpy 向量 / 纯 Python BM25 / 抽取式生成），保证无网络、无模型、无 Key 全绿；
- 生产实现（`fastembed` / `faiss-cpu` / `llama-cpp-python` / `pypdf`）作为同一 Protocol 的可选实现，仅在 `requirements-prod.txt` 声明，经 `NEBULA_*` 环境变量切换；
- 依赖注入集中在 `core/factory.py`，入口零业务。

## Consequences

- 正面：默认链路可在任意干净 Python 环境 100% 复现；生产能力按需开启，不污染最小闭包。
- 负面：两套实现需保持行为一致（已在单测中覆盖关键不变量）。
- 关联：ADR-002（离线优先验证）。
