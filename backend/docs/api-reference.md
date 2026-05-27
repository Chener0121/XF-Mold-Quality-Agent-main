# API Reference

## 基础信息

- 基础路径: `/api/v1`
- 数据格式: JSON（SSE 接口除外）
- Swagger 文档: `/docs`

## 接口总览

| 模块 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 健康检查 | GET | `/health` | 服务状态检查 |
| 文档管理 | POST | `/documents` | 上传文档 |
| | GET | `/documents` | 文档列表 |
| | GET | `/documents/{task_id}` | 查询处理进度 |
| | POST | `/documents/analysis` | 分析文档结构（调试） |
| 智能体配置 | GET | `/documents/agents/{agent}/documents` | 获取智能体关联文档 |
| | PUT | `/documents/agents/{agent}/documents` | 设置智能体关联文档 |
| 智能问答 | POST | `/chat` | SSE 流式 RAG 问答 |
| 会话管理 | GET | `/conversations` | 会话列表 |
| | GET | `/conversations/{id}` | 会话详情（含消息） |
| | DELETE | `/conversations/{id}` | 删除会话 |

---

## 健康检查

`GET /api/v1/health`

**响应** (`200 OK`):
```json
{ "status": "ok" }
```

---

## 文档管理

### 上传文档

`POST /api/v1/documents`

上传 FMEA / VDA6.4 质量手册等文档，后台异步处理（解析 → 语义分块 → VLM 增强 → Embedding → 入库）。相同文件内容的文档会自动去重跳过。

- **Content-Type**: `multipart/form-data`
- **字段**: `file`（`.docx` 或 `.pdf`）

**成功响应** (`201 Created`):
```json
{
  "id": "task-uuid",
  "filename": "FMEA手册.docx",
  "status": "processing"
}
```

**错误响应** (`415`):
```json
{ "detail": "仅支持 .docx / .pdf 格式" }
```

### 文档列表

`GET /api/v1/documents`

返回 ChromaDB 中所有已入库文档的 source 列表。

**响应** (`200 OK`):
```json
[
  { "id": "XF模具VDA6.4质量手册.docx", "filename": "XF模具VDA6.4质量手册.docx" },
  { "id": "FMEA手册-2019年6月5版.docx", "filename": "FMEA手册-2019年6月5版.docx" }
]
```

### 查询处理进度

`GET /api/v1/documents/{task_id}`

上传接口返回的 `id` 即为 `task_id`，用于轮询处理进度。

**路径参数:**
| 参数 | 说明 |
|------|------|
| `task_id` | 上传时返回的任务 UUID |

**响应** (`200 OK`):
```json
{
  "task_id": "uuid",
  "filename": "FMEA手册.docx",
  "stage": "embedding",
  "progress": { "filename": "FMEA手册.docx", "total_chunks": 128 },
  "status": "processing"
}
```

`stage` 流转: `queued` → `parsing` → `processing` → `enriching` → `chunking` → `embedding` → `completed`

`status` 可能值: `processing` | `completed` | `failed`

**未找到** (`404`):
```json
{ "detail": "任务不存在" }
```

### 分析文档结构

`POST /api/v1/documents/analysis`

调试接口。仅支持 `.docx`，解析文档到 SemanticBlock 并返回，**不走 VLM、Embedding、入库**，用于验证 heading_path 等解析结果。

- **Content-Type**: `multipart/form-data`
- **字段**: `file`（`.docx`）

**响应** (`200 OK`):
```json
{
  "total_elements": 420,
  "total_blocks": 85,
  "blocks": [
    {
      "type": "text",
      "heading_path": ["8.0 质量管理体系", "8.5 过程乌龟图", "C6 生产过程"],
      "section_title": "C6 生产过程",
      "is_heading": true,
      "content": "C6 生产过程"
    }
  ]
}
```

---

## 智能体文档配置

为 `quality` / `rd` 智能体配置可检索的文档范围。`general` 智能体始终检索全量知识库，无需配置。

### 获取智能体关联文档

`GET /api/v1/documents/agents/{agent}/documents`

**路径参数:**
| 参数 | 说明 |
|------|------|
| `agent` | 智能体名称：`quality`、`rd`、`general` |

**响应** (`200 OK`):
```json
["FMEA手册-2019年6月5版.docx"]
```

返回该智能体关联的文档 source（文件名）列表。

### 设置智能体关联文档

`PUT /api/v1/documents/agents/{agent}/documents`

全量替换该智能体的文档关联。

