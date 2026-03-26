<template>
  <div class="h-full flex flex-col">
    <!-- Hero -->
    <div class="relative overflow-hidden bg-gradient-to-br from-amber-50 via-white to-yellow-50 border-b border-gray-100">
      <div class="absolute inset-0 opacity-20">
        <div class="absolute top-3 left-16 w-48 h-48 bg-amber-200 rounded-full blur-3xl animate-pulse"></div>
        <div class="absolute bottom-0 right-10 w-40 h-40 bg-yellow-200 rounded-full blur-3xl animate-pulse" style="animation-delay: 1s;"></div>
      </div>
      <div class="relative px-6 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-amber-500 to-yellow-600 flex items-center justify-center shadow-md shadow-amber-500/20 shrink-0">
              <CandlestickChart class="w-4.5 h-4.5 text-white" />
            </div>
            <div>
              <h1 class="text-base font-bold text-gray-900">K线与基础行情</h1>
              <p class="text-[11px] text-gray-500 mt-0.5">实时行情、日K线与分时走势，快速把握市场脉搏</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <div class="relative">
              <Search class="w-3.5 h-3.5 text-gray-400 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input v-model="searchText" @keydown.enter="loadStock" type="text" placeholder="股票代码/名称..."
                class="pl-8 pr-3 py-2 text-xs border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-400 w-44 transition-all" />
            </div>
            <div class="flex items-center bg-gray-50 rounded-lg p-0.5 border border-gray-100">
              <button v-for="p in periods" :key="p.value" @click="activePeriod = p.value"
                :class="['px-2.5 py-1.5 text-[11px] font-medium rounded-md transition-all',
                  activePeriod === p.value ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700']"
              >{{ p.label }}</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="flex-1 flex min-h-0">
      <!-- Chart Area -->
      <div class="flex-1 flex flex-col min-h-0 p-5">
        <!-- Stock Info Bar -->
        <div v-if="stockInfo" class="flex items-center gap-4 mb-4">
          <div>
            <span class="text-sm font-bold text-gray-900">{{ stockInfo.name }}</span>
            <span class="text-xs text-gray-400 ml-1.5 font-mono">{{ stockInfo.code }}</span>
          </div>
          <div class="flex items-center gap-3">
            <span :class="['text-lg font-bold font-mono', stockInfo.change >= 0 ? 'text-rose-600' : 'text-emerald-600']">
              {{ stockInfo.price }}
            </span>
            <span :class="['text-xs font-mono px-2 py-0.5 rounded', stockInfo.change >= 0 ? 'bg-rose-50 text-rose-600' : 'bg-emerald-50 text-emerald-600']">
              {{ stockInfo.change >= 0 ? '+' : '' }}{{ stockInfo.change }}%
            </span>
          </div>
          <div class="flex items-center gap-4 ml-auto text-[11px] text-gray-500">
            <span>成交量: <b class="text-gray-700">{{ stockInfo.volume }}</b></span>
            <span>换手率: <b class="text-gray-700">{{ stockInfo.turnover }}</b></span>
            <span>市值: <b class="text-gray-700">{{ stockInfo.marketCap }}</b></span>
          </div>
        </div>

        <!-- K-Line Chart -->
        <div class="flex-1 bg-white border border-gray-100 rounded-xl shadow-sm overflow-hidden">
          <div ref="klineRef" class="w-full h-full"></div>
        </div>
      </div>

      <!-- Right: Quick Stats -->
      <div class="w-64 border-l border-gray-100 bg-gray-50/50 p-4 flex flex-col gap-3 shrink-0 overflow-y-auto custom-scrollbar">
        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <h4 class="text-[11px] font-bold text-gray-700 mb-3">日K基本指标</h4>
          <div class="space-y-2.5">
            <div v-for="item in dailyStats" :key="item.label" class="flex justify-between text-xs">
              <span class="text-gray-500">{{ item.label }}</span>
              <span class="font-mono font-medium" :class="item.color || 'text-gray-800'">{{ item.value }}</span>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <h4 class="text-[11px] font-bold text-gray-700 mb-3">五日资金</h4>
          <div ref="miniFlowRef" class="w-full h-28"></div>
        </div>

        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm flex-1">
          <h4 class="text-[11px] font-bold text-gray-700 mb-3">自选股</h4>
          <div v-if="watchlist.length === 0" class="text-[10px] text-gray-400 text-center py-4">暂无自选股</div>
          <div v-for="w in watchlist" :key="w.code"
            @click="searchText = w.code; loadStock()"
            class="flex items-center justify-between px-2 py-1.5 rounded-lg hover:bg-amber-50 cursor-pointer transition-colors text-xs mb-1">
            <span class="font-medium text-gray-700">{{ w.name }}</span>
            <span :class="['font-mono text-[11px]', w.change >= 0 ? 'text-rose-500' : 'text-emerald-500']">
              {{ w.change >= 0 ? '+' : '' }}{{ w.change }}%
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { CandlestickChart, Search } from 'lucide-vue-next'

const searchText = ref('600519')
const activePeriod = ref('daily')
const klineRef = ref(null)
const miniFlowRef = ref(null)

