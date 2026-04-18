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
            <div class="relative">
              <Search class="w-3.5 h-3.5 text-gray-400 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input v-model="searchText" @input="onSearchInput" @focus="showSuggestions = true" @keydown.enter="loadIndicators" type="text" placeholder="股票代码/名称..."
                class="pl-8 pr-3 py-2 text-xs border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 w-48 transition-all" />
              <div v-if="showSuggestions && suggestions.length > 0"
                class="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-xl shadow-xl z-50 max-h-52 overflow-y-auto custom-scrollbar">
                <div v-for="s in suggestions" :key="s.ts_code" @click="pickStock(s)"
                  class="flex items-center justify-between px-3 py-2 hover:bg-indigo-50 transition-colors text-xs cursor-pointer border-b border-gray-50 last:border-0">
                  <span class="font-medium text-gray-900">{{ s.name }}</span>
                  <span class="text-[10px] text-gray-400 font-mono">{{ s.ts_code }}</span>
                </div>
              </div>
            </div>
            <button @click="loadIndicators" :disabled="dataLoading"
              class="px-4 py-2 bg-indigo-600 text-white text-xs font-medium rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-60 flex items-center gap-1.5">
              <Loader2 v-if="dataLoading" class="w-3.5 h-3.5 animate-spin" />
              <Search v-else class="w-3.5 h-3.5" /> 分析
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="flex-1 flex min-h-0">
      <!-- Charts -->
      <div class="flex-1 flex flex-col min-h-0 p-5 gap-4">
        <!-- Stock Name Banner -->
        <div v-if="currentStockName" class="flex items-center gap-2 shrink-0">
          <span class="text-sm font-bold text-gray-900">{{ currentStockName }}</span>
          <span class="text-xs text-gray-400 font-mono">{{ currentTsCode }}</span>
        </div>
        <!-- MACD -->
        <div class="bg-white border border-gray-100 rounded-xl shadow-sm flex-1 overflow-hidden relative">
          <div class="px-4 py-2.5 border-b border-gray-50 flex items-center justify-between">
            <h3 class="text-xs font-bold text-gray-800">MACD 指标</h3>
            <span class="text-[10px] text-gray-400">DIF / DEA / 柱状图</span>
          </div>
          <div v-if="dataLoading" class="absolute inset-0 top-9 flex items-center justify-center bg-white/80 z-10">
            <Loader2 class="w-6 h-6 animate-spin text-indigo-500" />
          </div>
          <div ref="macdRef" class="w-full" style="height: calc(100% - 36px);"></div>
        </div>
        <!-- RSI -->
        <div class="bg-white border border-gray-100 rounded-xl shadow-sm flex-1 overflow-hidden relative">
          <div class="px-4 py-2.5 border-b border-gray-50 flex items-center justify-between">
            <h3 class="text-xs font-bold text-gray-800">RSI 相对强弱指数</h3>
            <span class="text-[10px] text-gray-400">RSI(6) / RSI(12) / RSI(24)</span>
          </div>
          <div v-if="dataLoading" class="absolute inset-0 top-9 flex items-center justify-center bg-white/80 z-10">
            <Loader2 class="w-6 h-6 animate-spin text-indigo-500" />
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
          <div v-if="signals.length === 0" class="text-[10px] text-gray-400 text-center py-3">选择股票后自动生成</div>
          <div v-else class="space-y-2">
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
              <input type="range" min="5" max="20" v-model="macdFast" @change="recompute" class="w-full h-1 accent-indigo-500" />
              <span class="text-[10px] text-gray-400 float-right">{{ macdFast }}</span>
            </div>
            <div>
              <label class="text-[10px] text-gray-500 block mb-1">MACD 慢线</label>
              <input type="range" min="15" max="40" v-model="macdSlow" @change="recompute" class="w-full h-1 accent-indigo-500" />
              <span class="text-[10px] text-gray-400 float-right">{{ macdSlow }}</span>
            </div>
            <div>
              <label class="text-[10px] text-gray-500 block mb-1">RSI 周期</label>
              <input type="range" min="3" max="30" v-model="rsiPeriod" @change="recompute" class="w-full h-1 accent-indigo-500" />
              <span class="text-[10px] text-gray-400 float-right">{{ rsiPeriod }}</span>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm flex-1">
          <h4 class="text-[11px] font-bold text-gray-700 mb-3 flex items-center gap-1.5">
            <TrendingUp class="w-3.5 h-3.5 text-emerald-500" /> 趋势判断
          </h4>
          <div v-if="trendItems.length === 0" class="text-[10px] text-gray-400 text-center py-3">选择股票后显示</div>
          <div v-else class="space-y-2">
            <div v-for="t in trendItems" :key="t.label" :class="['p-2.5 rounded-lg', t.bg]">
              <p :class="['text-[10px] font-bold', t.titleColor]">{{ t.label }}</p>
              <p :class="['text-[10px] mt-0.5', t.textColor]">{{ t.desc }}</p>
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
import { Activity, Search, Zap, TrendingUp, Loader2 } from 'lucide-vue-next'
import { tushareApi } from '../../../api/tushare.js'