**请求体:**
```json
{
  "document_ids": ["FMEA手册-2019年6月5版.docx", "XF模具VDA6.4质量手册.docx"]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `document_ids` | `list[string]` | 文档 source（文件名）列表，传空数组则清除关联 |

**响应** (`200 OK`):
```json
{ "ok": true }
```

---

## 智能问答

`POST /api/v1/chat`

基于 LangGraph ReAct Agent 自动检索知识库并生成回答。支持多轮对话上下文。响应为 **SSE（Server-Sent Events）** 流式输出。

### 请求

```json
{
  "query": "C6生产过程的失效模式有哪些？",
  "conversation_id": null,
  "agent": "quality",
  "rules": null
}
```

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `query` | string | 必填 | 用户问题 |
| `conversation_id` | string \| null | `null` | 已有会话 ID，为空则创建新会话 |
| `agent` | string \| null | `"general"` | 智能体类型：`quality`（质量）、`rd`（研发）、`general`（通用） |
| `rules` | string \| null | `null` | 用户自定义规则，追加到智能体 system prompt 末尾 |

**智能体行为说明：**

| 智能体 | 领域过滤 | 文档范围 | system prompt |
|--------|----------|----------|---------------|
| `quality` | `domains contains "quality"` | 仅前端配置的文档 | 质量管理专家（VDA6.4） |
| `rd` | `domains contains "rd"` | 仅前端配置的文档 | 研发专家（模具设计/工艺开发） |
| `general` | 无 | 全量知识库 | 综合助手 |

- 向量检索和 BM25 检索均会按文档过滤，确保只检索配置范围内的内容
- `rules` 会追加到对应智能体的 system prompt 末尾，用于自定义回答风格或补充约束

### 响应

`200 OK`，`Content-Type: text/event-stream`

SSE 事件格式: `event: <type>\ndata: <json>\n\n`

| 事件类型 | 说明 | data 字段 |
|----------|------|-----------|
| `meta` | 前置元信息，第一条事件 | `conversation_id`, `domain`, `rewritten_query` |
| `thinking` | 思考过程 token（工具调用前的 LLM 输出） | `content` |
| `token` | 回答内容 token（工具调用后） | `content` |
| `done` | 流结束，附带检索记录 | `tool_calls` |
| `error` | 错误信息 | `message` |

**完整 SSE 示例：**
```
event: meta
data: {"conversation_id": "uuid", "domain": "quality", "rewritten_query": null}

event: thinking
data: {"content": "我需要搜索"}

event: thinking
data: {"content": "相关文档"}

event: token
data: {"content": "根据"}

event: token
data: {"content": "FMEA手册"}

event: done
data: {"tool_calls": [{"tool_name": "knowledge_search", "content_preview": "C6 生产过程..."}]}
```

**处理流程：**

1. 加载或创建会话，保存用户消息
2. 加载最近 20 条历史消息作为上下文
3. 判断是否需要 query 改写（基于历史上下文）
4. 非通用智能体查询其关联文档列表
5. 调用 LangGraph ReAct Agent（自动调用 `knowledge_search` 工具检索）
6. 流式输出 thinking → token → done
7. 保存 assistant 消息，新会话自动设置标题

---

## 会话管理

### 会话列表

`GET /api/v1/conversations`

**查询参数:**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `offset` | int | `0` | 偏移量 |
| `limit` | int | `50` | 每页数量 |

**响应** (`200 OK`):
```json
{
  "items": [
    { "id": "uuid", "title": "FMEA相关问题", "created_at": "2026-05-26T12:00:00Z" }
  ],
  "total": 1
}
```

### 会话详情

`GET /api/v1/conversations/{conversation_id}`

返回会话信息及全部消息（含每条 assistant 消息的检索引用）。

**响应** (`200 OK`):
```json
{
  "id": "uuid",
  "title": "FMEA相关问题",
  "messages": [
    {
      "id": "msg-uuid",
      "role": "user",
      "content": "DFMEA七步法是什么？",
      "retrievals": [],
      "created_at": "2026-05-26T12:00:00Z"
    },
    {
      "id": "msg-uuid-2",
      "role": "assistant",
      "content": "DFMEA七步法包括...",
      "retrievals": [
        { "tool_name": "knowledge_search", "content_preview": "七步法概述..." }
      ],
      "created_at": "2026-05-26T12:00:01Z"
    }
  ],
  "created_at": "2026-05-26T12:00:00Z"
}
```

**未找到** (`404`):
```json
{ "detail": "会话不存在" }
```

### 删除会话

`DELETE /api/v1/conversations/{conversation_id}`

级联删除会话及其所有消息。

**响应** (`204 No Content`)

**未找到** (`404`):
```json
{ "detail": "会话不存在" }
```
