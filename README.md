# XF Mold Quality Agent

基于 FMEA 手册与 VDA6.4 质量手册的模具质量智能问答系统。通过大模型 API 与 LangGraph Agent 实现知识抽取、检索及智能问答，结合 ChromaDB 向量库构建质量知识库，自动识别过程中的失效风险并推送 FMEA 分析步骤与体系改进建议。

## 架构概览

```
┌──────────┐     ┌──────────┐     ┌──────────────┐
│  Vue3    │────▶│  FastAPI  │────▶│  PostgreSQL   │
│  前端    │◀─── │  后端     │     │  (pgvector)   │
│  :5173   │ SSE │  :8000    │     └──────────────┘
└──────────┘     └────┬─────┘     ┌──────────────┐
                      ├──────────▶│  ChromaDB     │
                      │           │  向量存储      │
                      │           └──────────────┘
                      ├──────────▶│  LLM API      │
                      │           │  (OpenAI兼容)  │
                      │           └──────────────┘
```

- **前端**：Vue 3 + TypeScript + Pinia，Vite 开发服务器
- **后端**：FastAPI + LangGraph ReAct Agent，混合检索（向量 + BM25 + RRF）
- **存储**：PostgreSQL (pgvector) + ChromaDB
- **部署**：Docker Compose，Nginx 反向代理

## 三个智能体

| 智能体 | 领域 | 说明 |
|--------|------|------|
| 模具通用智能体 (general) | 全部 | 检索全量知识库，综合回答 |
| 模具质量智能体 (quality) | 质量管理 | 专注 VDA6.4 体系，仅检索配置的文档 |
| 模具研发智能体 (rd) | 研发设计 | 专注模具设计/工艺开发，仅检索配置的文档 |

每个智能体可独立配置关联文档和自定义规则。

## 快速开始

### 环境要求

- Docker & Docker Compose
- Git

### 1. 克隆项目

```bash
git clone <repo-url>
cd XF-Mold-Quality-Agent-main
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，填写 LLM API 配置（必填）：

```env
LLM_API_KEY=your-api-key
LLM_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
LLM_VLM_MODEL=qwen-vl-plus
LLM_EMBEDDING_MODEL=text-embedding-v3
```

### 3. 启动开发环境

```bash
docker compose up -d
```

启动后：
- 前端：http://localhost:5173
- 后端 API：http://localhost:8000
- Swagger 文档：http://localhost:8000/docs

### 4. 生产部署

```bash
docker compose -f docker-compose.prod.yml up -d
```

Nginx 监听 80/443 端口，反向代理至后端。

## 项目结构

```
project-root/
├── frontend/                # Vue3 前端（详见 frontend/README.md）
├── backend/                 # FastAPI 后端（详见 backend/README.md）
├── docker/                  # Docker 配置
│   ├── api.Dockerfile       #   后端生产镜像
│   ├── api-dev.Dockerfile   #   后端开发镜像（热重载）
│   ├── web.Dockerfile       #   前端生产镜像
│   ├── web-dev.Dockerfile   #   前端开发镜像
│   ├── nginx.conf           #   Nginx 反向代理配置
│   └── postgres/init.sql    #   数据库初始化
├── .env.example             # 环境变量模板
├── docker-compose.yml       # 开发环境编排
├── docker-compose.prod.yml  # 生产环境编排
├── pyproject.toml           # Python 依赖（uv）
├── CLAUDE.md                # AI 开发助手上下文
└── README.md
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3, TypeScript, Pinia, Vue Router, Vite, Less |
| UI | Lucide Icons, KaTeX (数学公式), Marked (Markdown渲染) |
| 后端 | FastAPI, Pydantic v2, SQLAlchemy 2.0 (async) |
| AI | LangGraph, LangChain, OpenAI API (兼容格式) |
| 检索 | ChromaDB (向量), BM25 (关键词), RRF 融合 |
| 文档 | python-docx, pypdf |
| 数据库 | PostgreSQL 16 + pgvector |
| 部署 | Docker Compose, Nginx |

## API 文档

后端接口文档：[backend/docs/api-reference.md](backend/docs/api-reference.md)

也可启动服务后访问 Swagger UI：http://localhost:8000/docs
