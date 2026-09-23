# Spec - Nebula AI Core v1.0.0

> 生成日期：2026-09-24
> 基于：需求（端到端可运行 AI 系统）+ 架构设计 + 实现验证
> 状态：已确认（开发已据此完成并验证）
> 作者：晨星

---

## 1. 产品定义

- **一句话描述**：端到端可运行的模块化 AI 引擎，覆盖加载/分块/嵌入/检索/生成/RAG/智能体全链路。
- **目标用户**：需要可复现、可部署、可二次开发的 AI 工程团队与个人开发者。
- **核心问题**：避免从零自研，复用开源旗舰，在干净环境中一键复现完整可运行 AI 系统。

## 2. MVP 范围（锁定）

| 优先级 | 功能 | 验收标准摘要 |
|--------|------|--------------|
| P0 | 文档索引（ingest） | 给定 .txt/.md/.pdf，分块并写入向量+稀疏索引 |
| P0 | RAG 问答（query） | 返回非空答案 + 带评分上下文 |
| P0 | 智能体（agent） | 算术路由到计算器；知识路由到 RAG |
| P0 | HTTP 服务 | /health /ingest /query /agent 可用 |
| P0 | 离线可复现 | 无网络/模型/Key 下 pytest + E2E 全绿 |
| P1 | 生产后端切换 | faiss/fastembed/llama-cpp 经环境变量启用 |
| P1 | Docker 部署 | 镜像构建并暴露服务 |

## 3. 明确不做（Out-of-Scope）

| 不做的功能 | 原因 | 何时考虑 |
|------------|------|----------|
| 多用户/鉴权 | MVP 聚焦单进程引擎 | 接入外部网关时 |
| 持久化向量库(外部) | 默认进程内即可复现 | 多实例部署时 |
| 微调/训练 | 复用开源推理即可 | 有专属语料需求时 |
| 前端界面 | 提供 OpenAPI/Swagger | 有产品化需求时 |

## 4. 技术架构（锁定）

| 层 | 技术 | 版本 | 锁定原因 |
|----|------|------|----------|
| 运行时 | Python | 3.13 | 环境与复现基线 |
| 默认依赖 | numpy / fastapi / uvicorn / pydantic / loguru / httpx | 见 requirements.txt | 最小闭包、离线可装 |
| 生产依赖 | faiss-cpu / fastembed / llama-cpp-python / pypdf / onnxruntime | 见 requirements-prod.txt | 复用开源旗舰 |
| 服务 | FastAPI | 0.141.1 | 契约优先、自带 Swagger |
| 测试 | pytest | 8.4.2 | 逐模块独立验证 |

## 5. API 端点清单（锁定）

| Method | Path | 功能 | 认证 | 请求体 | 响应体 |
|--------|------|------|------|--------|--------|
| GET | /health | 健康检查 + 后端状态 | 无 | — | {status,version,llm,embedder,vector_store,indexed_chunks} |
| POST | /ingest | 索引文档 | 无 | {source} | {doc_id,title,source,chunks} |
| POST | /query | RAG 问答 | 无 | {question,top_k?} | {answer,query,contexts[],meta} |
| POST | /agent | 智能体推理 | 无 | {query} | {answer,query,steps[],meta} |

## 6. 数据库表清单（锁定）

当前默认实现为进程内 `DocRepository`，无外部数据库。对外数据结构：

| 结构 | 核心字段 |
|------|----------|
| Document | doc_id, title, text, source, meta |
| Chunk | chunk_id, doc_id, text, index, meta |
| RetrievedChunk | chunk, score, rank |

## 7. 页面清单（锁定）

无前端页面；提供 OpenAPI/Swagger 文档（`/docs`）。

## 8. 设计 Token（锁定）

后端引擎，无 UI 视觉 Token。代码规范：单文件 ≤ 300 行、入口零业务、模块只依赖 Protocol、禁止 emoji 功能图标（P0 门禁扫描）。

## 9. 验收标准（EARS）

| 编号 | 功能 | 验收标准 |
|------|------|----------|
| AC-01 | ingest | When 给定合法文件路径，系统**必须**返回 chunks>0 的索引统计 |
| AC-02 | query | When 查询已索引知识，系统**必须**返回非空 answer 与至少 1 条 context |
| AC-03 | agent 算术 | When 查询含算术表达式，系统**必须**调用计算器并返回正确数值 |
| AC-04 | agent 知识 | When 查询为知识类，系统**必须**走 RAG 并返回非空答案 |
| AC-05 | health | While 服务运行，GET /health **必须**返回 status=ok |
| AC-06 | 复现 | While 干净环境安装 requirements.txt，pytest + verify **必须**全绿 |

## 10. 边界与约束

- 默认向量库/仓储为进程内，重启即清空（已在 ADR 登记）。
- `chunk_overlap` 必须 < `chunk_size`。
- 生产大模型需要 GGUF 权重或远端服务；默认实现不依赖。
- 不支持 IE；目标 Python ≥ 3.10。

## 11. 内嵌已知坑（来自验证实践）

| 坑 | 技术栈指纹 | 根因 | 修法 |
|----|------------|------|------|
| BM25 小语料 idf 为负致排序反转 | rank_bm25 | 半数文档命中时 idf=ln(1)=0 | 默认改用 Robertson idf 恒非负 |
| localhost httpx 走系统 SOCKS | httpx + 代理 | trust_env=True | OpenAICompatibleLLM 设 trust_env=False |
| 提示符与上下文分隔符撞名 | 自写 prompt | `<context>` 字面量冲突 | 使用全局唯一 `<kb-context>` |

## 12. 端到端验证步骤

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest -q                       # 25 passed
python tools/scan_emoji.py      # OK
python scripts/verify.py        # E2E PASS
python -m nebula.cli ingest samples/sample.md
python -m nebula.cli query "什么是向量数据库？"
python -m nebula.cli agent "计算 12 * (3 + 4) = ?"
```

## 13. 变更记录

| 日期 | 变更内容 | 原因 | 影响范围 |
|------|----------|------|----------|
| 2026-09-24 | 初始版本 v1.0.0 | 首次交付 | 全量 |
