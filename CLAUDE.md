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
│   │   │   ├── config.py
│   │   │   ├── dependencies.py
│   │   │   ├── exceptions.py
│   │   │   ├── middleware.py
│   │   │   ├── logger.py
│   │   │   └── llm_client.py
│   │   │
│   │   ├── api/                           # API层
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   ├── chat.py
│   │   │       │   ├── document.py
│   │   │       │   └── health.py
│   │   │       │
│   │   │       └── router.py
│   │   │
│   │   ├── models/                        # 数据模型
│   │   │   ├── entities/
│   │   │   │   ├── document.py
│   │   │   │   ├── chunk.py
│   │   │   │   └── conversation.py
│   │   │   │
│   │   │   └── schemas/
│   │   │       ├── document.py
│   │   │       ├── chat.py
│   │   │       └── common.py
│   │   │
│   │   ├── repositories/                  # 数据访问层
│   │   │   ├── document_repository.py
│   │   │   ├── chunk_repository.py
│   │   │   └── conversation_repository.py
│   │   │
│   │   ├── services/                      # 业务逻辑层
│   │   │   ├── document_service.py
│   │   │   ├── rag_service.py
│   │   │   └── chat_service.py
│   │   │
│   │   ├── ai/                            # AI核心
│   │   │   ├── agents/
│   │   │   ├── prompts/
│   │   │   ├── tools/
│   │   │   ├── memory/
│   │   │   │
│   │   │   ├── rag/
│   │   │   │   ├── embeddings/
│   │   │   │   ├── retrievers/
│   │   │   │   ├── rerankers/
│   │   │   │   ├── vectorstores/
│   │   │   │   └── pipelines/
│   │   │   │
│   │   │   └── workflows/
│   │   │
│   │   ├── document/                      # 文档理解核心
│   │   │   ├── parsers/                   # docx/pdf解析
│   │   │   └──  processors/               # 后处理
│   │   │
│   │   ├── storage/
│   │   │   ├── postgres/
│   │   │   ├── pgvector/
│   │   │   └── minio/
│   │   │
│   │   └── utils/
│   │       ├── file.py
│   │       ├── markdown.py
│   │       └── text.py
│   │
│   ├── docs/
│   │   └── api-reference.md
│   │
│   └── tests/
│       ├── unit/
│       └── integration/
│
├── docker/
│   ├──api.Dockerfile
│   ├── web.Dockerfile
│   ├──nginx.conf
│   │
│   ├── postgres/
│   │   └── init.sql
│   │
│   └── minio/
│
├── volumes/                               # Docker 数据卷（不要提交Git）
│   ├── postgres/
│   ├── minio/
│   └── redis/
│
├── .env
├── .gitignore
├── docker-compose.yml                     # 开发时使用
├── docker-compose.prod.yml                # 部署云服务器时使用
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