const periods = [
  { label: '日K', value: 'daily' },
  { label: '周K', value: 'weekly' },
  { label: '月K', value: 'monthly' },
  { label: '分时', value: 'minute' }
]

const stockInfo = ref({
  name: '贵州茅台', code: '600519.SH', price: '1856.50',
  change: 2.35, volume: '3.2万手', turnover: '0.25%', marketCap: '2.33万亿'
})

const dailyStats = ref([
  { label: '开盘', value: '1823.00' },
  { label: '最高', value: '1862.80', color: 'text-rose-600' },
  { label: '最低', value: '1818.50', color: 'text-emerald-600' },
  { label: '昨收', value: '1813.88' },
  { label: '振幅', value: '2.44%' },
  { label: '量比', value: '1.15' },
  { label: 'PE(TTM)', value: '28.5x' },
  { label: 'PB', value: '9.8x' }
])

const watchlist = ref([
  { name: '贵州茅台', code: '600519', change: 2.35 },
  { name: '比亚迪', code: '002594', change: -1.2 },
  { name: '宁德时代', code: '300750', change: 0.85 },
  { name: '招商银行', code: '600036', change: -0.42 }
])

const generateKlineData = () => {
  const data = []
  let base = 1800
  for (let i = 0; i < 60; i++) {
    const open = base + (Math.random() - 0.48) * 30
    const close = open + (Math.random() - 0.48) * 25
    const low = Math.min(open, close) - Math.random() * 15
    const high = Math.max(open, close) + Math.random() * 15
    const d = new Date(2024, 0, 1)
    d.setDate(d.getDate() + i)
    data.push([d.toISOString().slice(0, 10), open.toFixed(2), close.toFixed(2), low.toFixed(2), high.toFixed(2), Math.floor(Math.random() * 50000 + 10000)])
    base = close
  }
  return data
}

const initKline = () => {
  if (!klineRef.value) return
  const chart = echarts.init(klineRef.value)
  const raw = generateKlineData()
  const dates = raw.map(d => d[0])
  const ohlc = raw.map(d => [+d[1], +d[2], +d[3], +d[4]])
  const volumes = raw.map((d, i) => ({ value: d[5], itemStyle: { color: +d[2] >= +d[1] ? '#ef444480' : '#22c55e80' } }))

  chart.setOption({
    animation: true,
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' }, textStyle: { fontSize: 11 } },
    grid: [
      { left: 60, right: 20, top: 20, height: '60%' },
      { left: 60, right: 20, top: '75%', height: '15%' }
    ],
    xAxis: [
      { type: 'category', data: dates, axisLabel: { fontSize: 10 }, gridIndex: 0, boundaryGap: true },
      { type: 'category', data: dates, axisLabel: { show: false }, gridIndex: 1, boundaryGap: true }
    ],
    yAxis: [
      { scale: true, axisLabel: { fontSize: 10 }, splitLine: { lineStyle: { color: '#f3f4f6' } }, gridIndex: 0 },
      { scale: true, axisLabel: { fontSize: 10 }, splitLine: { lineStyle: { color: '#f3f4f6' } }, gridIndex: 1 }
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: 50, end: 100 },
      { type: 'slider', xAxisIndex: [0, 1], bottom: 5, height: 20, start: 50, end: 100 }
    ],
    series: [
      {
        type: 'candlestick', data: ohlc, xAxisIndex: 0, yAxisIndex: 0,
        itemStyle: { color: '#ef4444', color0: '#22c55e', borderColor: '#ef4444', borderColor0: '#22c55e' }
      },
      { type: 'bar', data: volumes, xAxisIndex: 1, yAxisIndex: 1, barWidth: '60%' }
    ]
  })
  window.addEventListener('resize', () => chart.resize())
}

const initMiniFlow = () => {
  if (!miniFlowRef.value) return
  const chart = echarts.init(miniFlowRef.value)
  chart.setOption({
    grid: { top: 5, bottom: 20, left: 5, right: 5, containLabel: false },
    xAxis: { type: 'category', data: ['周一', '周二', '周三', '周四', '周五'], axisLabel: { fontSize: 9 }, axisLine: { show: false }, axisTick: { show: false } },
    yAxis: { show: false },
    series: [{
      type: 'bar', data: [
        { value: 2.5, itemStyle: { color: '#ef4444', borderRadius: [3, 3, 0, 0] } },
        { value: -1.2, itemStyle: { color: '#22c55e', borderRadius: [0, 0, 3, 3] } },
        { value: 3.8, itemStyle: { color: '#ef4444', borderRadius: [3, 3, 0, 0] } },
        { value: 1.5, itemStyle: { color: '#ef4444', borderRadius: [3, 3, 0, 0] } },
        { value: -0.8, itemStyle: { color: '#22c55e', borderRadius: [0, 0, 3, 3] } }
      ], barWidth: '50%'
    }]
  })
}

const loadStock = () => {
  initKline()
}

onMounted(() => {
  nextTick(() => { initKline(); initMiniFlow() })
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }
</style>
