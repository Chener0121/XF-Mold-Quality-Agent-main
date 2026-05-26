<template>
  <div class="sidebar" :class="{ 'sidebar--collapsed': !open }">
    <!-- 头部：logo + toggle -->
    <div class="sidebar__header">
      <button class="sidebar__toggle sidebar__toggle--logo" @click="!open && $emit('toggle')" :title="open ? '' : '展开侧边栏'">
        <span class="sidebar__toggle-xf">XF</span>
        <PanelLeftOpen v-if="!open" class="sidebar__toggle-hover-icon" :size="20" />
      </button>
      <button class="sidebar__toggle" @click="$emit('toggle')" title="收起侧边栏">
        <PanelLeftClose :size="18" />
      </button>
    </div>

    <!-- 功能按钮 -->
    <div class="sidebar__actions">
      <button class="sidebar__action" :class="{ active: !chatStore.activeId }" @click="chatStore.goHome()" :title="open ? '' : '新建对话'">
        <span class="sidebar__action-icon"><Plus :size="18" /></span>
        <span class="sidebar__action-label">New Chat</span>
      </button>
      <button class="sidebar__action" :class="{ 'sidebar__action--active': searchOpen }" @click="toggleSearch" :title="open ? '' : '搜索对话'">
        <span class="sidebar__action-icon"><Search :size="18" /></span>
        <span class="sidebar__action-label">Search Chats</span>
      </button>
    </div>

    <!-- 搜索框（展开态下） -->
    <div v-if="open && searchOpen" class="sidebar__search">
      <input
        ref="searchRef"
        v-model="searchQuery"
        class="sidebar__search-input"
        placeholder="搜索对话..."
      />
    </div>

    <!-- 会话列表 -->
    <div v-if="open" class="sidebar__list">
      <div class="sidebar__list-label">Recent</div>
      <div
        v-for="conv in filteredConversations"
        :key="conv.id"
        class="sidebar__item"
        :class="{ active: conv.id === chatStore.activeId }"
        @click="chatStore.switchConversation(conv.id)"
      >
        <MessageSquare :size="14" />
        <span class="sidebar__title">{{ conv.title }}</span>
        <Trash2 :size="12" class="sidebar__delete" @click.stop="chatStore.deleteConversation(conv.id)" />
      </div>
      <div v-if="filteredConversations.length === 0" class="sidebar__empty">
        {{ searchQuery ? '未找到对话' : '暂无对话' }}
      </div>
    </div>

    <!-- 底部：文档上传 -->
    <div class="sidebar__footer">
      <el-upload
        :auto-upload="true"
        :show-file-list="false"
        accept=".docx"
        :before-upload="beforeUpload"
        :http-request="handleUpload"
      >
        <button class="sidebar__action sidebar__upload-trigger" :title="open ? '' : '上传文档'">
          <span class="sidebar__action-icon"><UploadCloud :size="18" /></span>
          <span class="sidebar__action-label">上传文档</span>
        </button>
      </el-upload>
      <!-- 任务列表 -->
      <div v-if="open && tasks.length > 0" class="sidebar__tasks">
        <div v-for="task in tasks" :key="task.task_id" class="task-item">
          <FileText :size="12" />
          <span class="task-item__name">{{ task.filename }}</span>
          <span class="task-item__status" :class="'task-item__status--' + task.status">{{ statusLabel(task.status) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Search, MessageSquare, Trash2, UploadCloud, FileText, PanelLeftClose, PanelLeftOpen } from 'lucide-vue-next'
import { useChatStore } from '@/stores/chat'
import { uploadDocument, getTaskStatus } from '@/apis/document'

defineProps<{ open: boolean }>()
defineEmits<{ toggle: [] }>()

const chatStore = useChatStore()

const searchOpen = ref(false)
const searchQuery = ref('')
const searchRef = ref<HTMLInputElement>()

const filteredConversations = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  let list = chatStore.conversations
  if (q) {
    list = list.filter(c =>
      c.title.toLowerCase().includes(q) ||
      c.messages.some(m => m.content.toLowerCase().includes(q)),
    )
  }
  return [...list].sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
})

function toggleSearch() {
  searchOpen.value = !searchOpen.value
  if (searchOpen.value) {
    nextTick(() => searchRef.value?.focus())
  } else {
    searchQuery.value = ''
  }
}

interface TaskInfo {
  task_id: string
  filename: string
  stage: string
  status: string
}

const tasks = ref<TaskInfo[]>([])
const timers = new Map<string, number>()

function statusLabel(status: string): string {
  return { processing: '处理中', completed: '完成', failed: '失败' }[status] || status
}

function startPolling(taskId: string) {
  if (timers.has(taskId)) return
  const timer = window.setInterval(async () => {
    try {
      const result = await getTaskStatus(taskId)
      const task = tasks.value.find(t => t.task_id === taskId)
      if (task) {
        task.stage = result.stage
        task.status = result.status
      }
      if (result.status === 'completed' || result.status === 'failed') {
        clearInterval(timer)
        timers.delete(taskId)
      }
    } catch {
      clearInterval(timer)
      timers.delete(taskId)
    }
  }, 2000)
  timers.set(taskId, timer)
}

