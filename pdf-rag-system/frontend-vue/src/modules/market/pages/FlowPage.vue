<template>
  <div class="h-full flex flex-col">
    <!-- Hero -->
    <div class="relative overflow-hidden bg-gradient-to-br from-cyan-50 via-white to-sky-50 border-b border-gray-100">
      <div class="absolute inset-0 opacity-20">
        <div class="absolute top-3 left-16 w-48 h-48 bg-cyan-200 rounded-full blur-3xl animate-pulse"></div>
        <div class="absolute bottom-0 right-10 w-40 h-40 bg-sky-200 rounded-full blur-3xl animate-pulse" style="animation-delay: 1s;"></div>
      </div>
      <div class="relative px-6 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-500 to-sky-600 flex items-center justify-center shadow-md shadow-cyan-500/20 shrink-0">
              <ArrowLeftRight class="w-4.5 h-4.5 text-white" />
            </div>
            <div>
              <h1 class="text-base font-bold text-gray-900">资金流向</h1>
              <p class="text-[11px] text-gray-500 mt-0.5">主力资金、北向资金等资金面分析，洞察市场资金动向</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <div class="relative">
              <Search class="w-3.5 h-3.5 text-gray-400 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input v-model="searchText" @input="onSearchInput" @focus="showSuggestions = true" @keydown.enter="loadFlow" type="text" placeholder="股票代码/名称..."
                class="pl-8 pr-3 py-2 text-xs border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 focus:border-cyan-400 w-48 transition-all" />
              <div v-if="showSuggestions && suggestions.length > 0"
                class="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-xl shadow-xl z-50 max-h-52 overflow-y-auto custom-scrollbar">
                <div v-for="s in suggestions" :key="s.ts_code" @click="pickStock(s)"
                  class="flex items-center justify-between px-3 py-2 hover:bg-cyan-50 transition-colors text-xs cursor-pointer border-b border-gray-50 last:border-0">
                  <span class="font-medium text-gray-900">{{ s.name }}</span>
                  <span class="text-[10px] text-gray-400 font-mono">{{ s.ts_code }}</span>
                </div>
              </div>
            </div>
            <button @click="loadFlow" :disabled="dataLoading"
              class="px-4 py-2 bg-cyan-600 text-white text-xs font-medium rounded-lg hover:bg-cyan-700 transition-colors disabled:opacity-60 flex items-center gap-1.5">
              <Loader2 v-if="dataLoading" class="w-3.5 h-3.5 animate-spin" />
              <Search v-else class="w-3.5 h-3.5" /> 查询
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

        <!-- Main Flow Chart -->
        <div class="bg-white border border-gray-100 rounded-xl shadow-sm flex-[2] overflow-hidden relative">
          <div class="px-4 py-2.5 border-b border-gray-50 flex items-center justify-between">
            <h3 class="text-xs font-bold text-gray-800">主力资金流向（净流入）</h3>
            <div class="flex items-center gap-1 bg-gray-50 rounded-lg p-0.5 border border-gray-100">
              <button v-for="p in flowPeriods" :key="p.value" @click="changeFlowPeriod(p.value)"
                :class="['px-2 py-1 text-[10px] font-medium rounded transition-all',
                  flowPeriod === p.value ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500']"
              >{{ p.label }}</button>
            </div>
          </div>
          <div v-if="dataLoading" class="absolute inset-0 top-9 flex items-center justify-center bg-white/80 z-10">
            <Loader2 class="w-6 h-6 animate-spin text-cyan-500" />
          </div>
          <div ref="flowChartRef" class="w-full" style="height: calc(100% - 38px);"></div>
        </div>

        <!-- Detail Bar Chart: 大单/超大单/中单/小单 -->
        <div class="bg-white border border-gray-100 rounded-xl shadow-sm flex-1 overflow-hidden relative">
          <div class="px-4 py-2.5 border-b border-gray-50">
            <h3 class="text-xs font-bold text-gray-800">分类资金明细（最近交易日）</h3>
          </div>
          <div v-if="dataLoading" class="absolute inset-0 top-9 flex items-center justify-center bg-white/80 z-10">
            <Loader2 class="w-6 h-6 animate-spin text-cyan-500" />
          </div>
          <div ref="detailRef" class="w-full" style="height: calc(100% - 38px);"></div>
        </div>
      </div>

      <!-- Right Panel -->
      <div class="w-72 border-l border-gray-100 bg-gray-50/50 p-4 flex flex-col gap-3 shrink-0 overflow-y-auto custom-scrollbar">
        <!-- Summary Cards -->
        <div class="grid grid-cols-2 gap-2">
          <div v-for="card in summaryCards" :key="card.label"
            class="bg-white rounded-xl border border-gray-100 p-3 shadow-sm text-center">
            <p class="text-[10px] text-gray-500 mb-1">{{ card.label }}</p>
            <p :class="['text-base font-bold font-mono', card.color]">{{ card.value }}</p>
            <p class="text-[9px] text-gray-400">{{ card.sub }}</p>
          </div>
        </div>

        <!-- Recent Days Table -->
        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <h4 class="text-[11px] font-bold text-gray-700 mb-3 flex items-center gap-1.5">
            <TrendingUp class="w-3.5 h-3.5 text-rose-500" /> 近5日资金净流入
          </h4>
          <div v-if="recentFlowTable.length === 0" class="text-[10px] text-gray-400 text-center py-3">选择股票后显示</div>
          <div v-else class="space-y-1.5">
            <div v-for="(row, i) in recentFlowTable" :key="i" class="flex items-center justify-between px-2 py-1.5 rounded-lg hover:bg-gray-50 transition-colors">
              <span class="text-[11px] text-gray-500 font-mono">{{ row.date }}</span>
              <span :class="['text-[11px] font-mono font-semibold', row.net >= 0 ? 'text-rose-600' : 'text-emerald-600']">
                {{ row.net >= 0 ? '+' : '' }}{{ row.netStr }}万
              </span>
            </div>
          </div>
        </div>

        <!-- Cumulative stats -->
        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm flex-1">
          <h4 class="text-[11px] font-bold text-gray-700 mb-3 flex items-center gap-1.5">
            <Globe class="w-3.5 h-3.5 text-blue-500" /> 累计统计
          </h4>
          <div v-if="cumulativeStats.length === 0" class="text-[10px] text-gray-400 text-center py-3">选择股票后显示</div>
          <div v-else class="space-y-2">
            <div v-for="item in cumulativeStats" :key="item.label" class="flex justify-between text-xs">
              <span class="text-gray-500">{{ item.label }}</span>
              <span :class="['font-mono font-semibold', item.color]">{{ item.value }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ArrowLeftRight, Search, TrendingUp, TrendingDown, Globe, Loader2 } from 'lucide-vue-next'
