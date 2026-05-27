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
          <p class="config-section__desc">上传的文档将自动加入当前智能体的知识库</p>
        </section>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { X } from 'lucide-vue-next'

defineProps<{ open: boolean }>()
defineEmits<{ close: [] }>()

const ruleText = ref('')
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

.config-section__desc {
  font-size: 13px;
  color: var(--gray-500);
  margin: 0;
  line-height: 1.5;
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
</style>
