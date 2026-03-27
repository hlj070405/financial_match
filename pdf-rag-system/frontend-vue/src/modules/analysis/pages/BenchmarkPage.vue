<template>
  <div class="h-full flex flex-col">
    <!-- Hero -->
    <div class="relative overflow-hidden bg-gradient-to-br from-emerald-50 via-white to-teal-50 border-b border-gray-100">
      <div class="absolute inset-0 opacity-20">
        <div class="absolute top-3 left-16 w-48 h-48 bg-emerald-200 rounded-full blur-3xl animate-pulse"></div>
        <div class="absolute bottom-0 right-10 w-40 h-40 bg-teal-200 rounded-full blur-3xl animate-pulse" style="animation-delay: 1s;"></div>
      </div>
      <div class="relative px-6 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center shadow-md shadow-emerald-500/20 shrink-0">
              <Scale class="w-4.5 h-4.5 text-white" />
            </div>
            <div>
              <h1 class="text-base font-bold text-gray-900">多维对标分析</h1>
              <p class="text-[11px] text-gray-500 mt-0.5">同行业横向对比，多维度量化评估企业竞争力</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <input v-model="companyA" type="text" placeholder="公司A..."
              class="px-3 py-2 text-xs border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-400 w-28 transition-all" />
            <span class="text-xs text-gray-400 font-bold">VS</span>
            <input v-model="companyB" type="text" placeholder="公司B..."
              class="px-3 py-2 text-xs border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-400 w-28 transition-all" />
            <button @click="runBenchmark" :disabled="loading"
              class="px-4 py-2 bg-emerald-600 text-white text-xs font-medium rounded-lg hover:bg-emerald-700 transition-colors disabled:opacity-50 flex items-center gap-1.5">
              <Loader2 v-if="loading" class="w-3.5 h-3.5 animate-spin" />
              <ArrowRightLeft v-else class="w-3.5 h-3.5" />
              {{ loading ? '对比中...' : '对标分析' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto p-6 custom-scrollbar">
      <!-- Empty State -->
      <div v-if="!loading && !result" class="flex items-center justify-center h-full">
        <div class="text-center max-w-md">
          <div class="p-3 rounded-xl bg-emerald-50 inline-block mb-3">
            <Scale class="w-10 h-10 text-emerald-300" />
          </div>
          <h3 class="text-sm font-semibold text-gray-700 mb-1.5">输入两家公司进行对标分析</h3>
          <p class="text-xs text-gray-400 leading-relaxed mb-4">AI 将从财务指标、盈利能力、成长性、估值水平等多个维度进行横向对比</p>
          <div class="flex flex-wrap gap-2 justify-center">
            <button v-for="pair in examplePairs" :key="pair[0]+pair[1]"
              @click="companyA = pair[0]; companyB = pair[1]; runBenchmark()"
              class="px-3 py-1.5 text-[11px] text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-emerald-50 hover:border-emerald-300 hover:text-emerald-700 transition-all">
              {{ pair[0] }} vs {{ pair[1] }}
            </button>
          </div>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex flex-col items-center justify-center h-full">
        <div class="text-center">
          <Loader2 class="w-8 h-8 animate-spin text-emerald-500 mx-auto" />
          <p class="text-xs text-gray-500 mt-3">AI 正在多维度对标分析...</p>
        </div>
        <div v-if="streamText" class="mt-4 max-w-2xl w-full bg-gray-50 border border-gray-100 rounded-xl p-4 max-h-48 overflow-y-auto">
          <p class="text-[10px] font-bold text-gray-400 mb-1 uppercase tracking-wider">实时生成中</p>
          <pre class="text-[11px] text-gray-600 whitespace-pre-wrap font-mono leading-relaxed">{{ streamText.slice(-800) }}</pre>
        </div>
      </div>

      <!-- Results -->
      <div v-if="result && !loading" class="max-w-5xl mx-auto space-y-5">
        <!-- Demo Banner -->
        <div v-if="isDemo" class="bg-emerald-50 border border-emerald-200 rounded-xl px-4 py-2.5 flex items-center justify-between">
          <p class="text-[11px] text-emerald-600"><span class="font-bold">示例数据</span> — 当前展示的是比亚迪 vs 长城汽车对标示例，输入公司名称可获取实时分析</p>
          <button @click="clearDemo" class="text-[10px] text-emerald-500 hover:text-emerald-700 font-medium">清除示例</button>
        </div>
        <!-- Summary -->
        <div class="bg-gradient-to-r from-emerald-600 to-teal-600 rounded-xl p-5 text-white">
          <div class="flex items-center gap-2 mb-2">
            <Sparkles class="w-3.5 h-3.5 text-amber-300" />
            <span class="text-[10px] font-bold text-amber-200 uppercase tracking-wider">AI 对标结论</span>
          </div>
          <p class="text-sm leading-relaxed">{{ result.summary }}</p>
        </div>

        <!-- Charts -->
        <div class="grid grid-cols-2 gap-5">
          <div class="bg-white border border-gray-100 rounded-xl p-5 shadow-sm">
            <h3 class="text-xs font-bold text-gray-800 flex items-center gap-2 mb-3">
              <Radar class="w-4 h-4 text-emerald-500" /> 综合能力雷达
            </h3>
            <div ref="radarRef" class="w-full h-56"></div>
          </div>
          <div class="bg-white border border-gray-100 rounded-xl p-5 shadow-sm">
            <h3 class="text-xs font-bold text-gray-800 flex items-center gap-2 mb-3">
              <TrendingUp class="w-4 h-4 text-blue-500" /> 营收趋势对比
            </h3>
            <div ref="trendRef" class="w-full h-56"></div>
          </div>
        </div>

        <!-- Metric Table -->
        <div class="bg-white border border-gray-100 rounded-xl shadow-sm overflow-hidden">
          <table class="w-full text-xs">
            <thead>
              <tr class="bg-gray-50 border-b border-gray-100">
                <th class="px-4 py-3 text-left font-bold text-gray-700">指标</th>
                <th class="px-4 py-3 text-center font-bold text-emerald-700">{{ result.companyA }}</th>
                <th class="px-4 py-3 text-center font-bold text-blue-700">{{ result.companyB }}</th>
                <th class="px-4 py-3 text-center font-bold text-gray-600">优势方</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(m, i) in result.metrics" :key="i" class="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
                <td class="px-4 py-2.5 font-medium text-gray-700">{{ m.name }}</td>
                <td class="px-4 py-2.5 text-center font-mono" :class="m.winner === 'A' ? 'text-emerald-600 font-bold' : 'text-gray-600'">{{ m.valueA }}</td>
                <td class="px-4 py-2.5 text-center font-mono" :class="m.winner === 'B' ? 'text-blue-600 font-bold' : 'text-gray-600'">{{ m.valueB }}</td>
                <td class="px-4 py-2.5 text-center">
                  <span :class="[
                    'px-2 py-0.5 rounded-full text-[10px] font-medium',
                    m.winner === 'A' ? 'bg-emerald-100 text-emerald-700' :
                    m.winner === 'B' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-500'
                  ]">{{ m.winner === 'A' ? result.companyA : m.winner === 'B' ? result.companyB : '持平' }}</span>
                </td>
              </tr>
            </tbody>
          </table>
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
import { Scale, ArrowRightLeft, Loader2, Sparkles, Radar, TrendingUp } from 'lucide-vue-next'
import { useSSE } from '../../../composables/useSSE'
import { EXAMPLE_BENCHMARK } from '../../../composables/exampleData'

const companyA = ref('')
const companyB = ref('')
const radarRef = ref(null)
const trendRef = ref(null)
const isDemo = ref(false)
let radarChart = null
let trendChart = null

const { loading, error, streamText, result, fetchSSE } = useSSE()
const examplePairs = [['贵州茅台', '五粮液'], ['比亚迪', '长城汽车'], ['招商银行', '兴业银行'], ['宁德时代', '亿纬锂能']]

onMounted(() => {
  result.value = EXAMPLE_BENCHMARK
  isDemo.value = true
  nextTick(() => initCharts(EXAMPLE_BENCHMARK))
})

const initCharts = (data) => {
  nextTick(() => {
    if (radarRef.value) {
      if (radarChart) radarChart.dispose()
      radarChart = echarts.init(radarRef.value)
      const labels = data.radarLabels || ['盈利能力', '成长能力', '估值水平', '运营效率', '财务健康', '市场地位']
      radarChart.setOption({
        tooltip: { backgroundColor: 'rgba(255,255,255,0.95)', borderColor: '#e5e7eb', borderWidth: 1, textStyle: { color: '#1f2937', fontSize: 11 } },
        legend: { data: [data.companyA, data.companyB], bottom: 0, textStyle: { fontSize: 11 } },
        radar: {
          indicator: labels.map(n => ({ name: n, max: 100 })),
          shape: 'polygon',
          radius: '60%',
          splitArea: { show: true, areaStyle: { color: ['#f9fafb', '#fff'] } },
          axisLine: { lineStyle: { color: '#e5e7eb' } },
          splitLine: { lineStyle: { color: '#e5e7eb' } },
          axisName: { color: '#6b7280', fontSize: 10 }
        },
        series: [{
          type: 'radar',
          data: [
            { value: data.radarA, name: data.companyA, areaStyle: { color: 'rgba(16,185,129,0.15)' }, lineStyle: { color: '#10b981', width: 2 }, itemStyle: { color: '#10b981' }, symbol: 'circle', symbolSize: 5 },
            { value: data.radarB, name: data.companyB, areaStyle: { color: 'rgba(59,130,246,0.15)' }, lineStyle: { color: '#3b82f6', width: 2 }, itemStyle: { color: '#3b82f6' }, symbol: 'circle', symbolSize: 5 }
          ]
        }]
      })
    }
    if (trendRef.value && data.trend) {
      if (trendChart) trendChart.dispose()
      trendChart = echarts.init(trendRef.value)
      trendChart.setOption({
        tooltip: { trigger: 'axis', textStyle: { fontSize: 11 }, backgroundColor: 'rgba(255,255,255,0.95)', borderColor: '#e5e7eb', borderWidth: 1 },
        legend: { data: [data.companyA, data.companyB], bottom: 0, textStyle: { fontSize: 11 } },
        grid: { top: 10, bottom: 40, left: 10, right: 10, containLabel: true },
        xAxis: { type: 'category', data: data.trend.years, axisLabel: { fontSize: 10 }, axisLine: { lineStyle: { color: '#e5e7eb' } }, axisTick: { show: false } },
        yAxis: { type: 'value', axisLabel: { fontSize: 10 }, splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } }, axisLine: { show: false } },
        series: [
          { name: data.companyA, type: 'line', data: data.trend.seriesA, smooth: true, symbol: 'circle', symbolSize: 6, lineStyle: { color: '#10b981', width: 2.5 }, itemStyle: { color: '#10b981' }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(16,185,129,0.15)' }, { offset: 1, color: 'rgba(16,185,129,0)' }]) } },
          { name: data.companyB, type: 'line', data: data.trend.seriesB, smooth: true, symbol: 'circle', symbolSize: 6, lineStyle: { color: '#3b82f6', width: 2.5 }, itemStyle: { color: '#3b82f6' }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(59,130,246,0.15)' }, { offset: 1, color: 'rgba(59,130,246,0)' }]) } }
        ]
      })
    }
  })
}

const handleResize = () => { radarChart?.resize(); trendChart?.resize() }

const clearDemo = () => { result.value = null; isDemo.value = false }

const runBenchmark = () => {
  if (!companyA.value.trim() || !companyB.value.trim()) return
  isDemo.value = false
  fetchSSE('/api/diagnosis/benchmark', { companyA: companyA.value.trim(), companyB: companyB.value.trim() }, {
    onDone: (data) => {
      initCharts(data)
      window.addEventListener('resize', handleResize)
    }
  })
}

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  radarChart?.dispose()
  trendChart?.dispose()
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }
</style>
