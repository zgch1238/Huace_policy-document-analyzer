<script setup>
import { ref, onMounted } from 'vue';
import Sidebar from './components/Sidebar.vue';
import ChatBox from './components/ChatBox.vue';
import ChatInput from './components/ChatInput.vue';
import ModelSelector from './components/ModelSelector.vue';
import Login from './components/Login.vue';
import Register from './components/Register.vue';
import { authService } from './utils/auth';

const currentUser = ref(null);
const authPage = ref('login'); // 'login' or 'register'

const currentSessionId = ref(null);
const messages = ref([]);
const sessions = ref([]);
const providers = ref([]);
const modelConfig = ref({
    providerID: '',
    modelID: '',
    mode: 'plan'
});
const isHistoryCollapsed = ref(false);
const isTyping = ref(false);

const handleLoginSuccess = (user) => {
    currentUser.value = user;
    loadHistory();
    loadConfig();
};

const handleLogout = () => {
    authService.logout();
    currentUser.value = null;
    currentSessionId.value = null;
    messages.value = [];
    authPage.value = 'login';
};

const appendMessage = (text, sender, timestamp) => {
    messages.value.push({
        text,
        sender,
        timestamp: timestamp || new Date().toISOString()
    });
};

const loadConfig = async () => {
    try {
        const response = await fetch('/api/config/providers');
        const data = await response.json();
        providers.value = Array.isArray(data) ? data : (data.providers || []);
        
        // Set default values from first available provider/model if not set
        if (providers.value.length > 0) {
            const firstProvider = providers.value[0];
            modelConfig.value.providerID = firstProvider.id;
            if (firstProvider.models) {
                const models = Object.keys(firstProvider.models);
                if (models.length > 0) {
                    modelConfig.value.modelID = models[0];
                }
            }
        }
    } catch (error) {
        console.error('Error loading config:', error);
    }
};

const loadHistory = async () => {
    if (!currentUser.value) return;
    
    try {
        // 1. Get all sessions from primary backend
        const response = await fetch('/api/session');
        const data = await response.json();
        const allSessions = Array.isArray(data) ? data : (data.sessions || []);
        
        // 2. Get allowed session IDs from auth backend
        const allowedIds = await authService.getUserSessions(currentUser.value.username);
        
        // 3. Filter sessions
        sessions.value = allSessions.filter(s => allowedIds.includes(s.id));
    } catch (error) {
        console.error('Error loading history:', error);
    }
};

const handleNewChat = () => {
    currentSessionId.value = null;
    messages.value = [{
        text: '您好！我是您的 **GICI-lib 知识库助手**。我专注于 GNSS/INS 组合导航、RTK 定位以及传感器融合技术。今天有什么我可以帮您的吗？',
        sender: 'assistant',
        timestamp: new Date().toISOString()
    }];
};

const handleSelectSession = async (sessionId) => {
    if (sessionId === currentSessionId.value) return;
    
    currentSessionId.value = sessionId;
    messages.value = [];
    
    try {
        const response = await fetch(`/api/session/${sessionId}/message`);
        const data = await response.json();
        
        if (Array.isArray(data)) {
            data.forEach(msg => {
                const role = msg.info ? msg.info.role : msg.role;
                const timestamp = msg.info && msg.info.time ? msg.info.time.created : null;
                const textParts = (msg.parts || [])
                    .filter(part => part.type === 'text')
                    .map(part => part.text)
                    .join('');
                
                if (textParts) {
                    appendMessage(textParts, role === 'user' ? 'user' : 'assistant', timestamp);
                }
            });
        }
    } catch (error) {
        console.error('Error loading session messages:', error);
        appendMessage('**系统错误：** 无法加载会话历史。', 'assistant');
    }
};

