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

    <!-- 工作台面板 - 毛玻璃悬浮效果 -->
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
        class="absolute top-full mt-2 right-0 w-96 max-h-[500px] bg-white/80 backdrop-blur-xl rounded-2xl shadow-2xl border border-white/50 overflow-hidden z-50"
      >
        <!-- 头部 -->
        <div class="px-4 py-3 bg-gradient-to-r from-emerald-500/10 to-teal-500/10 border-b border-emerald-200/50">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <div class="w-8 h-8 rounded-lg bg-emerald-100 flex items-center justify-center">
                <FileText class="w-4 h-4 text-emerald-600" />
              </div>
              <div>
                <h3 class="text-sm font-semibold text-gray-900">当前会话文件</h3>
                <p class="text-xs text-gray-500">{{ files.length }} 个文件</p>
              </div>
            </div>
            <button
              @click="isOpen = false"
              class="p-1 hover:bg-gray-200/50 rounded-lg transition-colors"
            >
              <X class="w-4 h-4 text-gray-500" />
            </button>
          </div>
        </div>

        <!-- 文件列表 -->
        <div class="overflow-y-auto max-h-[400px] custom-scrollbar">
          <div v-if="files.length === 0" class="p-8 text-center">
            <FileQuestion class="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p class="text-sm text-gray-500">暂无文件</p>
            <p class="text-xs text-gray-400 mt-1">财报文件会自动添加到这里</p>
          </div>

          <div v-else class="p-3 space-y-2">
            <div
              v-for="(file, index) in files"
              :key="index"
              class="group relative bg-white/60 hover:bg-white/80 backdrop-blur-sm rounded-xl p-3 border border-gray-200/50 hover:border-emerald-300/50 transition-all duration-200 hover:shadow-md"
              :class="{ 'ring-2 ring-emerald-400 bg-emerald-50/50': file.selected }"
            >
              <!-- 文件信息 -->
              <div class="flex items-start gap-3">
                <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-orange-100 to-red-100 flex items-center justify-center shrink-0">
                  <FileText class="w-5 h-5 text-orange-600" />
                </div>
                
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2 mb-1">
                    <h4 class="text-sm font-medium text-gray-900 truncate">
                      {{ getDisplayName(file) }}
                    </h4>
                    <span v-if="file.selected" class="px-2 py-0.5 bg-emerald-500 text-white text-xs rounded-full">
                      已选中
                    </span>
                  </div>
                  <p class="text-xs text-gray-500">
                    {{ file.stock_code ? `股票代码: ${file.stock_code}` : (file.source === 'upload' ? '用户上传文件' : '财报文件') }}
                  </p>
                  <p class="text-xs text-gray-400 mt-1">{{ formatFileSize(file.size) }}</p>
                </div>
              </div>

              <!-- 操作按钮 -->
              <div class="flex items-center gap-2 mt-3">
                <button
                  @click="viewFile(file)"
                  class="flex-1 px-3 py-1.5 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 hover:border-emerald-400 hover:text-emerald-600 transition-all text-xs font-medium flex items-center justify-center gap-1.5"
                >
                  <Eye class="w-3.5 h-3.5" />
                  查看
                </button>
                <button
                  @click="toggleSelect(file)"
                  class="flex-1 px-3 py-1.5 rounded-lg transition-all text-xs font-medium flex items-center justify-center gap-1.5"
                  :class="file.selected 
                    ? 'bg-emerald-500 text-white hover:bg-emerald-600' 
                    : 'bg-emerald-50 text-emerald-600 hover:bg-emerald-100 border border-emerald-200'"
                >
                  <CheckCircle2 v-if="file.selected" class="w-3.5 h-3.5" />
                  <Circle v-else class="w-3.5 h-3.5" />
                  {{ file.selected ? '已选中' : '选为语料' }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- 底部操作栏 -->
        <div v-if="selectedFiles.length > 0" class="px-4 py-3 bg-gradient-to-r from-emerald-500/10 to-teal-500/10 border-t border-emerald-200/50">
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-600">
              已选中 <span class="font-semibold text-emerald-600">{{ selectedFiles.length }}</span> 个文件
            </span>
            <button
              @click="analyzeSelected"
              class="px-4 py-2 bg-gradient-to-r from-emerald-500 to-teal-500 text-white rounded-lg hover:from-emerald-600 hover:to-teal-600 transition-all text-sm font-medium shadow-md hover:shadow-lg flex items-center gap-2"
            >
              <Sparkles class="w-4 h-4" />
              基于选中文件分析
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { FolderOpen, FileText, FileQuestion, Eye, CheckCircle2, Circle, Sparkles, X, ChevronDown } from 'lucide-vue-next'

const props = defineProps({
  files: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['view-file', 'analyze-files'])

const isOpen = ref(false)

const toggleWorkspace = () => {
  isOpen.value = !isOpen.value
}

const selectedFiles = computed(() => {
  return props.files.filter(f => f.selected)
})

const viewFile = (file) => {
  emit('view-file', file)
}

const toggleSelect = (file) => {
  file.selected = !file.selected
}

const analyzeSelected = () => {
  emit('analyze-files', selectedFiles.value)
  isOpen.value = false
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

const formatFileSize = (bytes) => {
  if (!bytes) return '未知大小'
  const mb = bytes / 1024 / 1024
  return `${mb.toFixed(2)} MB`
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
