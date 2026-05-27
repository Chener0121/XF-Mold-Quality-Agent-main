<template>
  <aside class="config-panel" :class="{ 'config-panel--open': open }">
    <div class="config-panel__inner">
      <div class="config-panel__header">
        <span class="config-panel__title">配置</span>
        <button class="config-panel__close" @click="$emit('close')">
          <X :size="16" />
        </button>
      </div>

      <div class="config-panel__body">
        <section class="config-section">
          <h4 class="config-section__title">规则配置</h4>
          <textarea
            v-model="ruleText"
            class="config-textarea"
            placeholder="输入自定义规则..."
            rows="6"
          ></textarea>
        </section>

        <section class="config-section">
          <h4 class="config-section__title">知识库</h4>
          <p v-if="agent === 'general'" class="config-section__hint">
            通用智能体默认包含所有文档
          </p>

          <div v-if="loading" class="config-section__loading">加载中...</div>
          <div v-else-if="docs.length === 0" class="config-section__empty">暂无已完成的文档</div>
          <div v-else class="config-doc-list">
            <label
              v-for="doc in docs"
              :key="doc.id"
              class="config-doc-item"
              :class="{ 'config-doc-item--disabled': agent === 'general' }"
            >
              <input
                type="checkbox"
                :checked="agent === 'general' || selectedIds.includes(doc.id)"
                :disabled="agent === 'general'"
                @change="toggleDoc(doc.id)"
              />
              <FileText :size="14" class="config-doc-item__icon" />
              <span class="config-doc-item__name">{{ doc.filename }}</span>
            </label>
          </div>

          <button
            v-if="agent !== 'general' && docs.length > 0"
            class="config-save-btn"
            :disabled="saving"
            @click="saveSelection"
          >
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </section>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { X, FileText } from 'lucide-vue-next'
import { listDocuments, getAgentDocuments, setAgentDocuments } from '@/apis/document'

const props = defineProps<{
  open: boolean
  agent: string
}>()

const emit = defineEmits<{ close: [] }>()

const ruleText = ref('')
const docs = ref<{ id: string; filename: string }[]>([])
const selectedIds = ref<string[]>([])
const loading = ref(false)
const saving = ref(false)

const RULES_KEY = 'agent_rules'

function loadRules() {
  try {
    const all = JSON.parse(localStorage.getItem(RULES_KEY) || '{}')
    ruleText.value = all[props.agent] || ''
  } catch {
    ruleText.value = ''
  }
}

function saveRules() {
  try {
    const all = JSON.parse(localStorage.getItem(RULES_KEY) || '{}')
    all[props.agent] = ruleText.value
    localStorage.setItem(RULES_KEY, JSON.stringify(all))
  } catch { /* ignore */ }
}

watch(ruleText, saveRules)

async function loadDocs() {
  loading.value = true
  try {
    const [docList, agentDocIds] = await Promise.all([
      listDocuments(),
      props.agent !== 'general' ? getAgentDocuments(props.agent) : Promise.resolve([]),
    ])
    docs.value = docList
    selectedIds.value = agentDocIds
  } catch {
    docs.value = []
    selectedIds.value = []
  } finally {
    loading.value = false
  }
}

function toggleDoc(id: string) {
  const idx = selectedIds.value.indexOf(id)
  if (idx >= 0) {
    selectedIds.value.splice(idx, 1)
  } else {
    selectedIds.value.push(id)
  }
}

async function saveSelection() {
  saving.value = true
  try {
    await setAgentDocuments(props.agent, selectedIds.value)
  } finally {
    saving.value = false
  }
}

// 面板打开时加载数据
watch(() => props.open, (val) => {
  if (val) {
    loadDocs()
    loadRules()
  }
})

// 切换智能体时重新加载
watch(() => props.agent, () => {
  if (props.open) loadDocs()
  loadRules()
})
</script>

<style scoped lang="less">
.config-panel {
  width: 0;
  flex-shrink: 0;
  background: var(--main-0);
  overflow: hidden;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.config-panel--open {
  width: 340px;
  border-left: 1px solid var(--gray-200);
}

.config-panel__inner {
  width: 340px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.config-panel__header {
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  border-bottom: 1px solid var(--gray-200);
  flex-shrink: 0;
}

.config-panel__title {
  font-size: 14px;
  font-weight: 600;
  color: var(--main-900);
}

.config-panel__close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--gray-500);
  cursor: pointer;
  transition: background 0.15s;

  &:hover {
    background: var(--gray-50);
  }
}

.config-panel__body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.config-section {
  margin-bottom: 24px;

  &:last-child {
    margin-bottom: 0;
  }
}

.config-section__title {
  font-size: 13px;
  font-weight: 600;
  color: var(--main-800);
  margin: 0 0 8px;
}

.config-section__hint {
  font-size: 12px;
  color: var(--color-primary-500);
  margin: 0 0 10px;
}

.config-section__loading,
.config-section__empty {
  font-size: 13px;
  color: var(--gray-400);
  padding: 8px 0;
}

.config-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--gray-200);
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.6;
  color: var(--main-900);
  background: var(--main-0);
  resize: vertical;
  font-family: inherit;
  outline: none;
  box-sizing: border-box;
  transition: border-color 0.2s;

  &:focus {
    border-color: var(--color-primary-500);
  }

  &::placeholder {
    color: var(--gray-400);
  }
}

.config-doc-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.config-doc-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  color: var(--main-800);
  transition: background 0.15s;

  &:hover {
    background: var(--gray-50);
  }

  &--disabled {
    opacity: 0.7;
    cursor: default;

    &:hover {
      background: transparent;
    }
  }

  input[type="checkbox"] {
    accent-color: var(--color-primary-500);
  }
}

.config-doc-item__icon {
  flex-shrink: 0;
  color: var(--gray-400);
}

.config-doc-item__name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.config-save-btn {
  margin-top: 12px;
  width: 100%;
  padding: 8px;
  border: 1px solid var(--gray-200);
  border-radius: 8px;
  background: var(--main-0);
  font-size: 13px;
  color: var(--main-800);
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;

  &:hover:not(:disabled) {
    background: var(--gray-50);
    border-color: var(--gray-300);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}
</style>
