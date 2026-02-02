<script setup>
import { ref, onMounted, inject, computed } from 'vue'
import { api } from '../utils/api'

const currentUser = inject('currentUser')

const documents = ref([])
const loading = ref(false)
const selectedDocs = ref(new Set())
const searchKeyword = ref('')
const searchTimer = ref(null)

const emit = defineEmits(['view-document'])

// 检查是否是管理员
const isAdmin = computed(() => {
  return currentUser.value && currentUser.value.role === 'admin'
})

const loadDocuments = async (keyword = '') => {
  loading.value = true
  try {
    const data = await api.getDocuments(keyword)
    if (data.documents && data.documents.length > 0) {
      documents.value = data.documents
    } else {
      documents.value = []
    }
  } catch (error) {
    console.error('加载文档失败:', error)
    documents.value = []
  } finally {
    loading.value = false
  }
}

const handleRefresh = async () => {
  await loadDocuments(searchKeyword.value)
}

const handleSearch = () => {
  if (searchTimer.value) {
    clearTimeout(searchTimer.value)
  }
  searchTimer.value = setTimeout(() => {
    loadDocuments(searchKeyword.value)
  }, 300)
}

const clearSearch = () => {
  searchKeyword.value = ''
  loadDocuments('')
}

const toggleDoc = (path) => {
  if (selectedDocs.value.has(path)) {
    selectedDocs.value.delete(path)
  } else {
    selectedDocs.value.add(path)
  }
}

const toggleAll = () => {
  const allPaths = getAllPaths()
  if (selectedDocs.value.size === allPaths.length) {
    selectedDocs.value.clear()
  } else {
    allPaths.forEach(p => selectedDocs.value.add(p))
  }
}

const getAllPaths = () => {
  const paths = []
  documents.value.forEach(folder => {
    folder.files.forEach(file => {
      const fullPath = folder.name === '根目录' ? file : `${folder.name}/${file}`
      paths.push(fullPath)
    })
  })
  return paths
}

const handleDownload = async () => {
  const files = Array.from(selectedDocs.value)
  if (files.length === 0) return

  for (const filePath of files) {
    try {
      const result = await api.downloadDocuments([filePath])
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
  const files = Array.from(selectedDocs.value)
  if (files.length === 0) return

  if (!confirm(`确定要删除这 ${files.length} 个文件吗？此操作不可恢复。`)) {
    return
  }

  try {
    const result = await api.deleteDocuments(files, currentUser.value.username)
    if (result.success) {
      alert('删除成功')
      selectedDocs.value.clear()
      await loadDocuments()
    } else {
      alert(result.message || '删除失败')
    }
  } catch (error) {
    console.error('删除失败:', error)
    alert('删除失败，请重试')
  }
}

const handleDocClick = (folder, file) => {
  const docName = folder.name === '根目录' ? file : `${folder.name}/${file}`
  emit('view-document', docName)
}

onMounted(() => {
  loadDocuments()
})
</script>

<template>
  <div class="documents-view">
    <div class="view-header">
      <div class="header-left">
        <h2>政策文档管理</h2>
      </div>
      <div class="view-actions">
        <!-- 搜索框 -->
        <div class="search-box">
          <input
            v-model="searchKeyword"
            @input="handleSearch"
            @keyup.esc="clearSearch"
            type="text"
            placeholder="搜索文档..."
            class="search-input"
          />
          <button v-if="searchKeyword" @click="clearSearch" class="search-clear">x</button>
        </div>
        <button class="refresh-btn" @click="handleRefresh" :disabled="loading">
          {{ loading ? '加载中...' : '刷新' }}
        </button>
        <button
          class="download-btn"
          @click="handleDownload"
          :disabled="selectedDocs.size === 0"
        >
          下载 ({{ selectedDocs.size }})
        </button>
        <button
          v-if="isAdmin"
          class="delete-btn"
          @click="handleDelete"
          :disabled="selectedDocs.size === 0"
        >
          删除 ({{ selectedDocs.size }})
        </button>
      </div>
    </div>

    <div class="view-content">
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <span>加载中...</span>
      </div>

      <div v-else-if="documents.length === 0" class="empty-state">
        <div class="empty-icon">📂</div>
        <span>{{ searchKeyword ? '没有找到匹配的文档' : '暂无政策文档' }}</span>
        <button v-if="searchKeyword" @click="clearSearch" class="clear-search-btn">
          清除搜索
        </button>
      </div>

      <div v-else class="doc-list">
        <!-- 全选 -->
        <div class="list-header">
          <label class="checkbox-wrapper">
            <input
              type="checkbox"
              :checked="selectedDocs.size === getAllPaths().length"
              :indeterminate="selectedDocs.size > 0 && selectedDocs.size < getAllPaths().length"
              @change="toggleAll"
            />
          </label>
          <span class="col-name">文件名</span>
          <span class="col-actions" v-if="selectedDocs.size > 0">
            已选择 {{ selectedDocs.size }} 个文件
          </span>
        </div>

        <!-- 按文件夹分组 -->
        <div v-for="folder in documents" :key="folder.name" class="folder-group">
          <div class="folder-title">
            <span class="folder-icon">📁</span>
            <span>{{ folder.name }}</span>
            <span class="folder-count">({{ folder.files.length }}个文件)</span>
          </div>

          <div class="file-list">
            <div
              v-for="file in folder.files"
              :key="file"
              class="file-item"
              :class="{ selected: selectedDocs.has(folder.name === '根目录' ? file : `${folder.name}/${file}`) }"
              @click="handleDocClick(folder, file)"
            >
              <label class="checkbox-wrapper" @click.stop>
                <input
                  type="checkbox"
                  :checked="selectedDocs.has(folder.name === '根目录' ? file : `${folder.name}/${file}`)"
                  @change="toggleDoc(folder.name === '根目录' ? file : `${folder.name}/${file}`)"
                />
              </label>
              <span class="file-icon">📄</span>
              <span class="file-name">{{ file }}</span>
              <span class="file-actions">
                <button @click.stop="handleDocClick(folder, file)" class="view-btn">查看</button>
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.documents-view {
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
  gap: 12px;
}

.view-header h2 {
  font-size: 1.25rem;
  font-weight: 600;
}

.doc-count {
  font-size: 0.875rem;
  color: var(--text-muted);
}

.view-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 搜索框 */
.search-box {
  position: relative;
  display: flex;
  align-items: center;
}

.search-input {
  padding: 8px 32px 8px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--background);
  font-size: 0.875rem;
  width: 200px;
  transition: all 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: var(--accent);
  width: 260px;
}

.search-clear {
  position: absolute;
  right: 8px;
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 1rem;
  padding: 2px 6px;
  border-radius: 4px;
}

.search-clear:hover {
  background: var(--border);
}

.refresh-btn, .download-btn, .delete-btn {
  padding: 8px 16px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--surface);
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.delete-btn {
  border-color: var(--error);
  color: var(--error);
}

.delete-btn:hover:not(:disabled) {
  background: rgba(239, 68, 68, 0.1);
}

.refresh-btn:hover:not(:disabled), .download-btn:hover:not(:disabled) {
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

.clear-search-btn {
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
