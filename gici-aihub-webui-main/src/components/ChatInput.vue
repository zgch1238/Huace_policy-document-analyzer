<script setup>
import { ref } from 'vue';

const emit = defineEmits(['send']);
const message = ref('');

const handleSend = () => {
  if (message.value.trim()) {
    emit('send', message.value.trim());
    message.value = '';
  }
};
</script>

<template>
  <div class="input-container">
    <div class="input-wrapper">
      <input 
        v-model="message" 
        type="text" 
        placeholder="输入关于 GICI-lib 的问题..." 
        autocomplete="off"
        @keypress.enter.prevent="handleSend"
      >
      <button class="send-btn" @click="handleSend" :disabled="!message.trim()">
        <i class="fa-solid fa-paper-plane" style="font-size: 20px;"></i>
      </button>
    </div>
    <p class="input-hint">按 Enter 键发送。描述越详细（如传感器型号或具体算法），回答越准确。</p>
    <div class="footer-info">
      <a 
        href="https://github.com/zvictorliu/gici-aihub-webui.git" 
        target="_blank" 
        rel="noopener noreferrer"
        class="github-link"
      >
        <i class="fa-brands fa-github" style="font-size: 14px;"></i>
      </a>
      <p class="copyright">© 2026 GICI-aihub All Rights Reserved</p>
    </div>
  </div>
</template>

<style scoped>
.input-container {
  padding: 24px 15% 40px;
  background: transparent;
}

.input-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--surface);
  padding: 8px 8px 8px 20px;
  border-radius: 16px;
  border: 1px solid var(--border);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  transition: border-color 0.2s;
}

.input-wrapper:focus-within {
  border-color: var(--accent);
}

input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 1rem;
  padding: 12px 0;
  font-family: inherit;
}

.send-btn {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--accent);
  color: white;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: transform 0.2s, background-color 0.2s;
}

.send-btn:disabled {
  background-color: var(--text-secondary);
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.send-btn:not(:disabled):hover {
  background-color: #025a8b;
  transform: scale(1.05);
}

.send-btn:active {
  transform: scale(0.95);
}

.input-hint {
  margin-top: 12px;
  font-size: 0.75rem;
  color: var(--text-secondary);
  text-align: center;
}

.copyright {
  font-size: 0.75rem;
  color: rgba(0, 0, 0, 0.3);
}

.footer-info {
  margin-top: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.github-link {
  color: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  transition: color 0.2s;
}

.github-link:hover {
  color: var(--primary);
}

@media (max-width: 1024px) {
  .input-container {
    padding-left: 5%;
    padding-right: 5%;
  }
}
</style>
