<script setup>
import { ref, watch, nextTick } from 'vue';
import MessageItem from './MessageItem.vue';

const props = defineProps({
  messages: Array,
  isTyping: Boolean
});

const chatBoxRef = ref(null);

watch(() => props.messages, () => {
  nextTick(() => {
    if (chatBoxRef.value) {
      chatBoxRef.value.scrollTop = chatBoxRef.value.scrollHeight;
    }
  });
}, { deep: true });
</script>

<template>
  <div ref="chatBoxRef" class="chat-box">
    <MessageItem 
      v-for="(msg, index) in messages" 
      :key="index" 
      :message="msg" 
    />
    
    <div v-if="isTyping" class="typing-indicator animate-fade-in">
      <div class="dot"></div>
      <div class="dot"></div>
      <div class="dot"></div>
    </div>
  </div>
</template>

<style scoped>
.chat-box {
  flex: 1;
  overflow-y: auto;
  padding: 40px 15%;
  display: flex;
  flex-direction: column;
  gap: 24px;
  scroll-behavior: smooth;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: var(--message-assistant);
  border-radius: 16px;
  width: fit-content;
  margin-bottom: 24px;
}

.dot {
  width: 8px;
  height: 8px;
  background: var(--text-secondary);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1.0); }
}

@media (max-width: 1024px) {
  .chat-box {
    padding-left: 5%;
    padding-right: 5%;
  }
}
</style>
