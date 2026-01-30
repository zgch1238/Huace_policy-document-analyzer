<script setup>
import { computed } from 'vue'

const props = defineProps({
  message: Object
})

const isUser = computed(() => props.message.sender === 'user')

// 格式化消息内容
const formattedContent = computed(() => {
  return formatMessage(props.message.text)
})

function formatMessage(text) {
  if (!text) return ''

  // HTML 转义
  text = escapeHtml(text)

  // 代码块
  text = text.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')

  // 行内代码
  text = text.replace(/`([^`]+)`/g, '<code>$1</code>')

  // 粗体
  text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')

  // 斜体
  text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>')

  // 删除线
  text = text.replace(/~~([^~]+)~~/g, '<del>$1</del>')

  // 引用
  text = text.replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>')

  // 链接
  text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')

  // 标题
  text = text.replace(/^### (.+)$/gm, '<h3>$1</h3>')
  text = text.replace(/^## (.+)$/gm, '<h2>$1</h2>')
  text = text.replace(/^# (.+)$/gm, '<h1>$1</h1>')

  // 无序列表
  text = text.replace(/^- (.+)$/gm, '<li>$1</li>')
  text = text.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')

  // 有序列表
  text = text.replace(/^\d+\. (.+)$/gm, '<li>$1</li>')

  // 段落
  text = text.replace(/\n\n/g, '</p><p>')
  text = '<p>' + text + '</p>'

  // 换行
  text = text.replace(/\n/g, '<br>')

  return text
}

function escapeHtml(text) {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}
</script>

<template>
  <div class="message" :class="{ user: isUser, assistant: !isUser }">
    <div class="message-avatar">
      {{ isUser ? '你' : 'AI' }}
    </div>
    <div class="message-content" v-html="formattedContent"></div>
  </div>
</template>

<style scoped>
.message {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.message.user {
  flex-direction: row-reverse;
  margin-left: auto;
}

.message.assistant {
  margin-right: auto;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  color: white;
  flex-shrink: 0;
}

.message.user .message-avatar {
  background: var(--accent);
}

.message.assistant .message-avatar {
  background: var(--success);
}

.message-content {
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
  font-size: 0.9375rem;
  max-width: 600px;
  word-break: break-word;
}

.message.user .message-content {
  background: var(--accent);
  color: white;
  border-bottom-right-radius: 4px;
}

.message.assistant .message-content {
  background: var(--surface);
  color: var(--text-primary);
  border-bottom-left-radius: 4px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

/* Markdown 样式 */
.message-content :deep(pre) {
  background: #1e293b;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 8px 0;
}

.message-content :deep(code) {
  font-family: 'Fira Code', monospace;
  font-size: 0.875em;
}

.message-content :deep(pre code) {
  color: #e2e8f0;
}

.message-content :deep(code:not(pre code)) {
  background: rgba(0, 0, 0, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.875em;
}

.message-content :deep(strong) {
  font-weight: 600;
}

.message-content :deep(em) {
  font-style: italic;
}

.message-content :deep(del) {
  text-decoration: line-through;
  color: var(--text-muted);
}

.message-content :deep(blockquote) {
  border-left: 3px solid var(--accent);
  margin: 8px 0;
  padding-left: 12px;
  color: var(--text-muted);
}

.message-content :deep(a) {
  color: inherit;
  text-decoration: underline;
}

.message-content :deep(h1),
.message-content :deep(h2),
.message-content :deep(h3) {
  margin: 12px 0 8px;
  font-weight: 600;
}

.message-content :deep(h1) { font-size: 1.25rem; }
.message-content :deep(h2) { font-size: 1.125rem; }
.message-content :deep(h3) { font-size: 1rem; }

.message-content :deep(ul),
.message-content :deep(ol) {
  margin: 8px 0;
  padding-left: 20px;
}

.message-content :deep(li) {
  margin: 4px 0;
}

.message-content :deep(p) {
  margin: 8px 0;
}

.message.user .message-content :deep(a),
.message.user .message-content :deep(pre),
.message.user .message-content :deep(code:not(pre code)),
.message.user .message-content :deep(blockquote) {
  color: inherit;
}
</style>
