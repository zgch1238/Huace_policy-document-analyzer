<script setup>
import { ref, computed, watch, nextTick } from 'vue'

const props = defineProps({
  isGenerating: Boolean
})

const emit = defineEmits(['send', 'stop'])

const message = ref('')
const textareaRef = ref(null)

const canSend = computed(() => message.value.trim() && !props.isGenerating)

// 自动调整高度
const adjustHeight = () => {
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
    textareaRef.value.style.height = Math.min(textareaRef.value.scrollHeight, 200) + 'px'
  }
}

// 监听消息变化
watch(message, () => {
  nextTick(adjustHeight)
})

const handleSend = () => {
  if (canSend.value) {
    emit('send', message.value.trim())
    message.value = ''
    nextTick(() => {
      if (textareaRef.value) {
        textareaRef.value.style.height = 'auto'
      }
    })
  }
}

const handleKeydown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

const handleStop = () => {
  emit('stop')
}
</script>

<template>
  <div class="input-container">
    <div class="input-wrapper">
      <textarea
        ref="textareaRef"
        v-model="message"
        class="message-input"
        placeholder="输入消息，按 Enter 发送，Shift+Enter 换行..."
        rows="1"
        @keydown="handleKeydown"
      ></textarea>

      <div class="action-buttons">
        <button
          v-if="isGenerating"
          class="stop-btn"
          @click="handleStop"
          title="停止生成"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="6" y="6" width="12" height="12" rx="2"/>
          </svg>
        </button>
        <button
          class="send-btn"
          :disabled="!canSend"
          @click="handleSend"
          title="发送"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="22" y1="2" x2="11" y2="13"/>
            <polygon points="22 2 15 22 11 13 2 9 22 2"/>
          </svg>
        </button>
      </div>
    </div>

    <p class="input-hint">按 Enter 发送，Shift+Enter 换行</p>
  </div>
</template>

<style scoped>
.input-container {
  padding: 16px 24px 20px;
  background: var(--surface);
  border-top: 1px solid var(--border);
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  background: var(--background);
  padding: 12px 16px;
  border-radius: 12px;
  border: 1px solid var(--border);
  transition: border-color 0.2s;
  max-width: 900px;
  margin: 0 auto;
}

.input-wrapper:focus-within {
  border-color: var(--accent);
}

.message-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 0.9375rem;
  font-family: inherit;
  resize: none;
  line-height: 1.5;
  padding: 4px 0;
  min-height: 24px;
  max-height: 200px;
  height: auto;
  overflow-y: auto;
}

.action-buttons {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.stop-btn, .send-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.stop-btn {
  background: var(--error);
  color: white;
}

.send-btn {
  background: var(--accent);
  color: white;
}

.send-btn:disabled {
  background: var(--text-muted);
  cursor: not-allowed;
}

.stop-btn:hover:not(:disabled), .send-btn:not(:disabled):hover {
  transform: scale(1.05);
}

.stop-btn svg, .send-btn svg {
  width: 16px;
  height: 16px;
}

.input-hint {
  margin-top: 8px;
  font-size: 0.75rem;
  color: var(--text-muted);
  text-align: center;
}
</style>