const searchText = ref('')
const macdRef = ref(null)
const rsiRef = ref(null)
const macdFast = ref(12)
const macdSlow = ref(26)
const rsiPeriod = ref(14)

const dataLoading = ref(false)
const showSuggestions = ref(false)
const suggestions = ref([])
const allStocks = ref([])
const stocksLoaded = ref(false)
const currentTsCode = ref('')
const currentStockName = ref('')
const rawData = ref([])
const signals = ref([])
const trendItems = ref([])

let macdChart = null
let rsiChart = null
let searchTimer = null

// ============ Search ============
const loadAllStocks = async () => {
  if (stocksLoaded.value) return
  try {
    const res = await tushareApi.getStockBasic()
    allStocks.value = res.data || []
    stocksLoaded.value = true
  } catch (e) { console.error('加载股票列表失败:', e) }
}

const onSearchInput = () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    const q = searchText.value.trim().toLowerCase()
    if (!q) { suggestions.value = []; return }
    suggestions.value = allStocks.value
      .filter(s => s.ts_code.toLowerCase().includes(q) || s.symbol?.includes(q) || s.name?.toLowerCase().includes(q))
      .slice(0, 10)
    showSuggestions.value = true
  }, 200)
}

const pickStock = (s) => {
  searchText.value = `${s.name} ${s.ts_code}`
  showSuggestions.value = false
  currentTsCode.value = s.ts_code
  currentStockName.value = s.name
  loadIndicators()
}

// ============ Technical Indicator Calculations ============
const calcEMA = (data, period) => {
  const k = 2 / (period + 1)
  const result = [data[0]]
  for (let i = 1; i < data.length; i++) {
    result.push(data[i] * k + result[i - 1] * (1 - k))
  }
  return result
}

const calcMACD = (closes, fast, slow, signal = 9) => {
  const emaFast = calcEMA(closes, fast)
  const emaSlow = calcEMA(closes, slow)
  const dif = emaFast.map((v, i) => +(v - emaSlow[i]).toFixed(4))
  const dea = calcEMA(dif, signal).map(v => +v.toFixed(4))
  const hist = dif.map((v, i) => +((v - dea[i]) * 2).toFixed(4))
  return { dif, dea, hist }
}

const calcRSI = (closes, period) => {
  const result = new Array(closes.length).fill(null)
  for (let i = period; i < closes.length; i++) {
    let gains = 0, losses = 0
    for (let j = i - period + 1; j <= i; j++) {
      const diff = closes[j] - closes[j - 1]
      if (diff >= 0) gains += diff
      else losses -= diff
    }
    const rs = losses === 0 ? 100 : gains / losses
    result[i] = +(100 - 100 / (1 + rs)).toFixed(2)
  }
  return result
}

const calcMA = (closes, period) => {
  const result = new Array(closes.length).fill(null)
  for (let i = period - 1; i < closes.length; i++) {
    let sum = 0
    for (let j = i - period + 1; j <= i; j++) sum += closes[j]
    result[i] = +(sum / period).toFixed(4)
  }
  return result
}

// ============ Data Loading ============
const loadIndicators = async () => {
  if (!currentTsCode.value) return
  dataLoading.value = true
  try {
    const res = await tushareApi.getDaily(currentTsCode.value)
    rawData.value = res.data || []
  } catch (e) {
    console.error('获取日线数据失败:', e)
    rawData.value = []
  }
  dataLoading.value = false
  await nextTick()
  recompute()
}

const recompute = () => {
  if (rawData.value.length < 30) return
  renderMACD()
  renderRSI()
  computeSignals()
}

