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
              <input v-model="searchText" @input="onSearchInput" @focus="showSuggestions = true" @keydown.enter="loadStock" type="text" placeholder="股票代码/名称..."
                class="pl-8 pr-3 py-2 text-xs border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-400 w-52 transition-all" />
              <!-- Search Suggestions -->
              <div v-if="showSuggestions && suggestions.length > 0"
                class="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-xl shadow-xl z-50 max-h-52 overflow-y-auto custom-scrollbar">
                <div v-for="s in suggestions" :key="s.ts_code" @click="pickStock(s)"
                  class="flex items-center justify-between px-3 py-2 hover:bg-amber-50 transition-colors text-xs cursor-pointer border-b border-gray-50 last:border-0">
                  <span class="font-medium text-gray-900">{{ s.name }}</span>
                  <span class="text-[10px] text-gray-400 font-mono">{{ s.ts_code }}</span>
                </div>
              </div>
            </div>
            <div class="flex items-center bg-gray-50 rounded-lg p-0.5 border border-gray-100">
              <button v-for="p in periods" :key="p.value" @click="changePeriod(p.value)"
                :class="['px-2.5 py-1.5 text-[11px] font-medium rounded-md transition-all',
                  activePeriod === p.value ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700']"
              >{{ p.label }}</button>
            </div>
            <button @click="refreshAll" :disabled="pageLoading"
              class="px-3 py-2 bg-gray-900 text-white text-xs font-medium rounded-lg hover:bg-gray-800 transition-colors disabled:opacity-60 flex items-center gap-1.5">
              <RefreshCw :class="['w-3.5 h-3.5', pageLoading ? 'animate-spin' : '']" /> 刷新
            </button>
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
            <span :class="['text-lg font-bold font-mono', stockInfo.pctChg >= 0 ? 'text-rose-600' : 'text-emerald-600']">
              {{ stockInfo.price }}
            </span>
            <span :class="['text-xs font-mono px-2 py-0.5 rounded', stockInfo.pctChg >= 0 ? 'bg-rose-50 text-rose-600' : 'bg-emerald-50 text-emerald-600']">
              {{ stockInfo.pctChg >= 0 ? '+' : '' }}{{ stockInfo.pctChg }}%
            </span>
          </div>
          <div class="flex items-center gap-4 ml-auto text-[11px] text-gray-500">
            <span>成交量: <b class="text-gray-700">{{ stockInfo.volume }}</b></span>
            <span v-if="stockInfo.turnover">换手率: <b class="text-gray-700">{{ stockInfo.turnover }}</b></span>
            <span v-if="stockInfo.totalMv">总市值: <b class="text-gray-700">{{ stockInfo.totalMv }}</b></span>
          </div>
        </div>
        <div v-else class="flex items-center gap-2 mb-4 text-xs text-gray-400">
          <Search class="w-4 h-4" /> 搜索股票代码或名称查看行情
        </div>

        <!-- K-Line Chart -->
        <div class="flex-1 bg-white border border-gray-100 rounded-xl shadow-sm overflow-hidden relative">
          <div v-if="chartLoading" class="absolute inset-0 flex items-center justify-center bg-white/80 z-10">
            <Loader2 class="w-7 h-7 animate-spin text-amber-500" />
          </div>
          <div ref="klineRef" class="w-full h-full"></div>
        </div>
      </div>

      <!-- Right: Quick Stats -->
      <div class="w-64 border-l border-gray-100 bg-gray-50/50 p-4 flex flex-col gap-3 shrink-0 overflow-y-auto custom-scrollbar">
        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <h4 class="text-[11px] font-bold text-gray-700 mb-3">日K基本指标</h4>
          <div v-if="dailyStats.length === 0" class="text-[10px] text-gray-400 text-center py-3">选择股票后显示</div>
          <div v-else class="space-y-2.5">
            <div v-for="item in dailyStats" :key="item.label" class="flex justify-between text-xs">
              <span class="text-gray-500">{{ item.label }}</span>
              <span class="font-mono font-medium" :class="item.color || 'text-gray-800'">{{ item.value }}</span>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <h4 class="text-[11px] font-bold text-gray-700 mb-3">五日资金</h4>
          <div v-if="!currentTsCode" class="text-[10px] text-gray-400 text-center py-3">选择个股后显示</div>
          <div v-else-if="miniFlowLoading" class="flex items-center justify-center py-4">
            <Loader2 class="w-5 h-5 animate-spin text-blue-400" />
          </div>
          <div v-else ref="miniFlowRef" class="w-full h-28"></div>
        </div>

        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm flex-1">
          <h4 class="text-[11px] font-bold text-gray-700 mb-3 flex items-center gap-1.5">
            <Star class="w-3.5 h-3.5 text-amber-500" /> 自选股
          </h4>
          <div v-if="watchlist.length === 0" class="text-[10px] text-gray-400 text-center py-4">暂无自选股</div>
          <div v-for="w in watchlist" :key="w.ts_code"
            @click="pickStock({ ts_code: w.ts_code, name: w.name })"
            :class="['flex items-center justify-between px-2 py-1.5 rounded-lg hover:bg-amber-50 cursor-pointer transition-colors text-xs mb-1',
              currentTsCode === w.ts_code ? 'bg-amber-50 border border-amber-200' : '']">
            <span class="font-medium text-gray-700">{{ w.name }}</span>
            <span class="font-mono text-[11px] text-gray-400">{{ w.ts_code.split('.')[0] }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import { CandlestickChart, Search, RefreshCw, Loader2, Star } from 'lucide-vue-next'
import { tushareApi, watchlistApi } from '../../../api/tushare.js'

const searchText = ref('')
const activePeriod = ref('daily')
const klineRef = ref(null)
const miniFlowRef = ref(null)

const pageLoading = ref(false)
const chartLoading = ref(false)
const miniFlowLoading = ref(false)
const showSuggestions = ref(false)
const suggestions = ref([])
const allStocks = ref([])
const stocksLoaded = ref(false)

const currentTsCode = ref('')
const currentStockName = ref('')
const klineData = ref([])
const dailyBasicData = ref(null)
const moneyflowData = ref([])
const watchlist = ref([])

let klineChart = null
let miniFlowChart = null
let searchTimer = null
let fetchToken = 0

const periods = [
  { label: '日K', value: 'daily' },
  { label: '周K', value: 'weekly' },
  { label: '月K', value: 'monthly' }
]

// ============ Helpers ============
const fmtNum = (v, d = 2) => (v == null ? '--' : Number(v).toFixed(d))
const fmtVol = (v) => {
  if (!v) return '--'
  const n = Number(v)
  if (n >= 1e8) return (n / 1e8).toFixed(1) + '亿'
  if (n >= 1e4) return (n / 1e4).toFixed(1) + '万'
  return n.toFixed(0)
}
const fmtWanYi = (v) => {
  if (v == null) return '--'
  const n = Number(v)
  if (Math.abs(n) >= 1e4) return (n / 1e4).toFixed(2) + '亿'
  return n.toFixed(2) + '万'
}

const ymd = (date) => {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}${m}${d}`
}

const getRange = (days) => {
  const end = new Date()
  const start = new Date(end)
  start.setDate(start.getDate() - days)
  return { start_date: ymd(start), end_date: ymd(end) }
}

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms))

const hasRows = (arr) => Array.isArray(arr) && arr.length > 0

const extractRows = (payload) => {
  const rows = Array.isArray(payload?.data) ? payload.data : []
  if (!Array.isArray(rows) || rows.length === 0) return { rows: [], error: null }
  if (rows.length === 1 && rows[0] && typeof rows[0] === 'object' && rows[0].error) {
    return { rows: [], error: String(rows[0].error) }
  }
  return { rows, error: null }
}

const calcSig = (arr, fields = []) => {
  if (!hasRows(arr)) return ''
  const last = arr[arr.length - 1] || {}
  const picked = fields.map(f => String(last?.[f] ?? '')).join('|')
  return `${arr.length}|${picked}`
}

// ============ Stock Info ============
const stockInfo = computed(() => {
  if (!currentTsCode.value || klineData.value.length === 0) return null
  const last = klineData.value[klineData.value.length - 1]
  const basic = dailyBasicData.value
  return {
    name: currentStockName.value,
    code: currentTsCode.value,
    price: fmtNum(last.close),
    pctChg: last.pct_chg != null ? Number(last.pct_chg).toFixed(2) : (last.change != null ? Number(last.change).toFixed(2) : 0),
    volume: fmtVol(last.vol),
    turnover: basic?.turnover_rate ? basic.turnover_rate.toFixed(2) + '%' : null,
    totalMv: basic?.total_mv ? fmtWanYi(basic.total_mv) : null,
  }
})

// ============ Daily Stats ============
const dailyStats = computed(() => {
  if (klineData.value.length === 0) return []
  const last = klineData.value[klineData.value.length - 1]
  const prev = klineData.value.length > 1 ? klineData.value[klineData.value.length - 2] : null
  const basic = dailyBasicData.value
  const items = [
    { label: '开盘', value: fmtNum(last.open) },
    { label: '最高', value: fmtNum(last.high), color: 'text-rose-600' },
    { label: '最低', value: fmtNum(last.low), color: 'text-emerald-600' },
    { label: '昨收', value: prev ? fmtNum(prev.close) : '--' },
  ]
  if (last.high != null && last.low != null && prev?.close) {
    const amp = ((last.high - last.low) / prev.close * 100).toFixed(2) + '%'
    items.push({ label: '振幅', value: amp })
  }
  if (basic) {
    if (basic.pe_ttm != null) items.push({ label: 'PE(TTM)', value: fmtNum(basic.pe_ttm) + 'x' })
    if (basic.pb != null) items.push({ label: 'PB', value: fmtNum(basic.pb) + 'x' })
    if (basic.dv_ratio != null) items.push({ label: '股息率', value: fmtNum(basic.dv_ratio) + '%' })
  }
  return items
})

// ============ Search ============
const loadAllStocks = async () => {
  if (stocksLoaded.value) return
  try {
    const res = await tushareApi.getStockBasic()
    allStocks.value = res.data || []
    stocksLoaded.value = true
  } catch (e) {
    console.error('加载股票列表失败:', e)
  }
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
  fetchStockData()
}

// ============ Data Fetching ============
const fetchStockData = async () => {
  if (!currentTsCode.value) return
  const currentToken = ++fetchToken
  chartLoading.value = true
  miniFlowLoading.value = true

  const code = currentTsCode.value
  const fetchFn = activePeriod.value === 'weekly' ? tushareApi.getWeekly
    : activePeriod.value === 'monthly' ? tushareApi.getMonthly
    : tushareApi.getDaily

  const [kRes, bRes, mfRes] = await Promise.allSettled([
    fetchFn(code),
    tushareApi.getDailyBasic(code),
    tushareApi.getMoneyflow(code),
  ])

  if (currentToken !== fetchToken) return

  if (kRes.status === 'fulfilled') {
    let { rows: data, error: kErr } = extractRows(kRes.value)
    if (kErr) console.error('K线API错误:', kErr)
    if (data.length === 0) {
      try {
        const days = activePeriod.value === 'monthly' ? 365 * 3 : activePeriod.value === 'weekly' ? 365 : 90
        const { start_date, end_date } = getRange(days)
        const retry = await fetchFn(code, start_date, end_date)
        const parsed = extractRows(retry)
        data = parsed.rows
        if (parsed.error) console.error('K线空数据补拉API错误:', parsed.error)
      } catch (e) {
        console.error('K线空数据补拉失败:', e)
      }
    }
    if (data.length > 0) klineData.value = data
  } else {
    console.error('K线:', kRes.reason)
  }
  chartLoading.value = false

  if (bRes.status === 'fulfilled') {
    let { rows: d, error: bErr } = extractRows(bRes.value)
    if (bErr) console.error('日指标API错误:', bErr)
    if (d.length === 0) {
      try {
        const today = ymd(new Date())
        const retry = await tushareApi.getDailyBasic(code, today)
        const parsed = extractRows(retry)
        d = parsed.rows
        if (parsed.error) console.error('日指标空数据补拉API错误:', parsed.error)
      } catch (e) {
        console.error('日指标空数据补拉失败:', e)
      }
    }
    dailyBasicData.value = (d && d.length > 0) ? d[0] : null
  } else {
    console.error('日指标:', bRes.reason)
  }

  if (mfRes.status === 'fulfilled') {
    let { rows: data, error: mErr } = extractRows(mfRes.value)
    if (mErr) console.error('资金流API错误:', mErr)
    if (data.length === 0) {
      try {
        const { start_date, end_date } = getRange(30)
        const retry = await tushareApi.getMoneyflow(code, start_date, end_date)
        const parsed = extractRows(retry)
        data = parsed.rows
        if (parsed.error) console.error('资金流空数据补拉API错误:', parsed.error)
      } catch (e) {
        console.error('资金流空数据补拉失败:', e)
      }
    }
    if (data.length > 0) moneyflowData.value = data
  } else {
    console.error('资金流:', mfRes.reason)
  }

  let kStable = hasRows(klineData.value)
  let bStable = !!dailyBasicData.value
  let mStable = hasRows(moneyflowData.value)
  const maxRetryRounds = 120

  for (let round = 0; round < maxRetryRounds; round += 1) {
    if (currentToken !== fetchToken) return
    if (kStable && bStable && mStable) break

    await sleep(1200)
    if (currentToken !== fetchToken) return

    const tasks = []
    const labels = []

    if (!kStable) {
      const days = activePeriod.value === 'monthly' ? 365 * 3 : activePeriod.value === 'weekly' ? 365 : 90
      const { start_date, end_date } = getRange(days)
      tasks.push(fetchFn(code, start_date, end_date))
      labels.push('k')
    }
    if (!bStable) {
      tasks.push(tushareApi.getDailyBasic(code, ymd(new Date())))
      labels.push('b')
    }
    if (!mStable) {
      const { start_date, end_date } = getRange(30)
      tasks.push(tushareApi.getMoneyflow(code, start_date, end_date))
      labels.push('m')
    }

    if (tasks.length === 0) break
    const results = await Promise.allSettled(tasks)
    if (currentToken !== fetchToken) return

    for (let i = 0; i < results.length; i += 1) {
      const label = labels[i]
      const res = results[i]
      if (res.status !== 'fulfilled') continue
      const parsed = extractRows(res.value)
      const rows = parsed.rows
      if (parsed.error) console.error(`${label}轮询API错误:`, parsed.error)
      if (!hasRows(rows)) continue

      if (label === 'k') {
        const sig1 = calcSig(rows, ['trade_date', 'close'])
        const confirm = await fetchFn(code, ...(activePeriod.value === 'monthly'
          ? [getRange(365 * 3).start_date, getRange(365 * 3).end_date]
          : activePeriod.value === 'weekly'
            ? [getRange(365).start_date, getRange(365).end_date]
            : [getRange(90).start_date, getRange(90).end_date]))
        const parsed2 = extractRows(confirm)
        const rows2 = parsed2.rows
        if (parsed2.error) console.error('K线确认API错误:', parsed2.error)
        const sig2 = calcSig(rows2, ['trade_date', 'close'])
        if (hasRows(rows2) && sig1 === sig2) {
          klineData.value = rows2
          kStable = true
        }
      }

      if (label === 'b') {
        const sig1 = calcSig(rows, ['trade_date', 'close', 'pe_ttm'])
        const confirm = await tushareApi.getDailyBasic(code, ymd(new Date()))
        const parsed2 = extractRows(confirm)
        const rows2 = parsed2.rows
        if (parsed2.error) console.error('日指标确认API错误:', parsed2.error)
        const sig2 = calcSig(rows2, ['trade_date', 'close', 'pe_ttm'])
        if (hasRows(rows2) && sig1 === sig2) {
          dailyBasicData.value = rows2[0]
          bStable = true
        }
      }

      if (label === 'm') {
        const sig1 = calcSig(rows, ['trade_date', 'buy_sm_amount', 'sell_sm_amount'])
        const { start_date, end_date } = getRange(30)
        const confirm = await tushareApi.getMoneyflow(code, start_date, end_date)
        const parsed2 = extractRows(confirm)
        const rows2 = parsed2.rows
        if (parsed2.error) console.error('资金流确认API错误:', parsed2.error)
        const sig2 = calcSig(rows2, ['trade_date', 'buy_sm_amount', 'sell_sm_amount'])
        if (hasRows(rows2) && sig1 === sig2) {
          moneyflowData.value = rows2
          mStable = true
        }
      }
    }
  }

  miniFlowLoading.value = false
  chartLoading.value = false

  await nextTick()
  if (klineData.value.length > 0) renderKlineChart()
  if (moneyflowData.value.length > 0) renderMiniFlow()
}

const changePeriod = (p) => {
  activePeriod.value = p
  if (currentTsCode.value) fetchStockData()
}

const refreshAll = async () => {
  pageLoading.value = true
  await loadWatchlist()
  if (currentTsCode.value) await fetchStockData()
  pageLoading.value = false
}

// ============ Watchlist ============
const loadWatchlist = async () => {
  try { watchlist.value = await watchlistApi.list() } catch (e) { console.error('自选股:', e) }
}

// ============ Charts ============
const renderKlineChart = () => {
  if (!klineRef.value || klineData.value.length === 0) return
  if (klineChart) klineChart.dispose()
  klineChart = echarts.init(klineRef.value)

  const dates = klineData.value.map(d => d.trade_date)
  const ohlc = klineData.value.map(d => [d.open, d.close, d.low, d.high])
  const volumes = klineData.value.map(d => d.vol)
  const colors = klineData.value.map(d => d.close >= d.open ? '#ef444480' : '#22c55e80')

  klineChart.setOption({
    animation: true,
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' }, textStyle: { fontSize: 11 },
      backgroundColor: 'rgba(255,255,255,0.95)', borderColor: '#f3f4f6', borderWidth: 1,
      extraCssText: 'box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-radius: 8px;' },
    grid: [
      { left: 60, right: 20, top: 20, height: '58%' },
      { left: 60, right: 20, top: '75%', height: '15%' }
    ],
    xAxis: [
      { type: 'category', data: dates, axisLabel: { fontSize: 10, color: '#9ca3af' }, axisLine: { lineStyle: { color: '#e5e7eb' } }, axisTick: { show: false }, gridIndex: 0, boundaryGap: true },
      { type: 'category', data: dates, axisLabel: { show: false }, axisLine: { lineStyle: { color: '#e5e7eb' } }, axisTick: { show: false }, gridIndex: 1, boundaryGap: true }
    ],
    yAxis: [
      { scale: true, axisLabel: { fontSize: 10, color: '#9ca3af' }, splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } }, axisLine: { show: false }, axisTick: { show: false }, gridIndex: 0 },
      { scale: true, axisLabel: { show: false }, splitLine: { show: false }, axisLine: { show: false }, axisTick: { show: false }, gridIndex: 1 }
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: 60, end: 100 },
      { type: 'slider', xAxisIndex: [0, 1], bottom: 5, height: 18, start: 60, end: 100,
        borderColor: '#e5e7eb', fillerColor: 'rgba(245,158,11,0.1)', handleStyle: { color: '#f59e0b' }, textStyle: { color: '#9ca3af', fontSize: 10 } }
    ],
    series: [
      {
        type: 'candlestick', data: ohlc, xAxisIndex: 0, yAxisIndex: 0,
        itemStyle: { color: '#ef4444', color0: '#10b981', borderColor: '#ef4444', borderColor0: '#10b981' }
      },
      {
        type: 'bar', data: volumes.map((v, i) => ({ value: v, itemStyle: { color: colors[i] } })),
        xAxisIndex: 1, yAxisIndex: 1, barMaxWidth: 6
      }
    ]
  })
  window.addEventListener('resize', () => klineChart?.resize())
}

const renderMiniFlow = () => {
  if (!miniFlowRef.value) return
  if (miniFlowChart) miniFlowChart.dispose()

  const recent = moneyflowData.value.slice(-5)
  if (recent.length === 0) return
  miniFlowChart = echarts.init(miniFlowRef.value)

  const dates = recent.map(d => d.trade_date?.slice(-4) || '')
  const netFlow = recent.map(d => {
    const inflow = (d.buy_sm_amount || 0) + (d.buy_md_amount || 0) + (d.buy_lg_amount || 0) + (d.buy_elg_amount || 0)
    const outflow = (d.sell_sm_amount || 0) + (d.sell_md_amount || 0) + (d.sell_lg_amount || 0) + (d.sell_elg_amount || 0)
    return +((inflow - outflow) / 10000).toFixed(2)
  })

  miniFlowChart.setOption({
    tooltip: { trigger: 'axis', textStyle: { fontSize: 9 }, formatter: (p) => `${p[0].name}<br/>净流入: <b>${p[0].value}</b>亿` },
    grid: { top: 5, bottom: 20, left: 5, right: 5, containLabel: false },
    xAxis: { type: 'category', data: dates, axisLabel: { fontSize: 9 }, axisLine: { show: false }, axisTick: { show: false } },
    yAxis: { show: false },
    series: [{
      type: 'bar', data: netFlow.map(v => ({
        value: v,
        itemStyle: { color: v >= 0 ? '#ef4444' : '#10b981', borderRadius: v >= 0 ? [3, 3, 0, 0] : [0, 0, 3, 3] }
      })), barWidth: '50%'
    }]
  })
  window.addEventListener('resize', () => miniFlowChart?.resize())
}

watch(() => activePeriod.value, () => {})

// ============ Click outside ============
const handleClickOutside = (e) => {
  if (!e.target.closest('.relative')) showSuggestions.value = false
}

// ============ Lifecycle ============
onMounted(async () => {
  document.addEventListener('click', handleClickOutside)
  await Promise.all([loadAllStocks(), loadWatchlist()])
  // 默认加载平安银行
  currentTsCode.value = '000001.SZ'
  currentStockName.value = '平安银行'
  searchText.value = '平安银行 000001.SZ'
  fetchStockData()
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }
</style>
