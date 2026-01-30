const CURRENT_USER_KEY = 'aihub_current_user';

export const authService = {
  // Register via Python backend
  async register(username, password) {
    const response = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || '注册失败');
    }
    return data;
  },

  // Login via Python backend
  async login(username, password) {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || '登录失败');
    }
    
    localStorage.setItem(CURRENT_USER_KEY, JSON.stringify({ username: data.username }));
    return data;
  },

  // Record a session ID for a user
  async addSession(username, sessionId) {
    try {
      await fetch('/api/auth/add_session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, sessionId })
      });
    } catch (e) {
      console.error('Failed to sync session to auth backend:', e);
    }
  },

  // Get allowed session IDs for a user
  async getUserSessions(username) {
    try {
      const response = await fetch(`/api/auth/user_sessions?username=${encodeURIComponent(username)}`);
      if (!response.ok) return [];
      return await response.json();
    } catch (e) {
      console.error('Failed to get user sessions:', e);
      return [];
    }
  },

  // Remove a session ID for a user
  async removeSession(username, sessionId) {
    try {
      await fetch('/api/auth/remove_session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, sessionId })
      });
    } catch (e) {
      console.error('Failed to remove session from auth backend:', e);
    }
  },

  // Logout
  logout() {
    localStorage.removeItem(CURRENT_USER_KEY);
  },

  // Get current session
  getCurrentUser() {
    const userJson = localStorage.getItem(CURRENT_USER_KEY);
    return userJson ? JSON.parse(userJson) : null;
  }
};
