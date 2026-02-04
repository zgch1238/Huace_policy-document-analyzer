<script setup>
defineOptions({ name: 'CrawlerView' })

import { ref, onMounted, computed } from 'vue'
import { api } from '../utils/api'

// 状态
const loading = ref(false)
const crawling = ref(false)
const results = ref([])
const message = ref('')
const messageType = ref('info')

// 关键词分类面板状态
const showKeywordCategoryPanel = ref(false)
const keywordCategories = ref({})
const selectedMainCategory = ref('')

// 板块筛选选项（动态加载）
const sectionFilterOptions = ref([])
const showSectionFilter = ref(true)

// 表单数据
const form = ref({
  region: '',
  department: '',
  keywords: '',
  startDate: '2025-01-01',
  endDate: '',
  dateFilter: '',
  sectionFilter: 'all',
  fetchContent: true
})

// 选项数据
const regions = ref([])
const departments = ref([])
const dateFilterOptions = [
  { value: '', label: '不限时间' },
  { value: '3d', label: '最近3天' },
  { value: '7d', label: '最近7天' },
  { value: '30d', label: '最近1个月' },
  { value: '90d', label: '最近3个月' },
  { value: 'cur-year', label: '今年' },
  { value: 'pre-year', label: '去年' }
]

// 监听地区变化，加载部门
const onRegionChange = async () => {
  form.value.department = ''
  form.value.sectionFilter = 'all'
  departments.value = []
  sectionFilterOptions.value = []
  showSectionFilter.value = true

  if (!form.value.region) return

  try {
    const res = await api.getDepartments(form.value.region)
    if (res.success) {
      departments.value = res.data
    }
  } catch (e) {
    showMessage('加载部门失败: ' + e.message, 'error')
  }
}

// 加载板块选项
const loadSectionOptions = async () => {
  if (!form.value.region || !form.value.department) return

  try {
    const res = await api.getSections(form.value.region, form.value.department)
    if (res.success && res.data && Object.keys(res.data).length > 0) {
      // 将后端返回的SECTION_OPTIONS转换为前端选项格式
      sectionFilterOptions.value = Object.entries(res.data).map(([value, label]) => ({
        value,
        label
      }))
      showSectionFilter.value = true
    } else {
      // 没有板块选项，隐藏板块筛选
      showSectionFilter.value = false
      form.value.sectionFilter = 'all'
    }
  } catch (e) {
    console.error('加载板块选项失败:', e)
    showSectionFilter.value = false
    form.value.sectionFilter = 'all'
  }
}

// 监听部门变化，加载板块选项
const onDepartmentChange = () => {
  form.value.sectionFilter = 'all'
  loadSectionOptions()
}

// 开始爬取
const startCrawl = async () => {
  if (!form.value.region || !form.value.department) {
    showMessage('请选择地区和部门', 'error')
    return
  }

  if (!form.value.keywords?.trim()) {
    showMessage('请输入关键词', 'error')
    return
  }

  loading.value = true
  crawling.value = true
  results.value = []
  message.value = '正在爬取中，请稍候...'
  messageType.value = 'info'

  try {
    const res = await api.crawl({
      region: form.value.region,
      department: form.value.department,
      keywords: form.value.keywords,
      start_date: form.value.startDate,
      end_date: form.value.endDate || undefined,
      date_filter: form.value.dateFilter || undefined,
      section_filter: form.value.sectionFilter,
      fetch_content: form.value.fetchContent
    })

    if (res.success) {
      results.value = res.data || []
      const count = res.count || 0
      showMessage(`爬取完成！共找到 ${count} 条相关信息`, 'success')

      if (res.saved_csv_file) {
        console.log('CSV已保存:', res.saved_csv_file)
      }
      if (res.saved_md_file) {
        console.log('Markdown已保存:', res.saved_md_file)
      }
    } else {
      showMessage('爬取失败: ' + (res.error || '未知错误'), 'error')
    }
  } catch (e) {
    showMessage('爬取出错: ' + e.message, 'error')
  } finally {
    loading.value = false
    crawling.value = false
  }
}

// 显示消息
const showMessage = (msg, type = 'info') => {
  message.value = msg
  messageType.value = type
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '未知'
  return dateStr
}

// 打开链接
const openUrl = (url) => {
  if (url) {
    window.open(url, '_blank')
  }
}

// 切换关键词分类面板显示
const toggleKeywordPanel = () => {
  showKeywordCategoryPanel.value = !showKeywordCategoryPanel.value
  if (showKeywordCategoryPanel.value && Object.keys(keywordCategories.value).length === 0) {
    loadKeywordCategories()
  }
}

