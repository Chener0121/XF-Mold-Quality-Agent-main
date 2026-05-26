# 项目概述

XF-Mold-Quality-Agent-main 是基于用户上传的FMEA手册与VDA6.4质量手册，通过大模型API与LangChain Agent实现知识抽取、检索及智能问答，结合Chroma向量库构建质量知识图谱，自动识别过程中的失效风险并推送FMEA分析步骤与体系改进建议，辅助高效解决模具设计及生产中的质量问题。

## 项目结构参考 (Project Overview)

project-root/
│
├── frontend/                              # Vue3 前端
│
├── backend/                               # FastAPI 后端
│   ├── src/
│   │   ├── main.py                        # FastAPI 入口
│   │   │
│   │   ├── core/                          # 核心基础设施
│   │   │   ├── config.py                  #   Pydantic Settings 配置
│   │   │   ├── dependencies.py            #   依赖注入（DB session 等）
│   │   │   ├── exceptions.py              #   自定义异常 + 全局异常处理
│   │   │   ├── middleware.py              #   请求日志中间件
│   │   │   ├── logger.py                  #   logging 配置
│   │   │   ├── llm_client.py              #   LLM 客户端工厂
│   │   │   └── vlm_client.py              #   视觉语言模型客户端
│   │   │
│   │   ├── api/                           # API 层
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   ├── document.py        #   文档上传 + 任务状态 + debug/blocks
│   │   │       │   ├── health.py          #   健康检查
│   │   │       │   └── rag.py             #   RAG 智能问答
│   │   │       │
│   │   │       └── router.py              #   路由注册
│   │   │
│   │   ├── models/                        # 数据模型
│   │   │   ├── entities/                  #   SQLAlchemy ORM（预留）
│   │   │   │   ├── document.py
│   │   │   │   ├── chunk.py
│   │   │   │   └── conversation.py
│   │   │   │
│   │   │   └── schemas/                   #   Pydantic 请求/响应模型
│   │   │       ├── document.py            #     DocumentResponse, TaskStatusResponse
│   │   │       ├── rag.py                 #     RAGQueryRequest, RAGQueryResponse
│   │   │       └── common.py              #     PageResponse[T] 分页泛型
│   │   │
│   │   ├── repositories/                  # 数据访问层（预留）
│   │   │   ├── document_repository.py
│   │   │   ├── chunk_repository.py
│   │   │   └── conversation_repository.py
│   │   │
│   │   ├── services/                      # 业务逻辑层
│   │   │   └── document_service.py        #   文档处理流水线（解析→语义→VLM→分块→嵌入→入库）
│   │   │
│   │   ├── ai/                            # AI 核心
│   │   │   ├── agents/
│   │   │   │   └── rag_agent.py           #   LangGraph ReAct Agent（quality/rd/general）
│   │   │   ├── prompts/
│   │   │   │   └── rag_prompt.py          #   Agent system prompts
│   │   │   ├── tools/
│   │   │   │   └── knowledge_search.py    #   LangChain Tool: 知识库检索
│   │   │   │
│   │   │   └── rag/
│   │   │       ├── cache/                 #   处理缓存（文档/VLM/Embedding）
│   │   │       │   ├── document_cache.py
│   │   │       │   ├── vlm_cache.py
│   │   │       │   ├── embedding_cache.py
│   │   │       │   └── hash_utils.py
│   │   │       ├── embeddings/
│   │   │       │   ├── embedder.py        #   OpenAI 兼容 Embedding 客户端
│   │   │       │   ├── pipeline.py        #   Embedding 流水线（缓存+批量嵌入）
│   │   │       │   └── models.py          #   EmbeddedBlock 模型
│   │   │       ├── retrievers/
│   │   │       │   ├── retriever.py       #   混合检索（向量 + BM25 + RRF 融合）
│   │   │       │   ├── bm25_index.py      #   BM25 关键词索引
│   │   │       │   ├── context_builder.py #   检索结果格式化
│   │   │       │   ├── domain_classifier.py # 领域分类（quality/rd）
│   │   │       │   ├── models.py          #   RetrievalResult 模型
│   │   │       │   └── evaluation/        #   检索评估日志
│   │   │       └── vectorstores/
│   │   │           └── chroma_store.py    #   ChromaDB 向量存储
│   │   │
│   │   ├── document/                      # 文档理解核心
│   │   │   ├── parsers/
│   │   │   │   └── docx_parser.py         #   docx 解析（段落/表格/图片）
│   │   │   └── processors/
│   │   │       ├── semantic_processor.py  #   标题层级传播 + 短块合并
│   │   │       ├── semantic_block.py      #   SemanticBlock 模型
│   │   │       ├── chunker.py             #   语义分块（句子级拆分+重叠）
│   │   │       └── vlm_processor.py       #   VLM 图片理解（乌龟图等）
│   │   │
│   │   ├── storage/                       # 存储层（预留）
│   │   │   ├── postgres/
│   │   │   ├── pgvector/
│   │   │   └── minio/
│   │   │
│   │   └── utils/
│   │       ├── file.py                    #   文件哈希
│   │       ├── markdown.py                #   Markdown 清理
│   │       └── text.py                    #   文本工具
│   │
│   ├── docs/
│   │   └── api-reference.md               # API 接口文档
│   │
│   └── tests/
│       ├── unit/
│       └── integration/
│
├── docker/
│   ├── api.Dockerfile                      # 生产环境
│   ├── api-dev.Dockerfile                  # 开发环境（热重载）
│   ├── web.Dockerfile                      # 前端构建
│   └── nginx.conf
│
├── .env                                    # 环境变量
├── .gitignore
├── docker-compose.yml                      # 开发环境
├── docker-compose.prod.yml                 # 生产部署
├── CLAUDE.md
└── README.md

