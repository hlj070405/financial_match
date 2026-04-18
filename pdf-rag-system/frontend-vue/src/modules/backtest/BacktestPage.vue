<template>
  <div class="h-full w-full flex flex-col bg-gray-50">
    <!-- Header -->
    <div class="bg-white border-b border-gray-100 px-6 py-3 flex items-center justify-between shrink-0">
      <div class="flex items-center gap-2">
        <div class="p-2 rounded-xl bg-violet-50">
          <TrendingUp class="w-4 h-4 text-violet-600" />
        </div>
        <span class="text-sm font-bold text-gray-900">量化回测</span>
      </div>
    </div>

    <div class="flex-1 overflow-auto p-6">
      <div class="max-w-6xl mx-auto grid grid-cols-12 gap-6">
        <!-- Left: Config Panel -->
        <div class="col-span-4 space-y-4">
          <!-- Stock Selection -->
          <div class="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
            <h3 class="text-sm font-semibold text-gray-800 mb-3">股票选择</h3>
            <input
              v-model="stockSearch"
              @input="onStockSearch"
              type="text"
              placeholder="输入股票代码或名称..."
              class="w-full px-3 py-2 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-violet-200 focus:border-violet-400"
            />
            <!-- Stock dropdown -->
            <div v-if="stockOptions.length > 0 && showDropdown" class="mt-1 border border-gray-200 rounded-xl bg-white shadow-lg max-h-48 overflow-y-auto">
              <div
                v-for="s in stockOptions.slice(0, 10)"
                :key="s.ts_code"
                @click="selectStock(s)"
                class="px-3 py-2 text-sm cursor-pointer hover:bg-violet-50 transition-colors"
              >
                <span class="font-medium text-gray-900">{{ s.name }}</span>
                <span class="text-gray-400 ml-2">{{ s.ts_code }}</span>
              </div>
            </div>
            <div v-if="selectedStock" class="mt-2 px-3 py-1.5 bg-violet-50 rounded-lg text-sm text-violet-700 font-medium">
              {{ selectedStock.name }} ({{ selectedStock.ts_code }})
            </div>
          </div>

          <!-- Strategy Selection -->
          <div class="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
            <div class="flex items-center justify-between mb-3">
              <h3 class="text-sm font-semibold text-gray-800">策略选择</h3>
              <button
                @click="showAiChat = true"
                class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-violet-600 bg-violet-50 hover:bg-violet-100 rounded-lg transition-colors border border-violet-200"
              >
                <Sparkles class="w-3.5 h-3.5" />
                AI 帮你写策略
              </button>
            </div>
            <div class="space-y-2">
              <div
                v-for="s in strategies"
                :key="s.id"
                @click="selectedStrategy = s.id"
                :class="[
                  'p-3 rounded-xl border cursor-pointer transition-all duration-200',
                  selectedStrategy === s.id
                    ? 'border-violet-400 bg-violet-50 shadow-sm'
                    : 'border-gray-100 hover:border-gray-200 hover:bg-gray-50'
                ]"
              >
                <div class="text-sm font-medium text-gray-900">{{ s.name }}</div>
                <div class="text-xs text-gray-500 mt-0.5">{{ s.description }}</div>
              </div>
            </div>
          </div>

          <!-- Strategy Params -->
          <div v-if="currentStrategyParams.length > 0" class="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
            <h3 class="text-sm font-semibold text-gray-800 mb-3">策略参数</h3>
            <div class="space-y-3">
              <div v-for="p in currentStrategyParams" :key="p.key">
                <label class="text-xs text-gray-500 mb-1 block">{{ p.name }} ({{ p.min }}-{{ p.max }})</label>
                <input
                  v-model.number="paramValues[p.key]"
                  type="number"
                  :min="p.min"
                  :max="p.max"
                  class="w-full px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-violet-200"
                />
              </div>
            </div>
          </div>

          <!-- Date Range & Cash -->
          <div class="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
            <h3 class="text-sm font-semibold text-gray-800 mb-3">回测设置</h3>
            <div class="space-y-3">
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="text-xs text-gray-500 mb-1 block">起始日期</label>
                  <input v-model="startDate" type="date" class="w-full px-2 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-violet-200" />
                </div>
                <div>
                  <label class="text-xs text-gray-500 mb-1 block">结束日期</label>
                  <input v-model="endDate" type="date" class="w-full px-2 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-violet-200" />
                </div>
              </div>
              <div>
                <label class="text-xs text-gray-500 mb-1 block">初始资金 (元)</label>
                <input v-model.number="initialCash" type="number" min="1000" class="w-full px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-violet-200" />
              </div>
            </div>
          </div>

          <!-- Run Button -->
          <button
            @click="runBacktest"
            :disabled="!canRun || loading"
            :class="[
              'w-full py-3 rounded-xl text-sm font-semibold transition-all duration-200',
              canRun && !loading
                ? 'bg-violet-600 text-white hover:bg-violet-700 shadow-lg shadow-violet-200'
                : 'bg-gray-100 text-gray-400 cursor-not-allowed'
            ]"
          >
            <span v-if="loading" class="flex items-center justify-center gap-2">
              <Loader2 class="w-4 h-4 animate-spin" /> 回测中...
            </span>
            <span v-else>开始回测</span>
          </button>
        </div>

        <!-- Right: Results -->
        <div class="col-span-8 space-y-4">
          <!-- Empty State -->
          <div v-if="!result && !loading" class="bg-white rounded-2xl border border-gray-100 p-16 flex flex-col items-center justify-center shadow-sm">
            <BarChart3 class="w-12 h-12 text-gray-300 mb-4" />
            <p class="text-sm text-gray-400">选择股票和策略，点击"开始回测"查看结果</p>
          </div>

          <!-- Error -->
          <div v-if="error" class="bg-red-50 border border-red-200 rounded-2xl p-4 text-sm text-red-600">
            {{ error }}
          </div>

          <!-- Summary Cards -->
          <div v-if="result" class="grid grid-cols-4 gap-3">
            <div v-for="card in summaryCards" :key="card.label" class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
              <div class="text-xs text-gray-500">{{ card.label }}</div>
              <div :class="['text-lg font-bold mt-1', card.color]">{{ card.value }}</div>
            </div>
          </div>

          <!-- Equity Curve Chart -->
          <div v-if="result" class="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
            <h3 class="text-sm font-semibold text-gray-800 mb-3">资金曲线</h3>
            <div ref="chartRef" style="width: 100%; height: 320px;"></div>
          </div>

          <!-- Trade List -->
          <div v-if="result && result.trades.length > 0" class="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
            <h3 class="text-sm font-semibold text-gray-800 mb-3">交易明细 (共{{ result.trades.length }}笔)</h3>
            <div class="overflow-x-auto max-h-64 overflow-y-auto">
              <table class="w-full text-xs">
                <thead class="text-gray-500 border-b border-gray-100">
                  <tr>
                    <th class="text-left py-2 px-2">开仓日</th>
                    <th class="text-left py-2 px-2">平仓日</th>
                    <th class="text-right py-2 px-2">方向</th>
                    <th class="text-right py-2 px-2">数量</th>
                    <th class="text-right py-2 px-2">开仓价</th>
                    <th class="text-right py-2 px-2">平仓价</th>
                    <th class="text-right py-2 px-2">盈亏</th>
                    <th class="text-right py-2 px-2">收益率</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(t, i) in result.trades" :key="i" class="border-b border-gray-50 hover:bg-gray-50">
                    <td class="py-2 px-2 text-gray-700">{{ t.open_date }}</td>
                    <td class="py-2 px-2 text-gray-700">{{ t.close_date }}</td>
                    <td class="py-2 px-2 text-right">
                      <span :class="t.direction === 'long' ? 'text-red-500' : 'text-green-500'">
                        {{ t.direction === 'long' ? '做多' : '做空' }}
                      </span>
                    </td>
                    <td class="py-2 px-2 text-right text-gray-700">{{ t.size }}</td>
                    <td class="py-2 px-2 text-right text-gray-700">{{ t.open_price }}</td>
                    <td class="py-2 px-2 text-right text-gray-700">{{ t.close_price }}</td>
                    <td :class="['py-2 px-2 text-right font-medium', t.pnl >= 0 ? 'text-red-500' : 'text-green-500']">
                      {{ t.pnl >= 0 ? '+' : '' }}{{ t.pnl.toFixed(2) }}
                    </td>
                    <td :class="['py-2 px-2 text-right', t.pnl_pct >= 0 ? 'text-red-500' : 'text-green-500']">
                      {{ t.pnl_pct >= 0 ? '+' : '' }}{{ t.pnl_pct.toFixed(2) }}%
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- AI Chat Panel Overlay -->
    <Transition name="slide-panel">
      <div v-if="showAiChat" class="fixed inset-0 z-50 flex justify-end">
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/20 backdrop-blur-sm" @click="showAiChat = false"></div>
        <!-- Panel -->
        <div class="relative w-[480px] h-full bg-white shadow-2xl flex flex-col">
          <!-- Header -->
          <div class="px-5 py-4 border-b border-gray-100 flex items-center justify-between shrink-0">
            <div class="flex items-center gap-2">
              <div class="p-1.5 rounded-lg bg-violet-100">
                <Sparkles class="w-4 h-4 text-violet-600" />
              </div>
              <div>
                <div class="text-sm font-bold text-gray-900">AI 策略顾问</div>
                <div class="text-xs text-gray-400">描述你的交易想法，我帮你变成可回测的策略</div>
              </div>
            </div>
            <button @click="showAiChat = false" class="p-1.5 rounded-lg hover:bg-gray-100 transition-colors">
              <X class="w-4 h-4 text-gray-400" />
            </button>
          </div>

          <!-- Messages -->
          <div ref="chatContainerRef" class="flex-1 overflow-y-auto px-5 py-4 space-y-4">
            <!-- Welcome -->
            <div v-if="chatMessages.length === 0" class="text-center py-8">
              <MessageCircle class="w-10 h-10 text-violet-200 mx-auto mb-3" />
              <p class="text-sm text-gray-500 mb-1">告诉我你的交易想法</p>
              <p class="text-xs text-gray-400">比如："我想在股价跌破20日均线时买入"</p>
              <div class="mt-4 flex flex-wrap justify-center gap-2">
                <button v-for="hint in quickHints" :key="hint" @click="sendChatMessage(hint)" class="px-3 py-1.5 text-xs bg-violet-50 text-violet-600 rounded-full hover:bg-violet-100 transition-colors border border-violet-100">
                  {{ hint }}
                </button>
              </div>
            </div>

            <div v-for="(msg, i) in chatMessages" :key="i" :class="['flex', msg.role === 'user' ? 'justify-end' : 'justify-start']">
              <div :class="[
                'max-w-[85%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap',
                msg.role === 'user'
                  ? 'bg-violet-600 text-white rounded-br-md'
                  : 'bg-gray-100 text-gray-800 rounded-bl-md'
              ]">
                {{ msg.content }}
              </div>
            </div>

            <!-- Streaming indicator -->
            <div v-if="chatStreaming" class="flex justify-start">
              <div class="bg-gray-100 text-gray-800 px-4 py-2.5 rounded-2xl rounded-bl-md text-sm leading-relaxed whitespace-pre-wrap">
                {{ streamBuffer || '...' }}<span class="animate-pulse">|</span>
              </div>
            </div>

            <!-- Apply button when strategy is ready -->
            <div v-if="pendingStrategy" class="bg-green-50 border border-green-200 rounded-xl p-4">
              <div class="text-sm font-semibold text-green-800 mb-2">策略方案已就绪</div>
              <div class="text-xs text-green-700 space-y-1 mb-3">
                <div>{{ pendingStrategy.stock_name }} ({{ pendingStrategy.ts_code }})</div>
                <div>策略: {{ strategyDisplayName(pendingStrategy.strategy) }}</div>
                <div>区间: {{ pendingStrategy.start_date }} ~ {{ pendingStrategy.end_date }}</div>
                <div>资金: ¥{{ (pendingStrategy.initial_cash || 100000).toLocaleString() }}</div>
              </div>
              <button @click="applyStrategy" class="w-full py-2 bg-green-600 text-white text-sm font-semibold rounded-lg hover:bg-green-700 transition-colors">
                应用到回测表单
              </button>
            </div>
          </div>

          <!-- Input -->
          <div class="px-5 py-3 border-t border-gray-100 shrink-0">
            <div class="flex items-center gap-2">
              <input
                v-model="chatInput"
                @keydown.enter.prevent="sendChatMessage(chatInput)"
                :disabled="chatStreaming"
                type="text"
                placeholder="描述你的策略想法..."
                class="flex-1 px-4 py-2.5 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-violet-200 focus:border-violet-400 disabled:bg-gray-50"
              />
              <button
                @click="sendChatMessage(chatInput)"
                :disabled="!chatInput.trim() || chatStreaming"
                :class="[
                  'p-2.5 rounded-xl transition-colors',
                  chatInput.trim() && !chatStreaming
                    ? 'bg-violet-600 text-white hover:bg-violet-700'
                    : 'bg-gray-100 text-gray-300 cursor-not-allowed'
                ]"
              >
                <Send class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { TrendingUp, Loader2, BarChart3, Sparkles, X, Send, MessageCircle } from 'lucide-vue-next'
