<script setup>
import { ref } from 'vue';
import { authService } from '../utils/auth';

const emit = defineEmits(['login-success', 'go-to-register']);

const username = ref('');
const password = ref('');
const error = ref('');

const handleLogin = async () => {
  try {
    const user = await authService.login(username.value, password.value);
    emit('login-success', user);
  } catch (e) {
    error.value = e.message;
  }
};
</script>

<template>
  <div class="auth-container">
    <div class="auth-card animate-fade-in">
      <h2>欢迎回来</h2>
      <p class="subtitle">登录您的 GICI-AIHUB 账户</p>
      
      <form @submit.prevent="handleLogin" class="auth-form">
        <div class="form-group">
          <label>用户名</label>
          <input 
            v-model="username" 
            type="text" 
            placeholder="输入您的用户名" 
            required
          />
        </div>
        
        <div class="form-group">
          <label>密码</label>
          <input 
            v-model="password" 
            type="password" 
            placeholder="输入您的密码" 
            required
          />
        </div>
        
        <p v-if="error" class="error-msg">{{ error }}</p>
        
        <button type="submit" class="auth-btn">登录</button>
      </form>
      
      <p class="switch-auth">
        没有账户？ <a @click="$emit('go-to-register')">立即注册</a>
      </p>
    </div>
  </div>
</template>

<style scoped>
.auth-container {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  width: 100vw;
  background-color: var(--background);
}

.auth-card {
  background: var(--surface);
  padding: 40px;
  border-radius: 16px;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
  border: 1px solid var(--border);
}

h2 {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--primary);
  margin-bottom: 8px;
  text-align: center;
}

.subtitle {
  color: var(--text-secondary);
  text-align: center;
  margin-bottom: 32px;
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
  font-weight: 600;
  color: var(--secondary);
}

.form-group input {
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--background);
  font-size: 1rem;
  transition: all 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(3, 105, 161, 0.1);
}

.auth-btn {
  background: var(--accent);
  color: white;
  padding: 12px;
  border-radius: 8px;
  border: none;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s;
  margin-top: 10px;
}

.auth-btn:hover {
  background: #025a8b;
}

.error-msg {
  color: #ef4444;
  font-size: 0.875rem;
  text-align: center;
}

.switch-auth {
  margin-top: 24px;
  text-align: center;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.switch-auth a {
  color: var(--accent);
  font-weight: 600;
  cursor: pointer;
}

.switch-auth a:hover {
  text-decoration: underline;
}
</style>
