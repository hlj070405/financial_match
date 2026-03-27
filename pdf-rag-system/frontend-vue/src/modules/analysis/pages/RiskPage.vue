<template>
  <div class="h-full flex flex-col">
    <!-- Hero -->
    <div class="relative overflow-hidden bg-gradient-to-br from-rose-50 via-white to-orange-50 border-b border-gray-100">
      <div class="absolute inset-0 opacity-20">
        <div class="absolute top-3 left-16 w-48 h-48 bg-rose-200 rounded-full blur-3xl animate-pulse"></div>
        <div class="absolute bottom-0 right-10 w-40 h-40 bg-orange-200 rounded-full blur-3xl animate-pulse" style="animation-delay: 1s;"></div>
      </div>
      <div class="relative px-6 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-rose-500 to-orange-600 flex items-center justify-center shadow-md shadow-rose-500/20 shrink-0">
              <ShieldAlert class="w-4.5 h-4.5 text-white" />
            </div>
            <div>
              <h1 class="text-base font-bold text-gray-900">风险预警评分</h1>
              <p class="text-[11px] text-gray-500 mt-0.5">基于财务数据的风险量化评分与预警，识别潜在财务危机</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <input v-model="companyInput" @keydown.enter="runRiskCheck" type="text" placeholder="输入公司名称..."
              class="px-3 py-2 text-xs border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-rose-500/20 focus:border-rose-400 w-40 transition-all" />
            <button @click="runRiskCheck" :disabled="loading"
              class="px-4 py-2 bg-rose-600 text-white text-xs font-medium rounded-lg hover:bg-rose-700 transition-colors disabled:opacity-50 flex items-center gap-1.5">
              <Loader2 v-if="loading" class="w-3.5 h-3.5 animate-spin" />
              <Search v-else class="w-3.5 h-3.5" />
              {{ loading ? '检测中...' : '风险检测' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto p-6 custom-scrollbar">
      <!-- Empty -->
      <div v-if="!loading && !result" class="flex items-center justify-center h-full">
        <div class="text-center max-w-sm">
          <div class="p-3 rounded-xl bg-rose-50 inline-block mb-3">
            <ShieldAlert class="w-10 h-10 text-rose-300" />
          </div>
          <h3 class="text-sm font-semibold text-gray-700 mb-1.5">输入公司名称进行风险检测</h3>
          <p class="text-xs text-gray-400 leading-relaxed mb-4">系统将从财务造假风险、偿债能力、经营风险等多维度进行量化评分</p>
          <div class="flex flex-wrap gap-2 justify-center">
            <button v-for="ex in examples" :key="ex" @click="companyInput = ex; runRiskCheck()"
              class="px-3 py-1.5 text-[11px] text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-rose-50 hover:border-rose-300 hover:text-rose-700 transition-all">{{ ex }}</button>
          </div>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex flex-col items-center justify-center h-full">
        <div class="text-center">
          <Loader2 class="w-8 h-8 animate-spin text-rose-500 mx-auto" />
          <p class="text-xs text-gray-500 mt-3">AI 正在量化风险因子...</p>
        </div>
        <div v-if="streamText" class="mt-4 max-w-2xl w-full bg-gray-50 border border-gray-100 rounded-xl p-4 max-h-48 overflow-y-auto">
          <p class="text-[10px] font-bold text-gray-400 mb-1 uppercase tracking-wider">实时生成中</p>
          <pre class="text-[11px] text-gray-600 whitespace-pre-wrap font-mono leading-relaxed">{{ streamText.slice(-800) }}</pre>
        </div>
      </div>

      <!-- Results -->
      <div v-if="result && !loading" class="max-w-5xl mx-auto space-y-5">
        <!-- Demo Banner -->
        <div v-if="isDemo" class="bg-rose-50 border border-rose-200 rounded-xl px-4 py-2.5 flex items-center justify-between">
          <p class="text-[11px] text-rose-600"><span class="font-bold">示例数据</span> — 当前展示的是恒大地产风险评估示例，输入公司名称可获取实时分析</p>
          <button @click="clearDemo" class="text-[10px] text-rose-500 hover:text-rose-700 font-medium">清除示例</button>
        </div>
        <!-- Overall Score -->
        <div class="grid grid-cols-4 gap-4">
          <div class="col-span-1 bg-white border border-gray-100 rounded-xl p-5 shadow-sm flex flex-col items-center justify-center">
            <div ref="gaugeRef" class="w-full h-36"></div>
            <p class="text-xs font-bold text-gray-700 mt-1">综合风险评分</p>
            <p class="text-[10px] text-gray-400">{{ result.riskLevel }}</p>
          </div>
          <div class="col-span-3 grid grid-cols-3 gap-4">
            <div v-for="cat in result.categories" :key="cat.name"
              class="bg-white border rounded-xl p-4 shadow-sm transition-all hover:shadow-md"
              :class="cat.score > 70 ? 'border-rose-200' : cat.score > 40 ? 'border-amber-200' : 'border-emerald-200'">
              <div class="flex items-center justify-between mb-3">
                <h4 class="text-xs font-bold text-gray-800">{{ cat.name }}</h4>
                <span :class="[
                  'px-2 py-0.5 rounded-full text-[10px] font-bold',
                  cat.score > 70 ? 'bg-rose-100 text-rose-700' : cat.score > 40 ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'
                ]">{{ cat.score }}分</span>
              </div>
              <div class="w-full h-2 bg-gray-100 rounded-full overflow-hidden mb-2">
                <div class="h-full rounded-full transition-all duration-1000"
                  :class="cat.score > 70 ? 'bg-rose-500' : cat.score > 40 ? 'bg-amber-500' : 'bg-emerald-500'"
                  :style="{ width: cat.score + '%' }"></div>
              </div>
              <p class="text-[10px] text-gray-500 leading-relaxed">{{ cat.detail }}</p>
            </div>
          </div>
        </div>

        <!-- Risk Factors -->
        <div class="bg-white border border-gray-100 rounded-xl shadow-sm overflow-hidden">
          <div class="px-5 py-3 bg-gray-50 border-b border-gray-100">
            <h3 class="text-xs font-bold text-gray-800 flex items-center gap-2">
              <AlertTriangle class="w-3.5 h-3.5 text-amber-500" /> 风险因子明细
            </h3>
          </div>
          <div class="divide-y divide-gray-50">
            <div v-for="(f, i) in result.factors" :key="i" class="px-5 py-3 flex items-center gap-4 hover:bg-gray-50/50 transition-colors">
              <div :class="[
                'w-2 h-2 rounded-full shrink-0',
                f.level === 'high' ? 'bg-rose-500' : f.level === 'medium' ? 'bg-amber-500' : 'bg-emerald-500'
              ]"></div>
              <div class="flex-1 min-w-0">
                <p class="text-xs font-medium text-gray-800">{{ f.name }}</p>
                <p class="text-[10px] text-gray-500">{{ f.desc }}</p>
              </div>
              <span :class="[
                'px-2 py-0.5 rounded text-[10px] font-bold shrink-0',
                f.level === 'high' ? 'bg-rose-50 text-rose-600' : f.level === 'medium' ? 'bg-amber-50 text-amber-600' : 'bg-emerald-50 text-emerald-600'
              ]">{{ f.level === 'high' ? '高风险' : f.level === 'medium' ? '中风险' : '低风险' }}</span>
            </div>
          </div>
        </div>

        <!-- AI Summary -->
        <div class="bg-gradient-to-r from-gray-900 to-gray-800 rounded-xl p-5 text-white">
          <div class="flex items-center gap-2 mb-2">
            <Sparkles class="w-3.5 h-3.5 text-orange-400" />
            <span class="text-[10px] font-bold text-orange-300 uppercase tracking-wider">AI 风险研判</span>
          </div>
          <p class="text-xs text-gray-300 leading-relaxed">{{ result.aiSummary }}</p>
        </div>
      </div>

      <!-- Error -->
      <div v-if="error" class="max-w-5xl mx-auto mt-4 bg-red-50 border border-red-100 rounded-xl p-4 text-xs text-red-600">{{ error }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import { ShieldAlert, Search, Loader2, Sparkles, AlertTriangle } from 'lucide-vue-next'
import { useSSE } from '../../../composables/useSSE'
import { EXAMPLE_RISK } from '../../../composables/exampleData'

const companyInput = ref('')
const gaugeRef = ref(null)
const isDemo = ref(false)
let gaugeChart = null
const examples = ['贵州茅台', '比亚迪', '恒大地产', '招商银行']
const { loading, error, streamText, result, fetchSSE } = useSSE()

onMounted(() => {
  result.value = EXAMPLE_RISK
  isDemo.value = true
  nextTick(() => initGauge(EXAMPLE_RISK.overallScore))
})

const initGauge = (score) => {
  nextTick(() => {
    if (!gaugeRef.value) return
    if (gaugeChart) gaugeChart.dispose()
    gaugeChart = echarts.init(gaugeRef.value)
    gaugeChart.setOption({
      series: [{
        type: 'gauge', startAngle: 200, endAngle: -20, min: 0, max: 100,
        progress: { show: true, width: 14, roundCap: true, itemStyle: { color: score > 70 ? '#f43f5e' : score > 40 ? '#f59e0b' : '#10b981' } },
        pointer: { show: false },
        axisLine: { lineStyle: { width: 14, color: [[1, '#f3f4f6']] } },
        axisTick: { show: false }, splitLine: { show: false }, axisLabel: { show: false }, title: { show: false },
        detail: { valueAnimation: true, offsetCenter: [0, '10%'], fontSize: 28, fontWeight: 'bold', color: score > 70 ? '#f43f5e' : score > 40 ? '#f59e0b' : '#10b981', formatter: '{value}' },
        data: [{ value: score }]
      }]
    })
  })
}

const clearDemo = () => { result.value = null; isDemo.value = false }

const runRiskCheck = () => {
  if (!companyInput.value.trim()) return
  isDemo.value = false
  fetchSSE('/api/diagnosis/risk', { company: companyInput.value.trim() }, {
    onDone: (data) => { initGauge(data.overallScore) }
  })
}

onBeforeUnmount(() => {
  gaugeChart?.dispose()
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }
</style>