import * as echarts from 'echarts'
import { backtestApi } from '../../api/backtest.js'
import { tushareApi } from '../../api/tushare.js'

// State
const strategies = ref([])
const selectedStrategy = ref('')
const paramValues = ref({})
const stockSearch = ref('')
const stockOptions = ref([])
const showDropdown = ref(false)
const selectedStock = ref(null)
const startDate = ref('2022-01-01')
const endDate = ref(new Date().toISOString().split('T')[0])
const initialCash = ref(100000)
const loading = ref(false)
const result = ref(null)
const error = ref('')
const chartRef = ref(null)
let chartInstance = null
let allStocks = []

// AI Chat State
const showAiChat = ref(false)
const chatMessages = ref([])
const chatInput = ref('')
const chatStreaming = ref(false)
const streamBuffer = ref('')
const pendingStrategy = ref(null)
const chatContainerRef = ref(null)

const quickHints = [
  '均线金叉策略测一下茅台',
  'RSI超卖时抄底平安银行',
  'MACD信号做比亚迪',
  '我想做一个趋势跟踪策略'
]

const canRun = computed(() => selectedStock.value && selectedStrategy.value)

const currentStrategyParams = computed(() => {
  const s = strategies.value.find(s => s.id === selectedStrategy.value)
  return s?.params || []
})

