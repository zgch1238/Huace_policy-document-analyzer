// 华测导航政策分析助手 - 主交互逻辑

document.addEventListener('DOMContentLoaded', function() {
    // ===== 状态管理 =====
    const state = {
        messages: [],
        history: [],
        currentChatId: null,  // 当前对话 ID
        currentView: 'chat',
        isConnected: false,
        isLoadingDocs: false,
        isLoadingAnalysis: false,
        isGenerating: false,
        abortController: null
    };

    // ===== DOM 元素 =====
    const elements = {
        // 菜单
        menuItems: document.querySelectorAll('.menu-item'),
        newChatBtn: document.getElementById('newChatBtn'),

        // 视图
        viewPanels: document.querySelectorAll('.view-panel'),
        chatView: document.getElementById('chatView'),
        documentsView: document.getElementById('documentsView'),
        analysisView: document.getElementById('analysisView'),

        // 聊天
        welcomeArea: document.getElementById('welcomeArea'),
        messagesContainer: document.getElementById('messagesContainer'),
        messageInput: document.getElementById('messageInput'),
        sendButton: document.getElementById('sendButton'),
        stopButton: document.getElementById('stopButton'),
        commandBtns: document.querySelectorAll('.command-btn'),

        // 文档
        docGrid: document.getElementById('docGrid'),
        refreshDocs: document.getElementById('refreshDocs'),

        // 分析
        analysisList: document.getElementById('analysisList'),

        // 状态
        connectionStatus: document.getElementById('connectionStatus'),
        analyzeStatus: document.getElementById('analyzeStatus')
    };

    // ===== 初始化 =====
    init();

    function init() {
        bindEvents();
        checkConnection();
        loadHistory();
        loadAnalyzeStatus();
    }

    // ===== 事件绑定 =====
    function bindEvents() {
        // 菜单导航 - 使用事件委托（因为 historyList 内容会动态变化）
        const menuList = document.querySelector('.menu-list');
        menuList.addEventListener('click', (e) => {
            const menuItem = e.target.closest('.menu-item');
            if (!menuItem) return;

            // 视图切换
            if (menuItem.dataset.view) {
                switchView(menuItem.dataset.view);
            }
            // 历史对话加载
            else if (menuItem.dataset.chatId) {
                loadChat(menuItem.dataset.chatId);
            }
        });

        // 新建对话
        elements.newChatBtn.addEventListener('click', newChat);

        // 发送消息
        elements.sendButton.addEventListener('click', sendMessage);
        elements.messageInput.addEventListener('keydown', handleInputKeydown);

        // 自动调整输入框高度
        elements.messageInput.addEventListener('input', autoResizeInput);

        // 快捷指令
        elements.commandBtns.forEach(btn => {
            btn.addEventListener('click', () => executeCommand(btn.dataset.command));
        });

        // 刷新文档
        elements.refreshDocs?.addEventListener('click', loadDocuments);

        // 下载文档按钮
        document.getElementById('downloadDocs')?.addEventListener('click', downloadSelectedDocs);

        // 刷新分析结果
        document.getElementById('refreshAnalysis')?.addEventListener('click', loadAnalysisResults);

        // 下载分析结果按钮
        document.getElementById('downloadAnalysis')?.addEventListener('click', downloadSelectedAnalysis);

        // 删除文档按钮
        document.getElementById('deleteDocs')?.addEventListener('click', deleteSelectedDocs);

        // 删除分析结果按钮
        document.getElementById('deleteAnalysis')?.addEventListener('click', deleteSelectedAnalysis);

        // 停止生成按钮
        elements.stopButton.addEventListener('click', stopGeneration);
    }

    // ===== 视图切换 =====
    function switchView(viewName) {
        // 如果已经在该视图，不重复加载
        if (state.currentView === viewName) return;

        // 更新菜单状态
        const menuItems = document.querySelectorAll('.menu-item');
        menuItems.forEach(item => {
            item.classList.toggle('active', item.dataset.view === viewName);
        });

        // 切换视图
        elements.viewPanels.forEach(panel => {
            panel.classList.toggle('active', panel.id === viewName + 'View');
        });

        state.currentView = viewName;

        // 视图特定初始化（防重复加载）
        if (viewName === 'documents' && !state.isLoadingDocs) {
            loadDocuments();
        } else if (viewName === 'analysis' && !state.isLoadingAnalysis) {
            loadAnalysisResults();
        }
    }

    // ===== 新建对话 =====
    function newChat() {
        // 生成新对话 ID
        state.currentChatId = Date.now();

        // 创建新对话记录
        const chatItem = {
            id: state.currentChatId,
            preview: '新对话',
            messages: []
        };
        state.history.unshift(chatItem);

        // 限制历史数量
        if (state.history.length > 20) {
            state.history.pop();
        }
        renderHistoryList();

        // 清空消息并显示欢迎界面
        clearCurrentChat();
    }

    // ===== 清空当前对话（不创建新记录） =====
    function clearCurrentChat() {
        state.messages = [];
        elements.messagesContainer.innerHTML = '';
        elements.messagesContainer.classList.remove('has-messages');
        elements.chatView.classList.remove('has-messages');
        elements.welcomeArea.style.display = 'flex';

        // 清空输入框
        elements.messageInput.value = '';
        autoResizeInput();
    }

    // ===== 发送消息 =====
    async function sendMessage() {
        const message = elements.messageInput.value.trim();
        if (!message) return;

        // 如果正在生成，忽略发送
        if (state.isGenerating) return;

        // 如果没有当前对话 ID，创建新对话
        if (!state.currentChatId) {
            state.currentChatId = Date.now();
            const chatItem = {
                id: state.currentChatId,
                preview: message.substring(0, 30) + (message.length > 30 ? '...' : ''),
                messages: []
            };
            state.history.unshift(chatItem);
            if (state.history.length > 20) {
                state.history.pop();
            }
            renderHistoryList();
        }

        // 隐藏欢迎区域
        elements.welcomeArea.style.display = 'none';
        elements.chatView.classList.add('has-messages');

        // 添加用户消息
        addMessage('user', message);
        elements.messageInput.value = '';
        autoResizeInput();

        // 设置生成状态
        state.isGenerating = true;
        updateActionButtons();

        // 显示加载状态
        const loadingId = showLoading();

        try {
            // 创建 AbortController 用于停止和超时
            state.abortController = new AbortController();

            // 设置超时（60秒）
            const timeoutId = setTimeout(() => {
                if (state.abortController) {
                    state.abortController.abort('timeout');
                }
            }, 60000);

            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message }),
                signal: state.abortController.signal
            });

            clearTimeout(timeoutId);

            const data = await response.json();
            removeLoading(loadingId);

            if (data.response) {
                addMessage('assistant', data.response);
                // 更新当前对话
                updateCurrentChat();
            } else {
                addMessage('assistant', '抱歉，出现了一些问题。请稍后重试。');
            }
        } catch (error) {
            removeLoading(loadingId);
            if (error.name === 'AbortError') {
                // 用户停止生成或超时
                if (error.message === 'timeout' || error.message.includes('timeout')) {
                    addMessage('assistant', '请求超时（60秒）。请检查 OpenCode 服务是否正常运行，或稍后重试。');
                } else {
                    addMessage('assistant', '已停止生成。');
                }
            } else {
                addMessage('assistant', '抱歉，连接失败。请检查 OpenCode 服务是否运行。错误: ' + error.message);
            }
        } finally {
            // 重置生成状态
            state.isGenerating = false;
            state.abortController = null;
            updateActionButtons();
        }
    }

    // ===== 停止生成 =====
    function stopGeneration() {
        if (state.abortController) {
            state.abortController.abort();
        }
    }

    // ===== 更新按钮状态 =====
    function updateActionButtons() {
        if (state.isGenerating) {
            elements.stopButton.classList.add('visible');
            elements.sendButton.style.display = 'none';
        } else {
            elements.stopButton.classList.remove('visible');
            elements.sendButton.style.display = 'flex';
        }
    }

    // ===== 键盘事件 =====
    function handleInputKeydown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    }

    // ===== 自动调整输入框高度 =====
    function autoResizeInput() {
        elements.messageInput.style.height = 'auto';
        elements.messageInput.style.height = Math.min(elements.messageInput.scrollHeight, 120) + 'px';
    }

    // ===== 添加消息 =====
    function addMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = role === 'user' ? '你' : 'AI';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = formatMessage(content);

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);
        elements.messagesContainer.appendChild(messageDiv);

        // 保存到状态
        state.messages.push({ role, content });

        // 滚动到底部
        scrollToBottom();
    }

    // ===== 显示加载状态 =====
    function showLoading() {
        const loadingId = 'loading-' + Date.now();
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message assistant';
        loadingDiv.id = loadingId;
        loadingDiv.innerHTML = `
            <div class="message-avatar">AI</div>
            <div class="message-content">
                <div class="loading">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        elements.messagesContainer.appendChild(loadingDiv);
        scrollToBottom();
        return loadingId;
    }

    // ===== 移除加载状态 =====
    function removeLoading(loadingId) {
        const loadingDiv = document.getElementById(loadingId);
        if (loadingDiv) loadingDiv.remove();
    }

    // ===== 滚动到底部 =====
    function scrollToBottom() {
        elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
    }

    // ===== 格式化消息（Markdown 支持） =====
    function formatMessage(text) {
        text = escapeHtml(text);

        // 代码块
        text = text.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');

        // 行内代码
        text = text.replace(/`([^`]+)`/g, '<code>$1</code>');

        // 粗体
        text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

        // 斜体
        text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');

        // 删除线
        text = text.replace(/~~([^~]+)~~/g, '<del>$1</del>');

        // 引用
        text = text.replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>');

        // 链接
        text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');

        // 表格
        text = text.replace(/\|(.+)\|/g, function(match) {
            if (match.includes('---')) return '';
            const cells = match.split('|').filter(c => c.trim());
            if (cells[0] === '') cells.shift();
            if (cells[cells.length - 1] === '') cells.pop();
            return '<tr>' + cells.map(c => '<td>' + c.trim() + '</td>').join('') + '</tr>';
        });

        // 标题
        text = text.replace(/^### (.+)$/gm, '<h3>$1</h3>');
        text = text.replace(/^## (.+)$/gm, '<h2>$1</h2>');
        text = text.replace(/^# (.+)$/gm, '<h1>$1</h1>');

        // 无序列表
        text = text.replace(/^- (.+)$/gm, '<li>$1</li>');
        text = text.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');

        // 有序列表
        text = text.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');

        // 段落
        text = text.replace(/\n\n/g, '</p><p>');
        text = '<p>' + text + '</p>';

        // 换行
        text = text.replace(/\n/g, '<br>');

        return text;
    }

    // ===== HTML 转义 =====
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ===== 执行快捷指令 =====
    function executeCommand(command) {
        elements.messageInput.value = command;
        autoResizeInput();
        elements.messageInput.focus();
    }

    // ===== 连接状态 =====
    async function checkConnection() {
        try {
            const response = await fetch('/health');
            const data = await response.json();
            updateConnectionStatus(data.opencode === 'connected');
        } catch (error) {
            updateConnectionStatus(false);
        }

        // 定期检查（间隔 60 秒）
        setTimeout(checkConnection, 60000);
    }

    function updateConnectionStatus(connected) {
        state.isConnected = connected;
        const statusDot = elements.connectionStatus.querySelector('.status-dot');
        const statusText = elements.connectionStatus.querySelector('.status-text');

        statusDot.className = 'status-dot ' + (connected ? 'connected' : 'disconnected');
        statusText.textContent = connected ? '已连接' : '连接失败';
    }

    // ===== 历史记录管理 =====

    // 更新当前对话（发送消息后调用）
    function updateCurrentChat() {
        const chat = state.history.find(h => h.id === state.currentChatId);
        if (chat) {
            chat.messages = [...state.messages];
            // 更新预览为最后一条用户消息
            const lastUserMsg = [...state.messages].reverse().find(m => m.role === 'user');
            if (lastUserMsg) {
                chat.preview = lastUserMsg.content.substring(0, 30) + (lastUserMsg.content.length > 30 ? '...' : '');
            }
            renderHistoryList();
        }
    }

    function loadHistory() {
        renderHistoryList();
    }

    function renderHistoryList() {
        const historyList = document.getElementById('historyList');
        const currentChat = historyList.querySelector('[data-view="chat"]');

        // 保留当前对话项
        let html = currentChat.outerHTML;

        // 添加历史记录
        state.history.forEach(item => {
            html += `
                <li class="menu-item history-item" data-chat-id="${item.id}">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
                    </svg>
                    <span class="history-title">${escapeHtml(item.preview)}</span>
                    <button class="history-delete-btn" data-chat-id="${item.id}" title="删除对话">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="18" y1="6" x2="6" y2="18"/>
                            <line x1="6" y1="6" x2="18" y2="18"/>
                        </svg>
                    </button>
                </li>
            `;
        });

        historyList.innerHTML = html;

        // 绑定删除按钮事件
        historyList.querySelectorAll('.history-delete-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const chatId = parseInt(btn.dataset.chatId);
                deleteChat(chatId);
            });
        });
    }

    // 删除对话
    function deleteChat(chatId) {
        const chat = state.history.find(h => h.id === chatId);
        if (!chat) return;

        if (confirm(`确定要删除对话 "${chat.preview}" 吗？`)) {
            // 从历史中删除
            state.history = state.history.filter(h => h.id !== chatId);

            // 如果删除的是当前对话，清空消息但不创建新记录
            if (state.currentChatId === chatId) {
                state.currentChatId = null;
                clearCurrentChat();
            }

            // 重新渲染历史列表
            renderHistoryList();
        }
    }

    function loadChat(chatId) {
        const chat = state.history.find(h => h.id === parseInt(chatId));
        if (!chat) return;

        // 设置当前对话 ID
        state.currentChatId = parseInt(chatId);

        // 清空当前消息
        state.messages = [];
        elements.messagesContainer.innerHTML = '';

        // 加载历史消息
        chat.messages.forEach(msg => {
            addMessage(msg.role, msg.content);
        });

        // 显示消息区域
        elements.welcomeArea.style.display = 'none';
        elements.chatView.classList.add('has-messages');
    }

    // ===== 文档管理 =====
    // 选中的文件列表
    let selectedDocs = new Set();

    async function loadDocuments() {
        // 防止重复加载
        if (state.isLoadingDocs) return;

        state.isLoadingDocs = true;
        selectedDocs.clear();
        updateDownloadButton('docs');
        updateDeleteButton('docs');
        elements.docGrid.innerHTML = '<div style="text-align:center;color:#737373;padding:40px;">加载中...</div>';

        try {
            // 直接调用 API，不经过 AI（毫秒级响应）
            const response = await fetch('/api/documents');
            const data = await response.json();

            if (data.documents && data.documents.length > 0) {
                renderDocumentList(data.documents);
            } else {
                const msg = data.message || '未找到政策文档';
                elements.docGrid.innerHTML = `<div style="text-align:center;color:#737373;padding:40px;">${msg}</div>`;
            }
        } catch (error) {
            console.error('加载文档列表失败:', error);
            elements.docGrid.innerHTML = '<div style="text-align:center;color:#737373;padding:40px;">加载失败，请重试</div>';
        } finally {
            state.isLoadingDocs = false;
        }
    }

    function renderDocumentList(folderData) {
        // folderData 现在是 folders 数组 [{name: "文件夹名", files: ["文件1.md", "文件2.md"]}]
        let html = `
            <div class="file-list-header">
                <div class="col-checkbox">
                    <div class="checkbox-wrapper">
                        <input type="checkbox" id="selectAllDocs" title="全选">
                    </div>
                </div>
                <span class="col-name">文件名</span>
            </div>
        `;

        // 按文件夹分组显示
        folderData.forEach(folder => {
            // 添加文件夹标题（可选择整个文件夹）
            html += `
                <div class="folder-group-title" data-folder="${escapeHtml(folder.name)}">
                    <div class="checkbox-wrapper">
                        <input type="checkbox" class="folder-checkbox" data-folder="${escapeHtml(folder.name)}">
                    </div>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/>
                    </svg>
                    <span>${escapeHtml(folder.name)}</span>
                    <span class="folder-count">(${folder.files.length}个文件)</span>
                </div>
            `;

            // 添加该文件夹下的文件
            folder.files.forEach((fileName) => {
                const fullPath = folder.name === '根目录' ? fileName : `${folder.name}/${fileName}`;
                html += `
                    <div class="doc-card" data-doc="${fileName}" data-folder="${folder.name}" data-path="${fullPath}">
                        <div class="doc-checkbox">
                            <div class="checkbox-wrapper">
                                <input type="checkbox" class="doc-checkbox-input" data-path="${fullPath}">
                            </div>
                        </div>
                        <div class="doc-icon">📄</div>
                        <div class="doc-info">
                            <div class="doc-card-title">${escapeHtml(fileName)}</div>
                            <div class="doc-card-meta">${escapeHtml(folder.name)}</div>
                        </div>
                    </div>
                `;
            });
        });

        elements.docGrid.innerHTML = html;

        // 绑定全选复选框
        document.getElementById('selectAllDocs')?.addEventListener('change', (e) => {
            const checked = e.target.checked;
            document.querySelectorAll('.doc-checkbox-input').forEach(cb => {
                cb.checked = checked;
                const path = cb.dataset.path;
                if (checked) {
                    selectedDocs.add(path);
                } else {
                    selectedDocs.delete(path);
                }
            });
            // 更新文件夹复选框状态
            document.querySelectorAll('.folder-checkbox').forEach(cb => {
                cb.checked = checked;
            });
            updateDownloadButton('docs');
        });

        // 绑定文件夹复选框
        document.querySelectorAll('.folder-checkbox').forEach(cb => {
            cb.addEventListener('change', (e) => {
                const folderName = e.target.dataset.folder;
                const checked = e.target.checked;
                document.querySelectorAll(`.doc-card[data-folder="${folderName}"] .doc-checkbox-input`).forEach(docCb => {
                    docCb.checked = checked;
                    const path = docCb.dataset.path;
                    if (checked) {
                        selectedDocs.add(path);
                    } else {
                        selectedDocs.delete(path);
                    }
                });
                updateDownloadButton('docs');
                updateSelectAllState('docs');
            });
        });

        // 绑定文件复选框
        document.querySelectorAll('.doc-checkbox-input').forEach(cb => {
            cb.addEventListener('change', (e) => {
                e.stopPropagation();
                const path = cb.dataset.path;
                if (cb.checked) {
                    selectedDocs.add(path);
                } else {
                    selectedDocs.delete(path);
                }
                updateDownloadButton('docs');
                updateSelectAllState('docs');
                updateFolderCheckboxState(cb);
            });
        });

        // 绑定点击事件（跳转到聊天）
        elements.docGrid.querySelectorAll('.doc-card').forEach(card => {
            card.addEventListener('click', (e) => {
                // 如果点击的是复选框，不触发跳转
                if (e.target.type === 'checkbox' || e.target.closest('.checkbox-wrapper')) {
                    return;
                }
                const folder = card.dataset.folder || '';
                const docName = folder ? `${folder}/${card.dataset.doc}` : card.dataset.doc;
                elements.messageInput.value = `分析文档：${docName}`;
                autoResizeInput();
                switchView('chat');
            });
        });
    }

    function updateSelectAllState(type) {
        const totalDocs = document.querySelectorAll('.doc-checkbox-input').length;
        const selectedCount = selectedDocs.size;
        const selectAll = document.getElementById('selectAllDocs');
        if (selectAll) {
            selectAll.checked = selectedCount > 0 && selectedCount === totalDocs;
            selectAll.indeterminate = selectedCount > 0 && selectedCount < totalDocs;
        }
    }

    function updateFolderCheckboxState(changedCb) {
        // 找到该文件所属的文件夹
        const card = changedCb.closest('.doc-card');
        const folderName = card.dataset.folder;
        const folderCheckboxes = document.querySelectorAll(`.doc-card[data-folder="${folderName}"] .doc-checkbox-input`);
        const checkedCount = Array.from(folderCheckboxes).filter(cb => cb.checked).length;
        const folderCb = document.querySelector(`.folder-checkbox[data-folder="${folderName}"]`);
        if (folderCb) {
            folderCb.checked = checkedCount === folderCheckboxes.length;
            folderCb.indeterminate = checkedCount > 0 && checkedCount < folderCheckboxes.length;
        }
    }

    function updateDownloadButton(type) {
        const count = type === 'docs' ? selectedDocs.size : selectedAnalysis.size;
        const downloadBtn = type === 'docs' ? document.getElementById('downloadDocs') : document.getElementById('downloadAnalysis');
        const countSpan = type === 'docs' ? document.getElementById('selectedDocCount') : document.getElementById('selectedAnalysisCount');
        const deleteBtn = type === 'docs' ? document.getElementById('deleteDocs') : document.getElementById('deleteAnalysis');

        if (downloadBtn && countSpan) {
            countSpan.textContent = count;
            downloadBtn.disabled = count === 0;
        }
        if (deleteBtn) {
            deleteBtn.disabled = count === 0;
        }
    }

    // 下载选中的文档（逐个下载）
    async function downloadSelectedDocs() {
        if (selectedDocs.size === 0) return;

        const downloadBtn = document.getElementById('downloadDocs');
        const originalText = downloadBtn.innerHTML;
        downloadBtn.disabled = true;
        downloadBtn.innerHTML = '<span>下载中...</span>';

        // 遍历所有选中的文件，逐个下载
        const files = Array.from(selectedDocs);
        for (let i = 0; i < files.length; i++) {
            const filePath = files[i];
            downloadBtn.innerHTML = `<span>下载中 (${i + 1}/${files.length})</span>`;

            try {
                const response = await fetch('/api/download-documents', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ files: [filePath] })
                });

                const data = await response.json();
                if (data.success) {
                    downloadFile(data.fileName, data.content);
                } else {
                    console.error(`下载失败: ${filePath}`, data.message);
                }
            } catch (error) {
                console.error(`下载失败: ${filePath}`, error);
            }

            // 添加小延迟，避免浏览器阻止多个下载
            await new Promise(resolve => setTimeout(resolve, 300));
        }

        downloadBtn.innerHTML = originalText;
        downloadBtn.disabled = selectedDocs.size === 0;
    }

    function downloadFile(fileName, content) {
        const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    // 更新删除按钮状态
    function updateDeleteButton(type) {
        const count = type === 'docs' ? selectedDocs.size : selectedAnalysis.size;
        const deleteBtn = type === 'docs' ? document.getElementById('deleteDocs') : document.getElementById('deleteAnalysis');
        if (deleteBtn) {
            deleteBtn.disabled = count === 0;
        }
    }

    // 确认删除对话框
    function confirmDelete(type, count) {
        const typeName = type === 'docs' ? '政策文档' : '分析结果';
        const msg = `确定要删除选中的 ${count} 个${typeName}吗？\n\n此操作不可恢复！`;
        return confirm(msg);
    }

    // 删除选中的文档
    async function deleteSelectedDocs() {
        if (selectedDocs.size === 0) return;
        const count = selectedDocs.size;

        // 确认删除
        if (!confirmDelete('docs', count)) return;

        const deleteBtn = document.getElementById('deleteDocs');
        const originalText = deleteBtn.innerHTML;
        deleteBtn.disabled = true;
        deleteBtn.innerHTML = '<span>删除中...</span>';

        try {
            const response = await fetch('/api/delete-documents', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ files: Array.from(selectedDocs) })
            });

            const data = await response.json();
            if (data.success) {
                alert(data.message);
                // 清空选择并重新加载
                selectedDocs.clear();
                updateDownloadButton('docs');
                updateDeleteButton('docs');
                loadDocuments();
            } else {
                alert(data.message || '删除失败');
            }
        } catch (error) {
            console.error('删除文档失败:', error);
            alert('删除失败，请重试');
        } finally {
            deleteBtn.innerHTML = originalText;
            deleteBtn.disabled = selectedDocs.size === 0;
        }
    }

    // 删除选中的分析结果
    async function deleteSelectedAnalysis() {
        if (selectedAnalysis.size === 0) return;
        const count = selectedAnalysis.size;

        // 确认删除
        if (!confirmDelete('analysis', count)) return;

        const deleteBtn = document.getElementById('deleteAnalysis');
        const originalText = deleteBtn.innerHTML;
        deleteBtn.disabled = true;
        deleteBtn.innerHTML = '<span>删除中...</span>';

        try {
            const response = await fetch('/api/delete-analysis', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ files: Array.from(selectedAnalysis) })
            });

            const data = await response.json();
            if (data.success) {
                alert(data.message);
                // 清空选择并重新加载
                selectedAnalysis.clear();
                updateDownloadButton('analysis');
                updateDeleteButton('analysis');
                loadAnalysisResults();
            } else {
                alert(data.message || '删除失败');
            }
        } catch (error) {
            console.error('删除分析结果失败:', error);
            alert('删除失败，请重试');
        } finally {
            deleteBtn.innerHTML = originalText;
            deleteBtn.disabled = selectedAnalysis.size === 0;
        }
    }

    // ===== 分析结果 =====
    // 选中的分析结果列表
    let selectedAnalysis = new Set();

    async function loadAnalysisResults() {
        // 防止重复加载
        if (state.isLoadingAnalysis) return;

        state.isLoadingAnalysis = true;
        selectedAnalysis.clear();
        updateDownloadButton('analysis');
        updateDeleteButton('analysis');
        elements.analysisList.innerHTML = '<div style="text-align:center;color:#737373;padding:40px;">加载中...</div>';

        try {
            const response = await fetch('/api/analysis-results');
            const data = await response.json();

            if (data.results && data.results.length > 0) {
                renderAnalysisList(data.results);
            } else {
                const msg = data.message || '暂无分析结果';
                elements.analysisList.innerHTML = `<div style="text-align:center;color:#737373;padding:40px;">${msg}</div>`;
            }
        } catch (error) {
            console.error('加载分析结果列表失败:', error);
            elements.analysisList.innerHTML = '<div style="text-align:center;color:#737373;padding:40px;">加载失败，请重试</div>';
        } finally {
            state.isLoadingAnalysis = false;
        }
    }

    function renderAnalysisList(folderData) {
        let html = `
            <div class="file-list-header">
                <div class="col-checkbox">
                    <div class="checkbox-wrapper">
                        <input type="checkbox" id="selectAllAnalysis" title="全选">
                    </div>
                </div>
                <span class="col-name">文件名</span>
            </div>
        `;

        // 按文件夹分组显示
        folderData.forEach(folder => {
            // 添加文件夹标题
            html += `
                <div class="folder-group-title" data-folder="${escapeHtml(folder.name)}">
                    <div class="checkbox-wrapper">
                        <input type="checkbox" class="folder-checkbox" data-folder="${escapeHtml(folder.name)}">
                    </div>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/>
                    </svg>
                    <span>${escapeHtml(folder.name)}</span>
                    <span class="folder-count">(${folder.files.length}个文件)</span>
                </div>
            `;

            // 添加该文件夹下的文件
            folder.files.forEach(fileName => {
                const fullPath = folder.name === '根目录' ? fileName : `${folder.name}/${fileName}`;
                html += `
                    <div class="doc-card" data-result="${fileName}" data-folder="${folder.name}" data-path="${fullPath}">
                        <div class="doc-checkbox">
                            <div class="checkbox-wrapper">
                                <input type="checkbox" class="analysis-checkbox-input" data-path="${fullPath}">
                            </div>
                        </div>
                        <div class="doc-icon">📊</div>
                        <div class="doc-info">
                            <div class="doc-card-title">${escapeHtml(fileName)}</div>
                            <div class="doc-card-meta">${escapeHtml(folder.name)}</div>
                        </div>
                    </div>
                `;
            });
        });

        elements.analysisList.innerHTML = html;

        // 绑定全选复选框
        document.getElementById('selectAllAnalysis')?.addEventListener('change', (e) => {
            const checked = e.target.checked;
            document.querySelectorAll('.analysis-checkbox-input').forEach(cb => {
                cb.checked = checked;
                const path = cb.dataset.path;
                if (checked) {
                    selectedAnalysis.add(path);
                } else {
                    selectedAnalysis.delete(path);
                }
            });
            document.querySelectorAll('#analysisView .folder-checkbox').forEach(cb => {
                cb.checked = checked;
            });
            updateDownloadButton('analysis');
        });

        // 绑定文件夹复选框
        document.querySelectorAll('#analysisView .folder-checkbox').forEach(cb => {
            cb.addEventListener('change', (e) => {
                const folderName = e.target.dataset.folder;
                const checked = e.target.checked;
                document.querySelectorAll(`#analysisList .doc-card[data-folder="${folderName}"] .analysis-checkbox-input`).forEach(docCb => {
                    docCb.checked = checked;
                    const path = docCb.dataset.path;
                    if (checked) {
                        selectedAnalysis.add(path);
                    } else {
                        selectedAnalysis.delete(path);
                    }
                });
                updateDownloadButton('analysis');
                updateAnalysisSelectAllState();
            });
        });

        // 绑定文件复选框
        document.querySelectorAll('.analysis-checkbox-input').forEach(cb => {
            cb.addEventListener('change', (e) => {
                e.stopPropagation();
                const path = cb.dataset.path;
                if (cb.checked) {
                    selectedAnalysis.add(path);
                } else {
                    selectedAnalysis.delete(path);
                }
                updateDownloadButton('analysis');
                updateAnalysisSelectAllState();
                updateAnalysisFolderCheckboxState(cb);
            });
        });

        // 绑定点击事件
        elements.analysisList.querySelectorAll('.doc-card').forEach(card => {
            card.addEventListener('click', (e) => {
                if (e.target.type === 'checkbox' || e.target.closest('.checkbox-wrapper')) {
                    return;
                }
                const folder = card.dataset.folder || '';
                const resultName = folder ? `${folder}/${card.dataset.result}` : card.dataset.result;
                elements.messageInput.value = `查看分析结果：${resultName}`;
                autoResizeInput();
                switchView('chat');
            });
        });
    }

    function updateAnalysisSelectAllState() {
        const total = document.querySelectorAll('.analysis-checkbox-input').length;
        const selected = selectedAnalysis.size;
        const selectAll = document.getElementById('selectAllAnalysis');
        if (selectAll) {
            selectAll.checked = selected > 0 && selected === total;
            selectAll.indeterminate = selected > 0 && selected < total;
        }
    }

    function updateAnalysisFolderCheckboxState(changedCb) {
        const card = changedCb.closest('.doc-card');
        const folderName = card.dataset.folder;
        const checkboxes = document.querySelectorAll(`#analysisList .doc-card[data-folder="${folderName}"] .analysis-checkbox-input`);
        const checked = Array.from(checkboxes).filter(cb => cb.checked).length;
        const folderCb = document.querySelector(`#analysisView .folder-checkbox[data-folder="${folderName}"]`);
        if (folderCb) {
            folderCb.checked = checked === checkboxes.length;
            folderCb.indeterminate = checked > 0 && checked < checkboxes.length;
        }
    }

    // 下载选中的分析结果（逐个下载）
    async function downloadSelectedAnalysis() {
        if (selectedAnalysis.size === 0) return;

        const downloadBtn = document.getElementById('downloadAnalysis');
        const originalText = downloadBtn.innerHTML;
        downloadBtn.disabled = true;
        downloadBtn.innerHTML = '<span>下载中...</span>';

        // 遍历所有选中的文件，逐个下载
        const files = Array.from(selectedAnalysis);
        for (let i = 0; i < files.length; i++) {
            const filePath = files[i];
            downloadBtn.innerHTML = `<span>下载中 (${i + 1}/${files.length})</span>`;

            try {
                const response = await fetch('/api/download-analysis', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ files: [filePath] })
                });

                const data = await response.json();
                if (data.success) {
                    downloadFile(data.fileName, data.content);
                } else {
                    console.error(`下载失败: ${filePath}`, data.message);
                }
            } catch (error) {
                console.error(`下载失败: ${filePath}`, error);
            }

            // 添加小延迟，避免浏览器阻止多个下载
            await new Promise(resolve => setTimeout(resolve, 300));
        }

        downloadBtn.innerHTML = originalText;
        downloadBtn.disabled = selectedAnalysis.size === 0;
    }

    // ===== 加载分析状态 =====
    async function loadAnalyzeStatus() {
        const analyzeStatusEl = document.getElementById('analyzeStatus');
        if (!analyzeStatusEl) return;

        try {
            const response = await fetch('/api/analyze-status');
            const data = await response.json();

            if (data.success) {
                const { status } = data;

                let icon = '';
                let text = '';
                let statusClass = '';

                if (status === 'success') {
                    icon = '✅';
                    text = '已自动分析成功';
                    statusClass = 'success';
                } else if (status === 'session_failed') {
                    icon = '❌';
                    text = '已自动分析失败';
                    statusClass = 'failed';
                } else {
                    icon = '⏳';
                    text = '等待自动分析';
                    statusClass = 'pending';
                }

                analyzeStatusEl.innerHTML = `
                    <span class="analyze-icon">${icon}</span>
                    <span class="analyze-text ${statusClass}">${text}</span>
                    <button class="manual-analyze-btn" id="manualAnalyzeBtn" title="手动执行分析">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polygon points="5 3 19 12 5 21 5 3"/>
                        </svg>
                    </button>
                `;

                // 绑定手动分析按钮事件
                document.getElementById('manualAnalyzeBtn')?.addEventListener('click', triggerManualAnalyze);
            }
        } catch (error) {
            console.error('加载分析状态失败:', error);
            document.getElementById('analyzeStatus').innerHTML = `
                <span class="analyze-icon">❌</span>
                <span class="analyze-text">状态加载失败</span>
                <button class="manual-analyze-btn" id="manualAnalyzeBtn" title="手动执行分析">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="5 3 19 12 5 21 5 3"/>
                    </svg>
                </button>
            `;
            document.getElementById('manualAnalyzeBtn')?.addEventListener('click', triggerManualAnalyze);
        }
    }

    // ===== 手动触发分析 =====
    async function triggerManualAnalyze() {
        const btn = document.getElementById('manualAnalyzeBtn');
        if (!btn || btn.classList.contains('loading')) return;

        if (!confirm('确定要手动执行政策文档分析吗？\n这将分析所有政策文档并生成分析结果。')) {
            return;
        }

        // 显示加载状态
        btn.classList.add('loading');
        btn.title = '分析执行中...';

        const analyzeStatusEl = document.getElementById('analyzeStatus');
        const analyzeText = analyzeStatusEl.querySelector('.analyze-text');
        if (analyzeText) {
            analyzeText.textContent = '分析执行中...';
            analyzeText.className = 'analyze-text pending';
        }

        try {
            const response = await fetch('/api/trigger-analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            const data = await response.json();

            if (data.success) {
                // 重新加载分析状态
                await loadAnalyzeStatus();
                alert(`分析完成！成功: ${data.successCount}, 失败: ${data.failedCount}`);
            } else {
                alert(data.message || '分析失败，请重试');
                loadAnalyzeStatus();
            }
        } catch (error) {
            console.error('手动分析失败:', error);
            alert('分析失败，请重试');
            loadAnalyzeStatus();
        } finally {
            btn.classList.remove('loading');
            btn.title = '手动执行分析';
        }
    }

});
