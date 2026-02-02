<script setup>
import { ref, onMounted, inject, computed } from 'vue'
import { api } from '../utils/api'

const currentUser = inject('currentUser')

const results = ref([])
const loading = ref(false)
const selectedResults = ref(new Set())
const analyzeStatus = ref({ status: 'pending', text: '等待自动分析' })

// 分析中状态，使用 localStorage 保持状态（防止页面切换导致状态丢失）
const isAnalyzing = ref(localStorage.getItem('isAnalyzing') === 'true')

// 搜索和筛选
const searchKeyword = ref('')
const minScore = ref(null)
const searchTimer = ref(null)

const emit = defineEmits(['view-result'])

// 检查是否是管理员
const isAdmin = computed(() => {
  return currentUser.value && currentUser.value.role === 'admin'
})

const loadResults = async (keyword = '', score = null) => {
  loading.value = true
  try {
    console.log('正在加载分析结果...')
    const data = await api.getAnalysisResults()
    console.log('API返回数据:', data)

    let filteredResults = data.results || []
    console.log('原始results:', filteredResults)

    // 只显示 .docx 文件（分析结果文档）
    filteredResults = filteredResults.map(group => ({
      ...group,
      files: group.files.filter(file => file.endsWith('.docx'))
    })).filter(group => group.files.length > 0)

    console.log('过滤后只保留 docx:', filteredResults)

    // 前端筛选
    if (keyword || score !== null) {
      filteredResults = filteredResults.map(group => ({
        ...group,
        files: group.files.filter(file => {
          // 搜索关键词筛选
          if (keyword && !file.toLowerCase().includes(keyword.toLowerCase())) {
            return false
          }
          // 分数筛选
          if (score !== null) {
            const match = file.match(/_分析结果_(\d+\.?\d*)\.docx$/)
            if (match) {
              const fileScore = parseFloat(match[1])
              if (fileScore < score) return false
            }
          }
          return true
        })
      })).filter(group => group.files.length > 0)
    }

    filteredResults = filteredResults.filter(group => group.files.length > 0)
    console.log('过滤后filteredResults:', filteredResults)
    console.log('过滤后filteredResults.length:', filteredResults.length)

    if (filteredResults.length > 0) {
      results.value = filteredResults
      console.log('已设置results.value:', results.value)
      console.log('results.value.length:', results.value.length)
    } else {
      results.value = []
    }
  } catch (error) {
    console.error('加载分析结果失败:', error)
    results.value = []
  } finally {
    loading.value = false
  }
}

const handleRefresh = async () => {
  await loadResults(searchKeyword.value, minScore.value)
}

const loadStatus = async () => {
  try {
    const data = await api.getAnalyzeStatus()
    if (data.success) {
      analyzeStatus.value = {
        status: data.status,
        text: data.text
      }
    }
  } catch (error) {
    console.error('加载状态失败:', error)
  }
}

const handleSearch = () => {
  if (searchTimer.value) {
    clearTimeout(searchTimer.value)
  }
  searchTimer.value = setTimeout(() => {
    loadResults(searchKeyword.value, minScore.value)
  }, 300)
}

const clearFilters = () => {
  searchKeyword.value = ''
  minScore.value = null
  loadResults('', null)
}

const toggleResult = (path) => {
  if (selectedResults.value.has(path)) {
    selectedResults.value.delete(path)
  } else {
    selectedResults.value.add(path)
  }
}

const toggleAll = () => {
  const allPaths = getAllPaths()
  if (selectedResults.value.size === allPaths.length) {
    selectedResults.value.clear()
  } else {
    allPaths.forEach(p => selectedResults.value.add(p))
  }
}

const getAllPaths = () => {
  const paths = []
  results.value.forEach(folder => {
    folder.files.forEach(file => {
      const fullPath = folder.name === '根目录' ? file : `${folder.name}/${file}`
      paths.push(fullPath)
    })
  })
  return paths
}

const handleDownload = async () => {
  const files = Array.from(selectedResults.value)
  if (files.length === 0) return

  for (const filePath of files) {
    try {
      const result = await api.downloadAnalysis([filePath])
      if (result.success) {
        downloadFile(result.fileName, result.content)
      }
    } catch (error) {
      console.error(`下载失败: ${filePath}`, error)
    }
    await new Promise(resolve => setTimeout(resolve, 300))
  }
}

