<template>
  <div class="dashboard">
    <!-- 文档上传 -->
    <div class="card">
      <div class="card__header">
        <UploadCloud :size="18" />
        <span>文档上传</span>
        <span class="card__hint">支持 .docx / .pdf 格式的 FMEA、VDA6.4 质量手册</span>
      </div>
      <el-upload
        drag
        :auto-upload="true"
        :show-file-list="false"
        accept=".pdf,.docx"
        :before-upload="beforeUpload"
        :http-request="handleUpload"
      >
        <div class="upload-area">
          <UploadCloud :size="28" />
          <p>拖拽或 <em>点击上传</em></p>
          <span class="upload-area__tip">PDF / DOCX</span>
        </div>
      </el-upload>
    </div>

    <!-- 任务列表 -->
    <div class="card">
      <div class="card__header">
        <FolderOpen :size="18" />
        <span>处理任务</span>
      </div>
      <div v-if="tasks.length === 0" class="empty">暂无文档处理任务，请先上传文档</div>
      <div v-else class="task-list">
        <div v-for="task in tasks" :key="task.task_id" class="task-item">
          <div class="task-item__info">
            <FileText :size="16" />
            <span class="task-item__name">{{ task.filename }}</span>
          </div>
          <div class="task-item__right">
            <span class="task-item__stage">{{ stageLabel(task.stage) }}</span>
            <el-tag size="small" :type="statusTagType(task.status)">{{ statusLabel(task.status) }}</el-tag>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { FileText, FolderOpen, UploadCloud } from 'lucide-vue-next'
import { uploadDocument, getTaskStatus } from '@/apis/document'

interface TaskInfo {
  task_id: string
  filename: string
  stage: string
  progress: Record<string, any>
  status: string
}

const tasks = ref<TaskInfo[]>([])
const timers = new Map<string, number>()

function stageLabel(stage: string): string {
  const map: Record<string, string> = {
    queued: '排队中',
    parsing: '解析文档',
    processing: '语义处理',
    enriching: 'VLM 增强',
    chunking: '分块',
    embedding: '向量化',
    completed: '完成',
    failed: '失败',
  }
  return map[stage] || stage
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    processing: '处理中',
    completed: '已完成',
    failed: '失败',
  }
  return map[status] || status
}

function statusTagType(status: string): string {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'danger'
  return 'warning'
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
        task.progress = result.progress
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
  if (!file.name.endsWith('.pdf') && !file.name.endsWith('.docx')) {
    ElMessage.error('仅支持 PDF、DOCX 格式')
    return false
  }
  if (file.size === 0) {
    ElMessage.error('文件为空，请选择有效文件')
    return false
  }
  return true
}

async function handleUpload(options: any) {
  try {
    const result = await uploadDocument(options.file)
    const task: TaskInfo = {
      task_id: result.id,
      filename: options.file.name,
      stage: 'queued',
      progress: {},
      status: 'processing',
    }
    tasks.value.unshift(task)
    ElMessage.success('文件上传成功，正在处理...')
    startPolling(result.id)
  } catch (e: any) {
    ElMessage.error(e.message || '上传失败')
  }
}
</script>

<style scoped lang="less">
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 800px;
}

.card {
  background: var(--main-0);
  border-radius: 12px;
  padding: 20px;
  border: 0.8px solid var(--gray-200);
  box-shadow: 0 1px 3px var(--shadow-1);
}

.card__header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: var(--main-800);
  margin-bottom: 16px;
}

.card__hint {
  font-size: 12px;
  font-weight: 400;
  color: var(--gray-500);
  margin-left: auto;
}

.upload-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px 0;
  color: var(--gray-500);

  em {
    color: var(--color-primary-500);
    font-style: normal;
  }

  p {
    margin: 4px 0 2px;
    font-size: 13px;
  }
}

.upload-area__tip {
  font-size: 11px;
  color: var(--gray-400);
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border-radius: 8px;
  background: var(--gray-50);
}

.task-item__info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--gray-600);
}

.task-item__name {
  font-size: 14px;
  color: var(--main-800);
}

.task-item__right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.task-item__stage {
  font-size: 12px;
  color: var(--gray-500);
}

.empty {
  text-align: center;
  padding: 24px 0;
  color: var(--gray-400);
  font-size: 13px;
}
</style>
