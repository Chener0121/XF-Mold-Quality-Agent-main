<template>
  <div class="layout">
    <Sidebar :open="sidebarOpen" @toggle="sidebarOpen = !sidebarOpen" />
    <div class="layout__main">
      <router-view />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import Sidebar from './Sidebar.vue'

const sidebarOpen = ref(true)
</script>

<style scoped lang="less">
.layout {
  display: flex;
  height: 100vh;
  min-width: var(--min-width);
}

.layout__main {
  flex: 1;
  overflow: hidden;
  background: var(--main-0);
  position: relative;
}
</style>