import { tushareApi } from '../../../api/tushare.js'

const searchText = ref('')
const flowPeriod = ref(20)
const flowChartRef = ref(null)
const detailRef = ref(null)

const dataLoading = ref(false)
const showSuggestions = ref(false)
const suggestions = ref([])
const allStocks = ref([])
const stocksLoaded = ref(false)
const currentTsCode = ref('')
const currentStockName = ref('')
const rawFlowData = ref([])

let flowChart = null
let detailChart = null
let searchTimer = null

const flowPeriods = [
  { label: '5日', value: 5 },
  { label: '20日', value: 20 },
  { label: '60日', value: 60 }
]

// ============ Helpers ============
const fmtWan = (v) => {
  if (v == null) return '--'
  const n = Number(v)
  if (Math.abs(n) >= 10000) return (n / 10000).toFixed(1) + '亿'
  return n.toFixed(0) + '万'
}

// ============ Computed ============
const calcNetFlow = (d) => {
  const inflow = (d.buy_sm_amount || 0) + (d.buy_md_amount || 0) + (d.buy_lg_amount || 0) + (d.buy_elg_amount || 0)
  const outflow = (d.sell_sm_amount || 0) + (d.sell_md_amount || 0) + (d.sell_lg_amount || 0) + (d.sell_elg_amount || 0)
  return inflow - outflow
}