const summaryCards = computed(() => {
  if (!result.value) return []
  const s = result.value.summary
  return [
    { label: '总收益率', value: `${s.total_return_pct >= 0 ? '+' : ''}${s.total_return_pct}%`, color: s.total_return_pct >= 0 ? 'text-red-500' : 'text-green-500' },
    { label: '年化收益', value: `${s.annual_return_pct >= 0 ? '+' : ''}${s.annual_return_pct}%`, color: s.annual_return_pct >= 0 ? 'text-red-500' : 'text-green-500' },
    { label: '夏普比率', value: s.sharpe_ratio.toFixed(2), color: s.sharpe_ratio >= 1 ? 'text-red-500' : s.sharpe_ratio >= 0 ? 'text-amber-500' : 'text-green-500' },
    { label: '最大回撤', value: `-${s.max_drawdown_pct}%`, color: 'text-green-500' },
    { label: '总交易数', value: `${s.total_trades}笔`, color: 'text-gray-900' },
    { label: '胜率', value: `${s.win_rate_pct}%`, color: s.win_rate_pct >= 50 ? 'text-red-500' : 'text-gray-500' },
    { label: '初始资金', value: `¥${s.initial_cash.toLocaleString()}`, color: 'text-gray-900' },
    { label: '最终价值', value: `¥${s.final_value.toLocaleString()}`, color: s.final_value >= s.initial_cash ? 'text-red-500' : 'text-green-500' },
  ]
})

