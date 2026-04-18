<template>
  <div class="relative">
    <!-- 触发按钮 -->
    <button
      @click="toggleWorkspace"
      class="group relative px-4 py-2 bg-gradient-to-r from-emerald-500 to-teal-500 text-white rounded-lg hover:from-emerald-600 hover:to-teal-600 transition-all duration-300 shadow-lg hover:shadow-xl flex items-center gap-2"
      :class="{ 'ring-2 ring-emerald-300': isOpen }"
    >
      <FolderOpen class="w-4 h-4" />
      <span class="text-sm font-medium">文件工作台</span>
      <span v-if="files.length > 0" class="px-2 py-0.5 bg-white/20 rounded-full text-xs">
        {{ files.length }}
      </span>
      <ChevronDown 
        class="w-4 h-4 transition-transform duration-300" 
        :class="{ 'rotate-180': isOpen }"
      />
    </button>

    <!-- 工作台面板 -->
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 translate-y-2"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 translate-y-2"
    >
      <div
        v-if="isOpen"
        class="absolute top-full mt-2 right-0 w-[420px] max-h-[560px] bg-white/90 backdrop-blur-xl rounded-2xl shadow-2xl border border-white/50 overflow-hidden z-50 flex flex-col"
      >
        <!-- 头部 -->
        <div class="px-4 py-3 bg-gradient-to-r from-emerald-500/10 to-teal-500/10 border-b border-emerald-200/50 shrink-0">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <div class="w-8 h-8 rounded-lg bg-emerald-100 flex items-center justify-center">
                <FileText class="w-4 h-4 text-emerald-600" />
              </div>
              <div>
                <h3 class="text-sm font-semibold text-gray-900">知识库 & 文件工作台</h3>
                <p class="text-xs text-gray-500">{{ files.length }} 个文档 · {{ indexedCount }} 个已向量化</p>
              </div>
            </div>
            <div class="flex items-center gap-1">
              <div class="relative">
                <button @click="showUploadMenu = !showUploadMenu" class="p-1.5 hover:bg-emerald-50 rounded-lg transition-colors" title="上传PDF">
                  <Upload class="w-4 h-4 text-emerald-600" />
                </button>
                <div v-if="showUploadMenu" class="absolute top-full right-0 mt-1 w-48 bg-white rounded-lg shadow-xl border border-gray-200 z-50 overflow-hidden">
                  <label class="flex items-center gap-2 px-3 py-2.5 hover:bg-emerald-50 cursor-pointer transition-colors text-xs text-gray-700">
                    <Database class="w-3.5 h-3.5 text-emerald-600" />
                    <div><div class="font-medium">上传并向量化</div><div class="text-[10px] text-gray-400">入知识库，可检索</div></div>
                    <input type="file" accept=".pdf" class="hidden" @change="onUploadEmbed" />
                  </label>
                  <label class="flex items-center gap-2 px-3 py-2.5 hover:bg-blue-50 cursor-pointer transition-colors text-xs text-gray-700 border-t border-gray-100">
                    <FileText class="w-3.5 h-3.5 text-blue-600" />
                    <div><div class="font-medium">仅上传</div><div class="text-[10px] text-gray-400">不入库，后续可向量化</div></div>
                    <input type="file" accept=".pdf" class="hidden" @change="onUploadOnly" />
                  </label>
                  <label class="flex items-center gap-2 px-3 py-2.5 hover:bg-amber-50 cursor-pointer transition-colors text-xs text-gray-700 border-t border-gray-100">
                    <Zap class="w-3.5 h-3.5 text-amber-600" />
                    <div><div class="font-medium">直接分析</div><div class="text-[10px] text-gray-400">OCR 提取 + AI 即时分析</div></div>
                    <input type="file" accept=".pdf" class="hidden" @change="onDirectAnalyze" />
                  </label>
                </div>
              </div>
              <button @click="isOpen = false" class="p-1.5 hover:bg-gray-200/50 rounded-lg transition-colors">
                <X class="w-4 h-4 text-gray-500" />
              </button>
            </div>
          </div>

          <!-- 搜索模式切换 -->
          <div class="flex items-center mt-2.5 bg-gray-100 rounded-lg p-0.5">
            <button
              @click="searchScope = 'all'"
              class="flex-1 px-3 py-1.5 text-xs font-medium rounded-md transition-all"
              :class="searchScope === 'all' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
            >全部文档</button>
            <button
              @click="searchScope = 'indexed'"
              class="flex-1 px-3 py-1.5 text-xs font-medium rounded-md transition-all"
              :class="searchScope === 'indexed' ? 'bg-white text-emerald-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
            >已向量化</button>
            <button
              @click="searchScope = 'not_indexed'"
              class="flex-1 px-3 py-1.5 text-xs font-medium rounded-md transition-all"
              :class="searchScope === 'not_indexed' ? 'bg-white text-amber-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
            >未向量化</button>
          </div>
        </div>

        <!-- 上传进度条 -->
        <div v-if="uploading" class="px-4 py-2 bg-blue-50 border-b border-blue-100 shrink-0">
          <div class="flex items-center gap-2 text-xs text-blue-700">
            <Loader2 class="w-3.5 h-3.5 animate-spin" />
            <span>{{ uploadingName }} 上传并向量化中...</span>
          </div>
        </div>

        <!-- 文件列表 -->
        <div class="flex-1 overflow-y-auto custom-scrollbar">
          <div v-if="filteredFiles.length === 0" class="p-8 text-center">
            <FileQuestion class="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p class="text-sm text-gray-500">{{ searchScope === 'all' ? '暂无文档' : searchScope === 'indexed' ? '暂无已向量化文档' : '所有文档都已向量化' }}</p>
            <p class="text-xs text-gray-400 mt-1">上传 PDF 文件，AI 将自动解析并建立向量索引</p>
          </div>

          <div v-else class="p-3 space-y-2">
            <div
              v-for="(file, index) in filteredFiles"
              :key="file.id || index"
              class="group relative bg-white/60 hover:bg-white/80 backdrop-blur-sm rounded-xl p-3 border border-gray-200/50 hover:border-emerald-300/50 transition-all duration-200 hover:shadow-md"
              :class="{ 'ring-2 ring-emerald-400 bg-emerald-50/50': file.selected }"
            >
              <div class="flex items-start gap-3">
                <div class="w-10 h-10 rounded-lg flex items-center justify-center shrink-0"
                  :class="file.indexed ? 'bg-gradient-to-br from-emerald-100 to-teal-100' : 'bg-gradient-to-br from-orange-100 to-red-100'">
                  <Database v-if="file.indexed" class="w-5 h-5 text-emerald-600" />
                  <FileText v-else class="w-5 h-5 text-orange-600" />
                </div>
                
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2 mb-1">
                    <h4 class="text-sm font-medium text-gray-900 truncate">{{ getDisplayName(file) }}</h4>
                    <span v-if="file.indexed" class="px-1.5 py-0.5 bg-emerald-100 text-emerald-700 text-[10px] rounded-full font-medium">
                      {{ file.chunks || 0 }} 块
                    </span>
                    <span v-else class="px-1.5 py-0.5 bg-amber-100 text-amber-700 text-[10px] rounded-full font-medium">
                      未向量化
                    </span>
                    <span v-if="file.selected" class="px-1.5 py-0.5 bg-emerald-500 text-white text-[10px] rounded-full font-medium">
                      已选中
                    </span>
                  </div>
                  <p class="text-xs text-gray-500">
                    {{ file.stock_code ? `${file.stock_code}` : '' }}
                    {{ file.company ? file.company : '' }}
                    {{ file.year ? `${file.year}年` : '' }}
                    {{ file.source === 'upload' ? '用户上传' : file.source === 'cninfo' ? '巨潮资讯' : '' }}
                  </p>
                </div>
              </div>

              <div class="flex items-center gap-2 mt-2.5">
                <button v-if="file.pdf_path"
                  @click="viewFile(file)"
                  class="flex-1 px-2.5 py-1.5 bg-white border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50 hover:border-emerald-300 hover:text-emerald-600 transition-all text-xs font-medium flex items-center justify-center gap-1"
                >
                  <Eye class="w-3 h-3" /> 查看
                </button>
                <button v-if="file.pdf_path && file.id"
                  @click="analyzeExisting(file)"
                  class="flex-1 px-2.5 py-1.5 bg-violet-50 border border-violet-200 text-violet-700 rounded-lg hover:bg-violet-100 transition-all text-xs font-medium flex items-center justify-center gap-1"
                >
                  <Sparkles class="w-3 h-3" /> 直接分析
                </button>
                <button v-if="!file.indexed"
                  @click="indexFile(file)"
                  :disabled="file._indexing"
                  class="flex-1 px-2.5 py-1.5 bg-amber-50 border border-amber-200 text-amber-700 rounded-lg hover:bg-amber-100 transition-all text-xs font-medium flex items-center justify-center gap-1 disabled:opacity-50"
                >
                  <Loader2 v-if="file._indexing" class="w-3 h-3 animate-spin" />
                  <Zap v-else class="w-3 h-3" />
                  {{ file._indexing ? '向量化中' : '向量化' }}
                </button>
                <button v-if="file.indexed"
                  @click="toggleSelect(file)"
                  class="flex-1 px-2.5 py-1.5 rounded-lg transition-all text-xs font-medium flex items-center justify-center gap-1"
                  :class="file.selected 
                    ? 'bg-emerald-500 text-white hover:bg-emerald-600' 
                    : 'bg-emerald-50 text-emerald-600 hover:bg-emerald-100 border border-emerald-200'"
                >
                  <CheckCircle2 v-if="file.selected" class="w-3 h-3" />
                  <Circle v-else class="w-3 h-3" />
                  {{ file.selected ? '取消选中' : '选为参考' }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- 底部操作栏 -->
        <div class="px-4 py-3 bg-gradient-to-r from-emerald-500/5 to-teal-500/5 border-t border-gray-100 shrink-0">
          <div v-if="selectedFiles.length > 0" class="flex items-center justify-between">
            <span class="text-xs text-gray-600">
              已选 <span class="font-bold text-emerald-600">{{ selectedFiles.length }}</span> 个文档作为参考
            </span>
            <div class="flex items-center gap-2">
              <button @click="clearSelection" class="px-3 py-1.5 text-xs text-gray-500 hover:text-gray-700 transition-colors">
                清除
              </button>
              <button
                @click="analyzeSelected"
                class="px-3 py-1.5 bg-gradient-to-r from-emerald-500 to-teal-500 text-white rounded-lg hover:from-emerald-600 hover:to-teal-600 transition-all text-xs font-medium shadow-md flex items-center gap-1.5"
              >
                <Sparkles class="w-3.5 h-3.5" /> 基于选中分析
              </button>
            </div>
          </div>
          <div v-else class="text-center">
            <p class="text-xs text-gray-400">选择已向量化的文档作为 AI 分析参考范围</p>
            <p class="text-[10px] text-gray-300 mt-0.5">不选择则 AI 检索全部文档</p>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { FolderOpen, FileText, FileQuestion, Eye, CheckCircle2, Circle, Sparkles, X, ChevronDown, Upload, Database, Zap, Loader2 } from 'lucide-vue-next'

const props = defineProps({
  files: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['view-file', 'analyze-files', 'upload-and-index', 'index-file', 'refresh', 'direct-analyze', 'analyze-existing'])

const isOpen = ref(false)
const searchScope = ref('all')
const uploading = ref(false)
const uploadingName = ref('')
const showUploadMenu = ref(false)

const toggleWorkspace = () => {
  isOpen.value = !isOpen.value
}

const indexedCount = computed(() => props.files.filter(f => f.indexed).length)

const filteredFiles = computed(() => {
  if (searchScope.value === 'indexed') return props.files.filter(f => f.indexed)
  if (searchScope.value === 'not_indexed') return props.files.filter(f => !f.indexed)
  return props.files
})

const selectedFiles = computed(() => {
  return props.files.filter(f => f.selected)
})

const viewFile = (file) => {
  emit('view-file', file)
}

const toggleSelect = (file) => {
  file.selected = !file.selected
}

const clearSelection = () => {
  props.files.forEach(f => { f.selected = false })
}

const analyzeSelected = () => {
  emit('analyze-files', selectedFiles.value)
  isOpen.value = false
}

const _doUpload = async (e, endpoint, successMsg) => {
  const file = e.target.files?.[0]
  if (!file) return
  showUploadMenu.value = false
  uploading.value = true
  uploadingName.value = file.name
  try {
    const token = localStorage.getItem('access_token')
    const formData = new FormData()
    formData.append('file', file)
    const resp = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    })
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}))
      throw new Error(err.detail || '上传失败')
    }
    emit('refresh')
    return resp
  } catch (err) {
    console.error('上传失败:', err)
    alert('上传失败: ' + err.message)
  } finally {
    uploading.value = false
    uploadingName.value = ''
    e.target.value = ''
  }
}