// 加载关键词分类
const loadKeywordCategories = async () => {
  try {
    const res = await api.getKeywordCategories()
    if (res.success) {
      keywordCategories.value = res.data
    }
  } catch (e) {
    console.error('加载关键词分类失败:', e)
  }
}

// 根据选中领域获取关键词列表
const currentKeywords = computed(() => {
  if (!selectedMainCategory.value || !keywordCategories.value[selectedMainCategory.value]) {
    return []
  }
  const category = keywordCategories.value[selectedMainCategory.value]
  if (category['全部']) {
    return category['全部']
  }
  const allKeywords = []
  Object.values(category).forEach(keywords => {
    allKeywords.push(...keywords)
  })
  return allKeywords
})

// 添加关键词到输入框
const addKeyword = (keyword) => {
  const currentKeywords = (form.value.keywords || '').trim()
  const existingKeywords = currentKeywords ? currentKeywords.split(/[、,，]/).map(k => k.trim()).filter(k => k) : []

  if (existingKeywords.includes(keyword)) {
    return
  }

  if (currentKeywords) {
    form.value.keywords = currentKeywords + '、' + keyword
  } else {
    form.value.keywords = keyword
  }
}

// 重置表单
const resetForm = () => {
  form.value.region = ''
  form.value.department = ''
  form.value.keywords = ''
  form.value.startDate = '2025-01-01'
  form.value.endDate = ''
  form.value.dateFilter = ''
  form.value.sectionFilter = 'all'
  form.value.fetchContent = true
  departments.value = []
  results.value = []
  message.value = ''
}

// 加载选项数据
onMounted(async () => {
  try {
    const res = await api.getRegions()
    if (res.success) {
      regions.value = res.data
    }
  } catch (e) {
    showMessage('加载地区列表失败: ' + e.message, 'error')
  }
})
</script>