function beforeUpload(file: File) {
  if (!file.name.endsWith('.docx')) {
    ElMessage.error('仅支持 DOCX 格式')
    return false
  }
  return true
}

async function handleUpload(options: any) {
  try {
    const result = await uploadDocument(options.file)
    tasks.value.unshift({
      task_id: result.id,
      filename: options.file.name,
      stage: 'queued',
      status: 'processing',
    })
    ElMessage.success('上传成功，正在处理...')
    startPolling(result.id)
  } catch (e: any) {
    ElMessage.error(e.message || '上传失败')
  }
}
</script>

<style scoped lang="less">
.sidebar {
  width: 260px;
  height: 100vh;
  background: var(--gray-25);
  border-right: 1px solid var(--gray-200);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: width 0.2s ease;
  overflow: hidden;
}

.sidebar--collapsed {
  width: 56px;
  border-right: none;
}

/* 头部 */
.sidebar__header {
  height: 52px;
  padding: 0 8px;
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.sidebar__toggle {
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: var(--gray-600);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.15s;
  padding: 0;

  &:hover {
    background: var(--gray-100);
  }
}

/* XF logo 按钮 */
.sidebar__toggle--logo {
  position: relative;
}

.sidebar__toggle-xf {
  font-size: 16px;
  font-weight: 700;
  color: var(--color-primary-500);
  transition: opacity 0.15s;
}

/* 收起态：hover 图标定位 */
.sidebar__toggle-hover-icon {
  position: absolute;
  opacity: 0;
  transition: opacity 0.15s;
}

.sidebar--collapsed .sidebar__toggle--logo:hover .sidebar__toggle-xf {
  opacity: 0;
}

.sidebar--collapsed .sidebar__toggle--logo:hover .sidebar__toggle-hover-icon {
  opacity: 1;
}

/* 关闭按钮：展开时靠右，收起时被 overflow 裁掉 */
.sidebar__header > .sidebar__toggle:last-child {
  margin-left: auto;
}

/* 功能按钮 */
.sidebar__actions {
  padding: 4px 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  align-items: stretch;
}

.sidebar__action {
  display: flex;
  align-items: center;
  width: 100%;
  height: 40px;
  padding: 0;
  border: none;
  border-radius: 20px;
  background: transparent;
  color: var(--gray-700);
  font-size: 13px;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.15s;

  &:hover {
    background: var(--gray-100);
  }

  &--active {
    background: var(--gray-100);
  }

  &.active {
    background: var(--color-primary-50);
    color: var(--color-primary-500);
  }
}

.sidebar__action-icon {
  width: 40px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sidebar__action-label {
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 搜索框 */
.sidebar__search {
  padding: 8px 16px;
}

.sidebar__search-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--gray-200);
  border-radius: 12px;
  font-size: 13px;
  outline: none;
  background: var(--main-0);
  color: var(--gray-800);
  box-sizing: border-box;
  transition: border-color 0.15s;

  &:focus {
    border-color: var(--color-primary-500);
  }

  &::placeholder {
    color: var(--gray-400);
  }
}

/* 会话列表 */
.sidebar__list {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px;
  scrollbar-width: none;
  &::-webkit-scrollbar { display: none; }
}

.sidebar__list-label {
  padding: 12px 12px 6px;
  font-size: 11px;
  font-weight: 600;
  color: var(--gray-400);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.sidebar__item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 12px;
  cursor: pointer;
  color: var(--gray-600);
  transition: background 0.15s;

  &:hover {
    background: var(--gray-100);

    .sidebar__delete { opacity: 1; }
  }

  &.active {
    background: var(--color-primary-50);
    color: var(--color-primary-500);
  }
}

.sidebar__title {
  flex: 1;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar__delete {
  opacity: 0;
  color: var(--gray-400);
  flex-shrink: 0;
  transition: opacity 0.15s;

  &:hover { color: var(--color-error-500); }
}

.sidebar__empty {
  text-align: center;
  padding: 24px 0;
  color: var(--gray-400);
  font-size: 13px;
}

/* 底部 */
.sidebar__footer {
  padding: 8px;
  margin-top: auto;

  :deep(.el-upload) {
    width: 100%;
  }
}

.sidebar__upload-trigger {
  width: 100%;
}

/* 任务列表 */
.sidebar__tasks {
  max-height: 120px;
  overflow-y: auto;
  padding: 4px 8px 0;
  scrollbar-width: none;
  &::-webkit-scrollbar { display: none; }
}

.task-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 0;
  font-size: 11px;
  color: var(--gray-500);
}

.task-item__name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-item__status {
  font-weight: 500;
  &--processing { color: var(--color-warning-700); }
  &--completed { color: var(--color-success-500); }
  &--failed { color: var(--color-error-500); }
}
</style>