// Load strategies and stocks on mount
onMounted(async () => {
  try {
    const res = await backtestApi.getStrategies()
    strategies.value = res.strategies || []
    if (strategies.value.length > 0) {
      selectedStrategy.value = strategies.value[0].id
      initParams(strategies.value[0])
    }
  } catch (e) {
    console.error('Failed to load strategies:', e)
  }
  try {
    const res = await tushareApi.getStockBasic()
    allStocks = (res.data || []).map(s => ({ ts_code: s.ts_code, name: s.name }))
  } catch (e) {
    console.error('Failed to load stocks:', e)
  }
})

function initParams(strategy) {
  const vals = {}
  for (const p of strategy.params || []) {
    vals[p.key] = p.default
  }
  paramValues.value = vals
}

watch(selectedStrategy, (id) => {
  const s = strategies.value.find(s => s.id === id)
  if (s) initParams(s)
})

function onStockSearch() {
  const q = stockSearch.value.trim().toLowerCase()
  if (!q) {
    stockOptions.value = []
    showDropdown.value = false
    return
  }
  stockOptions.value = allStocks.filter(s =>
    s.ts_code.toLowerCase().includes(q) || s.name.toLowerCase().includes(q)
  )
  showDropdown.value = true
}

function selectStock(stock) {
  selectedStock.value = stock
  stockSearch.value = `${stock.name} ${stock.ts_code}`
  showDropdown.value = false
}

