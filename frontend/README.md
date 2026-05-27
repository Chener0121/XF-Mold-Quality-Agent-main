# Frontend — XF Mold Quality Agent

Vue 3 前端，提供智能体切换、知识库配置、流式聊天问答界面。

## 目录结构

```
frontend/src/
├── apis/                            # API 接口封装
│   ├── rag.ts                       #   SSE 流式问答（fetch + ReadableStream）
│   ├── document.ts                  #   文档管理 + 智能体文档配置
│   ├── conversation.ts              #   会话 CRUD
│   └── index.ts                     #   统一导出
│
├── components/layout/               # 布局组件
│   ├── Layout.vue                   #   整体布局容器
│   ├── Headbar.vue                  #   顶部栏（智能体下拉切换、配置按钮）
│   ├── Sidebar.vue                  #   左侧会话列表
│   └── ConfigPanel.vue              #   右侧配置面板（规则 + 知识库勾选）
│
├── views/
│   └── ChatPage.vue                 #   聊天主页面（输入框、消息列表、流式渲染）
│
├── stores/
│   └── chat.ts                      #   Pinia 聊天状态（会话管理、流式 token）
│
├── router/
│   └── index.ts                     #   Vue Router 配置
│
├── assets/css/
│   └── base.css                     #   全局 CSS 变量（颜色、间距、圆角）
│
├── App.vue                          #   根组件
└── main.ts                          #   入口
```

## 功能模块

### 智能体切换

顶部下拉菜单切换三个智能体（通用/质量/研发），切换时：
- 重置输入框状态
- 检查新智能体是否有配置文档
- 右侧配置面板联动刷新

### 配置面板

右侧滑出面板，包含两个配置区域：

- **规则配置**：自定义规则文本，按智能体独立存储在 localStorage，发送消息时追加到 system prompt
- **知识库**：勾选该智能体可检索的文档（通用智能体默认包含全部，不可编辑）

### 聊天页面

- 欢迎模式：输入框居中，标题渐入动画
- 聊天模式：消息列表 + 底部固定输入框
- 流式渲染：token 通过 requestAnimationFrame 批量合并，减少 DOM 更新
- 思考过程：工具调用前的 LLM 输出可展开/收起
- 引用来源：检索结果可展开查看
- Markdown 渲染 + KaTeX 数学公式
- ResizeObserver 驱动的自动滚动

## 技术栈

| 类别 | 技术 |
|------|------|
| 框架 | Vue 3 (Composition API + `<script setup>`) |
| 语言 | TypeScript |
| 状态管理 | Pinia |
| 路由 | Vue Router 4 |
| 构建 | Vite 6 |
| 样式 | Less + CSS 变量 |
| 图标 | lucide-vue-next |
| Markdown | marked |
| 数学公式 | KaTeX |

## 开发规范

- API 接口统一定义在 `src/apis/` 目录
- 图标使用 `lucide-vue-next`（注意尺寸）
- 样式使用 Less，颜色必须使用 `base.css` 中的 CSS 变量
- UI 风格简洁一致，避免悬停位移、过度阴影和渐变
- 后端接口文档参考 `backend/docs/api-reference.md`
- **禁止直接运行 npm/pnpm**，统一通过 Docker 容器开发

## 开发

前端通过 Docker 开发容器运行，源码挂载实现热重载：

```bash
# 启动开发环境
docker compose up -d

# 查看日志
docker compose logs -f web-dev

# 重建（修改依赖后）
docker compose up -d --build web-dev
```

Vite 开发服务器运行在 `0.0.0.0:5173`，API 请求通过 Vite proxy 转发至后端容器：
- `/api/v1/chat` → SSE 流式接口（禁用缓冲）
- `/api` → 其余 API 接口

## 生产构建

```bash
# 通过 Docker 构建生产镜像
docker compose -f docker-compose.prod.yml build web
```

构建产物为 Nginx 静态资源，通过 Nginx 反向代理 API 请求。