<template>
  <div class="crawler-page">
    <div class="page-header">
      <h1>政府网站信息检索系统</h1>
      <p class="subtitle">智能检索政府科技政策与项目信息</p>
    </div>

    <div class="main-content">
      <!-- 左侧：检索条件设置 -->
      <section class="search-panel">
        <div class="panel-header">
          <h2>检索条件设置</h2>
        </div>

        <form class="search-form" @submit.prevent="startCrawl">
          <div class="form-row">
            <div class="form-group">
              <label>行政区域</label>
              <select v-model="form.region" @change="onRegionChange" :disabled="crawling">
                <option value="">请选择行政区域</option>
                <option v-for="r in regions" :key="r" :value="r">{{ r }}</option>
              </select>
            </div>

            <div class="form-group">
              <label>部门机构</label>
              <select v-model="form.department" @change="onDepartmentChange" :disabled="crawling || !form.region">
                <option value="">请选择部门</option>
                <option v-for="d in departments" :key="d" :value="d">{{ d }}</option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label>
              检索关键词
              <button type="button" class="keyword-btn" @click="toggleKeywordPanel" :disabled="crawling">
                📚 选择预设关键词
              </button>
            </label>
            <input
              type="text"
              v-model="form.keywords"
              placeholder="多个关键词用顿号（、）分隔，如：北斗导航、RTK、地理信息"
              :disabled="crawling"
            />
          </div>

          <!-- 关键词分类面板 -->
          <div v-if="showKeywordCategoryPanel" class="keyword-panel">
            <div class="keyword-panel-header">
              <span>📚 关键词分类库</span>
              <button type="button" @click="showKeywordCategoryPanel = false">✕ 关闭</button>
            </div>

            <div class="form-group">
              <label>选择领域</label>
              <select v-model="selectedMainCategory">
                <option value="">请选择领域</option>
                <option v-for="(cats, category) in keywordCategories" :key="category" :value="category">
                  {{ category }}
                </option>
              </select>
            </div>

            <div class="keyword-list">
              <button
                v-for="kw in currentKeywords"
                :key="kw"
                type="button"
                class="kw-item"
                @click="addKeyword(kw)"
              >
                {{ kw }}
              </button>
              <span v-if="!selectedMainCategory" class="no-kw">请选择领域查看关键词</span>
              <span v-else-if="currentKeywords.length === 0" class="no-kw">该分类暂无关键词</span>
            </div>

            <div class="keyword-hint">
              💡 点击关键词添加到输入框 | 支持多选（自动用顿号分隔）
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>开始日期</label>
              <input type="date" v-model="form.startDate" :disabled="crawling" />
            </div>

            <div class="form-group">
              <label>结束日期</label>
              <input type="date" v-model="form.endDate" :disabled="crawling" />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>网站时间筛选</label>
              <select v-model="form.dateFilter" :disabled="crawling">
                <option v-for="opt in dateFilterOptions" :key="opt.value" :value="opt.value">
                  {{ opt.label }}
                </option>
              </select>
            </div>

            <div class="form-group" v-if="showSectionFilter">
              <label>搜索板块</label>
              <select v-model="form.sectionFilter" :disabled="crawling">
                <option v-for="opt in sectionFilterOptions" :key="opt.value" :value="opt.value">
                  {{ opt.label }}
                </option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label class="checkbox-label">
              <input type="checkbox" v-model="form.fetchContent" :disabled="crawling" />
              <span>爬取原文内容</span>
            </label>
          </div>

          <div class="form-actions">
            <button type="submit" class="btn-primary" :disabled="crawling">
              {{ crawling ? '采集中...' : '开始检索' }}
            </button>
            <button type="button" class="btn-secondary" @click="resetForm" :disabled="crawling">
              重置条件
            </button>
          </div>
        </form>
      </section>

      <!-- 右侧：检索结果 -->
      <section class="results-panel">
        <div class="panel-header">
          <h2>检索结果</h2>
          <span class="results-count">{{ results.length }} 条结果</span>
        </div>

        <div class="results-container">
          <!-- 消息提示 -->
          <div v-if="message" :class="['message', messageType]">
            {{ message }}
          </div>

          <!-- 结果列表 -->
          <div v-if="results.length > 0" class="results-list">
            <div v-for="(item, idx) in results" :key="idx" class="result-card">
              <div class="result-header">
                <span class="result-date">{{ formatDate(item.publish_date_full) }}</span>
                <span class="result-category">{{ item.category || '政策文件' }}</span>
              </div>
              <h3 class="result-title">
                <a :href="item.url" target="_blank">{{ item.title }}</a>
              </h3>
              <div class="result-meta">
                <span>🏛️ {{ item.publisher }}</span>
                <span v-if="item.doc_number">📄 {{ item.doc_number }}</span>
              </div>
              <div v-if="item.matched_keywords && item.matched_keywords.length > 0" class="result-keywords">
                <span
                  v-for="kw in item.matched_keywords.slice(0, 5)"
                  :key="kw"
                  class="kw-tag"
                >
                  {{ kw }}
                </span>
              </div>
              <div class="result-actions">
                <a :href="item.url" target="_blank" class="link-btn">查看原文 →</a>
              </div>
              <div v-if="item.attachments && item.attachments.length > 0" class="attachments">
                <span class="att-label">附件:</span>
                <span v-for="(att, i) in item.attachments" :key="i" class="att-item">
                  {{ att.name }}
                </span>
              </div>
            </div>
          </div>

          <!-- 空状态 -->
          <div v-else-if="!crawling" class="empty-state">
            <div class="empty-icon">📋</div>
            <p>请设置检索条件后点击"开始检索"</p>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.crawler-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  min-height: calc(100vh - 100px);
  background: var(--background);
  box-sizing: border-box;
}

.page-header {
  text-align: center;
  margin-bottom: 20px;
  width: 100%;
  max-width: 1400px;
}

.page-header h1 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.subtitle {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.main-content {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 20px;
  width: 100%;
  max-width: 1400px;
  align-items: stretch;
}

/* 左侧面板 */
.search-panel {
  background: var(--surface);
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 180px);
}

.panel-header {
  padding: 16px 20px;
  background: linear-gradient(135deg, var(--accent) 0%, #0369a1 100%);
  color: white;
}

.panel-header h2 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
}

.search-form {
  padding: 20px;
  flex: 1;
  overflow-y: auto;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.form-group select,
.form-group input[type="text"],
.form-group input[type="date"] {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 0.875rem;
  background: var(--background);
  color: var(--text-primary);
  box-sizing: border-box;
}

.form-group select:disabled,
.form-group input:disabled {
  background: #f5f5f5;
  color: var(--text-muted);
}

.keyword-btn {
  padding: 3px 10px;
  font-size: 11px;
  border: 1px solid var(--accent);
  background: white;
  color: var(--accent);
  border-radius: 4px;
  cursor: pointer;
}

.keyword-btn:hover:not(:disabled) {
  background: var(--accent);
  color: white;
}

.keyword-btn:disabled {
  opacity: 0.6;
}

/* 关键词面板 */
.keyword-panel {
  padding: 12px;
  border: 2px solid var(--accent);
  border-radius: 8px;
  background: #f8f9fa;
  margin-bottom: 16px;
}

.keyword-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-weight: 600;
  font-size: 0.875rem;
}

