const API_BASE = ''

export const api = {
  // 认证相关
  async login(username, password) {
    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    })
    return res.json()
  },

  async register(username, password) {
    const res = await fetch(`${API_BASE}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    })
    return res.json()
  },

  // 发送消息
  async ask(message) {
    const res = await fetch(`${API_BASE}/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    })
    return res.json()
  },

  // 文档管理
  async getDocuments() {
    const res = await fetch(`${API_BASE}/api/documents`)
    return res.json()
  },

  async downloadDocuments(files) {
    const res = await fetch(`${API_BASE}/api/download-documents`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ files })
    })
    return res.json()
  },

  async deleteDocuments(files, username) {
    const res = await fetch(`${API_BASE}/api/delete-documents`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ files, username })
    })
    return res.json()
  },

  // 分析结果
  async getAnalysisResults() {
    const res = await fetch(`${API_BASE}/api/analysis-results`)
    return res.json()
  },

  async downloadAnalysis(files) {
    const res = await fetch(`${API_BASE}/api/download-analysis`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ files })
    })
    return res.json()
  },

  async deleteAnalysis(files, username) {
    const res = await fetch(`${API_BASE}/api/delete-analysis`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ files, username })
    })
    return res.json()
  },

  // 分析状态
  async getAnalyzeStatus() {
    const res = await fetch(`${API_BASE}/api/analyze-status`)
    return res.json()
  },

  async triggerAnalyze() {
    const res = await fetch(`${API_BASE}/api/trigger-analyze`, {
      method: 'POST'
    })
    return res.json()
  },

  // 会话管理
  async getUserSessions(username) {
    const res = await fetch(`${API_BASE}/api/sessions?username=${encodeURIComponent(username)}`)
    return res.json()
  },

  async createSession(username, title = '新对话') {
    const res = await fetch(`${API_BASE}/api/session`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, title })
    })
    return res.json()
  },

  async getSession(sessionId, username) {
    const res = await fetch(`${API_BASE}/api/session/${sessionId}?username=${encodeURIComponent(username)}`)
    return res.json()
  },

  async deleteSession(sessionId, username) {
    const res = await fetch(`${API_BASE}/api/session/${sessionId}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username })
    })
    return res.json()
  },

  async saveMessageToSession(sessionId, username, role, content) {
    const res = await fetch(`${API_BASE}/api/session/${sessionId}/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, role, content })
    })
    return res.json()
  }
}
