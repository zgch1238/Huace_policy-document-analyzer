<script setup>
import { ref } from 'vue'
import { api } from '../utils/api'

const emit = defineEmits(['go-to-login'])

const username = ref('')
const password = ref('')
const passwordConfirm = ref('')
const error = ref('')
const loading = ref(false)

const handleSubmit = async () => {
  error.value = ''

  if (!username.value || !password.value || !passwordConfirm.value) {
    error.value = '请填写完整信息'
    return
  }

  if (username.value.length < 3) {
    error.value = '用户名至少需要3个字符'
    return
  }

  if (password.value.length < 6) {
    error.value = '密码至少需要6个字符'
    return
  }

  if (password.value !== passwordConfirm.value) {
    error.value = '两次输入的密码不一致'
    return
  }

  loading.value = true

  try {
    const result = await api.register(username.value, password.value)
    if (result.success) {
      emit('go-to-login')
      alert('注册成功，请登录')
    } else {
      error.value = result.message || '注册失败'
    }
  } catch (e) {
    error.value = '网络错误，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-card">
    <div class="auth-header">
      <div class="logo">
        <svg viewBox="0 0 32 32" fill="none">
          <circle cx="16" cy="16" r="14" stroke="currentColor" stroke-width="2"/>
          <path d="M16 8 L16 16 L22 22" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          <circle cx="16" cy="16" r="3" fill="currentColor"/>
        </svg>
      </div>
      <h1>用户注册</h1>
      <p>创建您的账户</p>
    </div>

    <form @submit.prevent="handleSubmit" class="auth-form">
      <div class="form-group">
        <label>用户名</label>
        <input
          v-model="username"
          type="text"
          placeholder="至少3个字符"
          :disabled="loading"
        />
      </div>

      <div class="form-group">
        <label>密码</label>
        <input
          v-model="password"
          type="password"
          placeholder="至少6个字符"
          :disabled="loading"
        />
      </div>

      <div class="form-group">
        <label>确认密码</label>
        <input
          v-model="passwordConfirm"
          type="password"
          placeholder="请再次输入密码"
          :disabled="loading"
        />
      </div>

      <div v-if="error" class="error-message">{{ error }}</div>

      <button type="submit" class="submit-btn" :disabled="loading">
        {{ loading ? '注册中...' : '注册' }}
      </button>

      <div class="auth-switch">
        已有账号？<a href="#" @click.prevent="emit('go-to-login')">立即登录</a>
      </div>
    </form>
  </div>
</template>

<style scoped>
.auth-card {
  background: var(--surface);
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
  width: 400px;
  max-width: 90vw;
}

.auth-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo {
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  color: var(--accent);
}

.auth-header h1 {
  font-size: 1.5rem;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.auth-header p {
  color: var(--text-muted);
  font-size: 0.875rem;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 0.875rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.form-group input {
  padding: 12px 16px;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 1rem;
  outline: none;
  transition: border-color 0.2s;
}

.form-group input:focus {
  border-color: var(--accent);
}

.error-message {
  color: var(--error);
  font-size: 0.875rem;
  text-align: center;
}

.submit-btn {
  padding: 14px;
  background: var(--accent);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.submit-btn:hover:not(:disabled) {
  background: #025a8b;
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.auth-switch {
  text-align: center;
  font-size: 0.875rem;
  color: var(--text-muted);
}

.auth-switch a {
  color: var(--accent);
  text-decoration: none;
}

.auth-switch a:hover {
  text-decoration: underline;
}
</style>