// ============ Signals ============
const computeSignals = () => {
  if (rawData.value.length < 30) { signals.value = []; trendItems.value = []; return }
  const closes = rawData.value.map(d => d.close)
  const { dif, dea } = calcMACD(closes, +macdFast.value, +macdSlow.value)
  const rsi14 = calcRSI(closes, +rsiPeriod.value)
  const ma5 = calcMA(closes, 5)
  const ma20 = calcMA(closes, 20)
  const ma60 = calcMA(closes, 60)
  const n = closes.length - 1

  const sigs = []
  // MACD signal
  const lastDif = dif[n], lastDea = dea[n], prevDif = dif[n - 1], prevDea = dea[n - 1]
  if (prevDif <= prevDea && lastDif > lastDea) sigs.push({ name: 'MACD', type: 'buy', label: '金叉买入' })
  else if (prevDif >= prevDea && lastDif < lastDea) sigs.push({ name: 'MACD', type: 'sell', label: '死叉卖出' })
  else sigs.push({ name: 'MACD', type: 'neutral', label: lastDif > lastDea ? 'DIF>DEA' : 'DIF<DEA' })

  // RSI signal
  const lastRsi = rsi14[n]
  if (lastRsi != null) {
    if (lastRsi > 70) sigs.push({ name: `RSI(${rsiPeriod.value})`, type: 'sell', label: `超买 ${lastRsi}` })
    else if (lastRsi < 30) sigs.push({ name: `RSI(${rsiPeriod.value})`, type: 'buy', label: `超卖 ${lastRsi}` })
    else sigs.push({ name: `RSI(${rsiPeriod.value})`, type: 'neutral', label: `中性 ${lastRsi}` })
  }

  // MA signals
  if (ma5[n] != null && ma20[n] != null) {
    if (ma5[n] > ma20[n]) sigs.push({ name: 'MA(5/20)', type: 'buy', label: '短期多头' })
    else sigs.push({ name: 'MA(5/20)', type: 'sell', label: '短期空头' })
  }
  if (ma20[n] != null && ma60[n] != null) {
    if (ma20[n] > ma60[n]) sigs.push({ name: 'MA(20/60)', type: 'buy', label: '中期多头' })
    else sigs.push({ name: 'MA(20/60)', type: 'sell', label: '中期空头' })
  }

  // Price vs MA
  if (ma5[n] != null && closes[n] > ma5[n]) sigs.push({ name: '价格/MA5', type: 'buy', label: '站上5日线' })
  else if (ma5[n] != null) sigs.push({ name: '价格/MA5', type: 'sell', label: '跌破5日线' })

  signals.value = sigs

  // Trend
  const trends = []
  const shortBull = (lastDif > lastDea) && (lastRsi != null && lastRsi > 50)
  const shortBear = (lastDif < lastDea) && (lastRsi != null && lastRsi < 50)
  trends.push({
    label: '短期趋势',
    desc: shortBull ? `偏多 | DIF>${'DEA'} + RSI=${lastRsi}` : shortBear ? `偏空 | DIF<DEA + RSI=${lastRsi}` : `震荡 | RSI=${lastRsi || '--'}`,
    bg: shortBull ? 'bg-rose-50' : shortBear ? 'bg-emerald-50' : 'bg-amber-50',
    titleColor: shortBull ? 'text-rose-700' : shortBear ? 'text-emerald-700' : 'text-amber-700',
    textColor: shortBull ? 'text-rose-600' : shortBear ? 'text-emerald-600' : 'text-amber-600',
  })
  if (ma20[n] != null && ma60[n] != null) {
    const midBull = ma20[n] > ma60[n]
    trends.push({
      label: '中期趋势',
      desc: midBull ? '偏多 | MA20 > MA60' : '偏空 | MA20 < MA60',
      bg: midBull ? 'bg-rose-50' : 'bg-emerald-50',
      titleColor: midBull ? 'text-rose-700' : 'text-emerald-700',
      textColor: midBull ? 'text-rose-600' : 'text-emerald-600',
    })
  }
  trendItems.value = trends
}