const handleSendMessage = async (message) => {
    if (!message.trim()) return;

    appendMessage(message, 'user');
    isTyping.value = true;

    try {
        // Lazy session initialization
        if (!currentSessionId.value) {
            const sessionResp = await fetch('/api/session', { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: 'GICI Assistant Session' })
            });
            const sessionData = await sessionResp.json();
            const sid = sessionData.id || sessionData.session_id;
            if (sid) {
                currentSessionId.value = sid;
                // Sync new session to auth backend
                await authService.addSession(currentUser.value.username, sid);
                loadHistory();
            } else {
                throw new Error(sessionData.error || 'Failed to create session');
            }
        }

        const response = await fetch(`/api/session/${currentSessionId.value}/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                providerID: modelConfig.value.providerID,
                modelID: modelConfig.value.modelID,
                mode: modelConfig.value.mode,
                parts: [{ type: 'text', text: message }]
            }),
        });

        const data = await response.json();
        if (data.parts) {
            let textParts = data.parts
                .filter(part => part.type === 'text')
                .map(part => part.text)
                .join('');
            
            if (!textParts) {
                const hasToolCall = data.parts.some(part => part.type === 'tool_call');
                textParts = hasToolCall 
                    ? 'GICI 专家正在进行后台分析，请稍候。' 
                    : '收到空回复。专家可能正在思考或需要更多上下文信息。';
            }
            appendMessage(textParts, 'assistant');
        } else if (data.error) {
            throw new Error(data.error);
        } else {
            throw new Error('Unexpected response format from server');
        }
    } catch (error) {
        console.error('Error sending message:', error);
        appendMessage('**系统错误：** ' + (error.message || '无法连接到后端服务器'), 'assistant');
    } finally {
        isTyping.value = false;
    }
};

const handleRenameSession = async (session) => {
    const newTitle = prompt('请输入新的会话标题：', session.title);
    if (newTitle === null || newTitle.trim() === '' || newTitle === session.title) return;

    try {
        const response = await fetch(`/api/session/${session.id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: newTitle.trim() })
        });
        
        if (response.ok) {
            loadHistory();
        } else {
            alert('重命名失败，请稍后重试。');
        }
    } catch (error) {
        console.error('Error renaming session:', error);
        alert('系统错误：无法重命名会话。');
    }
};

const handleDeleteSession = async (session) => {
    if (!confirm('确定要删除这个会话吗？此操作不可撤销。')) return;

    try {
        const response = await fetch(`/api/session/${session.id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            // Also remove from auth backend
            await authService.removeSession(currentUser.value.username, session.id);
            
            if (session.id === currentSessionId.value) {
                handleNewChat();
            }
            loadHistory();
        } else {
            alert('删除失败，请稍后重试。');
        }
    } catch (error) {
        console.error('Error deleting session:', error);
        alert('系统错误：无法删除会话。');
    }
};

onMounted(() => {
    currentUser.value = authService.getCurrentUser();
    handleNewChat();
    if (currentUser.value) {
        loadHistory();
        loadConfig();
    }
});
</script>

<template>
  <div v-if="!currentUser">
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
  
  <div v-else class="app-layout">
    <Sidebar 
      :sessions="sessions" 
      :currentSessionId="currentSessionId"
      :isCollapsed="isHistoryCollapsed"
      @new-chat="handleNewChat"
      @select-session="handleSelectSession"
      @toggle-history="isHistoryCollapsed = !isHistoryCollapsed"
      @rename-session="handleRenameSession"
      @delete-session="handleDeleteSession"
    />
    
    <main class="main-container">
      <header class="app-header">
        <div class="header-info">
          <h1>GICI 知识库智能助手</h1>
          <p>欢迎, {{ currentUser.username }}</p>
        </div>
        <div class="header-actions">
          <button class="icon-btn" title="系统状态">
            <i class="fa-solid fa-chart-line" style="font-size: 20px;"></i>
          </button>
          <button class="icon-btn" title="退出登录" @click="handleLogout">
            <i class="fa-solid fa-right-from-bracket" style="font-size: 20px;"></i>
          </button>
        </div>
      </header>

      <ModelSelector 
        v-if="providers.length"
        v-model="modelConfig"
        :providers="providers"
      />
      
      <ChatBox :messages="messages" :isTyping="isTyping" />
      
      <ChatInput @send="handleSendMessage" />
    </main>
  </div>
</template>

<style>
:root {
  --primary: #0F172A;
  --secondary: #334155;
  --accent: #0369A1;
  --background: #F8FAFC;
  --surface: #FFFFFF;
  --text-primary: #020617;
  --text-secondary: #475569;
  --border: #E2E8F0;
  --glass-bg: rgba(255, 255, 255, 0.8);
  --glass-border: rgba(255, 255, 255, 0.2);
  --message-user: #0369A1;
  --message-assistant: #F1F5F9;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: 'Open Sans', sans-serif;
  background-color: var(--background);
  color: var(--text-primary);
  height: 100vh;
  overflow: hidden;
}

.app-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: var(--background);
  position: relative;
}

.app-header {
  height: 72px;
  padding: 0 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--glass-bg);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border);
  z-index: 10;
}

.header-info h1 {
  font-size: 1.125rem;
  font-weight: 600;
}

.header-info p {
  font-size: 0.8125rem;
  color: var(--text-secondary);
}

.header-actions {
  display: flex;
  gap: 8px;
}

.icon-btn {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.icon-btn:hover {
  background: var(--surface);
  color: var(--primary);
  border-color: var(--text-secondary);
}

/* Animations */
.animate-fade-in {
  animation: fadeIn 0.3s ease-out forwards;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