const downloadFile = (fileName, content) => {
  const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = fileName
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

const handleDelete = async () => {
  const files = Array.from(selectedResults.value)
  if (files.length === 0) return

  if (!confirm(`确定要删除这 ${files.length} 个文件吗？此操作不可恢复。`)) {
    return
  }

  try {
    const result = await api.deleteAnalysis(files, currentUser.value.username)
    if (result.success) {
      alert('删除成功')
      selectedResults.value.clear()
      await loadResults(searchKeyword.value, minScore.value)
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
  // 防止重复点击
  if (isAnalyzing.value) {
    return
  }

  if (!confirm('确定要手动执行政策文档分析吗？')) {
    return
  }

  // 禁用按钮，防止重复点击（使用 localStorage 保持状态）
  isAnalyzing.value = true
  localStorage.setItem('isAnalyzing', 'true')

  try {
    const data = await api.triggerAnalyze()
    if (data.success) {
      // 刷新结果
      await loadResults()
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

const handleResultClick = (folder, file) => {
  const resultName = folder.name === '根目录' ? file : `${folder.name}/${file}`
  emit('view-result', resultName)
}

const getScoreClass = (fileName) => {
  // 匹配格式: xxx_分析结果_85.0.docx 中的分数
  const match = fileName.match(/_分析结果_(\d+\.?\d*)\.docx$/)
  if (match) {
    const score = parseFloat(match[1])
    if (score >= 90) return 'score-high'
    if (score >= 80) return 'score-medium'
    if (score >= 70) return 'score-low'
    return 'score-lower'
  }
  return ''
}

const getScore = (fileName) => {
  // 提取分数值
  const match = fileName.match(/_分析结果_(\d+\.?\d*)\.docx$/)
  return match ? match[1] : null
}

onMounted(() => {
  loadResults()
  loadStatus()
})
</script>

<template>
  <div class="analysis-view">
    <div class="view-header">
      <div class="header-left">
        <h2>分析结果</h2>
        <span class="status-badge" :class="analyzeStatus.status">
          {{ analyzeStatus.text }}
        </span>
      </div>
      <div class="view-actions">
        <!-- 筛选器 -->
        <div class="filter-group">
          <input
            v-model="searchKeyword"
            @input="handleSearch"
            @keyup.esc="clearFilters"
            type="text"
            placeholder="搜索分析结果..."
            class="filter-input"
          />
          <select v-model="minScore" @change="handleSearch" class="filter-select">
            <option :value="null">所有分数</option>
            <option value="90">90分以上</option>
            <option value="80">80分以上</option>
            <option value="70">70分以上</option>
            <option value="60">60分以上</option>
          </select>
          <button v-if="searchKeyword || minScore" @click="clearFilters" class="filter-clear">
            清除
          </button>
        </div>
        <button class="analyze-btn" @click="handleAnalyze" :disabled="isAnalyzing">
          {{ isAnalyzing ? '分析中...' : '手动分析' }}
        </button>
        <button class="refresh-btn" @click="handleRefresh" :disabled="loading">
          {{ loading ? '加载中...' : '刷新' }}
        </button>
        <button
          class="download-btn"
          @click="handleDownload"
          :disabled="selectedResults.size === 0"
        >
          下载 ({{ selectedResults.size }})
        </button>
        <button
          v-if="isAdmin"
          class="delete-btn"
          @click="handleDelete"
          :disabled="selectedResults.size === 0"
        >
          删除 ({{ selectedResults.size }})
        </button>
      </div>
    </div>

    <div class="view-content">
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <span>加载中...</span>
      </div>

      <div v-else-if="results.length === 0" class="empty-state">
        <div class="empty-icon">📊</div>
        <span>{{ searchKeyword || minScore ? '没有找到匹配的分析结果' : '暂无分析结果' }}</span>
        <button v-if="searchKeyword || minScore" @click="clearFilters" class="clear-filter-btn">
          清除筛选
        </button>
      </div>

      <div v-else class="result-list">
        <!-- 全选 -->
        <div class="list-header">
          <label class="checkbox-wrapper">
            <input
              type="checkbox"
              :checked="selectedResults.size === getAllPaths().length"
              :indeterminate="selectedResults.size > 0 && selectedResults.size < getAllPaths().length"
              @change="toggleAll"
            />
          </label>
          <span class="col-name">文件名</span>
          <span class="col-actions" v-if="selectedResults.size > 0">
            已选择 {{ selectedResults.size }} 个结果
          </span>
        </div>

        <!-- 按日期分组 -->
        <div v-for="folder in results" :key="folder.name" class="folder-group">
          <div class="folder-title">
            <span class="folder-icon">📈</span>
            <span>{{ folder.name }}</span>
            <span class="folder-count">({{ folder.files.length }}个文件)</span>
          </div>

          <div class="file-list">
            <div
              v-for="file in folder.files"
              :key="file"
              class="file-item"
              :class="[
                { selected: selectedResults.has(folder.name === '根目录' ? file : `${folder.name}/${file}`) },
                getScoreClass(file)
              ]"
              @click="handleResultClick(folder, file)"
            >
              <label class="checkbox-wrapper" @click.stop>
                <input
                  type="checkbox"
                  :checked="selectedResults.has(folder.name === '根目录' ? file : `${folder.name}/${file}`)"
                  @change="toggleResult(folder.name === '根目录' ? file : `${folder.name}/${file}`)"
                />
              </label>
              <span class="file-icon">📈</span>
              <span class="file-name">{{ file }}</span>
              <span v-if="getScoreClass(file)" class="score-badge" :class="getScoreClass(file)">
                {{ getScore(file) }}%
              </span>
              <span class="file-actions">
                <button @click.stop="handleResultClick(folder, file)" class="view-btn">查看</button>
              </span>
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
  overflow: hidden;
}

.view-header {
  padding: 16px 32px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--surface);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.view-header h2 {
  font-size: 1.25rem;
  font-weight: 600;
}

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

.view-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

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
  width: 180px;
  transition: all 0.2s;
}

.filter-input:focus {
  outline: none;
  border-color: var(--accent);
  width: 240px;
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
  background: var(--background);
  color: var(--text-primary);
}

.analyze-btn, .refresh-btn, .download-btn, .delete-btn {
  padding: 8px 16px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--surface);
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.analyze-btn {
  background: var(--accent);
  color: white;
  border-color: var(--accent);
}

.analyze-btn:hover {
  background: #025a8b;
}

.analyze-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.delete-btn {
  border-color: var(--error);
  color: var(--error);
}

.delete-btn:hover:not(:disabled) {
  background: rgba(239, 68, 68, 0.1);
}

.analyze-btn:hover:not(:disabled), .refresh-btn:hover:not(:disabled), .download-btn:hover:not(:disabled) {
  background: var(--background);
}

.download-btn:disabled, .refresh-btn:disabled, .delete-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.view-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px 32px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-muted);
  padding: 60px 20px;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-muted);
  padding: 60px 20px;
}