const onUploadEmbed = (e) => _doUpload(e, '/api/rag/ingest/upload')

const onUploadOnly = (e) => _doUpload(e, '/api/rag/upload-only')

const onDirectAnalyze = async (e) => {
  const file = e.target.files?.[0]
  if (!file) return
  showUploadMenu.value = false
  // 直接分析模式: emit 事件给父组件处理（需要流式显示结果）
  emit('direct-analyze', file)
  e.target.value = ''
}

const analyzeExisting = (file) => {
  emit('analyze-existing', file)
}

const indexFile = async (file) => {
  if (!file.id) return
  file._indexing = true
  try {
    const token = localStorage.getItem('access_token')
    const resp = await fetch('/api/rag/ingest', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ document_id: file.id })
    })
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}))
      throw new Error(err.detail || '向量化失败')
    }
    emit('refresh')
  } catch (err) {
    console.error('向量化失败:', err)
    alert('向量化失败: ' + err.message)
  } finally {
    file._indexing = false
  }
}

const limitText = (text, maxLength = 32) => {
  const raw = String(text || '').trim()
  if (!raw) return '未命名文件'
  return raw.length > maxLength ? `${raw.slice(0, maxLength)}...` : raw
}

const getDisplayName = (file) => {
  if (file?.title) return limitText(file.title)
  if (file?.name) return limitText(file.name)
  if (file?.company && file?.year) return limitText(`${file.company} ${file.year}年财报`)
  return '未命名文件'
}
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(16, 185, 129, 0.3);
  border-radius: 2px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(16, 185, 129, 0.5);
}
</style>
