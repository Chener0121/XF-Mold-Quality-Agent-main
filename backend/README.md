# Backend — XF Mold Quality Agent

FastAPI 后端，提供文档管理、智能体配置、RAG 智能问答和会话管理功能。

## 目录结构

```
backend/src/
├── main.py                          # FastAPI 入口 + lifespan
│
├── core/                            # 核心基础设施
│   ├── config.py                    #   Pydantic Settings（读取 .env）
│   ├── dependencies.py              #   依赖注入（async DB session、engine）
│   ├── exceptions.py                #   AppException + 全局异常处理
│   ├── middleware.py                #   请求日志中间件
│   ├── logger.py                    #   logging 配置
│   ├── llm_client.py                #   LLM 客户端工厂（OpenAI 兼容）
│   └── vlm_client.py                #   视觉语言模型客户端
│
├── api/v1/                          # API 层
│   ├── endpoints/
│   │   ├── health.py                #   GET /health
│   │   ├── document.py              #   文档上传/列表/进度 + 智能体文档配置
│   │   ├── rag.py                   #   POST /chat SSE 流式问答
│   │   └── conversation.py          #   会话 CRUD
│   └── router.py                    #   路由注册
│
├── models/                          # 数据模型
│   ├── entities/                    #   SQLAlchemy ORM
│   │   ├── document.py              #     documents 表
│   │   ├── chunk.py                 #     chunks 表
│   │   ├── conversation.py          #     conversations + messages 表
│   │   └── agent_document.py        #     agent_documents 关联表
│   └── schemas/                     #   Pydantic 请求/响应模型
│       ├── document.py              #     DocumentResponse, TaskStatusResponse
│       ├── rag.py                   #     RAGQueryRequest
│       ├── conversation.py          #     ConversationListResponse 等
│       └── common.py                #     PageResponse[T] 分页泛型
│
├── repositories/                    # 数据访问层
│   ├── document_repository.py       #   智能体-文档关联 CRUD
│   └── conversation_repository.py   #   会话 + 消息 CRUD
│
├── services/
│   └── document_service.py          # 文档处理流水线
│
├── ai/                              # AI 核心
│   ├── agents/
│   │   └── rag_agent.py             #   LangGraph ReAct Agent
│   ├── prompts/
│   │   └── rag_prompt.py            #   三个智能体的 system prompt
│   ├── tools/
│   │   └── knowledge_search.py      #   知识库检索工具（支持文档过滤）
│   ├── chat/                        #   对话编排
│   │   ├── query_pipeline.py        #     流式 pipeline（rewrite → agent）
│   │   ├── history_manager.py       #     Token-aware 历史截断
│   │   ├── query_rewriter.py        #     Query 改写
│   │   └── rewrite_trigger.py       #     改写触发判断
│   └── rag/                         #   RAG 检索引擎
│       ├── cache/                   #     处理缓存
│       ├── embeddings/              #     Embedding 流水线
│       ├── retrievers/              #     混合检索（向量 + BM25 + RRF）
│       └── vectorstores/            #     ChromaDB 存储
│
├── document/                        # 文档理解
│   ├── parsers/docx_parser.py       #   docx 解析
│   └── processors/                  #   语义处理 + 分块 + VLM
│
├── storage/                         # 存储层（预留）
│
└── utils/file.py                    # 文件哈希工具
```

## API 概览

基础路径：`/api/v1`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/documents` | 上传文档（异步处理） |
| GET | `/documents` | 已入库文档列表 |
| GET | `/documents/{task_id}` | 文档处理进度 |
| POST | `/documents/analysis` | 文档结构分析（调试） |
| GET | `/documents/agents/{agent}/documents` | 获取智能体关联文档 |
| PUT | `/documents/agents/{agent}/documents` | 设置智能体关联文档 |
| POST | `/chat` | SSE 流式 RAG 问答 |
| GET | `/conversations` | 会话列表 |
| GET | `/conversations/{id}` | 会话详情 |
| DELETE | `/conversations/{id}` | 删除会话 |

详细接口文档：[docs/api-reference.md](docs/api-reference.md)

## 核心流程

### 文档处理流水线

```
上传文件 → 文件哈希去重 → docx 解析 → 语义处理（标题层级 + 领域分类）
→ VLM 图片增强 → 语义分块 → Embedding → ChromaDB 入库
```

### RAG 问答流程

```
用户提问 → Query 改写判断 → 加载历史上下文
→ 获取智能体关联文档 → LangGraph ReAct Agent
→ knowledge_search 工具（向量 + BM25 混合检索，RRF 融合）
→ 流式输出（thinking → token → done）
→ 保存会话消息
```

### 检索过滤机制

智能体检索时同时应用两层过滤：

1. **文档过滤**（`source`）：仅检索智能体配置的文档，向量检索和 BM25 均过滤
2. **领域过滤**（`domains`）：按 chunk 级别的领域标签（quality/rd）过滤

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `POSTGRES_HOST` | PostgreSQL 地址 | `postgres` |
| `POSTGRES_PORT` | PostgreSQL 端口 | `5432` |
| `POSTGRES_USER` | 数据库用户 | `moldagent` |
| `POSTGRES_PASSWORD` | 数据库密码 | `moldagent_secret` |
| `POSTGRES_DB` | 数据库名 | `mold_quality` |
| `LLM_API_KEY` | LLM API 密钥 | 必填 |
| `LLM_API_BASE` | LLM API 地址 | 阿里云 DashScope |
| `LLM_MODEL` | 聊天模型名称 | 必填 |
| `LLM_VLM_MODEL` | 视觉模型名称 | 必填 |
| `LLM_EMBEDDING_MODEL` | Embedding 模型 | 必填 |
| `CHROMA_PERSIST_DIR` | ChromaDB 持久化目录 | `./chroma_data` |
| `CACHE_DIR` | 处理缓存目录 | `./cache` |

## 开发

后端通过 Docker 开发容器运行，代码挂载实现热重载：

```bash
# 启动开发环境
docker compose up -d

# 查看日志
docker compose logs -f api-dev

# 重建（修改依赖后）
docker compose up -d --build api-dev
```

## 测试与脚本

```bash
# 检索评测数据集生成
docker compose exec api-dev python backend/scripts/generate_eval_dataset.py

# 运行检索评测
docker compose exec api-dev python backend/scripts/run_retrieval_eval.py
```