async function runBacktest() {
  if (!canRun.value) return
  loading.value = true
  error.value = ''
  result.value = null

  try {
    const res = await backtestApi.run({
      ts_code: selectedStock.value.ts_code,
      stock_name: selectedStock.value.name,
      strategy: selectedStrategy.value,
      params: paramValues.value,
      start_date: startDate.value,
      end_date: endDate.value,
      initial_cash: initialCash.value,
    })
    result.value = res
    await nextTick()
    renderChart(res.equity_curve)
  } catch (e) {
    error.value = e.message || '回测失败'
  } finally {
    loading.value = false
  }
}

// ====================== AI Chat Functions ======================

function strategyDisplayName(id) {
  const map = { sma_cross: '双均线交叉', macd_signal: 'MACD金叉死叉', rsi_reversal: 'RSI超卖反弹' }
  return map[id] || id
}

async function sendChatMessage(text) {
  if (!text || !text.trim() || chatStreaming.value) return
  const userMsg = text.trim()
  chatInput.value = ''
  chatMessages.value.push({ role: 'user', content: userMsg })
  pendingStrategy.value = null
  chatStreaming.value = true
  streamBuffer.value = ''

  await nextTick()
  scrollChatToBottom()

  try {
    const token = localStorage.getItem('access_token')
    const res = await fetch('/api/backtest/strategy-chat', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: chatMessages.value })
    })

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buf = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buf += decoder.decode(value, { stream: true })
      const lines = buf.split('\n')
      buf = lines.pop()

      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed || !trimmed.startsWith('data: ')) continue
        const payload = trimmed.slice(6)
        if (payload === '[DONE]') continue
        try {
          const evt = JSON.parse(payload)
          if (evt.type === 'text') {
            streamBuffer.value += evt.text
            scrollChatToBottom()
          }
        } catch {}
      }
    }

    // Finalize: push assistant message
    const fullText = streamBuffer.value
    chatMessages.value.push({ role: 'assistant', content: fullText })
    streamBuffer.value = ''

    // Try to extract strategy JSON
    tryExtractStrategy(fullText)

  } catch (e) {
    chatMessages.value.push({ role: 'assistant', content: `抱歉，出现错误: ${e.message}` })
  } finally {
    chatStreaming.value = false
    await nextTick()
    scrollChatToBottom()
  }
}

