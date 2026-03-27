<template>
  <div class="h-full flex flex-col">
    <!-- Hero -->
    <div class="relative overflow-hidden bg-gradient-to-br from-indigo-50 via-white to-violet-50 border-b border-gray-100">
      <div class="absolute inset-0 opacity-20">
        <div class="absolute top-3 left-16 w-48 h-48 bg-indigo-200 rounded-full blur-3xl animate-pulse"></div>
        <div class="absolute bottom-0 right-10 w-40 h-40 bg-violet-200 rounded-full blur-3xl animate-pulse" style="animation-delay:1s"></div>
      </div>
      <div class="relative px-6 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-md shadow-indigo-500/20 shrink-0">
              <Target class="w-4.5 h-4.5 text-white" />
            </div>
            <div>
              <h1 class="text-base font-bold text-gray-900">竞争格局对比</h1>
              <p class="text-[11px] text-gray-500 mt-0.5">行业竞争态势分析，市场份额与核心能力雷达对比</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <input v-model="industryInput" @keydown.enter="loadCompete" type="text" placeholder="输入行业名称..."
              class="px-3 py-2 text-xs border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 w-36 transition-all" />
            <button @click="loadCompete" :disabled="loading"
              class="px-4 py-2 bg-indigo-600 text-white text-xs font-medium rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 flex items-center gap-1.5">
              <Loader2 v-if="loading" class="w-3.5 h-3.5 animate-spin" />
              <Target v-else class="w-3.5 h-3.5" />
              {{ loading ? '分析中...' : '格局分析' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="flex-1 flex min-h-0">
      <!-- Empty State -->
      <div v-if="!loading && !result" class="flex-1 flex items-center justify-center">
        <div class="text-center max-w-sm">
          <div class="p-3 rounded-xl bg-indigo-50 inline-block mb-3">
            <Target class="w-10 h-10 text-indigo-300" />
          </div>
          <h3 class="text-sm font-semibold text-gray-700 mb-1.5">输入行业名称分析竞争格局</h3>
          <p class="text-xs text-gray-400 leading-relaxed mb-4">AI 将分析行业市场份额、波特五力、企业竞争力等多维度数据</p>
          <div class="flex flex-wrap gap-2 justify-center">
            <button v-for="ex in examples" :key="ex" @click="industryInput = ex; loadCompete()"
              class="px-3 py-1.5 text-[11px] text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-indigo-50 hover:border-indigo-300 hover:text-indigo-700 transition-all">{{ ex }}</button>
          </div>
        </div>
      </div>

      <!-- Loading -->
      <div v-else-if="loading" class="flex-1 flex flex-col items-center justify-center">
        <div class="text-center">
          <Loader2 class="w-8 h-8 animate-spin text-indigo-500 mx-auto" />
          <p class="text-xs text-gray-500 mt-3">AI 正在分析行业竞争格局...</p>
        </div>
        <div v-if="streamText" class="mt-4 max-w-2xl w-full bg-gray-50 border border-gray-100 rounded-xl p-4 max-h-48 overflow-y-auto">
          <p class="text-[10px] font-bold text-gray-400 mb-1 uppercase tracking-wider">实时生成中</p>
          <pre class="text-[11px] text-gray-600 whitespace-pre-wrap font-mono leading-relaxed">{{ streamText.slice(-800) }}</pre>
        </div>
      </div>

      <!-- Results -->
      <template v-else-if="result">
        <!-- Main -->
        <div class="flex-1 overflow-y-auto p-5 space-y-4 custom-scrollbar">
          <!-- Demo Banner -->
          <div v-if="isDemo" class="bg-indigo-50 border border-indigo-200 rounded-xl px-4 py-2.5 flex items-center justify-between">
            <p class="text-[11px] text-indigo-600"><span class="font-bold">示例数据</span> — 当前展示的是动力电池行业竞争格局示例，输入行业名称可获取实时分析</p>
            <button @click="clearDemo" class="text-[10px] text-indigo-500 hover:text-indigo-700 font-medium">清除示例</button>
          </div>
          <!-- Market Share + Radar -->
          <div class="grid grid-cols-2 gap-4">
            <div class="bg-white border border-gray-100 rounded-xl shadow-sm p-5">
              <h3 class="text-xs font-bold text-gray-800 flex items-center gap-2 mb-3">
                <PieChart class="w-4 h-4 text-indigo-500" /> 市场份额分布
              </h3>
              <div ref="shareRef" class="w-full h-52"></div>
            </div>
            <div class="bg-white border border-gray-100 rounded-xl shadow-sm p-5">
              <h3 class="text-xs font-bold text-gray-800 flex items-center gap-2 mb-3">
                <RadarIcon class="w-4 h-4 text-violet-500" /> 综合能力雷达
              </h3>
              <div ref="radarRef" class="w-full h-52"></div>
            </div>
          </div>

          <!-- Trend -->
          <div v-if="result.trend" class="bg-white border border-gray-100 rounded-xl shadow-sm overflow-hidden">
            <div class="px-5 py-3 border-b border-gray-50">
              <h3 class="text-xs font-bold text-gray-800">市场份额变化趋势</h3>
            </div>
            <div ref="trendRef" class="w-full h-48"></div>
          </div>

          <!-- Company Table -->
          <div class="bg-white border border-gray-100 rounded-xl shadow-sm overflow-hidden">
            <div class="px-5 py-3 bg-gray-50 border-b border-gray-100">
              <h3 class="text-xs font-bold text-gray-800">龙头企业对比</h3>
            </div>
            <table class="w-full text-xs">
              <thead>
                <tr class="border-b border-gray-100">
                  <th class="px-4 py-2.5 text-left font-bold text-gray-700">企业</th>
                  <th class="px-4 py-2.5 text-center font-bold text-gray-700">市占率</th>
                  <th class="px-4 py-2.5 text-center font-bold text-gray-700">营收(亿)</th>
                  <th class="px-4 py-2.5 text-center font-bold text-gray-700">增速</th>
                  <th class="px-4 py-2.5 text-center font-bold text-gray-700">毛利率</th>
                  <th class="px-4 py-2.5 text-center font-bold text-gray-700">研发占比</th>
                  <th class="px-4 py-2.5 text-center font-bold text-gray-700">竞争力</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="co in result.companies" :key="co.name" class="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
                  <td class="px-4 py-2.5">
                    <div class="flex items-center gap-2">
                      <div class="w-2 h-2 rounded-full" :style="{ background: co.color || '#6366f1' }"></div>
                      <span class="font-medium text-gray-700">{{ co.name }}</span>
                    </div>
                  </td>
                  <td class="px-4 py-2.5 text-center font-mono font-bold text-gray-800">{{ co.share }}%</td>
                  <td class="px-4 py-2.5 text-center font-mono text-gray-600">{{ co.revenue }}</td>
                  <td class="px-4 py-2.5 text-center">
                    <span :class="['font-mono', co.growth > 0 ? 'text-rose-600' : 'text-emerald-600']">
                      {{ co.growth > 0 ? '+' : '' }}{{ co.growth }}%
                    </span>
                  </td>
                  <td class="px-4 py-2.5 text-center font-mono text-gray-600">{{ co.margin }}%</td>
                  <td class="px-4 py-2.5 text-center font-mono text-gray-600">{{ co.rnd }}%</td>
                  <td class="px-4 py-2.5 text-center">
                    <div class="flex items-center justify-center gap-0.5">
                      <div v-for="s in 5" :key="s" :class="['w-2.5 h-1.5 rounded-sm', s <= co.strength ? 'bg-indigo-500' : 'bg-gray-200']"></div>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Right Sidebar -->
        <div class="w-64 border-l border-gray-100 bg-gray-50/50 p-4 flex flex-col gap-3 shrink-0 overflow-y-auto custom-scrollbar">
          <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
            <h4 class="text-[11px] font-bold text-gray-700 flex items-center gap-1.5 mb-3">
              <Shield class="w-3.5 h-3.5 text-indigo-500" /> 波特五力分析
            </h4>
            <div class="space-y-2.5">
              <div v-for="force in result.porterForces" :key="force.name">
                <div class="flex items-center justify-between mb-1">
                  <span class="text-[10px] text-gray-600">{{ force.name }}</span>
                  <span :class="['text-[9px] font-bold px-1.5 py-0.5 rounded',
                    force.level === '强' ? 'bg-rose-50 text-rose-600' : force.level === '中' ? 'bg-amber-50 text-amber-600' : 'bg-emerald-50 text-emerald-600']">{{ force.level }}</span>
                </div>
                <div class="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div class="h-full rounded-full transition-all duration-1000"
                    :class="force.score > 70 ? 'bg-rose-500' : force.score > 40 ? 'bg-amber-500' : 'bg-emerald-500'"
                    :style="{ width: force.score + '%' }"></div>
                </div>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm flex-1">
            <h4 class="text-[11px] font-bold text-gray-700 flex items-center gap-1.5 mb-3">
              <Lightbulb class="w-3.5 h-3.5 text-amber-500" /> 竞争要点
            </h4>
            <div class="space-y-2">
              <div v-for="point in result.keyPoints" :key="point" class="flex items-start gap-2">
                <div class="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-1 shrink-0"></div>
                <p class="text-[10px] text-gray-600 leading-relaxed">{{ point }}</p>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- Error -->
      <div v-if="error" class="absolute bottom-4 left-4 right-4 bg-red-50 border border-red-100 rounded-xl p-4 text-xs text-red-600 z-10">{{ error }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import { Target, PieChart, Radar as RadarIcon, Shield, Lightbulb, Loader2 } from 'lucide-vue-next'
import { useSSE } from '../../../composables/useSSE'
import { EXAMPLE_COMPETE } from '../../../composables/exampleData'

const shareRef = ref(null)
const radarRef = ref(null)
const trendRef = ref(null)
const industryInput = ref('')
const isDemo = ref(false)
let shareChart = null, radarChart = null, trendChart = null
const { loading, error, streamText, result, fetchSSE } = useSSE()

onMounted(() => {
  result.value = EXAMPLE_COMPETE
  isDemo.value = true
  nextTick(() => initCharts(EXAMPLE_COMPETE))
})

const examples = ['动力电池', '新能源汽车', '半导体', '白酒']
const COLORS = ['#6366f1', '#8b5cf6', '#a78bfa', '#c4b5fd', '#ddd6fe', '#e5e7eb', '#06b6d4', '#10b981']

const initCharts = (data) => {
  nextTick(() => {
    if (shareRef.value && data.companies) {
      if (shareChart) shareChart.dispose()
      shareChart = echarts.init(shareRef.value)
      const totalShare = data.companies.reduce((s, c) => s + (c.share || 0), 0)
      const pieData = data.companies.map((c, i) => ({ value: c.share, name: c.name, itemStyle: { color: c.color || COLORS[i % COLORS.length] } }))
      if (totalShare < 100) pieData.push({ value: +(100 - totalShare).toFixed(1), name: '其他', itemStyle: { color: '#e5e7eb' } })
      shareChart.setOption({
        tooltip: { textStyle: { fontSize: 10 } },
        series: [{ type: 'pie', radius: ['30%', '65%'], label: { fontSize: 9, formatter: '{b}\n{d}%' }, itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 }, data: pieData }]
      })
    }
    if (radarRef.value && data.radarIndicators && data.radarData) {
      if (radarChart) radarChart.dispose()
      radarChart = echarts.init(radarRef.value)
      radarChart.setOption({
        tooltip: { backgroundColor: 'rgba(255,255,255,0.95)', borderColor: '#e5e7eb', borderWidth: 1, textStyle: { fontSize: 10, color: '#374151' } },
        legend: { data: data.radarData.slice(0, 4).map(d => d.name), bottom: 0, textStyle: { fontSize: 9 } },
        radar: {
          indicator: data.radarIndicators.map(i => ({ name: i.name, max: i.max || 100 })),
          axisName: { color: '#6b7280', fontSize: 9 }, shape: 'polygon',
          splitArea: { areaStyle: { color: ['#f9fafb', '#fff'] } },
          axisLine: { lineStyle: { color: '#e5e7eb' } }, splitLine: { lineStyle: { color: '#e5e7eb' } }
        },
        series: [{ type: 'radar', data: data.radarData.slice(0, 4).map((d, i) => ({
          value: d.values, name: d.name,
          lineStyle: { color: d.color || COLORS[i], width: 2 },
          areaStyle: { color: (d.color || COLORS[i]) + '20' },
          itemStyle: { color: d.color || COLORS[i] }, symbol: 'circle', symbolSize: 4
        })) }]
      })
    }
    if (trendRef.value && data.trend) {
      if (trendChart) trendChart.dispose()
      trendChart = echarts.init(trendRef.value)
      trendChart.setOption({
        tooltip: { trigger: 'axis', textStyle: { fontSize: 10 } },
        legend: { data: data.trend.series.map(s => s.name), bottom: 5, textStyle: { fontSize: 9 } },
        grid: { top: 10, bottom: 40, left: 45, right: 15 },
        xAxis: { type: 'category', data: data.trend.years, axisLabel: { fontSize: 9 }, axisLine: { lineStyle: { color: '#e5e7eb' } } },
        yAxis: { type: 'value', axisLabel: { fontSize: 9, formatter: '{value}%' }, splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } } },
        series: data.trend.series.map((s, i) => ({
          name: s.name, type: 'line', data: s.data, smooth: true, symbol: 'circle', symbolSize: 5,
          lineStyle: { width: 2, color: s.color || COLORS[i] }, itemStyle: { color: s.color || COLORS[i] }
        }))
      })
    }
  })
}

const handleResize = () => { shareChart?.resize(); radarChart?.resize(); trendChart?.resize() }

const clearDemo = () => { result.value = null; isDemo.value = false }

const loadCompete = () => {
  if (!industryInput.value.trim()) return
  isDemo.value = false
  fetchSSE('/api/chain/compete', { industry: industryInput.value.trim() }, {
    onDone: (data) => {
      initCharts(data)
      window.addEventListener('resize', handleResize)
    }
  })
}

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  shareChart?.dispose(); radarChart?.dispose(); trendChart?.dispose()
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }
</style>
