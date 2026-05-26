# Frontend

Chen-Assistant 前端，基于 Vue 3 + Vite + TypeScript。

## 启动

```bash
npm install
npm run dev
```

开发地址：http://localhost:5173
API 请求自动代理到后端 http://127.0.0.1:8000

## 项目结构

```
src/
├── main.ts                    # 应用入口（Element Plus + Pinia + Router）
├── App.vue                    # 根组件
├── router/index.ts            # 路由（/dashboard /chat /graph）
├── apis/                      # API 接口层
│   ├── index.ts               # axios 封装（统一拦截、204 处理）
│   ├── document.ts            # 文档 CRUD
│   ├── analytics.ts           # 学习分析（薄弱知识点、每日统计）
│   ├── graph.ts               # 知识图谱
│   └── qa.ts                  # 智能问答 + 对话摘要压缩
├── stores/
│   └── chat.ts                # 会话状态管理（Pinia + localStorage + 摘要压缩）
├── views/
│   ├── Dashboard.vue          # 数据面板（统计卡片 + 柱状图 + 文档管理 + 薄弱知识点）
│   ├── ChatPage.vue           # 智能问答（会话列表 + 多轮记忆 + LaTeX/Markdown）
│   └── GraphPage.vue          # 知识图谱（ECharts 力导向/环形布局 + 学科配色 + 关联高亮）
├── components/
│   └── layout/                # 布局组件
│       ├── Layout.vue         # 整体骨架（Sidebar + Header + Content）
│       ├── Sidebar.vue        # 左侧导航（Logo + 路由菜单）
│       └── Header.vue         # 顶部栏（项目名 + 实时时钟）
└── assets/css/
    └── base.css               # 全局样式 + CSS 变量（色板、阴影、滚动条）
```

## 技术栈

| 技术 | 用途 |
|------|------|
| Vue 3 | 前端框架（script setup） |
| TypeScript | 类型安全 |
| Vite | 构建工具 |
| Vue Router | 路由管理 |
| Pinia | 状态管理（会话列表、localStorage 持久化） |
| Element Plus | UI 组件库（上传、标签、按钮） |
| Less | CSS 预处理器 |
| Axios | HTTP 请求 |
| ECharts | 图表（柱状图、知识图谱可视化） |
| KaTeX | LaTeX 公式渲染 |
| Marked | Markdown 渲染 |
| Lucide Vue Next | 图标库 |
