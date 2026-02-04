<script setup>
import { ref, onMounted, inject, computed } from 'vue'
import { api } from '../utils/api'

const currentUser = inject('currentUser')

// 当前路径和历史记录
const currentPath = ref('')  // 当前目录相对路径（analyze_result 或 policy_document_word 下的路径）
const history = ref([])      // 导航历史
const historyIndex = ref(-1) // 当前历史位置

// 数据
const folders = ref([])
const files = ref([])
const loading = ref(false)
const selectedItems = ref(new Set())
const searchKeyword = ref('')
const minScore = ref(null)

// 分析状态
const analyzeStatus = ref({ status: 'pending', text: '等待自动分析' })
const isAnalyzing = ref(localStorage.getItem('isAnalyzing') === 'true')

// 切换显示模式：false=分析结果，true=高亮文档
const showHighlight = ref(false)

const emit = defineEmits(['view-result'])

const isAdmin = computed(() => {
  return currentUser.value && currentUser.value.role === 'admin'
})

// 当前目录基础路径
const baseDir = computed(() => showHighlight.value ? 'policy_document_word' : 'analyze_result')

// 面包屑导航
const breadcrumbs = computed(() => {
  const parts = currentPath.value.split('/').filter(p => p)
  const result = [{ name: showHighlight.value ? '高亮文档' : '分析结果', path: '' }]
  let path = ''
  parts.forEach(part => {
    path = path ? `${path}/${part}` : part
    result.push({ name: part, path })
  })
  return result
})

// 能否后退/前进
const canGoBack = computed(() => historyIndex.value >= 0 && currentPath.value !== '')
const canGoForward = computed(() => historyIndex.value < history.value.length - 1)

// 加载目录内容
const loadDirectory = async (path = '', keyword = '', score = null) => {
  loading.value = true
  try {
    const data = await api.listAnalysisDir(baseDir.value, path, keyword, score)
    // 检查data是否有效
    if (data && data.success) {
      folders.value = data.folders || []
      files.value = data.files || []
    } else {
      folders.value = []
      files.value = []
    }
  } catch (error) {
    console.error('加载目录失败:', error)
    folders.value = []
    files.value = []
  } finally {
    loading.value = false
  }
}

// 进入文件夹
const enterFolder = (folderName) => {
  const newPath = currentPath.value
    ? `${currentPath.value}/${folderName}`
    : folderName

  addToHistory(currentPath.value)
  currentPath.value = newPath
  selectedItems.value.clear()
  loadDirectory(newPath, searchKeyword.value, minScore.value)
}

// 返回上一级
const goBack = () => {
  if (!canGoBack.value) return
  historyIndex.value--
  const newPath = history.value[historyIndex.value]
  currentPath.value = newPath
  selectedItems.value.clear()
  loadDirectory(newPath, searchKeyword.value, minScore.value)
}

// 前进
const goForward = () => {
  if (!canGoForward.value) return
  historyIndex.value++
  const newPath = history.value[historyIndex.value]
  currentPath.value = newPath
  selectedItems.value.clear()
  loadDirectory(newPath, searchKeyword.value, minScore.value)
}

// 跳转到面包屑路径
const navigateTo = (path) => {
  addToHistory(currentPath.value)
  currentPath.value = path
  historyIndex.value = history.value.length - 1
  selectedItems.value.clear()
  loadDirectory(path, searchKeyword.value, minScore.value)
}

// 添加到历史记录
const addToHistory = (path) => {
  if (historyIndex.value < history.value.length - 1) {
    history.value = history.value.slice(0, historyIndex.value + 1)
  }
  if (history.value.length > 0 && history.value[history.value.length - 1] === path) {
    return
  }
  history.value.push(path)
  historyIndex.value = history.value.length - 1
}

// 切换显示模式
const toggleShowMode = async () => {
  showHighlight.value = !showHighlight.value
  currentPath.value = ''
  history.value = []
  historyIndex.value = -1
  selectedItems.value.clear()
  searchKeyword.value = ''
  minScore.value = null
  await loadDirectory()
  await loadStatus()
}

// 刷新
const handleRefresh = () => {
  loadDirectory(currentPath.value, searchKeyword.value, minScore.value)
}

