// 政策文档分析系统 - 主应用逻辑

class PolicyAnalyzerApp {
    constructor() {
        this.documents = [];
        this.currentDoc = null;
        this.analysisResults = {};
        this.chatMessages = [];
        this.isConnected = false;

        this.init();
    }

    init() {
        this.bindElements();
        this.bindEvents();
        this.loadDocuments();
        this.checkConnection();
    }

    bindElements() {
        // 文档列表相关
        this.docList = document.getElementById('docList');
        this.docCount = document.getElementById('docCount');
        this.searchInput = document.getElementById('searchInput');

        // 面板相关
        this.docContent = document.getElementById('docContent');
        this.analysisContent = document.getElementById('analysisContent');

        // 聊天相关
        this.chatMessages = document.getElementById('chatMessages');
        this.chatInput = document.getElementById('chatInput');
        this.sendChat = document.getElementById('sendChat');
        this.connectionStatus = document.getElementById('connectionStatus');

        // 统计信息
        this.analyzedCount = document.getElementById('analyzedCount');
        this.pendingCount = document.getElementById('pendingCount');
        this.avgScore = document.getElementById('avgScore');

        // 按钮
        this.refreshDocs = document.getElementById('refreshDocs');
        this.analyzeAll = document.getElementById('analyzeAll');
        this.copyResult = document.getElementById('copyResult');
        this.exportResult = document.getElementById('exportResult');
    }