.keyword-panel-header button {
  padding: 2px 10px;
  font-size: 11px;
  border: 1px solid var(--border);
  background: white;
  border-radius: 4px;
  cursor: pointer;
}

.keyword-list {
  padding: 10px;
  background: white;
  border-radius: 6px;
  min-height: 50px;
  max-height: 150px;
  overflow-y: auto;
  margin-bottom: 10px;
}

.kw-item {
  margin: 4px;
  padding: 4px 10px;
  border: 1px solid var(--accent);
  background: white;
  color: var(--accent);
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}

.kw-item:hover {
  background: var(--accent);
  color: white;
}

.no-kw {
  color: #999;
  font-size: 12px;
  display: block;
  text-align: center;
  padding: 15px 0;
}

.keyword-hint {
  padding: 8px;
  background: #e8f4fd;
  border-radius: 4px;
  font-size: 11px;
  color: #555;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.8125rem;
  color: var(--text-secondary);
  cursor: pointer;
}

.checkbox-label input {
  width: 16px;
  height: 16px;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}

.btn-primary,
.btn-secondary {
  flex: 1;
  padding: 12px 16px;
  border: none;
  border-radius: 6px;
  font-size: 0.9375rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: var(--accent);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #025a8b;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: var(--background);
  border: 1px solid var(--border);
  color: var(--text-secondary);
}

.btn-secondary:hover:not(:disabled) {
  background: #f5f5f5;
}

/* 右侧结果面板 */
.results-panel {
  background: var(--surface);
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 180px);
}

.results-panel .panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
  background: linear-gradient(135deg, var(--accent) 0%, #0369a1 100%);
}

.search-panel .panel-header {
  flex-shrink: 0;
}

.results-count {
  font-size: 0.875rem;
  opacity: 0.9;
}

.results-container {
  padding: 20px;
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.message {
  padding: 12px 16px;
  border-radius: 6px;
  margin-bottom: 12px;
  font-size: 0.875rem;
  flex-shrink: 0;
}

.message.info {
  background: #e0f2fe;
  color: #0369a1;
}

.message.success {
  background: #dcfce7;
  color: #15803d;
}

.message.error {
  background: #fee2e2;
  color: #dc2626;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
}

.result-card {
  padding: 14px 16px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--background);
  transition: box-shadow 0.2s;
}

.result-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.result-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
  font-size: 0.8125rem;
}

.result-date {
  color: var(--text-secondary);
}

.result-category {
  background: #e0f2fe;
  color: #0369a1;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
}

.result-title {
  font-size: 1rem;
  font-weight: 500;
  margin: 0 0 10px 0;
  line-height: 1.5;
}

.result-title a {
  color: var(--text-primary);
  text-decoration: none;
}

.result-title a:hover {
  color: var(--accent);
}

.result-meta {
  display: flex;
  gap: 16px;
  font-size: 0.8125rem;
  color: var(--text-secondary);
  margin-bottom: 10px;
}

.result-keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.kw-tag {
  padding: 3px 8px;
  background: #fef3c7;
  color: #b45309;
  border-radius: 4px;
  font-size: 0.75rem;
}

.result-actions {
  margin-bottom: 10px;
}

.link-btn {
  display: inline-block;
  padding: 6px 12px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--accent);
  font-size: 0.8125rem;
  text-decoration: none;
  transition: all 0.2s;
}

.link-btn:hover {
  background: var(--accent);
  color: white;
}

.attachments {
  font-size: 0.8125rem;
  color: var(--text-secondary);
}

.att-label {
  margin-right: 6px;
}

.att-item {
  display: inline-block;
  padding: 2px 6px;
  background: #e0e7ff;
  color: #4338ca;
  border-radius: 4px;
  margin-right: 6px;
  font-size: 0.75rem;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-secondary);
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 16px;
}

.empty-state p {
  margin: 0;
  font-size: 0.9375rem;
}

/* 响应式 */
@media (max-width: 1200px) {
  .main-content {
    grid-template-columns: 280px 1fr;
    gap: 16px;
  }
}

@media (max-width: 1024px) {
  .main-content {
    grid-template-columns: 1fr;
  }

  .search-panel {
    position: static;
  }

  .results-panel {
    max-height: none;
    min-height: 400px;
  }
}
</style>