const summaryCards = computed(() => {
  if (rawFlowData.value.length === 0) return []
  const latest = rawFlowData.value[rawFlowData.value.length - 1]
  const elgNet = (latest.buy_elg_amount || 0) - (latest.sell_elg_amount || 0)
  const lgNet = (latest.buy_lg_amount || 0) - (latest.sell_lg_amount || 0)
  const mdNet = (latest.buy_md_amount || 0) - (latest.sell_md_amount || 0)
  const smNet = (latest.buy_sm_amount || 0) - (latest.sell_sm_amount || 0)
  const mainNet = elgNet + lgNet
  const retailNet = mdNet + smNet

  const fmtCard = (v) => (v >= 0 ? '+' : '') + fmtWan(v)
  return [
    { label: '主力净流入', value: fmtCard(mainNet), sub: `超大单+大单`, color: mainNet >= 0 ? 'text-rose-600' : 'text-emerald-600' },
    { label: '超大单净流入', value: fmtCard(elgNet), sub: mainNet !== 0 ? `占比 ${(Math.abs(elgNet) / (Math.abs(elgNet) + Math.abs(lgNet)) * 100).toFixed(0)}%` : '', color: elgNet >= 0 ? 'text-rose-600' : 'text-emerald-600' },
    { label: '大单净流入', value: fmtCard(lgNet), sub: mainNet !== 0 ? `占比 ${(Math.abs(lgNet) / (Math.abs(elgNet) + Math.abs(lgNet)) * 100).toFixed(0)}%` : '', color: lgNet >= 0 ? 'text-rose-500' : 'text-emerald-500' },
    { label: '散户净流入', value: fmtCard(retailNet), sub: '中单+小单', color: retailNet >= 0 ? 'text-rose-600' : 'text-emerald-600' }
  ]
})

const recentFlowTable = computed(() => {
  return rawFlowData.value.slice(-5).map(d => {
    const net = calcNetFlow(d)
    return { date: d.trade_date || '', net, netStr: fmtWan(net) }
  })
})

const cumulativeStats = computed(() => {
  if (rawFlowData.value.length === 0) return []
  const recent5 = rawFlowData.value.slice(-5)
  const recent20 = rawFlowData.value.slice(-20)
  const all = rawFlowData.value

  const sum = (arr) => arr.reduce((s, d) => s + calcNetFlow(d), 0)
  const s5 = sum(recent5), s20 = sum(recent20), sAll = sum(all)

  const fmt = (v) => (v >= 0 ? '+' : '') + fmtWan(v)
  return [
    { label: '近5日累计', value: fmt(s5), color: s5 >= 0 ? 'text-rose-600' : 'text-emerald-600' },
    { label: '近20日累计', value: fmt(s20), color: s20 >= 0 ? 'text-rose-600' : 'text-emerald-600' },
    { label: `全部(${all.length}日)`, value: fmt(sAll), color: sAll >= 0 ? 'text-rose-600' : 'text-emerald-600' },
  ]
})

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
  loadFlow()
}

// ============ Data Loading ============
const loadFlow = async () => {
  if (!currentTsCode.value) return
  dataLoading.value = true
  try {
    const res = await tushareApi.getMoneyflow(currentTsCode.value)
    rawFlowData.value = res.data || []
  } catch (e) {
    console.error('获取资金流向失败:', e)
    rawFlowData.value = []
  }
  dataLoading.value = false
  await nextTick()
  renderFlowChart()
  renderDetailChart()
}

const changeFlowPeriod = (p) => {
  flowPeriod.value = p
  renderFlowChart()
}

