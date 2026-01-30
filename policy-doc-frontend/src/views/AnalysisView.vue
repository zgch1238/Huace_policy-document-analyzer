<script setup>
import { ref, onMounted, inject, computed } from 'vue'
import { api } from '../utils/api'

const currentUser = inject('currentUser')

const results = ref([])
const loading = ref(false)
const selectedResults = ref(new Set())
const analyzeStatus = ref({ status: 'pending', text: '等待自动分析' })

const emit = defineEmits(['view-result'])

// 检查是否是管理员
const isAdmin = computed(() => {
  return currentUser.value && currentUser.value.role === 'admin'
})

const loadResults = async () => {
  loading.value = true
  try {
    const data = await api.getAnalysisResults()
    if (data.results && data.results.length > 0) {
      results.value = data.results
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

const handleTriggerAnalyze = async () => {
  if (!confirm('确定要手动执行政策文档分析吗？')) return

  try {
    const data = await api.triggerAnalyze()
    if (data.success) {
      alert(`分析完成！成功: ${data.successCount}, 失败: ${data.failedCount}`)
      loadResults()
      loadStatus()
    } else {
      alert(data.message || '分析失败')
    }
  } catch (error) {
    console.error('分析失败:', error)
    alert('分析失败，请重试')
  }
}

const handleResultClick = (folder, file) => {
  const resultName = folder.name === '根目录' ? file : `${folder.name}/${file}`
  emit('view-result', resultName)
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
      await loadResults()
    } else {
      alert(result.message || '删除失败')
    }
  } catch (error) {
    console.error('删除失败:', error)
    alert('删除失败，请重试')
  }
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
        <button class="analyze-btn" @click="handleTriggerAnalyze">
          手动分析
        </button>
        <button class="refresh-btn" @click="loadResults" :disabled="loading">
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
        加载中...
      </div>

      <div v-else-if="results.length === 0" class="empty-state">
        暂无分析结果
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
        </div>

        <!-- 按文件夹分组 -->
        <div v-for="folder in results" :key="folder.name" class="folder-group">
          <div class="folder-title">
            <span class="folder-icon">📊</span>
            <span>{{ folder.name }}</span>
            <span class="folder-count">({{ folder.files.length }}个文件)</span>
          </div>

          <div class="file-list">
            <div
              v-for="file in folder.files"
              :key="file"
              class="file-item"
              :class="{ selected: selectedResults.has(folder.name === '根目录' ? file : `${folder.name}/${file}`) }"
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
  padding: 20px 32px;
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
  gap: 12px;
}

.analyze-btn, .refresh-btn, .download-btn {
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

.analyze-btn:hover:not(:disabled), .refresh-btn:hover:not(:disabled), .download-btn:hover:not(:disabled) {
  background: var(--background);
}

.download-btn:disabled, .refresh-btn:disabled, .delete-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.delete-btn {
  border-color: var(--error);
  color: var(--error);
}

.delete-btn:hover:not(:disabled) {
  background: rgba(239, 68, 68, 0.1);
}

.view-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px 32px;
}

.loading-state, .empty-state {
  text-align: center;
  color: var(--text-muted);
  padding: 60px 20px;
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
</style>
