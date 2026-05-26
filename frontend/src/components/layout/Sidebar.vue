<template>
  <div class="sidebar">
    <!-- 顶部 Logo -->
    <div class="sidebar__logo">
      <span class="sidebar__logo-text">XF</span>
    </div>

    <!-- 导航菜单 -->
    <nav class="sidebar__nav">
      <router-link
        v-for="item in menuItems"
        :key="item.path"
        :to="item.path"
        class="sidebar__item"
        :class="{ 'is-active': route.path === item.path }"
      >
        <span class="sidebar__icon">
          <component :is="item.icon" :size="18" />
        </span>
      </router-link>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import { BarChart3, MessageCircle } from 'lucide-vue-next'

const route = useRoute()

const menuItems = [
  { path: '/dashboard', icon: BarChart3 },
  { path: '/chat', icon: MessageCircle },
]
</script>

<style scoped lang="less">
.sidebar {
  width: 64px;
  height: 100vh;
  overflow: hidden;
  background: var(--bg-sider);
  border-right: 1px solid var(--gray-200);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar__logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid var(--gray-200);
  flex-shrink: 0;
}

.sidebar__logo-text {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-primary-500);
}

.sidebar__nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 12px;
  gap: 4px;
}

.sidebar__item {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  text-decoration: none;
  cursor: pointer;

  .sidebar__icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 34px;
    height: 34px;
    border-radius: 8px;
    background: var(--gray-100);
    color: var(--gray-600);
    transition: all 0.2s;
  }

  &:hover .sidebar__icon {
    background: var(--main-50);
    color: var(--color-primary-500);
  }

  &.is-active .sidebar__icon {
    color: var(--main-0);
    background: var(--color-primary-500);
  }
}
</style>