    bindEvents() {
        // 刷新文档列表
        this.refreshDocs.addEventListener('click', () => this.loadDocuments());

        // 批量分析
        this.analyzeAll.addEventListener('click', () => this.batchAnalyze());

        // 搜索
        this.searchInput.addEventListener('input', (e) => this.filterDocuments(e.target.value));

        // 聊天发送
        this.sendChat.addEventListener('click', () => this.sendChatMessage());
        this.chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendChatMessage();
            }
        });

        // 自动调整输入框高度
        this.chatInput.addEventListener('input', () => {
            this.chatInput.style.height = 'auto';
            this.chatInput.style.height = Math.min(this.chatInput.scrollHeight, 150) + 'px';
        });

        // 复制结果
        this.copyResult.addEventListener('click', () => this.copyAnalysisResult());

        // 导出结果
        this.exportResult.addEventListener('click', () => this.exportAnalysisResult());

        // 快捷操作
        document.querySelectorAll('.quick-btn').forEach(btn => {
            btn.addEventListener('click', () => this.handleQuickAction(btn.dataset.action));
        });
    }

    // 加载文档列表
    async loadDocuments() {
        try {
            const response = await fetch('/api/documents');
            const data = await response.json();

            if (data.documents && data.documents.length > 0) {
                this.documents = data.documents.map((filename, index) => ({
                    id: index + 1,
                    name: filename,
                    path: `policy_document/${filename}`,
                    status: 'pending',
                    score: null
                }));

                this.renderDocumentList();
                this.updateStats();
            } else if (data.message === '文档目录不存在') {
                this.showNotification('文档目录不存在，请将政策文档放入 policy_document 文件夹', 'warning');
            }
        } catch (error) {
            console.error('加载文档列表失败:', error);
            this.showNotification('加载文档列表失败', 'error');
        }
    }

    // 渲染文档列表
    renderDocumentList(filter = '') {
        const filteredDocs = this.documents.filter(doc =>
            doc.name.toLowerCase().includes(filter.toLowerCase())
        );

        this.docList.innerHTML = filteredDocs.map(doc => `
            <div class="doc-item ${this.currentDoc?.id === doc.id ? 'active' : ''}"
                 data-id="${doc.id}" onclick="app.selectDocument(${doc.id})">
                <div class="doc-item-title" title="${doc.name}">${doc.name}</div>
                <div class="doc-item-meta">
                    <span>${this.getStatusText(doc.status)}</span>
                    <span class="doc-item-score ${this.getScoreClass(doc.score)}">
                        ${doc.score !== null ? doc.score + '分' : '待分析'}
                    </span>
                </div>
            </div>
        `).join('');

        this.docCount.textContent = `${filteredDocs.length} 篇`;
    }

    // 选择文档
    async selectDocument(id) {
        this.currentDoc = this.documents.find(d => d.id === id);
        if (!this.currentDoc) return;

        // 更新选中状态
        document.querySelectorAll('.doc-item').forEach(item => {
            item.classList.toggle('active', parseInt(item.dataset.id) === id);
        });

        // 加载文档内容
        await this.loadDocumentContent(this.currentDoc.path);

        // 如果已有分析结果，显示分析结果
        if (this.analysisResults[id]) {
            this.displayAnalysisResult(this.analysisResults[id]);
        } else {
            this.displayEmptyAnalysis();
        }
    }

    // 加载文档内容
    async loadDocumentContent(path) {
        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: `读取并显示文档 ${path} 的内容，不需要分析`
                })
            });

            const data = await response.json();
            if (data.response) {
                this.displayDocumentContent(data.response);
            }
        } catch (error) {
            console.error('加载文档内容失败:', error);
        }
    }

    // 显示文档内容
    displayDocumentContent(content) {
        this.docContent.innerHTML = `
            <div class="doc-detail">
                <div class="doc-detail-header">
                    <h3 class="doc-detail-title">${this.currentDoc.name}</h3>
                    <div class="doc-detail-meta">
                        <span class="doc-meta-item">
                            <strong>来源：</strong> ${this.extractSource(content)}
                        </span>
                    </div>
                </div>
                <div class="doc-detail-content">
                    ${this.formatContent(content)}
                </div>
            </div>
        `;
    }

    // 提取来源
    extractSource(content) {
        const match = content.match(/来自\s+(http[^\s]+)\s+的内容/);
        return match ? match[1] : '未知来源';
    }

    // 格式化内容
    formatContent(content) {
        // 简单的换行处理
        return content.replace(/\n/g, '<br>');
    }

    // 批量分析
    async batchAnalyze() {
        for (const doc of this.documents) {
            await this.analyzeDocument(doc);
        }
        this.showNotification('批量分析完成', 'success');
    }

    // 分析单个文档
    async analyzeDocument(doc) {
        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: `分析文档 ${doc.path}，按照以下四步流程：
1. 梳理基本信息：发布日期、发布机构、文件名称、文件编号、原文链接
2. 总结全文内容（100字左右）
3. 评估与华测导航业务的相关度（0-100分）及理由
4. 摘取3-5个相关段落原文（不加修饰，保持原文），并标注关联说明

请用以下格式回复：
【基本信息】
原文链接: xxx
发布机构: xxx
发布日期: xxx
文件名称: xxx
文件编号: xxx

【全文概要】
xxx（约100字）

【相关度评估】
评分: xxx/100
理由: xxx

【相关段落摘取】
段落1: xxx（关联说明：xxx）
段落2: xxx（关联说明：xxx）
段落3: xxx（关联说明：xxx）`
                })
            });

            const data = await response.json();
            if (data.response) {
                const result = this.parseAnalysisResult(data.response);
                this.analysisResults[doc.id] = result;

                // 更新文档状态
                doc.status = 'analyzed';
                doc.score = result.score;

                // 如果是当前选中的文档，显示分析结果
                if (this.currentDoc?.id === doc.id) {
                    this.displayAnalysisResult(result);
                }

                // 自动保存分析结果到服务器
                this.saveAnalysisToServer(doc.name, data.response);

                this.renderDocumentList(this.searchInput.value);
                this.updateStats();
            }
        } catch (error) {
            console.error('分析文档失败:', error);
        }
    }

    // 保存分析结果到服务器
    async saveAnalysisToServer(docName, resultText) {
        try {
            const response = await fetch('/api/save-analysis', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    docName: docName,
                    result: resultText
                })
            });
            const data = await response.json();
            if (data.success) {
                console.log('分析结果已保存:', data.path);
            } else {
                console.warn('保存分析结果失败:', data.message);
            }
        } catch (error) {
            console.error('保存分析结果失败:', error);
        }
    }

    // 解析分析结果
    parseAnalysisResult(text) {
        const result = {
            basicInfo: {},
            summary: '',
            score: 0,
            scoreReason: '',
            paragraphs: []
        };

        // 解析基本信息
        const basicInfoMatch = text.match(/【基本信息】([\s\S]*?)【全文概要】/);
        if (basicInfoMatch) {
            const lines = basicInfoMatch[1].split('\n');
            lines.forEach(line => {
                const match = line.match(/^(.+?):\s*(.+)$/);
                if (match) {
                    result.basicInfo[match[1].trim()] = match[2].trim();
                }
            });
        }

        // 解析全文概要
        const summaryMatch = text.match(/【全文概要】\s*([\s\S]*?)【相关度评估】/);
        if (summaryMatch) {
            result.summary = summaryMatch[1].trim();
        }

        // 解析相关度
        const scoreMatch = text.match(/评分:\s*(\d+)\/100/);
        const reasonMatch = text.match(/理由:\s*(.+?)(?:\n|$)/);
        if (scoreMatch) {
            result.score = parseInt(scoreMatch[1]);
        }
        if (reasonMatch) {
            result.scoreReason = reasonMatch[1].trim();
        }

        // 解析段落
        const paraMatch = text.match(/【相关段落摘取】([\s\S]*)/);
        if (paraMatch) {
            const paras = paraMatch[1].split(/\n段\d:/).filter(p => p.trim());
            paras.forEach((para, index) => {
                if (para.trim()) {
                    const parts = para.split('（关联说明：');
                    const content = parts[0].trim();
                    const note = parts[1] ? parts[1].replace('）', '').trim() : '';
                    result.paragraphs.push({ content, note, index: index + 1 });
                }
            });
        }

        return result;
    }

    // 显示分析结果
    displayAnalysisResult(result) {
        const scoreClass = this.getScoreClass(result.score);
        const scoreLabel = this.getScoreLabel(result.score);

        this.analysisContent.innerHTML = `
            <div class="analysis-result">
                <div class="analysis-section">
                    <div class="analysis-section-title">相关度评估</div>
                    <div class="score-display">
                        <div class="score-circle ${scoreClass}">
                            ${result.score}
                            <span class="score-label">${scoreLabel}</span>
                        </div>
                        <div class="score-reason">
                            <strong>评估理由：</strong><br>
                            ${result.scoreReason}
                        </div>
                    </div>
                </div>

                <div class="analysis-section">
                    <div class="analysis-section-title">全文概要</div>
                    <p style="font-size: 0.875rem; color: var(--text-secondary); line-height: 1.8;">
                        ${result.summary}
                    </p>
                </div>

                <div class="analysis-section">
                    <div class="analysis-section-title">相关段落摘取</div>
                    <div class="paragraph-list">
                        ${result.paragraphs.map(p => `
                            <div class="paragraph-item">
                                <span class="paragraph-number">段落${p.index}</span>
                                ${p.content}
                                ${p.note ? `<span class="paragraph-tag">${p.note}</span>` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>

                <div class="analysis-section">
                    <div class="analysis-section-title">基本信息</div>
                    <div style="display: grid; gap: 8px;">
                        ${Object.entries(result.basicInfo).map(([key, value]) => `
                            <div style="display: flex; gap: 8px; font-size: 0.8125rem;">
                                <span style="color: var(--text-muted); min-width: 70px;">${key}:</span>
                                <span style="color: var(--text-primary);">${value}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    // 显示空分析状态
    displayEmptyAnalysis() {
        this.analysisContent.innerHTML = `
            <div class="empty-state">
                <svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="1">
                    <circle cx="50" cy="50" r="40"/>
                    <path d="M50 30 L50 55 L65 70" stroke-width="3"/>
                    <circle cx="50" cy="50" r="3" fill="currentColor"/>
                </svg>
                <p>点击"分析文档"按钮开始分析</p>
            </div>
        `;
    }

    // 过滤文档
    filterDocuments(keyword) {
        this.renderDocumentList(keyword);
    }

    // 获取状态文本
    getStatusText(status) {
        const statusMap = {
            pending: '待分析',
            analyzing: '分析中...',
            analyzed: '已分析'
        };
        return statusMap[status] || status;
    }

    // 获取分数样式类
    getScoreClass(score) {
        if (score === null) return 'pending';
        if (score >= 80) return 'excellent';
        if (score >= 60) return 'good';
        if (score >= 40) return 'moderate';
        return 'low';
    }

    // 获取分数标签
    getScoreLabel(score) {
        if (score === null) return '待分析';
        if (score >= 80) return '高度相关';
        if (score >= 60) return '中度相关';
        if (score >= 40) return '低度相关';
        return '不相关';
    }

    // 更新统计信息
    updateStats() {
        const analyzed = this.documents.filter(d => d.status === 'analyzed').length;
        const pending = this.documents.length - analyzed;
        const scores = this.documents.filter(d => d.score !== null).map(d => d.score);
        const avg = scores.length > 0
            ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length)
            : '--';

        this.analyzedCount.textContent = analyzed;
        this.pendingCount.textContent = pending;
        this.avgScore.textContent = avg;
    }

    // 检查连接状态
    async checkConnection() {
        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: '检查连接状态' })
            });

            const data = await response.json();
            if (data.response && !data.response.includes('Error')) {
                this.isConnected = true;
                this.updateConnectionStatus(true);
            } else {
                this.updateConnectionStatus(false);
            }
        } catch (error) {
            this.updateConnectionStatus(false);
        }

        // 定期检查连接
        setTimeout(() => this.checkConnection(), 10000);
    }

    // 更新连接状态
    updateConnectionStatus(connected) {
        this.isConnected = connected;
        const statusDot = this.connectionStatus.querySelector('.status-dot');
        const statusText = this.connectionStatus.querySelector('.status-text');

        statusDot.className = 'status-dot ' + (connected ? 'connected' : 'disconnected');
        statusText.textContent = connected ? '已连接' : '连接失败';
    }

    // 发送聊天消息
    async sendChatMessage() {
        const message = this.chatInput.value.trim();
        if (!message || !this.isConnected) return;

        // 添加用户消息
        this.addChatMessage('user', message);
        this.chatInput.value = '';
        this.chatInput.style.height = 'auto';

        // 显示加载状态
        const loadingId = this.showChatLoading();

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: `作为华测导航政策分析助手，回答以下问题：${message}`
                })
            });

            const data = await response.json();
            this.removeChatLoading(loadingId);

            if (data.response) {
                this.addChatMessage('assistant', data.response);
            } else {
                this.addChatMessage('assistant', '抱歉，出现了一些问题。');
            }
        } catch (error) {
            this.removeChatLoading(loadingId);
            this.addChatMessage('assistant', '抱歉，连接失败。请检查服务状态。');
        }
    }

    // 添加聊天消息
    addChatMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${role}`;

        const avatar = document.createElement('div');
        avatar.className = 'ai-avatar';
        avatar.textContent = role === 'user' ? '你' : 'AI';

        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        bubble.innerHTML = this.formatChatContent(content);

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(bubble);
        this.chatMessages.appendChild(messageDiv);

        this.scrollToBottom();
    }

    // 显示聊天加载
    showChatLoading() {
        const loadingId = 'loading-' + Date.now();
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'chat-message assistant';
        loadingDiv.id = loadingId;
        loadingDiv.innerHTML = `
            <div class="ai-avatar">AI</div>
            <div class="message-bubble">
                <div class="loading-dots">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        this.chatMessages.appendChild(loadingDiv);
        this.scrollToBottom();
        return loadingId;
    }

    // 移除聊天加载
    removeChatLoading(loadingId) {
        const loadingDiv = document.getElementById(loadingId);
        if (loadingDiv) loadingDiv.remove();
    }

    // 滚动到底部
    scrollToBottom() {
        this.chatMessages.parentElement.scrollTop = this.chatMessages.parentElement.scrollHeight;
    }

    // 格式化聊天内容
    formatChatContent(text) {
        text = text.replace(/\n/g, '<br>');
        return text;
    }

    // 复制分析结果
    copyAnalysisResult() {
        if (!this.currentDoc || !this.analysisResults[this.currentDoc.id]) {
            this.showNotification('请先选择一个已分析的文档', 'warning');
            return;
        }

        const result = this.analysisResults[this.currentDoc.id];
        const text = this.formatResultForExport(result);

        navigator.clipboard.writeText(text).then(() => {
            this.showNotification('已复制到剪贴板', 'success');
        }).catch(() => {
            this.showNotification('复制失败', 'error');
        });
    }

    // 导出分析结果
    exportAnalysisResult() {
        if (!this.currentDoc || !this.analysisResults[this.currentDoc.id]) {
            this.showNotification('请先选择一个已分析的文档', 'warning');
            return;
        }

        const result = this.analysisResults[this.currentDoc.id];
        const text = this.formatResultForExport(result);

        const blob = new Blob([text], { type: 'text/markdown;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${this.currentDoc.name.replace('.md', '')}_分析结果.md`;
        a.click();
        URL.revokeObjectURL(url);

        this.showNotification('已开始下载', 'success');
    }

    // 格式化导出文本
    formatResultForExport(result) {
        return `# ${this.currentDoc.name} 分析结果

## 基本信息
${Object.entries(result.basicInfo).map(([k, v]) => `- ${k}: ${v}`).join('\n')}

## 全文概要
${result.summary}

## 相关度评估
- **评分**: ${result.score}/100
- **理由**: ${result.scoreReason}

## 相关段落摘取
${result.paragraphs.map(p => `### 段落${p.index}
${p.content}
> 关联说明: ${p.note || '无'}`).join('\n\n')}

---
*导出时间: ${new Date().toLocaleString('zh-CN')}*
`;
    }

    // 处理快捷操作
    handleQuickAction(action) {
        switch (action) {
            case 'analyze':
                if (this.currentDoc) {
                    this.analyzeDocument(this.currentDoc);
                } else {
                    this.showNotification('请先选择一个文档', 'warning');
                }
                break;
            case 'extract':
                this.showNotification('请先选择一个文档并分析', 'info');
                break;
            case 'export':
                this.exportAnalysisResult();
                break;
            case 'clear':
                this.analysisResults = {};
                this.documents.forEach(d => {
                    d.status = 'pending';
                    d.score = null;
                });
                this.renderDocumentList();
                this.updateStats();
                this.displayEmptyAnalysis();
                this.showNotification('已清空所有分析结果', 'success');
                break;
        }
    }

    // 显示通知
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            padding: 12px 20px;
            background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : type === 'warning' ? '#f59e0b' : '#3b82f6'};
            color: #fff;
            border-radius: 8px;
            font-size: 0.875rem;
            z-index: 1000;
            animation: slideIn 0.3s ease;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

// 添加动画样式
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100px); opacity: 0; }
    }
`;
document.head.appendChild(style);

// 初始化应用
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new PolicyAnalyzerApp();
});