function tryExtractStrategy(text) {
  // Look for ```json ... ``` block
  const match = text.match(/```json\s*([\s\S]*?)\s*```/)
  if (!match) return
  try {
    const obj = JSON.parse(match[1])
    if (obj.action === 'run_backtest' && obj.ts_code && obj.strategy) {
      pendingStrategy.value = obj
    }
  } catch {}
}

function applyStrategy() {
  if (!pendingStrategy.value) return
  const s = pendingStrategy.value

  // Find or create stock
  selectedStock.value = { ts_code: s.ts_code, name: s.stock_name || s.ts_code }
  stockSearch.value = `${s.stock_name || ''} ${s.ts_code}`

  // Set strategy
  if (s.strategy) selectedStrategy.value = s.strategy

  // Set params
  if (s.params) {
    for (const [k, v] of Object.entries(s.params)) {
      paramValues.value[k] = v
    }
  }

  // Set dates and cash
  if (s.start_date) startDate.value = s.start_date
  if (s.end_date) endDate.value = s.end_date
  if (s.initial_cash) initialCash.value = s.initial_cash

  pendingStrategy.value = null
  showAiChat.value = false
}

function scrollChatToBottom() {
  nextTick(() => {
    if (chatContainerRef.value) {
      chatContainerRef.value.scrollTop = chatContainerRef.value.scrollHeight
    }
  })
}

function renderChart(curve) {
  if (!chartRef.value || !curve || curve.length === 0) return
  if (chartInstance) chartInstance.dispose()
  chartInstance = echarts.init(chartRef.value)

  const dates = curve.map(p => p.date)
  const values = curve.map(p => p.value)
  const minVal = Math.min(...values)
  const maxVal = Math.max(...values)

  chartInstance.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const p = params[0]
        return `${p.name}<br/>资金: ¥${Number(p.value).toLocaleString()}`
      }
    },
    grid: { left: '8%', right: '4%', top: '8%', bottom: '12%' },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: { fontSize: 10, color: '#999' },
      axisLine: { lineStyle: { color: '#eee' } }
    },
    yAxis: {
      type: 'value',
      min: Math.floor(minVal * 0.98),
      max: Math.ceil(maxVal * 1.02),
      axisLabel: { fontSize: 10, color: '#999', formatter: v => `¥${(v/1000).toFixed(0)}k` },
      splitLine: { lineStyle: { color: '#f5f5f5' } }
    },
    series: [{
      type: 'line',
      data: values,
      smooth: true,
      symbol: 'none',
      lineStyle: { width: 2, color: '#7c3aed' },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(124,58,237,0.15)' },
          { offset: 1, color: 'rgba(124,58,237,0.02)' }
        ])
      }
    }]
  })
}
</script>

<style scoped>
.slide-panel-enter-active, .slide-panel-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.slide-panel-enter-active > div:last-child,
.slide-panel-leave-active > div:last-child {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.slide-panel-enter-from,
.slide-panel-leave-to {
  opacity: 0;
}
.slide-panel-enter-from > div:last-child {
  transform: translateX(100%);
}
.slide-panel-leave-to > div:last-child {
  transform: translateX(100%);
}
</style>
