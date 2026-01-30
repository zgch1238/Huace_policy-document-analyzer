<script setup>
import { ref, watch, nextTick } from 'vue'
import MessageItem from './MessageItem.vue'

const props = defineProps({
  messages: Array,
  isTyping: Boolean
})

const chatBoxRef = ref(null)

watch(() => props.messages, () => {
  nextTick(() => {
    if (chatBoxRef.value) {
      chatBoxRef.value.scrollTop = chatBoxRef.value.scrollHeight
    }
  })
}, { deep: true })
</script>

<template>
  <div ref="chatBoxRef" class="chat-box">
    <div class="messages-container">
      <MessageItem
        v-for="(msg, index) in messages"
        :key="index"
        :message="msg"
      />

      <div v-if="isTyping" class="typing-indicator">
        <span class="dot"></span>
        <span class="dot"></span>
        <span class="dot"></span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-box {
  flex: 1;
  overflow-y: auto;
  background: var(--background);
}

.messages-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: var(--surface);
  border-radius: 12px;
  width: fit-content;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  margin-left: 52px;
}

.dot {
  width: 8px;
  height: 8px;
  background: var(--text-muted);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}
</style>