.empty-icon {
  font-size: 3rem;
  opacity: 0.5;
}

.clear-filter-btn {
  padding: 8px 16px;
  border: 1px solid var(--accent);
  border-radius: 6px;
  background: var(--accent);
  color: white;
  cursor: pointer;
  font-size: 0.875rem;
}

.list-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--background);
  border-radius: 8px;
  margin-bottom: 16px;
}

.col-name {
  font-weight: 500;
  color: var(--text-secondary);
}

.col-actions {
  margin-left: auto;
  font-size: 0.875rem;
  color: var(--accent);
}

.checkbox-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  cursor: pointer;
}

.folder-group {
  margin-bottom: 24px;
}

.folder-title {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: var(--primary);
  color: white;
  border-radius: 8px;
  margin-bottom: 8px;
  font-weight: 500;
}

.folder-icon {
  font-size: 1rem;
}

.folder-count {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.6);
  font-weight: normal;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.file-item:hover {
  background: var(--background);
}

.file-item.selected {
  border-color: var(--accent);
  background: rgba(3, 105, 161, 0.05);
}

.file-item.score-high {
  border-left: 3px solid #10b981;
}

.file-item.score-medium {
  border-left: 3px solid #f59e0b;
}

.file-item.score-low {
  border-left: 3px solid #f97316;
}

.file-item.score-lower {
  border-left: 3px solid #ef4444;
}

.score-badge {
  padding: 2px 8px;
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

.file-icon {
  font-size: 1.125rem;
}

.file-name {
  flex: 1;
  font-size: 0.9375rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-actions {
  display: flex;
  gap: 8px;
}

.view-btn {
  padding: 4px 12px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--surface);
  cursor: pointer;
  font-size: 0.75rem;
  color: var(--text-secondary);
  transition: all 0.2s;
}

.view-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
}
</style>
