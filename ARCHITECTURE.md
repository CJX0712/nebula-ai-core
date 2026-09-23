# Nebula AI Core 架构设计

**作者：晨星** ｜ 版本：1.0.0

本文说明 Nebula 的模块划分、接口契约、依赖注入与调用关系，是 `docs/SPEC.md` 的设计依据。

---

## 1. 设计原则

1. **单一职责**：每个 AI 功能模块只解决一件事（加载、分块、嵌入、检索、生成……）。
2. **面向协议编程**：所有模块以 `typing.Protocol` 定义契约，调用方只依赖抽象，不依赖具体实现。
3. **依赖注入 + 工厂装配**：唯一装配点在 `core/factory.py`，按 `Settings` 选择并注入实现；入口（API/CLI）只装配、零业务。
4. **默认离线、生产可插拔**：每个 Protocol 至少有一个零依赖默认实现，保证无网络/无模型/无 Key 可跑；生产实现复用开源旗舰，经环境变量切换。
5. **可独立验证**：每个模块都有对应单测，可在隔离状态下验证；模块间通过纯数据结构（`Chunk`/`RetrievedChunk`/`QueryResult`）传递。

---

## 2. 模块契约与实现

| 模块 | Protocol | 默认实现 | 生产实现 |
|------|----------|----------|----------|
| 加载器 | `DocumentLoader` | `TextLoader` / `MarkdownLoader` | `PDFLoader`(pypdf) |
| 分块器 | （具体类） | `RecursiveChunker` | — |
| 嵌入器 | `Embedder` | `HashBigramEmbedder` | `FastEmbedEmbedder` |
| 向量库 | `VectorStore` | `MemoryVectorStore` | `FaissVectorStore` |
| 稀疏索引 | `LexicalIndex` | `BM25Index` | rank-bm25 |
| 检索器 | `Retriever` | `HybridRetriever`(RRF) | — |
| 重排器 | `Reranker` | `ScoreReranker` | CrossEncoder(可选) |
| 大模型 | `LLM` | `DeterministicLLM` | `LlamaCppLLM` / `OpenAICompatibleLLM` |
| 仓储 | （具体类） | `DocRepository` | SQLite(可选) |
| 管线 | — | `RAGPipeline` | — |
| 智能体 | — | `ReActAgent` | — |

### 关键不变量（可验证）

- `HashBigramEmbedder`：同一文本两次 `embed` 结果完全一致（确定性）；输出 L2 范数 = 1.0。
- `MemoryVectorStore` / `FaissVectorStore`：`search` 返回按相似度降序，`top_k` 截断正确。
- `BM25Index`：idf 恒非负（Robertson 公式），规避小语料 idf 为负导致排序反转。
- `HybridRetriever`：RRF 融合后输出按融合分降序，且 `rank` 从 1 连续编号。
- `ReActAgent`：算术表达式确定性路由到计算器（返回正确数值）；其余走 RAG。

---

## 3. 调用关系

```
CLI / API
   │
   ├─ Factory.build_system(Settings)   ← 唯一装配点
   │
   ├─ ReActAgent.run(query)
   │     ├─ (算术) CalculatorTool        → 直接返回数值
   │     └─ (知识) RAGPipeline.query()
   │
   └─ RAGPipeline.ingest(source) / query(question)
         ├─ Loader.load            → Document
         ├─ Chunker.chunk          → list[Chunk]
         ├─ Embedder.embed_batch   → list[vector]
         ├─ VectorStore.upsert     → 索引
         ├─ LexicalIndex.upsert    → 索引
         ├─ Retriever.retrieve     → list[RetrievedChunk]   (向量 + 稀疏 RRF 融合)
         ├─ Reranker.rerank        → 重排
         ├─ LLM.generate           → 答案
         └─ Repository.add_*       → 元数据持久化
```

数据在模块间以不可变 `dataclass`（`Document`/`Chunk`/`RetrievedChunk`/`QueryResult`/`AgentResult`）传递，模块之间不保存彼此状态，因此可独立替换与测试。

---

## 4. 默认实现为何能离线复现

默认链路不依赖任何需要下载权重的组件：

- 嵌入 = 哈希 trick（中文按字 + 二字 bigram，英文按词），纯算法确定性输出；
- 向量库 = numpy 内积 / 余弦，进程内存储；
- 稀疏检索 = 自写 Robertson BM25，纯 Python；
- 生成 = 抽取式（从检索上下文中挑选与查询词重叠最高的句子）+ 模板。

因此 `pytest` 与 `scripts/verify.py` 在**无网络、无模型、无 API Key** 下全绿，这是「干净环境一键复现」的硬保证。

---

## 5. 生产实现如何复用开源

生产实现只是同一 Protocol 的另一套实现，零侵入替换：

- 语义嵌入：`fastembed`（Qdrant 出品，ONNX 推理，CPU 友好，无需 torch）；
- 稠密检索：`faiss-cpu` 的 `IndexFlatIP`（L2 归一后等价余弦）；
- 本地大模型：`llama-cpp-python` 加载 GGUF（支持 Qwen/Llama 等）；
- 远端大模型：`OpenAICompatibleLLM` 对接 Ollama / vLLM / OpenAI（注意 `trust_env=False` 避免 localhost 流量被送进系统代理）；
- PDF 解析：`pypdf`。

这些依赖仅在 `requirements-prod.txt` 中声明，默认链路完全不引入，保证最小闭包可安装。

---

## 6. 验证体系

| 层级 | 工具 | 覆盖 |
|------|------|------|
| 单元 | `pytest`（`tests/`） | 每个模块独立验证 + 边界条件 |
| 门禁 | `tools/scan_emoji.py` | P0：禁止 emoji 功能图标 |
| 端到端 | `scripts/verify.py` | 拉起应用跑 ingest/query/agent 成功流与错误流 |
| 生产冒烟 | worldai 环境 | faiss 真实建库检索；生产模块全部 import 通过 |

详见 `README.md` 验证清单。