// 搜索
const handleSearch = () => {
  const timer = setTimeout(() => {
    loadDirectory(currentPath.value, searchKeyword.value, minScore.value)
  }, 300)
  return () => clearTimeout(timer)
}

// 清除筛选
const clearFilters = () => {
  searchKeyword.value = ''
  minScore.value = null
  loadDirectory(currentPath.value, '', null)
}

// 文件选择
const toggleItem = (itemName) => {
  if (selectedItems.value.has(itemName)) {
    selectedItems.value.delete(itemName)
  } else {
    selectedItems.value.add(itemName)
  }
}

const toggleAll = () => {
  const totalItems = folders.value.length + files.value.length
  if (selectedItems.value.size === totalItems) {
    selectedItems.value.clear()
  } else {
    folders.value.forEach(f => selectedItems.value.add(f))
    files.value.forEach(f => selectedItems.value.add(f))
  }
}

// 获取文件完整路径
const getFilePath = (fileName) => {
  return currentPath.value
    ? `${currentPath.value}/${fileName}`
    : fileName
}

// 查看文件
const viewFile = (fileName) => {
  const prefix = showHighlight.value ? 'highlight:' : 'result:'
  const resultName = prefix + getFilePath(fileName)
  emit('view-result', resultName)
}

// 双击处理
const handleItemDoubleClick = (item, type) => {
  if (type === 'folder') {
    enterFolder(item)
  } else {
    viewFile(item)
  }
}

// 分数相关
const getScoreClass = (fileName) => {
  const score = getScore(fileName)
  if (score >= 90) return 'score-high'
  if (score >= 80) return 'score-medium'
  if (score >= 70) return 'score-low'
  return 'score-lower'
}

const getScore = (fileName) => {
  const match = fileName.match(/_(\d+\.?\d*)\.(docx|md)$/)
  return match ? parseFloat(match[1]) : null
}

// 下载
const handleDownload = async () => {
  const fileList = Array.from(selectedItems.value).map(getFilePath)
  if (fileList.length === 0) return

  for (const filePath of fileList) {
    try {
      const result = await api.downloadAnalysis([filePath], baseDir.value)
      if (result.success) {
        downloadFile(result.fileName, result.content, result.isBinary)
      }
    } catch (error) {
      console.error(`下载失败: ${filePath}`, error)
    }
    await new Promise(resolve => setTimeout(resolve, 300))
  }
}