## 开发准则

Avoid over-engineering. Only make changes that are directly requested or clearly necessary. Keep solutions simple and focused.

Don't add features, refactor code, or make "improvements" beyond what was asked. A bug fix doesn't need surrounding code cleaned up. A simple feature doesn't need extra configurability.

Don't add error handling, fallbacks, or validation for scenarios that can't happen. Trust internal code and framework guarantees. Only validate at system boundaries (user input, external APIs). Don't use backwards-compatibility shims when you can just change the code.

Don't create helpers, utilities, or abstractions for one-time operations. Don't design for hypothetical future requirements. The right amount of complexity is the minimum needed for the current task. Reuse existing abstractions where possible and follow the DRY principle.

## 开发与调试 (Development & Debugging)

本项目完全通过 Docker Compose 进行管理。所有开发和调试都应在运行的容器环境中进行。使用 `docker compose up -d` 命令进行构建和启动。

### 前端开发规范

注意：

- API 接口规范：所有的 API 接口都应该定义在 `frontend/src/apis` 下面。
- Icon 应该从 @ant-design/icons-vue 或者 lucide-vue-next （推荐，但是需要注意尺寸）。
- Vue 中的样式使用 less，非必要情况必须使用[base.css](frontend/src/assets/css/base.css) 中的颜色变量。
- UI风格要简洁，同时要保持一致性，不要悬停位移，不要过度使用阴影以及渐变色。
- 后端接口文档放在了`backend/docs/api-reference.md`，需要对接后端接口时进行参考。
- 绝对不要尝试使用 npm/pnpm 等等运行前端开发服务器。

### 后端开发规范

注意：

- Python 代码要符合 Python 的规范，符合 pythonic 风格，尽量使用较新的语法，避免使用旧版本的语法（版本兼容到 3.12+）
- langchain使用较新的语法，避免使用旧版本的语法（参考版本为 v1.0+）
- 代码添加合适的注释，采用 RESTful 规范进行开发

**其他**：

- 如果需要新建说明文档（仅开发者可见，非必要不创建），则保存在 `docs/vibe` 文件夹下面
- 代码更新后要检查文档部分是否有需要更新的地方，文档应该更新最新版（`docs/latest`）
