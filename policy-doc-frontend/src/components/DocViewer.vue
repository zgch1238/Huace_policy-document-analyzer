<script setup>
import { ref, onMounted, watch } from 'vue'
import { api } from '../utils/api'

const props = defineProps({
  fileName: {
    type: String,
    required: true
  },
  source: {
    type: String,
    required: true,
    validator: (value) => ['highlight', 'result'].includes(value)
  }
})

const emit = defineEmits(['close'])

const docContent = ref('')
const isBinary = ref(false)
const base64Content = ref('')
const loading = ref(true)
const error = ref(null)

const loadDocument = async () => {
  loading.value = true
  error.value = null

  try {
    // 根据来源确定目录和 API
    let result
    if (props.source === 'document') {
      // 政策文档使用 downloadDocuments API
      result = await api.downloadDocuments([props.fileName])
    } else {
      // 分析结果和高亮文档使用 downloadAnalysis API
      const directory = props.source === 'highlight'
        ? 'policy_document_word'
        : 'analyze_result'
      result = await api.downloadAnalysis([props.fileName], directory)
    }

    if (result.success) {
      isBinary.value = result.isBinary || false

      if (isBinary.value && result.content) {
        // 二进制文件（docx）：显示提示信息
        base64Content.value = result.content
        const sourceName = props.source === 'highlight'
          ? '高亮文档 (policy_document_word)'
          : props.source === 'document'
            ? '政策文档 (policy_document)'
            : '分析结果 (analyze_result)'
        docContent.value = `这是一个 Word 文档文件。

文件: ${result.fileName || props.fileName}

来源: ${sourceName}

由于浏览器安全限制，无法直接在网页中预览 Word 文档。

请选择以下操作:
1. 点击"下载文档"按钮下载文件
2. 使用 Microsoft Word 或其他办公软件打开查看
`
      } else {
        // 文本文件直接显示内容
        base64Content.value = ''
        docContent.value = result.content || ''
      }
    } else {
      error.value = result.message || '无法加载文档'
    }
  } catch (err) {
    console.error('加载文档失败:', err)
    error.value = '加载文档失败: ' + err.message
  } finally {
    loading.value = false
  }
}

const downloadDocument = async () => {
  try {
    let result
    if (props.source === 'document') {
      // 政策文档使用 downloadDocuments API
      result = await api.downloadDocuments([props.fileName])
    } else {
      // 分析结果和高亮文档使用 downloadAnalysis API
      const directory = props.source === 'highlight'
        ? 'policy_document_word'
        : 'analyze_result'
      result = await api.downloadAnalysis([props.fileName], directory)
    }

    if (result.success) {
      if (result.isBinary && result.content) {
        // 二进制文件：使用 base64 解码，并转换为 Uint8Array 避免 UTF-16 编码问题
        const binaryData = atob(result.content)
        const bytes = new Uint8Array(binaryData.length)
        for (let i = 0; i < binaryData.length; i++) {
          bytes[i] = binaryData.charCodeAt(i)
        }
        const blob = new Blob([bytes], {
          type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = result.fileName || props.fileName
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
      } else {
        // 文本文件
        const blob = new Blob([result.content], {
          type: 'text/markdown;charset=utf-8'
        })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = result.fileName || props.fileName
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
      }
    }
  } catch (err) {
    console.error('下载文档失败:', err)
    alert('下载失败: ' + err.message)
  }
}

watch(() => props.fileName, () => {
  loadDocument()
})

onMounted(() => {
  loadDocument()
})
</script>

<template>
  <div class="doc-viewer-overlay" @click.self="emit('close')">
    <div class="doc-viewer">
      <div class="viewer-header">
        <h3>{{ fileName }}</h3>
        <button class="close-btn" @click="emit('close')">×</button>
      </div>

      <div class="viewer-content">
        <div v-if="loading" class="loading-state">
          <div class="loading-spinner"></div>
          <span>加载文档中...</span>
        </div>

        <div v-else-if="error" class="error-state">
          <span class="error-icon">⚠️</span>
          <span>{{ error }}</span>
        </div>

        <div v-else class="content-wrapper">
          <pre class="doc-content">{{ docContent }}</pre>

          <div class="viewer-actions">
            <button class="action-btn primary" @click="downloadDocument">
              下载文档
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.doc-viewer-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.doc-viewer {
  background: var(--surface);
  border-radius: 12px;
  width: 90%;
  max-width: 800px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.viewer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}

.viewer-header h3 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: var(--background);
  border-radius: 6px;
  cursor: pointer;
  font-size: 1.25rem;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: var(--border);
  color: var(--text-primary);
}

.viewer-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 60px 20px;
  color: var(--text-muted);
}

.error-state {
  color: var(--error);
}

.error-icon {
  font-size: 2rem;
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

.content-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.doc-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  margin: 0;
  font-family: inherit;
  font-size: 0.875rem;
  line-height: 1.6;
  color: var(--text-primary);
  white-space: pre-wrap;
  word-break: break-word;
}

.viewer-actions {
  padding: 16px 20px;
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.action-btn {
  padding: 8px 20px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--surface);
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.action-btn:hover {
  background: var(--background);
}

.action-btn.primary {
  background: var(--accent);
  color: white;
  border-color: var(--accent);
}

.action-btn.primary:hover {
  background: #025a8b;
}
</style>