// ============ Charts ============
const renderMACD = () => {
  if (!macdRef.value || rawData.value.length < 30) return
  if (macdChart) macdChart.dispose()
  macdChart = echarts.init(macdRef.value)

  const closes = rawData.value.map(d => d.close)
  const dates = rawData.value.map(d => d.trade_date)
  const { dif, dea, hist } = calcMACD(closes, +macdFast.value, +macdSlow.value)

  macdChart.setOption({
    tooltip: { trigger: 'axis', textStyle: { fontSize: 10 },
      backgroundColor: 'rgba(255,255,255,0.95)', borderColor: '#f3f4f6', borderWidth: 1,
      extraCssText: 'box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-radius: 8px;' },
    legend: { data: ['DIF', 'DEA', 'MACD'], bottom: 5, textStyle: { fontSize: 10 } },
    grid: { top: 15, bottom: 35, left: 55, right: 15 },
    dataZoom: [{ type: 'inside', start: 60, end: 100 }],
    xAxis: { type: 'category', data: dates, axisLabel: { fontSize: 9, color: '#9ca3af' }, axisLine: { lineStyle: { color: '#e5e7eb' } }, axisTick: { show: false } },
    yAxis: { scale: true, axisLabel: { fontSize: 9, color: '#9ca3af' }, splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } }, axisLine: { show: false }, axisTick: { show: false } },
    series: [
      { name: 'DIF', type: 'line', data: dif, lineStyle: { width: 1.5, color: '#6366f1' }, symbol: 'none' },
      { name: 'DEA', type: 'line', data: dea, lineStyle: { width: 1.5, color: '#f59e0b' }, symbol: 'none' },
      { name: 'MACD', type: 'bar', data: hist.map(v => ({ value: v, itemStyle: { color: v >= 0 ? '#ef444490' : '#22c55e90', borderRadius: v >= 0 ? [2, 2, 0, 0] : [0, 0, 2, 2] } })), barWidth: '50%' }
    ]
  })
  window.addEventListener('resize', () => macdChart?.resize())
}

const renderRSI = () => {
  if (!rsiRef.value || rawData.value.length < 30) return
  if (rsiChart) rsiChart.dispose()
  rsiChart = echarts.init(rsiRef.value)

  const closes = rawData.value.map(d => d.close)
  const dates = rawData.value.map(d => d.trade_date)
  const rsi6 = calcRSI(closes, 6)
  const rsi12 = calcRSI(closes, 12)
  const rsi24 = calcRSI(closes, 24)

  rsiChart.setOption({
    tooltip: { trigger: 'axis', textStyle: { fontSize: 10 },
      backgroundColor: 'rgba(255,255,255,0.95)', borderColor: '#f3f4f6', borderWidth: 1,
      extraCssText: 'box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-radius: 8px;' },
    legend: { data: ['RSI(6)', 'RSI(12)', 'RSI(24)'], bottom: 5, textStyle: { fontSize: 10 } },
    grid: { top: 15, bottom: 35, left: 55, right: 15 },
    dataZoom: [{ type: 'inside', start: 60, end: 100 }],
    xAxis: { type: 'category', data: dates, axisLabel: { fontSize: 9, color: '#9ca3af' }, axisLine: { lineStyle: { color: '#e5e7eb' } }, axisTick: { show: false } },
    yAxis: { min: 0, max: 100, axisLabel: { fontSize: 9, color: '#9ca3af' }, splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } }, axisLine: { show: false }, axisTick: { show: false } },
    visualMap: { show: false, pieces: [{ gt: 70, color: '#ef4444' }, { gte: 30, lte: 70, color: '#6366f1' }, { lt: 30, color: '#22c55e' }], seriesIndex: 0 },
    series: [
      { name: 'RSI(6)', type: 'line', data: rsi6, lineStyle: { width: 1.5 }, symbol: 'none', connectNulls: true },
      { name: 'RSI(12)', type: 'line', data: rsi12, lineStyle: { width: 1.5, color: '#f59e0b', type: 'dashed' }, symbol: 'none', connectNulls: true },
      { name: 'RSI(24)', type: 'line', data: rsi24, lineStyle: { width: 1.5, color: '#94a3b8', type: 'dotted' }, symbol: 'none', connectNulls: true }
    ]
  })
  window.addEventListener('resize', () => rsiChart?.resize())
}

// ============ Click outside ============
const handleClickOutside = (e) => {
  if (!e.target.closest('.relative')) showSuggestions.value = false
}

// ============ Lifecycle ============
onMounted(async () => {
  document.addEventListener('click', handleClickOutside)
  await loadAllStocks()
  // 默认加载平安银行
  currentTsCode.value = '000001.SZ'
  currentStockName.value = '平安银行'
  searchText.value = '平安银行 000001.SZ'
  loadIndicators()
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }
</style>
