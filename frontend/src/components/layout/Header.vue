<template>
  <div class="header">
    <div class="header__left">
      <span class="header__title">XF 模具质量管理助手</span>
      <span class="header__subtitle">基于 FMEA/VDA6.4 的智能质量管理平台</span>
    </div>
    <span class="header__time"><Clock :size="15" /> {{ currentTime }}</span>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { Clock } from 'lucide-vue-next'

const currentTime = ref('')
let timer: number

function updateTime() {
  const now = new Date()
  const y = now.getFullYear()
  const m = now.getMonth() + 1
  const d = now.getDate()
  const hh = String(now.getHours()).padStart(2, '0')
  const mm = String(now.getMinutes()).padStart(2, '0')
  const ss = String(now.getSeconds()).padStart(2, '0')
  currentTime.value = `${y}年${m}月${d}日 ${hh}:${mm}:${ss}`
}

onMounted(() => {
  updateTime()
  timer = window.setInterval(updateTime, 1000)
})

onUnmounted(() => {
  clearInterval(timer)
})
</script>

<style scoped lang="less">
.header {
  height: 64px;
  padding: 0 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--gray-25);
  // background: var(--main-0);
  // border-bottom: 1px solid var(--gray-200);
  flex-shrink: 0;
}

.header__left {
  display: flex;
  flex-direction: column;
}

.header__title {
  font-size: 16px;
  font-weight: 600;
  color: var(--main-800);
  line-height: 1.3;
}

.header__subtitle {
  font-size: 12px;
  color: var(--gray-500);
}

.header__time {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--gray-1000);
  font-variant-numeric: tabular-nums;
}
</style>