const downloadFile = (fileName, content, isBinary = false) => {
  let blob
  if (isBinary && content) {
    const binaryData = atob(content)
    const bytes = new Uint8Array(binaryData.length)
    for (let i = 0; i < binaryData.length; i++) {
      bytes[i] = binaryData.charCodeAt(i)
    }
    blob = new Blob([bytes], {
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    })
  } else {
    blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
  }
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = fileName
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

// 删除
const handleDelete = async () => {
  const fileList = Array.from(selectedItems.value).map(getFilePath)
  if (fileList.length === 0) return

  if (!confirm(`确定要删除这 ${fileList.length} 个文件吗？此操作不可恢复。`)) {
    return
  }

  try {
    const result = await api.deleteAnalysis(fileList, currentUser.value.username)
    if (result.success) {
      alert('删除成功')
      selectedItems.value.clear()
      loadDirectory(currentPath.value)
    } else {
      alert(result.message || '删除失败')
    }
  } catch (error) {
    console.error('删除失败:', error)
    alert('删除失败，请重试')
  }
}

// 手动触发分析
const handleAnalyze = async () => {
  if (isAnalyzing.value) return
  if (!confirm('确定要手动执行政策文档分析吗？')) return

  isAnalyzing.value = true
  localStorage.setItem('isAnalyzing', 'true')

  try {
    const data = await api.triggerAnalyze()
    if (data.success) {
      await loadDirectory()
      await loadStatus()
      alert(data.message || '分析完成')
    } else {
      alert(data.message || '分析失败')
    }
  } catch (error) {
    console.error('分析失败:', error)
    alert('分析失败，请重试')
  } finally {
    isAnalyzing.value = false
    localStorage.removeItem('isAnalyzing')
  }
}

// 加载分析状态
const loadStatus = async () => {
  try {
    const data = await api.getAnalyzeStatus()
    if (data.success) {
      analyzeStatus.value = { status: data.status, text: data.text }
    }
  } catch (error) {
    console.error('加载状态失败:', error)
  }
}

onMounted(async () => {
  await loadDirectory()
  await loadStatus()
})
</script>

<template>
  <div class="analysis-view">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <div class="toggle-group">
          <button
            class="toggle-btn"
            :class="{ active: !showHighlight }"
            @click="showHighlight && toggleShowMode()"
            :disabled="!showHighlight"
          >
            分析结果
          </button>
          <button
            class="toggle-btn"
            :class="{ active: showHighlight }"
            @click="!showHighlight && toggleShowMode()"
            :disabled="showHighlight"
          >
            高亮文档
          </button>
        </div>
        <span class="status-badge" :class="analyzeStatus.status">
          {{ analyzeStatus.text }}
        </span>
      </div>
      <div class="toolbar-right">
        <!-- 筛选器 -->
        <div class="filter-group">
          <input
            v-model="searchKeyword"
            @input="handleSearch()"
            type="text"
            placeholder="搜索..."
            class="filter-input"
          />
          <select v-model="minScore" @change="handleSearch()" class="filter-select">
            <option :value="null">所有分数</option>
            <option :value="90">90分以上</option>
            <option :value="80">80分以上</option>
            <option :value="70">70分以上</option>
            <option :value="60">60分以上</option>
          </select>
          <button v-if="searchKeyword || minScore" @click="clearFilters" class="filter-clear">
            清除
          </button>
        </div>
        <button
          class="tool-btn"
          @click="handleAnalyze"
          :disabled="isAnalyzing || showHighlight"
          title="手动分析"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="5 3 19 12 5 21 5 3"/>
          </svg>
          <span>{{ isAnalyzing ? '分析中...' : '手动分析' }}</span>
        </button>
        <button class="tool-btn" @click="handleRefresh" :disabled="loading" title="刷新">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
            <path d="M3 3v5h5"/>
            <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/>
            <path d="M16 16h5v5"/>
          </svg>
        </button>
        <button
          class="tool-btn primary"
          @click="handleDownload"
          :disabled="selectedItems.size === 0"
          title="下载"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7 10 12 15 17 10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          <span>下载 {{ selectedItems.size > 0 ? `(${selectedItems.size})` : '' }}</span>
        </button>
        <button
          v-if="isAdmin"
          class="tool-btn danger"
          @click="handleDelete"
          :disabled="selectedItems.size === 0"
          title="删除"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 6h18"/>
            <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>
            <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
          </svg>
          <span>删除 {{ selectedItems.size > 0 ? `(${selectedItems.size})` : '' }}</span>
        </button>
      </div>
    </div>

    <!-- 路径导航栏 -->
    <div class="path-bar">
      <div class="nav-buttons">
        <button
          class="nav-btn"
          :disabled="!canGoBack"
          @click="goBack"
          title="后退"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
        </button>
        <button
          class="nav-btn"
          :disabled="!canGoForward"
          @click="goForward"
          title="前进"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="9 18 15 12 9 6"/>
          </svg>
        </button>
      </div>
      <div class="breadcrumbs">
        <template v-for="(crumb, index) in breadcrumbs" :key="index">
          <span
            class="crumb"
            :class="{ clickable: index > 0 }"
            @click="index > 0 && navigateTo(crumb.path)"
          >
            {{ crumb.name }}
          </span>
          <span v-if="index < breadcrumbs.length - 1" class="separator">/</span>
        </template>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-overlay">
        <div class="loading-spinner"></div>
        <span>加载中...</span>
      </div>

      <!-- 空状态 -->
      <div v-else-if="folders.length === 0 && files.length === 0" class="empty-state">
        <div class="empty-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
          </svg>
        </div>
        <h3>{{ searchKeyword || minScore ? '没有找到匹配的文件' : '暂无文件' }}</h3>
        <p v-if="searchKeyword || minScore">请尝试其他筛选条件</p>
        <button v-if="searchKeyword || minScore" @click="clearFilters" class="clear-search-btn">
          清除筛选
        </button>
      </div>

      <!-- 文件列表 -->
      <div v-else class="file-browser">
        <!-- 表头 -->
        <div class="file-header">
          <div class="col-checkbox">
            <input
              type="checkbox"
              :checked="(folders.length + files.length) > 0 && selectedItems.size === (folders.length + files.length)"
              :indeterminate="selectedItems.size > 0 && selectedItems.size < (folders.length + files.length)"
              @change="toggleAll"
            />
          </div>
          <div class="col-name">名称</div>
          <div class="col-score">分数</div>
          <div class="col-actions">操作</div>
        </div>

        <!-- 文件夹列表 -->
        <div class="file-list">
          <div
            v-for="folder in folders"
            :key="folder"
            class="folder-row"
            :class="{ selected: selectedItems.has(folder) }"
            @dblclick="handleItemDoubleClick(folder, 'folder')"
          >
            <div class="col-checkbox">
              <input
                type="checkbox"
                :checked="selectedItems.has(folder)"
                @click="toggleItem(folder)"
              />
            </div>
            <div class="col-name folder-cell">
              <svg class="folder-icon" viewBox="0 0 24 24" fill="currentColor">
                <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
              </svg>
              <span class="folder-name">{{ folder }}</span>
            </div>
            <div class="col-score">-</div>
            <div class="col-actions">
              <button class="action-btn" @click="enterFolder(folder)">
                进入
              </button>
            </div>
          </div>

          <!-- 文件列表 -->
          <div
            v-for="file in files"
            :key="file"
            class="file-row"
            :class="[
              { selected: selectedItems.has(file) },
              getScoreClass(file)
            ]"
          >
            <div class="col-checkbox">
              <input
                type="checkbox"
                :checked="selectedItems.has(file)"
                @click="toggleItem(file)"
              />
            </div>
            <div class="col-name file-cell">
              <svg class="file-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
              </svg>
              <span class="file-name">{{ file }}</span>
            </div>
            <div class="col-score">
              <span v-if="getScore(file)" class="score-badge" :class="getScoreClass(file)">
                {{ getScore(file) }}%
              </span>
              <span v-else class="score-none">-</span>
            </div>
            <div class="col-actions">
              <button class="action-btn view" @click="viewFile(file)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                  <circle cx="12" cy="12" r="3"/>
                </svg>
                查看
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.analysis-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--surface);
  border-radius: 12px;
  overflow: hidden;
}

