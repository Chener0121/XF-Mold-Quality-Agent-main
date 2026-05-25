# API Reference

## 基础信息

- 基础路径: `/api/v1`
- 数据格式: JSON

## 接口列表

### 健康检查

`GET /api/v1/health`

**响应:**
```json
{ "status": "ok" }
```

### 认证

`POST /api/v1/auth/login`

单用户模式，直接返回 JWT 令牌。

**响应:**
```json
{ "access_token": "xxx", "token_type": "bearer" }
```

### 文档管理

`POST /api/v1/documents/upload`

上传文档（FMEA/VDA6.4 质量手册等）。支持 `.pdf`、`.docx` 格式。

**请求:** `multipart/form-data`，字段名 `file`

**响应:**
```json
{ "id": "uuid", "filename": "xxx.pdf", "status": "uploaded" }
```

`GET /api/v1/documents`

获取文档列表。

**响应:**
```json
{ "items": [...], "total": 10 }
```

`GET /api/v1/documents/{document_id}`

获取文档详情。

`DELETE /api/v1/documents/{document_id}`

删除文档。

### 智能问答

`POST /api/v1/chat`

**请求体:**
```json
{ "question": "FMEA中如何定义严重度？", "conversation_id": "可选" }
```

**响应:**
```json
{
  "answer": "...",
  "sources": [
    { "document_id": "xxx", "chunk_id": "xxx", "content": "...", "score": 0.95 }
  ]
}
```
