<template>
  <div class="h-full flex flex-col">
    <!-- Hero -->
    <div class="relative overflow-hidden bg-gradient-to-br from-amber-50 via-white to-red-50 border-b border-gray-100">
      <div class="absolute inset-0 opacity-20">
        <div class="absolute top-3 left-16 w-48 h-48 bg-amber-200 rounded-full blur-3xl animate-pulse"></div>
        <div class="absolute bottom-0 right-10 w-40 h-40 bg-red-200 rounded-full blur-3xl animate-pulse" style="animation-delay:1s"></div>
      </div>
      <div class="relative px-6 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-amber-500 to-red-600 flex items-center justify-center shadow-md shadow-amber-500/20 shrink-0">
              <ShieldAlert class="w-4.5 h-4.5 text-white" />
            </div>
            <div>
              <h1 class="text-base font-bold text-gray-900">供应链风险评估</h1>
              <p class="text-[11px] text-gray-500 mt-0.5">供应链中断风险识别、影响评估与替代方案分析</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <input v-model="industry" @keydown.enter="assess" type="text" placeholder="输入行业/企业..."
              class="px-3 py-2 text-xs border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-amber-500/20 w-40 transition-all" />
            <button @click="assess" :disabled="loading"
              class="px-4 py-2 bg-amber-600 text-white text-xs font-medium rounded-lg hover:bg-amber-700 transition-colors disabled:opacity-50 flex items-center gap-1.5">
              <Loader2 v-if="loading" class="w-3.5 h-3.5 animate-spin" />
              <Search v-else class="w-3.5 h-3.5" />
              评估
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto p-5 custom-scrollbar">
      <!-- Empty -->
      <div v-if="!loading && !result" class="flex items-center justify-center h-full">
        <div class="text-center max-w-sm">
          <div class="p-3 rounded-xl bg-amber-50 inline-block mb-3">
            <ShieldAlert class="w-10 h-10 text-amber-300" />
          </div>
          <h3 class="text-sm font-semibold text-gray-700 mb-1.5">输入行业或企业名称</h3>
          <p class="text-xs text-gray-400 leading-relaxed mb-4">系统将分析供应链各环节的中断风险、地缘政治影响及替代方案</p>
          <div class="flex flex-wrap gap-2 justify-center">
            <button v-for="ex in examples" :key="ex" @click="industry = ex; assess()"
              class="px-3 py-1.5 text-[11px] text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-amber-50 hover:border-amber-300 hover:text-amber-700 transition-all">{{ ex }}</button>
          </div>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex flex-col items-center justify-center h-full">
        <div class="text-center">
          <Loader2 class="w-8 h-8 animate-spin text-amber-500 mx-auto" />
          <p class="text-xs text-gray-500 mt-3">AI 正在评估供应链风险...</p>
        </div>
        <div v-if="streamText" class="mt-4 max-w-2xl w-full bg-gray-50 border border-gray-100 rounded-xl p-4 max-h-48 overflow-y-auto">
          <p class="text-[10px] font-bold text-gray-400 mb-1 uppercase tracking-wider">实时生成中</p>
          <pre class="text-[11px] text-gray-600 whitespace-pre-wrap font-mono leading-relaxed">{{ streamText.slice(-800) }}</pre>
        </div>
      </div>

      <!-- Results -->
      <div v-if="result && !loading" class="max-w-5xl mx-auto space-y-5">
        <!-- Demo Banner -->
        <div v-if="isDemo" class="bg-amber-50 border border-amber-200 rounded-xl px-4 py-2.5 flex items-center justify-between">
          <p class="text-[11px] text-amber-600"><span class="font-bold">示例数据</span> — 当前展示的是半导体供应链风险示例，输入行业/企业名称可获取实时分析</p>
          <button @click="clearDemo" class="text-[10px] text-amber-500 hover:text-amber-700 font-medium">清除示例</button>
        </div>
        <!-- Overall Risk -->
        <div class="grid grid-cols-4 gap-4">
          <div v-for="card in result.overallCards" :key="card.label"
            :class="['bg-white border rounded-xl p-4 shadow-sm text-center', card.border]">
            <p class="text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-1">{{ card.label }}</p>
            <p :class="['text-xl font-bold font-mono', card.valueColor]">{{ card.value }}</p>
            <p class="text-[9px] text-gray-400 mt-0.5">{{ card.sub }}</p>
          </div>
        </div>

        <!-- Risk Matrix -->
        <div class="grid grid-cols-2 gap-4">
          <div class="bg-white border border-gray-100 rounded-xl shadow-sm p-5">
            <h3 class="text-xs font-bold text-gray-800 flex items-center gap-2 mb-3">
              <AlertTriangle class="w-4 h-4 text-amber-500" /> 风险热力矩阵
            </h3>
            <div ref="heatmapRef" class="w-full h-56"></div>
          </div>
          <div class="bg-white border border-gray-100 rounded-xl shadow-sm p-5">
            <h3 class="text-xs font-bold text-gray-800 flex items-center gap-2 mb-3">
              <MapPin class="w-4 h-4 text-blue-500" /> 地缘风险分布
            </h3>
            <div class="space-y-2">
              <div v-for="geo in result.geoRisks" :key="geo.region" class="flex items-center gap-3">
                <span class="text-xs text-gray-600 w-20 shrink-0">{{ geo.region }}</span>
                <div class="flex-1 h-4 bg-gray-100 rounded-full overflow-hidden relative">
                  <div class="h-full rounded-full transition-all duration-1000"
                    :class="geo.level > 70 ? 'bg-rose-500' : geo.level > 40 ? 'bg-amber-500' : 'bg-emerald-500'"
                    :style="{ width: geo.level + '%' }"></div>
                </div>
                <span :class="['text-[10px] font-bold w-8 text-right',
                  geo.level > 70 ? 'text-rose-600' : geo.level > 40 ? 'text-amber-600' : 'text-emerald-600']">{{ geo.level }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Risk Detail Table -->
        <div class="bg-white border border-gray-100 rounded-xl shadow-sm overflow-hidden">
          <div class="px-5 py-3 bg-gray-50 border-b border-gray-100">
            <h3 class="text-xs font-bold text-gray-800">供应链环节风险明细</h3>
          </div>
          <table class="w-full text-xs">
            <thead>
              <tr class="border-b border-gray-100">
                <th class="px-4 py-2.5 text-left font-bold text-gray-700">环节</th>
                <th class="px-4 py-2.5 text-center font-bold text-gray-700">风险等级</th>
                <th class="px-4 py-2.5 text-left font-bold text-gray-700">主要风险</th>
                <th class="px-4 py-2.5 text-left font-bold text-gray-700">替代方案</th>
                <th class="px-4 py-2.5 text-center font-bold text-gray-700">影响度</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(r, i) in result.risks" :key="i" class="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
                <td class="px-4 py-2.5 font-medium text-gray-700">{{ r.segment }}</td>
                <td class="px-4 py-2.5 text-center">
                  <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold',
                    r.level === '高' ? 'bg-rose-100 text-rose-700' : r.level === '中' ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700']">{{ r.level }}</span>
                </td>
                <td class="px-4 py-2.5 text-gray-600">{{ r.risk }}</td>
                <td class="px-4 py-2.5 text-gray-600">{{ r.alternative }}</td>
                <td class="px-4 py-2.5 text-center">
                  <div class="flex items-center justify-center gap-0.5">
                    <div v-for="s in 5" :key="s" :class="['w-2 h-2 rounded-full', s <= r.impact ? 'bg-amber-500' : 'bg-gray-200']"></div>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- AI Summary -->
        <div class="bg-gradient-to-r from-gray-900 to-gray-800 rounded-xl p-5 text-white">
          <div class="flex items-center gap-2 mb-2">
            <Sparkles class="w-3.5 h-3.5 text-amber-400" />
            <span class="text-[10px] font-bold text-amber-300 uppercase tracking-wider">AI 供应链研判</span>
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
import { ShieldAlert, Search, Loader2, AlertTriangle, MapPin, Sparkles } from 'lucide-vue-next'
import { useSSE } from '../../../composables/useSSE'
import { EXAMPLE_SUPPLY_RISK } from '../../../composables/exampleData'

