<script setup>
const props = defineProps({
  currentUser: Object,
  currentView: String,
  sessions: Array
})

const emit = defineEmits(['switch-view', 'logout', 'select-session', 'delete-session', 'new-chat'])

const menuItems = [
  { id: 'chat', icon: '💬', label: '智能对话' },
  { id: 'documents', icon: '📄', label: '政策文档' },
  { id: 'crawler', icon: '🔍', label: '政策采集' },
  { id: 'analysis', icon: '📊', label: '分析结果' }
]
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <div class="logo">
        <svg viewBox="0 0 32 32" fill="none">
          <circle cx="16" cy="16" r="14" stroke="currentColor" stroke-width="2"/>
          <path d="M16 8 L16 16 L22 22" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          <circle cx="16" cy="16" r="3" fill="currentColor"/>
        </svg>
      </div>
      <span class="logo-text">政策分析助手</span>
    </div>

    <nav class="nav-menu">
      <!-- 新建对话按钮 -->
      <button class="new-chat-btn" @click="emit('new-chat')">
        <span class="plus-icon">+</span>
        <span>新建对话</span>
      </button>

      <!-- 历史记录 -->
      <div class="history-section" v-if="sessions && sessions.length > 0">
        <div class="section-title">历史记录</div>
        <div class="history-list">
          <button
            v-for="session in sessions"
            :key="session.id"
            class="history-item"
            @click="emit('select-session', session.id)"
          >
            <span class="history-icon">💬</span>
            <span class="history-title">{{ session.title || '无标题对话' }}</span>
            <button
              class="delete-btn"
              @click.stop="emit('delete-session', session.id)"
              title="删除对话"
            >
              ×
            </button>
          </button>
        </div>
      </div>

      <!-- 功能菜单 -->
      <div class="nav-section">
        <span class="nav-label">功能菜单</span>
        <button
          v-for="item in menuItems"
          :key="item.id"
          class="nav-item"
          :class="{ active: currentView === item.id }"
          @click="emit('switch-view', item.id)"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </button>
      </div>
    </nav>

    <div class="sidebar-footer">
      <div class="user-info">
        <span class="username">{{ currentUser?.username }}</span>
        <button class="logout-btn" @click="emit('logout')">退出</button>
      </div>
      <div class="copyright">© 2024 华测导航</div>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 260px;
  background: var(--primary);
  color: white;
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.sidebar-header {
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo {
  width: 40px;
  height: 40px;
  color: #38BDF8;
}

.logo-text {
  font-size: 1.125rem;
  font-weight: 600;
}

.nav-menu {
  flex: 1;
  padding: 20px 16px;
  overflow-y: auto;
}

.new-chat-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  background: var(--accent);
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 0.9375rem;
  cursor: pointer;
  transition: background 0.2s;
  margin-bottom: 20px;
}

.new-chat-btn:hover {
  background: #025a8b;
}

.plus-icon {
  font-size: 1.25rem;
  font-weight: 600;
}

.history-section {
  margin-bottom: 20px;
}

.section-title {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: rgba(255, 255, 255, 0.5);
  padding-left: 12px;
  margin-bottom: 8px;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.history-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.05);
  border: none;
  border-radius: 6px;
  color: rgba(255, 255, 255, 0.8);
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
}

.history-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.history-icon {
  font-size: 0.875rem;
}

.history-title {
  flex: 1;
  font-size: 0.875rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.delete-btn {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.4);
  font-size: 1.125rem;
  cursor: pointer;
  opacity: 0;
  transition: all 0.2s;
}

.history-item:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  color: var(--error);
}

.nav-section {
  margin-top: auto;
}

.nav-label {
  display: block;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: rgba(255, 255, 255, 0.5);
  padding-left: 12px;
  margin-bottom: 12px;
}

.nav-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.7);
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9375rem;
  transition: all 0.2s;
  text-align: left;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.nav-item.active {
  background: var(--accent);
  color: white;
}

.nav-icon {
  font-size: 1.125rem;
}

.sidebar-footer {
  padding: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.user-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.username {
  font-size: 0.8125rem;
  color: rgba(255, 255, 255, 0.7);
}

.logout-btn {
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 4px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
}

.logout-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.copyright {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.4);
  text-align: center;
}
</style>
