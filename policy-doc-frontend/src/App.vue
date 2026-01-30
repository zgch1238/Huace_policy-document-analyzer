<script setup>
import { ref, onMounted, provide, nextTick } from 'vue'
import Sidebar from './components/Sidebar.vue'
import ChatView from './views/ChatView.vue'
import DocumentsView from './views/DocumentsView.vue'
import AnalysisView from './views/AnalysisView.vue'
import Login from './components/Login.vue'
import Register from './components/Register.vue'
import { api } from './utils/api'

// 用户状态
const currentUser = ref(null)
const authPage = ref('login')

// 当前视图
const currentView = ref('chat')

// 会话列表
const sessions = ref([])
const chatViewRef = ref(null)

// 视图映射
const viewComponents = {
  chat: ChatView,
  documents: DocumentsView,
  analysis: AnalysisView
}

// 提供用户状态给子组件
provide('currentUser', currentUser)

// 登录成功处理
const handleLoginSuccess = async (user) => {
  currentUser.value = user
  await loadSessions()
}

// 登出处理
const handleLogout = () => {
  currentUser.value = null
  sessions.value = []
  authPage.value = 'login'
}

// 视图切换
const switchView = (view) => {
  currentView.value = view
}

// 加载会话列表
const loadSessions = async () => {
  if (!currentUser.value) return

  try {
    console.log('加载会话列表，用户:', currentUser.value.username)
    const result = await api.getUserSessions(currentUser.value.username)
    console.log('API 返回结果:', result)
    if (result && result.sessions) {
      sessions.value = result.sessions
      console.log('会话列表已更新:', sessions.value)
    } else {
      console.log('没有会话数据或格式错误')
    }
  } catch (error) {
    console.error('加载会话列表失败:', error)
  }
}

// 选择会话
const handleSelectSession = async (sessionId) => {
  if (chatViewRef.value) {
    const success = await chatViewRef.value.loadSession(sessionId)
    if (success) {
      switchView('chat')
    }
  }
}

// 删除会话
const handleDeleteSession = async (sessionId) => {
  if (!confirm('确定要删除这个对话吗？')) return

  try {
    const result = await api.deleteSession(sessionId, currentUser.value.username)
    if (result.success) {
      sessions.value = sessions.value.filter(s => s.id !== sessionId)
      // 如果删除的是当前会话，重置聊天
      await chatViewRef.value?.resetChat()
    }
  } catch (error) {
    console.error('删除会话失败:', error)
    alert('删除失败，请重试')
  }
}

// 新建对话
const handleNewChat = async () => {
  if (chatViewRef.value) {
    await chatViewRef.value.resetChat()
    switchView('chat')
  }
}

// 检查是否有保存的登录状态
onMounted(async () => {
  const savedUser = localStorage.getItem('user')
  if (savedUser) {
    try {
      currentUser.value = JSON.parse(savedUser)
      await loadSessions()
    } catch (e) {
      localStorage.removeItem('user')
    }
  }
})
</script>

<template>
  <!-- 未登录状态 -->
  <div v-if="!currentUser" class="auth-container">
    <Login
      v-if="authPage === 'login'"
      @login-success="handleLoginSuccess"
      @go-to-register="authPage = 'register'"
    />
    <Register
      v-else
      @go-to-login="authPage = 'login'"
    />
  </div>

  <!-- 已登录状态 -->
  <div v-else class="app-layout">
    <Sidebar
      :currentUser="currentUser"
      :currentView="currentView"
      :sessions="sessions"
      @switch-view="switchView"
      @logout="handleLogout"
      @select-session="handleSelectSession"
      @delete-session="handleDeleteSession"
      @new-chat="handleNewChat"
    />

    <main class="main-content">
      <ChatView
        v-if="currentView === 'chat'"
        ref="chatViewRef"
      />
      <DocumentsView
        v-else-if="currentView === 'documents'"
      />
      <AnalysisView
        v-else-if="currentView === 'analysis'"
      />
    </main>
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:root {
  --primary: #0F172A;
  --secondary: #334155;
  --accent: #0369A1;
  --background: #F8FAFC;
  --surface: #FFFFFF;
  --text-primary: #020617;
  --text-secondary: #475569;
  --text-muted: #94A3B8;
  --border: #E2E8F0;
  --success: #10B981;
  --error: #EF4444;
}

body {
  font-family: 'PingFang SC', 'Microsoft YaHei', -apple-system, sans-serif;
  background-color: var(--background);
  color: var(--text-primary);
  height: 100vh;
  overflow: hidden;
}

#app {
  height: 100%;
}

.auth-container {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--background);
}

.app-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--background);
  overflow: hidden;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: var(--border);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--text-muted);
}
</style>
