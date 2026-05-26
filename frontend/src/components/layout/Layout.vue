<template>
  <div class="layout">
    <Sidebar />
    <div class="layout__main">
      <Header />
      <div class="layout__content">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'
</script>

<style scoped lang="less">
.layout {
  display: flex;
  height: 100vh;
  min-width: var(--min-width);
}

.layout__main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.layout__content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: var(--gray-25);
  scrollbar-width: none;

  &::-webkit-scrollbar {
    display: none;
  }
}
</style>