/* 工具栏 */
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 切换按钮组 */
.toggle-group {
  display: flex;
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
}

.toggle-btn {
  padding: 8px 16px;
  border: none;
  background: var(--surface);
  cursor: pointer;
  font-size: 0.875rem;
  color: var(--text-secondary);
  transition: all 0.2s;
}

.toggle-btn.active {
  background: var(--accent);
  color: white;
}

.toggle-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 状态标签 */
.status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.75rem;
  background: var(--background);
  color: var(--text-secondary);
}

.status-badge.success {
  background: rgba(16, 185, 129, 0.1);
  color: var(--success);
}

.status-badge.failed {
  background: rgba(239, 68, 68, 0.1);
  color: var(--error);
}

.status-badge.pending {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

/* 筛选器 */
.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-input {
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--background);
  font-size: 0.875rem;
  width: 160px;
  transition: all 0.2s;
}

.filter-input:focus {
  outline: none;
  border-color: var(--accent);
  width: 220px;
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--background);
  font-size: 0.875rem;
  cursor: pointer;
}

.filter-clear {
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--surface);
  cursor: pointer;
  font-size: 0.875rem;
  color: var(--text-muted);
}

.filter-clear:hover {
  background: var(--border);
  color: var(--text-primary);
}

/* 工具按钮 */
.tool-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface);
  cursor: pointer;
  font-size: 0.875rem;
  color: var(--text-secondary);
  transition: all 0.2s;
}

.tool-btn svg {
  width: 18px;
  height: 18px;
}

.tool-btn:hover:not(:disabled) {
  background: var(--background);
  border-color: var(--accent);
  color: var(--accent);
}

.tool-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.tool-btn.primary {
  background: var(--accent);
  border-color: var(--accent);
  color: white;
}

.tool-btn.primary:hover:not(:disabled) {
  background: #025a8b;
}

.tool-btn.danger {
  border-color: var(--error);
  color: var(--error);
}

.tool-btn.danger:hover:not(:disabled) {
  background: rgba(239, 68, 68, 0.1);
}

/* 路径导航栏 */
.path-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 24px;
  background: var(--background);
  border-bottom: 1px solid var(--border);
}

.nav-buttons {
  display: flex;
  gap: 4px;
}

