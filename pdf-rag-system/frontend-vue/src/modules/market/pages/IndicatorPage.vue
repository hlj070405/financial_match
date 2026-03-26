<template>
  <div class="h-full flex flex-col">
    <!-- Hero -->
    <div class="relative overflow-hidden bg-gradient-to-br from-indigo-50 via-white to-blue-50 border-b border-gray-100">
      <div class="absolute inset-0 opacity-20">
        <div class="absolute top-3 left-16 w-48 h-48 bg-indigo-200 rounded-full blur-3xl animate-pulse"></div>
        <div class="absolute bottom-0 right-10 w-40 h-40 bg-blue-200 rounded-full blur-3xl animate-pulse" style="animation-delay: 1s;"></div>
      </div>
      <div class="relative px-6 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-blue-600 flex items-center justify-center shadow-md shadow-indigo-500/20 shrink-0">
              <Activity class="w-4.5 h-4.5 text-white" />
            </div>
            <div>
              <h1 class="text-base font-bold text-gray-900">技术指标叠加</h1>
              <p class="text-[11px] text-gray-500 mt-0.5">MACD、RSI、布林带等经典技术指标，辅助趋势判断</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <input v-model="stockCode" @keydown.enter="loadIndicators" type="text" placeholder="股票代码..."
              class="px-3 py-2 text-xs border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 w-32 transition-all" />
            <button @click="loadIndicators"
              class="px-4 py-2 bg-indigo-600 text-white text-xs font-medium rounded-lg hover:bg-indigo-700 transition-colors flex items-center gap-1.5">
              <Search class="w-3.5 h-3.5" /> 分析
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="flex-1 flex min-h-0">
      <!-- Charts -->
      <div class="flex-1 flex flex-col min-h-0 p-5 gap-4">
        <!-- MACD -->
        <div class="bg-white border border-gray-100 rounded-xl shadow-sm flex-1 overflow-hidden">
          <div class="px-4 py-2.5 border-b border-gray-50 flex items-center justify-between">
            <h3 class="text-xs font-bold text-gray-800">MACD 指标</h3>
            <span class="text-[10px] text-gray-400">DIF / DEA / 柱状图</span>
          </div>
          <div ref="macdRef" class="w-full" style="height: calc(100% - 36px);"></div>
        </div>
        <!-- RSI -->
        <div class="bg-white border border-gray-100 rounded-xl shadow-sm flex-1 overflow-hidden">
          <div class="px-4 py-2.5 border-b border-gray-50 flex items-center justify-between">
            <h3 class="text-xs font-bold text-gray-800">RSI 相对强弱指数</h3>
            <span class="text-[10px] text-gray-400">RSI(6) / RSI(12) / RSI(24)</span>
          </div>
          <div ref="rsiRef" class="w-full" style="height: calc(100% - 36px);"></div>
        </div>
      </div>

      <!-- Right: Indicator Signals -->
      <div class="w-64 border-l border-gray-100 bg-gray-50/50 p-4 flex flex-col gap-3 shrink-0 overflow-y-auto custom-scrollbar">
        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <h4 class="text-[11px] font-bold text-gray-700 mb-3 flex items-center gap-1.5">
            <Zap class="w-3.5 h-3.5 text-amber-500" /> 信号汇总
          </h4>
          <div class="space-y-2">
            <div v-for="sig in signals" :key="sig.name" class="flex items-center justify-between">
              <span class="text-xs text-gray-600">{{ sig.name }}</span>
              <span :class="[
                'px-2 py-0.5 rounded text-[10px] font-bold',
                sig.type === 'buy' ? 'bg-rose-50 text-rose-600' :
                sig.type === 'sell' ? 'bg-emerald-50 text-emerald-600' : 'bg-gray-100 text-gray-500'
              ]">{{ sig.label }}</span>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <h4 class="text-[11px] font-bold text-gray-700 mb-3">指标参数</h4>
          <div class="space-y-3">
            <div>
              <label class="text-[10px] text-gray-500 block mb-1">MACD 快线</label>
              <input type="range" min="5" max="20" v-model="macdFast" class="w-full h-1 accent-indigo-500" />
              <span class="text-[10px] text-gray-400 float-right">{{ macdFast }}</span>
            </div>
            <div>
              <label class="text-[10px] text-gray-500 block mb-1">MACD 慢线</label>
              <input type="range" min="15" max="40" v-model="macdSlow" class="w-full h-1 accent-indigo-500" />
              <span class="text-[10px] text-gray-400 float-right">{{ macdSlow }}</span>
            </div>
            <div>
              <label class="text-[10px] text-gray-500 block mb-1">RSI 周期</label>
              <input type="range" min="3" max="30" v-model="rsiPeriod" class="w-full h-1 accent-indigo-500" />
              <span class="text-[10px] text-gray-400 float-right">{{ rsiPeriod }}</span>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm flex-1">
          <h4 class="text-[11px] font-bold text-gray-700 mb-3 flex items-center gap-1.5">
            <TrendingUp class="w-3.5 h-3.5 text-emerald-500" /> 趋势判断
          </h4>
          <div class="space-y-2">
            <div class="p-2.5 bg-rose-50 rounded-lg">
              <p class="text-[10px] font-bold text-rose-700">短期趋势</p>
              <p class="text-[10px] text-rose-600 mt-0.5">偏多 | MACD金叉 + RSI>50</p>
            </div>
            <div class="p-2.5 bg-amber-50 rounded-lg">
              <p class="text-[10px] font-bold text-amber-700">中期趋势</p>
              <p class="text-[10px] text-amber-600 mt-0.5">震荡 | 布林带收窄中</p>
            </div>
            <div class="p-2.5 bg-emerald-50 rounded-lg">
              <p class="text-[10px] font-bold text-emerald-700">长期趋势</p>
              <p class="text-[10px] text-emerald-600 mt-0.5">偏多 | 年线上方运行</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { Activity, Search, Zap, TrendingUp } from 'lucide-vue-next'

