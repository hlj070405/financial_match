<template>
  <div class="h-full flex flex-col">
    <!-- Hero -->
    <div class="relative overflow-hidden bg-gradient-to-br from-blue-50 via-white to-sky-50 border-b border-gray-100">
      <div class="absolute inset-0 opacity-20">
        <div class="absolute top-3 left-16 w-48 h-48 bg-blue-200 rounded-full blur-3xl animate-pulse"></div>
        <div class="absolute bottom-0 right-10 w-40 h-40 bg-sky-200 rounded-full blur-3xl animate-pulse" style="animation-delay: 1s;"></div>
      </div>
      <div class="relative px-6 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-sky-600 flex items-center justify-center shadow-md shadow-blue-500/20 shrink-0">
              <BarChart3 class="w-4.5 h-4.5 text-white" />
            </div>
            <div>
              <h1 class="text-base font-bold text-gray-900">基础财报解读</h1>
              <p class="text-[11px] text-gray-500 mt-0.5">核心财务指标提取与通俗解读，AI驱动的企业财务全景诊断</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <input v-model="companyInput" @keydown.enter="fetchDiagnosis" type="text" placeholder="输入公司名称..."
              class="px-3 py-2 text-xs border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 w-40 transition-all" />
            <button @click="fetchDiagnosis" :disabled="loading"
              class="px-4 py-2 bg-gray-900 text-white text-xs font-medium rounded-lg hover:bg-gray-800 transition-colors disabled:opacity-50 flex items-center gap-1.5">
              <Loader2 v-if="loading" class="w-3.5 h-3.5 animate-spin" />
              <Search v-else class="w-3.5 h-3.5" />
              {{ loading ? '分析中...' : '诊断' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Content -->
    <div class="flex-1 overflow-y-auto p-6 custom-scrollbar">
      <!-- Loading -->
      <div v-if="loading && !diagnosisData" class="flex flex-col items-center justify-center h-full">
        <div class="text-center">
          <Loader2 class="w-8 h-8 animate-spin text-blue-500 mx-auto" />
          <p class="text-xs text-gray-500 mt-3">AI 正在分析企业财务数据...</p>
        </div>
        <div v-if="streamText" class="mt-4 max-w-2xl w-full bg-gray-50 border border-gray-100 rounded-xl p-4 max-h-48 overflow-y-auto">
          <p class="text-[10px] font-bold text-gray-400 mb-1 uppercase tracking-wider">实时生成中</p>
          <pre class="text-[11px] text-gray-600 whitespace-pre-wrap font-mono leading-relaxed">{{ streamText.slice(-800) }}</pre>
        </div>
      </div>

      <!-- Empty -->
      <div v-else-if="!diagnosisData" class="flex items-center justify-center h-full">
        <div class="text-center max-w-sm">
          <div class="p-3 rounded-xl bg-gray-50 inline-block mb-3">
            <BarChart3 class="w-10 h-10 text-gray-300" />
          </div>
          <h3 class="text-sm font-semibold text-gray-700 mb-1.5">输入公司名称开始诊断</h3>
          <p class="text-xs text-gray-400 leading-relaxed">AI 将自动分析企业财报，提取核心指标，生成行业对标与风险评估</p>
          <div class="flex flex-wrap gap-2 justify-center mt-4">
            <button v-for="ex in examples" :key="ex" @click="companyInput = ex; fetchDiagnosis()"
              class="px-3 py-1.5 text-[11px] text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-blue-50 hover:border-blue-300 hover:text-blue-700 transition-all">{{ ex }}</button>
          </div>
        </div>
      </div>

      <!-- Results -->
      <template v-else>
        <!-- Demo Banner -->
        <div v-if="isDemo" class="bg-blue-50 border border-blue-200 rounded-xl px-4 py-2.5 mb-4 flex items-center justify-between">
          <p class="text-[11px] text-blue-600"><span class="font-bold">示例数据</span> — 当前展示的是AI分析示例，输入公司名称可获取实时分析</p>
          <button @click="diagnosisData = null; isDemo = false" class="text-[10px] text-blue-500 hover:text-blue-700 font-medium">清除示例</button>
        </div>
        <div v-if="diagnosisData.summary" class="bg-gradient-to-r from-gray-900 to-gray-800 rounded-xl p-5 text-white mb-5">
          <div class="flex items-center gap-2 mb-1.5">
            <Sparkles class="w-3.5 h-3.5 text-orange-400" />
            <span class="text-[10px] font-semibold text-orange-300 uppercase tracking-wider">AI 诊断摘要</span>
          </div>
          <h3 class="text-sm font-bold mb-1">{{ diagnosisData.company }} · {{ diagnosisData.period }}</h3>
          <p class="text-xs text-gray-300 leading-relaxed">{{ diagnosisData.summary }}</p>
        </div>
        <DiagnosisRenderer :components="diagnosisData.components || []" />
      </template>

      <div v-if="error" class="bg-red-50 border border-red-100 rounded-xl p-3 text-xs text-red-600 mt-4">{{ error }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { BarChart3, Search, Loader2, Sparkles } from 'lucide-vue-next'
import DiagnosisRenderer from '../../diagnosis/DiagnosisRenderer.vue'
import { useSSE } from '../../../composables/useSSE'
import { EXAMPLE_DIAGNOSIS } from '../../../composables/exampleData'

const companyInput = ref('')
const diagnosisData = ref(null)
const isDemo = ref(false)
const examples = ['贵州茅台', '比亚迪', '宁德时代', '招商银行']
const { loading, error, streamText, fetchSSE } = useSSE()

onMounted(() => {
  diagnosisData.value = EXAMPLE_DIAGNOSIS
  isDemo.value = true
})

const fetchDiagnosis = () => {
  if (!companyInput.value.trim()) return
  isDemo.value = false
  diagnosisData.value = null
  fetchSSE('/api/diagnosis/analyze', { company: companyInput.value.trim() }, {
    onDone: (data) => { diagnosisData.value = data }
  })
}
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }
</style>
