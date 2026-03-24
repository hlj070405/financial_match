<template>
  <!-- 财报准备中占位符 -->
  <div v-if="status === 'preparing'" class="bg-gray-50 border border-gray-200 rounded-xl p-4 flex items-center gap-3 animate-pulse">
    <div class="w-10 h-10 rounded-lg bg-gray-200 flex items-center justify-center">
      <FileText class="w-5 h-5 text-gray-400" />
    </div>
    <div class="flex-1">
      <p class="text-sm text-gray-600 font-medium">📄 正在获取相关财报资料...</p>
      <p class="text-xs text-gray-400 mt-0.5">请稍候，系统正在为您准备财报文件</p>
    </div>
    <Loader2 class="w-5 h-5 text-gray-400 animate-spin" />
  </div>

  <!-- 暂不支持占位符 -->
  <div v-else-if="status === 'unsupported'" class="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
    <div class="flex items-start gap-3">
      <div class="w-10 h-10 rounded-lg bg-yellow-100 flex items-center justify-center shrink-0">
        <FileText class="w-5 h-5 text-yellow-600" />
      </div>
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-1">
          <h4 class="text-sm font-semibold text-gray-900">{{ report.company }} ({{ report.stock_code }})</h4>
          <span class="px-2 py-0.5 bg-yellow-100 text-yellow-700 text-xs font-medium rounded-full">暂不支持</span>
        </div>
        <p class="text-xs text-gray-600">{{ report.message }}</p>
      </div>
    </div>
  </div>

  <!-- 财报就绪占位符 -->
  <div v-else-if="status === 'ready'" class="bg-gradient-to-r from-gray-50 to-gray-100/50 border border-gray-200 rounded-xl p-4 hover:shadow-md transition-all duration-300 group">
    <div class="flex items-start gap-3">
      <div class="w-10 h-10 rounded-lg bg-orange-100 flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform">
        <FileCheck class="w-5 h-5 text-orange-600" />
      </div>
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-1">
          <h4 class="text-sm font-semibold text-gray-900">{{ report.company }} {{ report.year }}年财报</h4>
          <span class="px-2 py-0.5 bg-green-100 text-green-700 text-xs font-medium rounded-full">已就绪</span>
        </div>
        <p class="text-xs text-gray-500 mb-3">{{ report.message }}</p>
        
        <div class="flex items-center gap-2">
          <button 
            @click="viewPdf"
            class="px-3 py-1.5 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 hover:border-orange-400 hover:text-orange-600 transition-all text-xs font-medium flex items-center gap-1.5 group/btn"
          >
            <Eye class="w-3.5 h-3.5" />
            查看财报
          </button>
          <button 
            @click="analyzeWithReport"
            class="px-3 py-1.5 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors text-xs font-medium flex items-center gap-1.5 shadow-sm"
          >
            <Sparkles class="w-3.5 h-3.5" />
            基于此财报深度分析
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { FileText, FileCheck, Loader2, Eye, Sparkles } from 'lucide-vue-next'

const props = defineProps({
  status: {
    type: String,
    required: true,
    validator: (value) => ['preparing', 'ready', 'unsupported'].includes(value)
  },
  report: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['view-pdf', 'analyze'])

const viewPdf = () => {
  emit('view-pdf', props.report)
}

const analyzeWithReport = () => {
  emit('analyze', props.report)
}
</script>
