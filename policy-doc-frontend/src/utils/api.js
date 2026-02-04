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
  async getDocuments(keyword = '') {
    const url = keyword
      ? `${API_BASE}/api/documents?keyword=${encodeURIComponent(keyword)}`
      : `${API_BASE}/api/documents`
    const res = await fetch(url)
    return res.json()
  },

  // 资源管理器风格：列出指定目录的内容
  async listDocumentsInDir(path = '', keyword = '') {
    let url = `${API_BASE}/api/documents/list?path=${encodeURIComponent(path)}`
    if (keyword) {
      url += `&keyword=${encodeURIComponent(keyword)}`
    }
    const res = await fetch(url)
    return res.json()
  },

  // 资源管理器风格：列出分析结果目录的内容
  async listAnalysisDir(baseDir, path = '', keyword = '', minScore = null) {
    let url = `${API_BASE}/api/analysis/list?baseDir=${encodeURIComponent(baseDir)}&path=${encodeURIComponent(path)}`
    if (keyword) {
      url += `&keyword=${encodeURIComponent(keyword)}`
    }
    if (minScore !== null) {
      url += `&minScore=${encodeURIComponent(minScore)}`
    }
    const res = await fetch(url)
    return res.json()
  },

  async syncData() {
    const res = await fetch(`${API_BASE}/api/sync-data`, {
      method: 'POST'
    })
    return res.json()
  },

  async getStatistics() {
    const res = await fetch(`${API_BASE}/api/statistics`)
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

  async downloadAnalysis(files, directory = 'analysis_results') {
    const res = await fetch(`${API_BASE}/api/download-analysis`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ files, directory })
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

  // 高亮文档列表
  async getHighlightDocs() {
    const res = await fetch(`${API_BASE}/api/highlight-docs`)
    return res.json()
  },

  async getAnalyzeProgress() {
    const res = await fetch(`${API_BASE}/api/analyze-progress`)
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