// ============ Charts ============
const renderFlowChart = () => {
  if (!flowChartRef.value || rawFlowData.value.length === 0) return
  if (flowChart) flowChart.dispose()
  flowChart = echarts.init(flowChartRef.value)

  const sliced = rawFlowData.value.slice(-flowPeriod.value)
  const dates = sliced.map(d => d.trade_date || '')
  const mainNet = sliced.map(d => {
    const elgNet = (d.buy_elg_amount || 0) - (d.sell_elg_amount || 0)
    const lgNet = (d.buy_lg_amount || 0) - (d.sell_lg_amount || 0)
    return +((elgNet + lgNet) / 10000).toFixed(2)
  })
  const retailNet = sliced.map(d => {
    const mdNet = (d.buy_md_amount || 0) - (d.sell_md_amount || 0)
    const smNet = (d.buy_sm_amount || 0) - (d.sell_sm_amount || 0)
    return +((mdNet + smNet) / 10000).toFixed(2)
  })

  flowChart.setOption({
    tooltip: { trigger: 'axis', textStyle: { fontSize: 10 },
      backgroundColor: 'rgba(255,255,255,0.95)', borderColor: '#f3f4f6', borderWidth: 1,
      extraCssText: 'box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-radius: 8px;',
      formatter: (params) => {
        let s = `<b>${params[0].name}</b><br/>`
        params.forEach(p => {
          const color = p.value >= 0 ? '#ef4444' : '#10b981'
          s += `${p.seriesName}: <b style="color:${color}">${p.value >= 0 ? '+' : ''}${p.value}亿</b><br/>`
        })
        return s
      }
    },
    legend: { data: ['主力净流入', '散户净流入'], bottom: 5, textStyle: { fontSize: 10 } },
    grid: { top: 15, bottom: 40, left: 55, right: 15 },
    xAxis: { type: 'category', data: dates, axisLabel: { fontSize: 9, color: '#9ca3af' }, axisLine: { lineStyle: { color: '#e5e7eb' } }, axisTick: { show: false } },
    yAxis: { type: 'value', axisLabel: { fontSize: 9, color: '#9ca3af', formatter: '{value}亿' }, splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } }, axisLine: { show: false }, axisTick: { show: false } },
    series: [
      {
        name: '主力净流入', type: 'bar', data: mainNet.map(v => ({
          value: v, itemStyle: { color: v >= 0 ? '#ef4444' : '#10b981', borderRadius: v >= 0 ? [3, 3, 0, 0] : [0, 0, 3, 3] }
        })), barWidth: '35%'
      },
      {
        name: '散户净流入', type: 'line', data: retailNet,
        lineStyle: { width: 1.5, color: '#f59e0b', type: 'dashed' }, symbol: 'none',
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(245,158,11,0.08)' }, { offset: 1, color: 'rgba(245,158,11,0)' }
        ]) }
      }
    ]
  })
  window.addEventListener('resize', () => flowChart?.resize())
}

const renderDetailChart = () => {
  if (!detailRef.value || rawFlowData.value.length === 0) return
  if (detailChart) detailChart.dispose()
  detailChart = echarts.init(detailRef.value)

  const recent = rawFlowData.value.slice(-10)
  const dates = recent.map(d => d.trade_date || '')

  const elgNet = recent.map(d => +(((d.buy_elg_amount || 0) - (d.sell_elg_amount || 0)) / 10000).toFixed(2))
  const lgNet = recent.map(d => +(((d.buy_lg_amount || 0) - (d.sell_lg_amount || 0)) / 10000).toFixed(2))
  const mdNet = recent.map(d => +(((d.buy_md_amount || 0) - (d.sell_md_amount || 0)) / 10000).toFixed(2))
  const smNet = recent.map(d => +(((d.buy_sm_amount || 0) - (d.sell_sm_amount || 0)) / 10000).toFixed(2))

  detailChart.setOption({
    tooltip: { trigger: 'axis', textStyle: { fontSize: 10 },
      backgroundColor: 'rgba(255,255,255,0.95)', borderColor: '#f3f4f6', borderWidth: 1,
      extraCssText: 'box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-radius: 8px;' },
    legend: { data: ['超大单', '大单', '中单', '小单'], bottom: 5, textStyle: { fontSize: 10 } },
    grid: { top: 15, bottom: 40, left: 55, right: 15 },
    xAxis: { type: 'category', data: dates, axisLabel: { fontSize: 9, color: '#9ca3af' }, axisLine: { lineStyle: { color: '#e5e7eb' } }, axisTick: { show: false } },
    yAxis: { type: 'value', axisLabel: { fontSize: 9, color: '#9ca3af', formatter: '{value}亿' }, splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } }, axisLine: { show: false }, axisTick: { show: false } },
    series: [
      { name: '超大单', type: 'bar', stack: 'flow', data: elgNet, barWidth: '40%', itemStyle: { color: '#ef4444' } },
      { name: '大单', type: 'bar', stack: 'flow', data: lgNet, itemStyle: { color: '#f97316' } },
      { name: '中单', type: 'bar', stack: 'flow', data: mdNet, itemStyle: { color: '#eab308' } },
      { name: '小单', type: 'bar', stack: 'flow', data: smNet, itemStyle: { color: '#22c55e' } },
    ]
  })
  window.addEventListener('resize', () => detailChart?.resize())
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
  loadFlow()
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }
</style>
