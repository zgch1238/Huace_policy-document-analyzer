<script setup>
import { ref, onMounted, nextTick, inject, watch } from 'vue'
import ChatBox from '../components/ChatBox.vue'
import ChatInput from '../components/ChatInput.vue'
import { api } from '../utils/api'

// 从父组件获取当前用户
const currentUser = inject('currentUser')

const messages = ref([])
const isTyping = ref(false)
const isGenerating = ref(false)
const abortController = ref(null)
const currentSessionId = ref(null)

// 欢迎语
const welcomeMessage = {
  text: '您好！我是华测导航政策文档分析助手。我可以帮助您：\n\n1. 分析政策文档内容\n2. 提取关键政策信息\n3. 解答相关政策问题\n4. 生成分析报告\n\n请输入您的问题或选择一篇政策文档开始分析。',
  sender: 'assistant',
  timestamp: new Date().toISOString()
}

onMounted(() => {
  resetChat()
})

// 监听用户变化，重置聊天
watch(() => currentUser?.value, (newUser) => {
  if (newUser) {
    resetChat()
  } else {
    messages.value = [welcomeMessage]
  }
})

const resetChat = () => {
  currentSessionId.value = null
  messages.value = [welcomeMessage]
}

// 创建会话
const createSession = async (title = '新对话') => {
  if (!currentUser.value) return null

  try {
    const result = await api.createSession(currentUser.value.username, title)
    if (result.success) {
      return result.id
    }
  } catch (error) {
    console.error('创建会话失败:', error)
  }
  return null
}

// 保存消息到会话
const saveMessage = async (sessionId, role, content) => {
  if (!currentUser.value || !sessionId) return

  try {
    await api.saveMessageToSession(sessionId, currentUser.value.username, role, content)
  } catch (error) {
    console.error('保存消息失败:', error)
  }
}

const handleSendMessage = async (message) => {
  if (!message.trim() || isGenerating.value) return

  // 如果用户已登录且没有会话，创建新会话（使用第一条消息作为标题）
  if (currentUser.value && !currentSessionId.value) {
    // 取消息前20字符作为标题
    const title = message.length > 20 ? message.substring(0, 20) + '...' : message
    const sessionId = await createSession(title)
    if (sessionId) {
      currentSessionId.value = sessionId
    }
  }

  // 添加用户消息
  const userMsg = {
    text: message,
    sender: 'user',
    timestamp: new Date().toISOString()
  }
  messages.value.push(userMsg)

  // 保存用户消息到会话
  if (currentUser.value && currentSessionId.value) {
    await saveMessage(currentSessionId.value, 'user', message)
  }

  isGenerating.value = true
  isTyping.value = true

  // 创建 AbortController
  abortController.value = new AbortController()

  // 60秒超时
  const timeoutId = setTimeout(() => {
    if (abortController.value) {
      abortController.value.abort('timeout')
    }
  }, 60000)

  try {
    const result = await api.ask(message)
    clearTimeout(timeoutId)

    // 添加AI回复
    if (result.response) {
      const assistantMsg = {
        text: result.response,
        sender: 'assistant',
        timestamp: new Date().toISOString()
      }
      messages.value.push(assistantMsg)

      // 保存AI回复到会话
      if (currentUser.value && currentSessionId.value) {
        await saveMessage(currentSessionId.value, 'assistant', result.response)
      }
    } else {
      messages.value.push({
        text: '抱歉，出现了一些问题。请稍后重试。',
        sender: 'assistant',
        timestamp: new Date().toISOString()
      })
    }
  } catch (error) {
    clearTimeout(timeoutId)

    if (error.name === 'AbortError') {
      messages.value.push({
        text: error.message === 'timeout'
          ? '请求超时（60秒）。请检查服务是否正常运行，或稍后重试。'
          : '已停止生成。',
        sender: 'assistant',
        timestamp: new Date().toISOString()
      })
    } else {
      messages.value.push({
        text: `抱歉，连接失败：${error.message}`,
        sender: 'assistant',
        timestamp: new Date().toISOString()
      })
    }
  } finally {
    isTyping.value = false
    isGenerating.value = false
    abortController.value = null
  }
}

const stopGeneration = () => {
  if (abortController.value) {
    abortController.value.abort()
  }
}

// 暴露方法给父组件
defineExpose({
  resetChat,
  loadSession: async (sessionId) => {
    if (!currentUser.value) return false

    try {
      const result = await api.getSession(sessionId, currentUser.value.username)
      if (result.success && result.session) {
        currentSessionId.value = sessionId
        // 转换消息格式：后端 role → 前端 sender
        messages.value = (result.session.messages || []).map(msg => ({
          text: msg.content,
          sender: msg.role === 'user' ? 'user' : 'assistant',
          timestamp: msg.timestamp
        }))
        return true
      }
    } catch (error) {
      console.error('加载会话失败:', error)
    }
    return false
  }
})
</script>

<template>
  <div class="chat-view">
    <ChatBox
      :messages="messages"
      :isTyping="isTyping"
    />

    <ChatInput
      @send="handleSendMessage"
      :isGenerating="isGenerating"
      @stop="stopGeneration"
    />
  </div>
</template>

<style scoped>
.chat-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}
</style>