const stockCode = ref('600519')
const macdRef = ref(null)
const rsiRef = ref(null)
const macdFast = ref(12)
const macdSlow = ref(26)
const rsiPeriod = ref(14)

const signals = ref([
  { name: 'MACD', type: 'buy', label: '金叉买入' },
  { name: 'RSI(14)', type: 'neutral', label: '中性 58.3' },
  { name: 'KDJ', type: 'buy', label: '超卖反弹' },
  { name: '布林带', type: 'neutral', label: '中轨运行' },
  { name: 'MA均线', type: 'buy', label: '多头排列' },
  { name: 'OBV', type: 'sell', label: '量能背离' }
])

const generateDates = (n) => {
  const dates = []
  const d = new Date(2024, 0, 1)
  for (let i = 0; i < n; i++) { d.setDate(d.getDate() + 1); dates.push(d.toISOString().slice(0, 10)) }
  return dates
}

const initMACD = () => {
  if (!macdRef.value) return
  const chart = echarts.init(macdRef.value)
  const dates = generateDates(60)
  const dif = [], dea = [], hist = []
  let d = 0, e = 0
  for (let i = 0; i < 60; i++) {
    d = d * 0.85 + (Math.random() - 0.48) * 3
    e = e * 0.9 + d * 0.1
    dif.push(+d.toFixed(2))
    dea.push(+e.toFixed(2))
    hist.push(+((d - e) * 2).toFixed(2))
  }
  chart.setOption({
    tooltip: { trigger: 'axis', textStyle: { fontSize: 10 } },
    grid: { top: 15, bottom: 25, left: 50, right: 15 },
    xAxis: { type: 'category', data: dates, axisLabel: { fontSize: 9 } },
    yAxis: { scale: true, axisLabel: { fontSize: 9 }, splitLine: { lineStyle: { color: '#f3f4f6' } } },
    series: [
      { name: 'DIF', type: 'line', data: dif, lineStyle: { width: 1.5, color: '#6366f1' }, symbol: 'none' },
      { name: 'DEA', type: 'line', data: dea, lineStyle: { width: 1.5, color: '#f59e0b' }, symbol: 'none' },
      { name: 'MACD', type: 'bar', data: hist.map(v => ({ value: v, itemStyle: { color: v >= 0 ? '#ef444490' : '#22c55e90', borderRadius: v >= 0 ? [2, 2, 0, 0] : [0, 0, 2, 2] } })), barWidth: '50%' }
    ]
  })
  window.addEventListener('resize', () => chart.resize())
}

const initRSI = () => {
  if (!rsiRef.value) return
  const chart = echarts.init(rsiRef.value)
  const dates = generateDates(60)
  const gen = () => { let v = 50; return Array.from({ length: 60 }, () => { v += (Math.random() - 0.5) * 8; return +Math.max(10, Math.min(90, v)).toFixed(1) }) }
  chart.setOption({
    tooltip: { trigger: 'axis', textStyle: { fontSize: 10 } },
    grid: { top: 15, bottom: 25, left: 50, right: 15 },
    xAxis: { type: 'category', data: dates, axisLabel: { fontSize: 9 } },
    yAxis: { min: 0, max: 100, axisLabel: { fontSize: 9 }, splitLine: { lineStyle: { color: '#f3f4f6' } } },
    visualMap: { show: false, pieces: [{ gt: 70, color: '#ef4444' }, { gte: 30, lte: 70, color: '#6366f1' }, { lt: 30, color: '#22c55e' }], seriesIndex: 0 },
    series: [
      { name: 'RSI(6)', type: 'line', data: gen(), lineStyle: { width: 1.5 }, symbol: 'none' },
      { name: 'RSI(12)', type: 'line', data: gen(), lineStyle: { width: 1.5, color: '#f59e0b', type: 'dashed' }, symbol: 'none' },
      { name: 'RSI(24)', type: 'line', data: gen(), lineStyle: { width: 1.5, color: '#94a3b8', type: 'dotted' }, symbol: 'none' }
    ]
  })
  window.addEventListener('resize', () => chart.resize())
}

const loadIndicators = () => { initMACD(); initRSI() }

onMounted(() => { nextTick(() => { initMACD(); initRSI() }) })
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }
</style>