.nav-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: var(--surface);
  border-radius: 6px;
  cursor: pointer;
  color: var(--text-secondary);
  transition: all 0.15s;
}

.nav-btn:hover:not(:disabled) {
  background: var(--border);
  color: var(--text-primary);
}

.nav-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.nav-btn svg {
  width: 16px;
  height: 16px;
}

.breadcrumbs {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.875rem;
  flex: 1;
  overflow: hidden;
}

.crumb {
  color: var(--text-secondary);
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.15s;
}

.crumb.clickable {
  cursor: pointer;
}

.crumb.clickable:hover {
  background: var(--border);
  color: var(--accent);
}

.separator {
  color: var(--text-muted);
}

/* 主内容区 */
.main-content {
  flex: 1;
  overflow: auto;
  position: relative;
}

/* 加载状态 */
.loading-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 80px 20px;
  color: var(--text-muted);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: var(--text-muted);
}

.empty-icon {
  width: 80px;
  height: 80px;
  margin-bottom: 16px;
  opacity: 0.4;
}

.empty-icon svg {
  width: 100%;
  height: 100%;
}

.empty-state h3 {
  font-size: 1.125rem;
  font-weight: 500;
  margin: 0 0 8px;
  color: var(--text-secondary);
}

.empty-state p {
  font-size: 0.875rem;
  margin: 0 0 16px;
}

.clear-search-btn {
  padding: 8px 20px;
  border: 1px solid var(--accent);
  border-radius: 6px;
  background: var(--accent);
  color: white;
  cursor: pointer;
  font-size: 0.875rem;
}

/* 文件浏览器 */
.file-browser {
  display: flex;
  flex-direction: column;
}

/* 表头 */
.file-header {
  display: flex;
  align-items: center;
  gap: 0;
  padding: 12px 24px;
  background: var(--background);
  border-bottom: 1px solid var(--border);
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.file-header .col-checkbox {
  width: 48px;
}

.file-header .col-name {
  flex: 1;
}

.file-header .col-score {
  width: 80px;
  text-align: center;
}

.file-header .col-actions {
  width: 100px;
  text-align: right;
}

/* 文件夹和文件行 */
.file-list {
  display: flex;
  flex-direction: column;
}

.folder-row,
.file-row {
  display: flex;
  align-items: center;
  gap: 0;
  padding: 10px 24px;
  border-bottom: 1px solid var(--border);
  transition: background 0.15s;
}

.folder-row {
  background: var(--background);
  font-weight: 500;
}

.file-row {
  background: var(--surface);
}

.file-row:hover {
  background: var(--background);
}

.file-row.selected {
  background: rgba(3, 105, 161, 0.05);
}

.file-row.score-high {
  border-left: 3px solid #10b981;
}

.file-row.score-medium {
  border-left: 3px solid #f59e0b;
}

.file-row.score-low {
  border-left: 3px solid #f97316;
}

.file-row.score-lower {
  border-left: 3px solid #ef4444;
}

.col-checkbox {
  width: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.col-checkbox input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: var(--accent);
}

.col-name {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  overflow: hidden;
}

.col-score {
  width: 80px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.col-actions {
  width: 100px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

/* 文件夹样式 */
.folder-cell {
  cursor: default;
}

.folder-icon {
  width: 20px;
  height: 20px;
  color: var(--accent);
  flex-shrink: 0;
}

.folder-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 分数徽章 */
.score-badge {
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 0.75rem;
  font-weight: 500;
}

.score-badge.score-high {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.score-badge.score-medium {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.score-badge.score-low {
  background: rgba(249, 115, 22, 0.1);
  color: #f97316;
}

.score-badge.score-lower {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.score-none {
  color: var(--text-muted);
}

/* 文件样式 */
.file-cell {
  cursor: default;
}

.file-icon {
  width: 18px;
  height: 18px;
  color: var(--accent);
  flex-shrink: 0;
}

.file-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.action-btn {
  padding: 4px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--surface);
  cursor: pointer;
  font-size: 0.75rem;
  color: var(--text-secondary);
  transition: all 0.15s;
}

.action-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.action-btn.view {
  display: flex;
  align-items: center;
  gap: 4px;
}

.action-btn.view svg {
  width: 14px;
  height: 14px;
}
</style>
