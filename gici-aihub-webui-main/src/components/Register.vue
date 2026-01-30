<script setup>
import { ref } from 'vue';
import { authService } from '../utils/auth';

const emit = defineEmits(['register-success', 'go-to-login']);

const username = ref('');
const password = ref('');
const confirmPassword = ref('');
const error = ref('');

const handleRegister = async () => {
  if (password.value !== confirmPassword.value) {
    error.value = '两次输入的密码不一致';
    return;
  }
  
  try {
    await authService.register(username.value, password.value);
    alert('注册成功！');
    emit('go-to-login');
  } catch (e) {
    error.value = e.message;
  }
};
</script>

<template>
  <div class="auth-container">
    <div class="auth-card animate-fade-in">
      <h2>创建账户</h2>
      <p class="subtitle">加入 GICI 智能知识库</p>
      
      <form @submit.prevent="handleRegister" class="auth-form">
        <div class="form-group">
          <label>用户名</label>
          <input 
            v-model="username" 
            type="text" 
            placeholder="选择一个用户名" 
            required
          />
        </div>
        
        <div class="form-group">
          <label>密码</label>
          <input 
            v-model="password" 
            type="password" 
            placeholder="设置您的密码" 
            required
          />
        </div>

        <div class="form-group">
          <label>确认密码</label>
          <input 
            v-model="confirmPassword" 
            type="password" 
            placeholder="再次输入密码" 
            required
          />
        </div>
        
        <p v-if="error" class="error-msg">{{ error }}</p>
        
        <button type="submit" class="auth-btn">注册</button>
      </form>
      
      <p class="switch-auth">
        已有账户？ <a @click="$emit('go-to-login')">立即登录</a>
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
