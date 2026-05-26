# API Reference

## 基础信息

- 基础路径: `/api/v1`
- 数据格式: JSON
- Swagger 文档: `/docs`

## 接口列表

### 健康检查

`GET /api/v1/health`

**响应:**
```json
{ "status": "ok" }
```

---

### 文档管理

#### 上传文档

`POST /api/v1/documents`

上传 FMEA / VDA6.4 质量手册等文档，后台异步处理（解析 → 语义分块 → VLM 增强 → Embedding → 入库）。

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

**错误响应** (`415 Unsupported Media Type`):
```json
{ "detail": "仅支持 .docx / .pdf 格式" }
```

#### 查询处理进度

`GET /api/v1/documents/{task_id}`

上传接口返回的 `id` 即为 `task_id`，用于轮询处理进度。

**成功响应** (`200 OK`):
```json
{
  "task_id": "uuid",
  "filename": "FMEA手册.docx",
  "stage": "embedding",
  "progress": { "filename": "FMEA手册.docx", "total_chunks": 128 },
  "status": "processing"
}
```

`stage` 可能值: `queued` → `parsing` → `processing` → `enriching` → `chunking` → `embedding` → `completed`

`status` 可能值: `processing` | `completed` | `failed`

**未找到** (`404 Not Found`):
```json
{ "detail": "任务不存在" }
```

#### 分析文档结构

`POST /api/v1/documents/analysis`

仅支持 `.docx`。解析文档到 SemanticBlock 并返回，**不走 VLM、Embedding、入库**，用于验证 heading_path 等解析结果。

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

### 智能问答

`POST /api/v1/chat/completions`

基于 LangGraph ReAct Agent 自动检索知识库并生成回答。支持多轮对话上下文，自动领域路由。

**请求体:**
```json
{
  "query": "C6生产过程的失效模式有哪些？",
  "conversation_id": null
}
```

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `query` | string | 必填 | 用户问题 |
| `conversation_id` | string \| null | `null` | 已有会话 ID，为空则创建新会话 |

**响应** (`200 OK`):
```json
{
  "answer": "根据FMEA手册，C6生产过程的主要失效模式包括...",
  "conversation_id": "uuid",
  "domain": "quality",
  "retrievals": [
    {
      "tool_name": "knowledge_search",
      "content_preview": "C6 生产过程 失效模式..."
    }
  ],
  "context_preview": "片段1内容...\n---\n片段2内容...",
  "context_length": 2340,
  "rewritten_query": null
}
```

---

### 会话管理

#### 会话列表

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

#### 会话详情

`GET /api/v1/conversations/{conversation_id}`

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
        { "tool_name": "knowledge_search", "content_preview": "..." }
      ],
      "created_at": "2026-05-26T12:00:01Z"
    }
  ],
  "created_at": "2026-05-26T12:00:00Z"
}
```

#### 删除会话

`DELETE /api/v1/conversations/{conversation_id}`

**响应** (`204 No Content`)

**未找到** (`404 Not Found`):
```json
{ "detail": "会话不存在" }
```