const industry = ref('')
const heatmapRef = ref(null)
const isDemo = ref(false)
let heatmapChart = null
const examples = ['新能源汽车', '半导体', '光伏产业', '消费电子']
const { loading, error, streamText, result, fetchSSE } = useSSE()

onMounted(() => {
  result.value = EXAMPLE_SUPPLY_RISK
  isDemo.value = true
  nextTick(() => initHeatmap(EXAMPLE_SUPPLY_RISK))
})

const initHeatmap = (data) => {
  nextTick(() => {
    if (!heatmapRef.value) return
    const segments = data.heatmapSegments || []
    const dimensions = data.heatmapDimensions || ['中断概率', '影响程度', '恢复时间']
    const heatData = data.heatmapData || []
    if (!segments.length || !heatData.length) return
    if (heatmapChart) heatmapChart.dispose()
    heatmapChart = echarts.init(heatmapRef.value)
    heatmapChart.setOption({
      tooltip: { textStyle: { fontSize: 10 }, formatter: p => `${segments[p.data[1]]} - ${dimensions[p.data[0]]}: ${p.data[2]}` },
      grid: { top: 5, bottom: 30, left: 55, right: 10 },
      xAxis: { type: 'category', data: dimensions, axisLabel: { fontSize: 9 }, splitArea: { show: true } },
      yAxis: { type: 'category', data: segments, axisLabel: { fontSize: 9 }, splitArea: { show: true } },
      visualMap: { min: 0, max: 100, show: false, inRange: { color: ['#dcfce7', '#fef9c3', '#fecaca', '#fca5a5'] } },
      series: [{ type: 'heatmap', data: heatData, label: { show: true, fontSize: 10, color: '#374151' }, emphasis: { itemStyle: { shadowBlur: 10 } } }]
    })
  })
}

const clearDemo = () => { result.value = null; isDemo.value = false }

const assess = () => {
  if (!industry.value.trim()) return
  isDemo.value = false
  fetchSSE('/api/chain/supply-risk', { name: industry.value.trim() }, {
    onDone: (data) => { initHeatmap(data) }
  })
}

onBeforeUnmount(() => { heatmapChart?.dispose() })
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }
</style>
