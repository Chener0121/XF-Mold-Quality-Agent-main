<template>
  <header class="chat-headbar">
    <div class="headbar-agent-selector" @click.stop="toggleMenu">
      <component :is="currentIcon" :size="16" />
      <span>{{ currentLabel }}</span>
      <ChevronDown :size="14" class="headbar-arrow" :class="{ 'headbar-arrow--open': showMenu }" />
    </div>
    <ul v-if="showMenu" class="headbar-dropdown">
      <li
        v-for="opt in options"
        :key="opt.value"
        :class="{ active: modelValue === opt.value }"
        @click.stop="select(opt.value)"
      >
        <component :is="opt.icon" :size="14" class="headbar-dropdown__icon" />
        <span>{{ opt.label }}</span>
        <Check v-if="modelValue === opt.value" :size="14" class="headbar-dropdown__check" />
      </li>
    </ul>
  </header>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { ChevronDown, Bot, ShieldCheck, Wrench, Check } from 'lucide-vue-next'

const options = [
  { value: 'general', label: '模具通用智能体', icon: Bot },
  { value: 'quality', label: '模具质量智能体', icon: ShieldCheck },
  { value: 'rd', label: '模具研发智能体', icon: Wrench },
]

const props = defineProps<{ modelValue: string }>()
const emit = defineEmits<{ 'update:modelValue': [value: string] }>()

const showMenu = ref(false)

const currentLabel = computed(
  () => options.find(o => o.value === props.modelValue)?.label ?? options[0].label,
)

const currentIcon = computed(
  () => options.find(o => o.value === props.modelValue)?.icon ?? Bot,
)

function toggleMenu() {
  showMenu.value = !showMenu.value
}

function select(value: string) {
  emit('update:modelValue', value)
  showMenu.value = false
}

function closeMenu() {
  showMenu.value = false
}

onMounted(() => document.addEventListener('click', closeMenu))
onBeforeUnmount(() => document.removeEventListener('click', closeMenu))
</script>

<style scoped lang="less">
.chat-headbar {
  height: 52px;
  display: flex;
  align-items: center;
  padding: 0 24px;
  border-bottom: 1px solid var(--gray-200);
  position: relative;
  background: var(--main-0);
  flex-shrink: 0;
}

.headbar-agent-selector {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: var(--main-800);
  transition: background 0.15s;

  &:hover {
    background: var(--gray-50);
  }
}

.headbar-arrow {
  transition: transform 0.2s;
}

.headbar-arrow--open {
  transform: rotate(180deg);
}

.headbar-dropdown {
  position: absolute;
  top: 46px;
  left: 16px;
  background: var(--main-0);
  border: 1px solid var(--gray-200);
  border-radius: 10px;
  box-shadow: 0 4px 16px var(--shadow-3);
  list-style: none;
  padding: 4px;
  margin: 0;
  z-index: 100;
  min-width: 200px;

  li {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 14px;
    color: var(--main-800);
    cursor: pointer;
    transition: background 0.15s;

    &:hover {
      background: var(--gray-50);
    }

    &.active {
      background: var(--main-50);
      color: var(--main-700);
      font-weight: 500;
    }
  }
}

.headbar-dropdown__icon {
  flex-shrink: 0;
}

.headbar-dropdown__check {
  margin-left: auto;
  color: var(--color-primary-500);
}
</style>
