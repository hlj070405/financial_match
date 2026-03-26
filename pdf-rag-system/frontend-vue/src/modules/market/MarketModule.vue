<template>

  <div class="h-full flex flex-col gap-5 p-2 font-sans overflow-hidden relative">

    <!-- Header: 自选股 + 工具栏 -->

    <div class="bg-white border border-gray-100 rounded-2xl p-4 shadow-sm shrink-0 flex items-center justify-between gap-4">

      <!-- 自选股区域 -->
      <div class="flex items-center gap-2 min-w-0 flex-1 overflow-x-auto custom-scrollbar">
        <div class="flex items-center gap-1.5 shrink-0 mr-1">
          <Star class="w-4 h-4 text-amber-500" />
          <span class="text-sm font-bold text-gray-700">自选</span>
        </div>

        <div v-if="watchlistItems.length === 0" class="text-xs text-gray-400 shrink-0">暂无自选股，搜索后点击 + 添加</div>

        <button
          v-for="w in watchlistItems"
          :key="w.ts_code"
          @click="jumpToWatchlistStock(w)"
          :class="cn(
            'shrink-0 px-3 py-1.5 rounded-lg text-xs font-medium transition-all border group relative',
            currentTsCode === w.ts_code
              ? 'bg-amber-50 border-amber-200 text-amber-700'
              : 'bg-gray-50 border-gray-100 text-gray-600 hover:bg-amber-50 hover:border-amber-200 hover:text-amber-700'
          )"
        >
          <span>{{ w.name }}</span>
          <span class="ml-1 text-[10px] opacity-60 font-mono">{{ w.ts_code.split('.')[0] }}</span>
          <span
            @click.stop="removeFromWatchlist(w.ts_code)"
            class="ml-1.5 opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition-all cursor-pointer"
          >&times;</span>
        </button>
      </div>



      <div class="flex items-center gap-3">

        <!-- Stock Search -->

        <div class="relative">

          <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">

            <Search class="w-4 h-4 text-gray-400" />

          </div>

          <input

            v-model="searchText"

            @input="onSearchInput"

            @focus="showSuggestions = true"

            placeholder="输入股票代码或名称..."

            class="pl-10 pr-4 py-2.5 w-72 text-sm bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500 transition-all placeholder-gray-400"

          />

          <!-- Suggestions Dropdown -->

          <div

            v-if="showSuggestions && suggestions.length > 0"

            class="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-xl shadow-xl z-50 max-h-60 overflow-y-auto custom-scrollbar"

          >

            <div
              v-for="s in suggestions"
              :key="s.ts_code"
              class="flex items-center justify-between px-4 py-2.5 hover:bg-amber-50 transition-colors text-sm border-b border-gray-50 last:border-0"
            >
              <button @click="selectStock(s)" class="flex-1 text-left flex items-center justify-between min-w-0">
                <span class="font-medium text-gray-900">{{ s.name }}</span>
                <span class="text-xs text-gray-400 font-mono">{{ s.ts_code }}</span>
              </button>
              <button
                @click.stop="addToWatchlist(s)"
                :class="cn(
                  'ml-2 shrink-0 w-6 h-6 rounded-md flex items-center justify-center text-xs transition-all',
                  isInWatchlist(s.ts_code)
                    ? 'bg-amber-100 text-amber-500 cursor-default'
                    : 'bg-gray-100 text-gray-400 hover:bg-amber-100 hover:text-amber-600'
                )"
                :title="isInWatchlist(s.ts_code) ? '已在自选' : '加自选'"
              >
                <Star :class="['w-3.5 h-3.5', isInWatchlist(s.ts_code) ? 'fill-amber-400' : '']" />
              </button>
            </div>

          </div>

        </div>



        <!-- Period Toggle -->

        <div class="flex items-center bg-gray-50 rounded-xl p-1 border border-gray-100">

          <button

            v-for="p in periods"

            :key="p.key"

            @click="changePeriod(p.key)"

            :class="cn(

              'px-3 py-1.5 text-xs font-medium rounded-lg transition-all relative group overflow-hidden',

              activePeriod === p.key

                ? 'bg-white text-gray-900 shadow-sm'

                : 'text-gray-500 hover:text-gray-900 hover:bg-white/50'

            )"

          >

            <div class="absolute bottom-0 left-0 w-full h-0.5 bg-orange-500 opacity-0 group-hover:opacity-100 transition-opacity"></div>

            {{ p.label }}

          </button>

        </div>



        <button

          @click="refreshData"

          :disabled="loading"

          class="flex items-center gap-2 px-4 py-2 bg-gray-900 text-white text-sm font-medium rounded-xl hover:bg-gray-800 active:scale-95 transition-all disabled:opacity-70 shadow-lg shadow-gray-900/20 relative group overflow-hidden"

        >

          <div class="absolute bottom-0 left-0 w-full h-0.5 bg-orange-500 opacity-0 group-hover:opacity-100 transition-opacity"></div>

          <RefreshCw :class="['w-4 h-4', loading ? 'animate-spin' : '']" />

          刷新

        </button>

      </div>

    </div>



    <!-- Index Overview Cards -->

    <div class="grid grid-cols-4 gap-5 shrink-0">

      <div

        v-for="idx in indexCards"

        :key="idx.code"

        @click="selectIndex(idx)"

        :class="cn(

          'bg-white border rounded-2xl p-4 shadow-sm hover:shadow-md transition-all cursor-pointer group relative overflow-hidden',

          selectedIndex === idx.code ? 'border-amber-300 ring-1 ring-amber-200' : 'border-gray-100'

        )"

      >

        <div class="absolute top-0 left-0 w-full h-0.5 transition-opacity"

          :class="idx.change >= 0 ? 'bg-rose-500' : 'bg-emerald-500'"

          :style="{ opacity: selectedIndex === idx.code ? 1 : 0 }"

        ></div>

        <div class="flex items-center justify-between mb-2">

          <span class="text-sm font-medium text-gray-600">{{ idx.name }}</span>

          <span class="text-[10px] font-mono text-gray-400">{{ idx.code }}</span>

        </div>

        <div class="flex items-baseline gap-3">

          <span class="text-2xl font-bold text-gray-900">{{ idx.close ?? '--' }}</span>

          <div class="flex items-center gap-1" v-if="idx.change !== null">

            <component

              :is="idx.change >= 0 ? TrendingUp : TrendingDown"

              :class="cn('w-3.5 h-3.5', idx.change >= 0 ? 'text-rose-500' : 'text-emerald-500')"

            />

            <span

              :class="cn('text-xs font-semibold', idx.change >= 0 ? 'text-rose-500' : 'text-emerald-500')"

            >{{ idx.change >= 0 ? '+' : '' }}{{ idx.pctChange }}%</span>

          </div>

        </div>

        <div class="mt-2 flex items-center gap-3 text-[10px] text-gray-400">

          <span>量 {{ formatVol(idx.vol) }}</span>

          <span>额 {{ formatAmount(idx.amount) }}</span>

        </div>

      </div>

    </div>



    <!-- Main Content -->

    <div class="flex-1 flex gap-5 min-h-0">

      <!-- Left: Chart & Data -->

      <div class="flex-1 flex flex-col gap-5 min-h-0">

        <!-- K-Line Chart -->

        <div class="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm flex-1 flex flex-col min-h-0">

          <div class="flex items-center justify-between mb-4">

            <h3 class="text-sm font-bold text-gray-900 flex items-center gap-2">

              <CandlestickChart class="w-4 h-4 text-amber-500" />

              {{ currentStockName || '请搜索股票' }}

              <span class="text-xs font-mono text-gray-400 ml-1">{{ currentTsCode || '' }}</span>

              <span v-if="activePeriod !== 'daily'" class="text-[10px] bg-amber-50 text-amber-600 px-2 py-0.5 rounded-full font-medium ml-1">

                {{ periods.find(p => p.key === activePeriod)?.label }}

              </span>

              <button
                v-if="currentTsCode && !isIndex"
                @click="agentLoading ? (agentMode = true) : startAgentAnalysis()"
                :class="[
                  'ml-3 px-3 py-1 text-[11px] font-semibold rounded-lg transition-all active:scale-95 flex items-center gap-1.5',
                  agentLoading
                    ? 'bg-purple-100 border border-purple-300 text-purple-600'
                    : agentHasCache
                      ? 'bg-white border border-purple-300 text-purple-600 hover:bg-purple-50 shadow-sm'
                      : 'bg-gradient-to-r from-violet-500 to-purple-600 text-white hover:from-violet-600 hover:to-purple-700 shadow-md shadow-purple-500/25'
                ]"
              >
                <Sparkles class="w-3.5 h-3.5" :class="agentLoading ? 'animate-spin' : ''" />
                {{ agentLoading ? '分析中...' : agentHasCache ? '查看分析报告' : 'Agent分析此刻行情' }}
              </button>

            </h3>

            <div class="flex items-center gap-2">

              <button

                v-for="ct in ['candle', 'line']"

                :key="ct"

                @click="chartType = ct"

                :class="cn(

                  'px-2.5 py-1 text-[11px] font-medium rounded-lg transition-all',

                  chartType === ct ? 'bg-gray-900 text-white' : 'text-gray-400 hover:text-gray-600 hover:bg-gray-50'

                )"

              >

                {{ ct === 'candle' ? 'K线' : '折线' }}

              </button>

            </div>

          </div>

          <div v-if="!currentTsCode" class="flex-1 flex items-center justify-center text-gray-300">

            <div class="text-center">

              <Search class="w-12 h-12 mx-auto mb-3 opacity-50" />

              <p class="text-sm">搜索股票或点击指数查看行情</p>

            </div>

          </div>

          <div v-else-if="chartLoading" class="flex-1 flex items-center justify-center">

            <Loader2 class="w-8 h-8 animate-spin text-amber-500" />

          </div>

          <div v-else ref="klineChartRef" class="flex-1 w-full min-h-[200px]"></div>

        </div>



        <!-- Money Flow Chart -->

        <div v-if="currentTsCode && !isIndex" class="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm h-56 shrink-0 flex flex-col">

          <div class="flex items-center justify-between mb-3">

            <h3 class="text-sm font-bold text-gray-900 flex items-center gap-2">

              <Waves class="w-4 h-4 text-blue-500" />

              资金流向

            </h3>

          </div>

          <div v-if="moneyflowLoading" class="flex-1 flex items-center justify-center">

            <Loader2 class="w-6 h-6 animate-spin text-blue-400" />

          </div>

          <div v-else ref="moneyflowChartRef" class="flex-1 w-full"></div>

        </div>

      </div>



      <!-- Right Panel -->

      <div class="w-80 flex flex-col gap-5 shrink-0 min-h-0">

        <!-- Stock Info Card -->

        <div class="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm shrink-0">

          <h3 class="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2">

            <FileText class="w-4 h-4 text-amber-500" />

            个股指标

          </h3>

          <div v-if="!currentTsCode" class="text-center py-6 text-gray-300">

            <BarChart3 class="w-8 h-8 mx-auto mb-2 opacity-50" />

            <p class="text-xs">选择股票后显示指标</p>

          </div>

          <div v-else-if="basicLoading" class="flex items-center justify-center py-8">

            <Loader2 class="w-6 h-6 animate-spin text-amber-400" />

          </div>

          <div v-else class="space-y-3">

            <div v-for="item in dailyBasicDisplay" :key="item.label" class="flex items-center justify-between">

              <span class="text-xs text-gray-500">{{ item.label }}</span>

              <span class="text-xs font-semibold text-gray-900 font-mono">{{ item.value }}</span>

            </div>

          </div>

        </div>



        <!-- Financial Quick View -->

        <div class="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm flex-1 flex flex-col min-h-0">

          <h3 class="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2">

            <ScrollText class="w-4 h-4 text-emerald-500" />

            财务速览

          </h3>

          <div v-if="!currentTsCode || isIndex" class="flex-1 flex items-center justify-center text-gray-300">

            <div class="text-center">

              <ScrollText class="w-8 h-8 mx-auto mb-2 opacity-50" />

              <p class="text-xs">选择个股后显示财务数据</p>

            </div>

          </div>

          <div v-else-if="finLoading" class="flex-1 flex items-center justify-center">

            <Loader2 class="w-6 h-6 animate-spin text-emerald-400" />

          </div>

          <div v-else class="flex-1 overflow-y-auto pr-1 custom-scrollbar">

            <!-- Tabs -->

            <div class="flex gap-1 mb-4 bg-gray-50 rounded-lg p-1">

              <button

                v-for="tab in ['资产负债', '现金流']"

                :key="tab"

                @click="finTab = tab"

                :class="cn(

                  'flex-1 px-2 py-1.5 text-[11px] font-medium rounded-md transition-all',

                  finTab === tab ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'

                )"

              >{{ tab }}</button>

            </div>



            <!-- Balance Sheet -->

            <div v-if="finTab === '资产负债'" class="space-y-2.5">

              <div v-for="item in balanceDisplay" :key="item.label" class="flex items-center justify-between py-1 border-b border-gray-50 last:border-0">

                <span class="text-[11px] text-gray-500">{{ item.label }}</span>

                <span class="text-[11px] font-semibold text-gray-900 font-mono">{{ item.value }}</span>

              </div>

              <div v-if="balanceDisplay.length === 0" class="text-center py-4 text-xs text-gray-400">暂无数据</div>

            </div>



            <!-- Cash Flow -->

            <div v-if="finTab === '现金流'" class="space-y-2.5">

              <div v-for="item in cashflowDisplay" :key="item.label" class="flex items-center justify-between py-1 border-b border-gray-50 last:border-0">

                <span class="text-[11px] text-gray-500">{{ item.label }}</span>

                <span class="text-[11px] font-semibold text-gray-900 font-mono">{{ item.value }}</span>

              </div>

              <div v-if="cashflowDisplay.length === 0" class="text-center py-4 text-xs text-gray-400">暂无数据</div>

            </div>

          </div>

        </div>

      </div>

    </div>

    <!-- ============ Agent Analysis Overlay ============ -->
    <Transition name="agent-fade">
      <div v-if="agentMode" class="absolute inset-0 z-50 bg-gray-50/95 backdrop-blur-sm flex flex-col overflow-hidden rounded-2xl">

        <!-- Top Bar -->
        <div class="flex items-center justify-between px-6 py-3 bg-white border-b border-gray-100 shrink-0">
          <div class="flex items-center gap-3">
            <Sparkles class="w-5 h-5 text-purple-500" />
            <span class="text-sm font-bold text-gray-900">Agent 智能分析</span>
            <span class="text-xs text-gray-400 font-mono">{{ currentStockName }} {{ currentTsCode }}</span>
            <span v-if="agentLoading" class="flex items-center gap-1.5 text-xs text-purple-500">
              <Loader2 class="w-3.5 h-3.5 animate-spin" />
              {{ agentPhase || 'AI 正在分析...' }}
            </span>
          </div>
          <div class="flex items-center gap-2">
            <button
              v-if="agentStreamDone && !agentLoading"
              @click="reAnalyze"
              class="px-3 py-1.5 text-xs font-medium text-purple-600 hover:text-purple-800 bg-purple-50 hover:bg-purple-100 rounded-lg transition-all"
            >
              <RefreshCw class="w-3 h-3 inline mr-1" />重新分析
            </button>
            <button @click="closeAgentMode" class="px-3 py-1.5 text-xs font-medium text-gray-500 hover:text-gray-900 bg-gray-100 hover:bg-gray-200 rounded-lg transition-all">
              返回行情
            </button>
          </div>
        </div>

        <!-- Main Agent Content -->
        <div class="flex-1 flex gap-4 p-4 min-h-0 overflow-hidden">

          <!-- Left: Mini K-Line + Streaming Markdown -->
          <div class="flex-1 flex flex-col gap-4 min-h-0">

            <!-- Mini K-Line (shrunk) -->
            <div class="bg-white border border-gray-100 rounded-xl p-3 shadow-sm shrink-0 agent-kline-enter" style="height: 180px;">
              <div class="flex items-center gap-2 mb-1">
                <CandlestickChart class="w-3.5 h-3.5 text-amber-500" />
                <span class="text-xs font-bold text-gray-700">K线走势</span>
              </div>
              <div ref="agentKlineRef" class="w-full" style="height: 148px;"></div>
            </div>

            <!-- Streaming Markdown Content -->
            <div class="flex-1 overflow-y-auto pr-1 custom-scrollbar">

              <!-- Phase indicator -->
              <div v-if="agentPhase && agentLoading" class="flex items-center gap-2 mb-3 px-1">
                <Loader2 class="w-3.5 h-3.5 text-purple-500 animate-spin" />
                <span class="text-xs text-purple-600 font-medium">{{ agentPhase }}</span>
              </div>

              <!-- Markdown rendered content -->
              <div
                v-if="agentStreamContent"
                class="bg-white border border-gray-100 rounded-xl p-5 shadow-sm agent-markdown"
                v-html="marked(agentStreamContent)"
              ></div>

              <!-- Typing cursor -->
              <div v-if="agentLoading && agentStreamContent" class="flex items-center gap-1.5 mt-2 px-1">
                <span class="inline-block w-1.5 h-4 bg-purple-500 rounded-sm animate-pulse"></span>
              </div>

              <!-- Error -->
              <div v-if="agentError" class="bg-red-50 border border-red-200 rounded-xl p-4 mt-2">
                <p class="text-xs text-red-600">{{ agentError }}</p>
              </div>

              <!-- Loading skeleton (before any content) -->
              <div v-if="agentLoading && !agentStreamContent && !agentError" class="space-y-3">
                <div v-for="i in 3" :key="i" class="bg-white border border-gray-100 rounded-xl p-4 shadow-sm animate-pulse">
                  <div class="h-3 bg-gray-200 rounded w-1/3 mb-2"></div>
                  <div class="h-2 bg-gray-100 rounded w-full mb-1"></div>
                  <div class="h-2 bg-gray-100 rounded w-2/3"></div>
                </div>
              </div>
            </div>
          </div>

          <!-- Right Panel: Follow-up options -->
          <div class="w-72 flex flex-col gap-3 shrink-0 min-h-0">

            <!-- Quick Actions -->
            <div class="bg-white border border-gray-100 rounded-xl p-4 shadow-sm shrink-0">
              <h4 class="text-xs font-bold text-gray-700 flex items-center gap-1.5 mb-3">
                <Zap class="w-3.5 h-3.5 text-amber-500" />
                深入了解
              </h4>
              <div class="space-y-2">
                <button
                  v-for="qa in quickActions"
                  :key="qa.label"
                  @click="askFollowup(qa.question)"
                  :disabled="followupLoading || agentLoading"
                  class="w-full text-left px-3 py-2.5 text-[11px] font-medium text-gray-700 bg-gray-50 hover:bg-purple-50 hover:text-purple-700 border border-gray-100 hover:border-purple-200 rounded-lg transition-all disabled:opacity-50"
                >
                  {{ qa.label }}
                </button>
              </div>
            </div>

            <!-- Custom Question -->
            <div class="bg-white border border-gray-100 rounded-xl p-4 shadow-sm flex-1 flex flex-col min-h-0">
              <h4 class="text-xs font-bold text-gray-700 flex items-center gap-1.5 mb-3">
                <MessageCircle class="w-3.5 h-3.5 text-purple-500" />
                向AI追问
              </h4>
              <div class="flex-1 overflow-y-auto custom-scrollbar space-y-2 mb-3">
                <div
                  v-for="(msg, mi) in followupMessages"
                  :key="mi"
                  :class="cn(
                    'rounded-lg p-2.5 text-[11px] leading-relaxed',
                    msg.role === 'user' ? 'bg-purple-50 text-purple-800 ml-6' : 'bg-gray-50 text-gray-700 mr-2'
                  )"
                >
                  <div v-if="msg.role === 'assistant'" class="agent-markdown" v-html="marked(msg.content)"></div>
                  <p v-else class="whitespace-pre-wrap">{{ msg.content }}</p>
                </div>
                <div v-if="followupLoading" class="flex items-center gap-1.5 text-xs text-purple-400 p-2">
                  <Loader2 class="w-3 h-3 animate-spin" />
                  思考中...
                </div>
              </div>
              <div class="flex gap-2 shrink-0">
                <input
                  v-model="followupInput"
                  @keydown.enter="askFollowup(followupInput)"
                  placeholder="输入你的问题..."
                  :disabled="agentLoading"
                  class="flex-1 px-3 py-2 text-xs bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500/20 focus:border-purple-500 transition-all disabled:opacity-50"
                />
                <button
                  @click="askFollowup(followupInput)"
                  :disabled="!followupInput.trim() || followupLoading || agentLoading"
                  class="px-3 py-2 text-xs font-medium bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-all"
                >
                  发送
                </button>
              </div>
            </div>

          </div>
        </div>

      </div>
    </Transition>

  </div>

</template>



<script setup>

import { ref, computed, onMounted, nextTick, watch } from 'vue'

import * as echarts from 'echarts'

import { clsx } from 'clsx'

import { twMerge } from 'tailwind-merge'

import {

  CandlestickChart,

  Search,

  RefreshCw,

  TrendingUp,

  TrendingDown,

  Loader2,

  FileText,

  BarChart3,

  ScrollText,

  Waves,

  Star,

  Sparkles,

  Newspaper,

  Zap,

  GitBranch,

  MessageCircle

} from 'lucide-vue-next'

import { tushareApi, watchlistApi, agentApi } from '../../api/tushare.js'
import { marked } from 'marked'



defineEmits(['logout'])

const cn = (...inputs) => twMerge(clsx(inputs))



// ============ State ============

const searchText = ref('')

const showSuggestions = ref(false)

const suggestions = ref([])

const allStocks = ref([])

const stocksLoaded = ref(false)

const watchlistItems = ref([])



const currentTsCode = ref('')

const currentStockName = ref('')

const isIndex = ref(false)

const activePeriod = ref('daily')

const chartType = ref('candle')



const loading = ref(false)

const chartLoading = ref(false)

const basicLoading = ref(false)

const moneyflowLoading = ref(false)

const finLoading = ref(false)



const klineChartRef = ref(null)

const moneyflowChartRef = ref(null)

const agentKlineRef = ref(null)



// ============ Agent State ============

const agentMode = ref(false)

const agentLoading = ref(false)

const agentResult = ref(null)

const agentError = ref('')

const agentStreamContent = ref('')

const agentPhase = ref('')

const agentStreamDone = ref(false)

const agentHasCache = ref(false)

const followupInput = ref('')

const followupLoading = ref(false)

const followupMessages = ref([])

let streamAbortCtrl = null

let agentKlineChart = null

const quickActions = [
  { label: '📊 详细分析上下游产业链', question: '请详细分析这只股票的上下游产业链关系，以及对应的投资标的' },
  { label: '📈 近期主力资金动向', question: '请搜索并分析这只股票近期的主力资金动向和机构持仓变化' },
  { label: '🔍 同行业竞品对比', question: '请对比这只股票与同行业主要竞争对手的估值和业绩情况' },
  { label: '⚠️ 潜在风险深度分析', question: '请深入分析这只股票当前面临的所有潜在风险因素' },
  { label: '📰 近期重大事件梳理', question: '请搜索并梳理这只股票近一个月内的所有重大事件和公告' },
  { label: '💡 短中长期操作建议', question: '请分别给出这只股票短期（1周）、中期（1月）、长期（3月）的操作建议' },
]



let klineChart = null

let mfChart = null



const klineData = ref([])

const dailyBasicData = ref(null)

const moneyflowData = ref([])

const balanceData = ref([])

const cashflowData_raw = ref([])

const finTab = ref('资产负债')



let searchTimer = null



const periods = [

  { key: 'daily', label: '日K' },

  { key: 'weekly', label: '周K' },

  { key: 'monthly', label: '月K' }

]



// ============ Index Cards ============

const indexList = [

  { code: '000001.SH', name: '上证综指' },

  { code: '399001.SZ', name: '深证成指' },

  { code: '399006.SZ', name: '创业板指' },

  { code: '000300.SH', name: '沪深300' }

]



const indexCards = ref(indexList.map(i => ({

  ...i,

  close: null,

  change: null,

  pctChange: null,

  vol: null,

  amount: null

})))



const selectedIndex = ref('')



// ============ Helpers ============

const formatNum = (v) => {

  if (v === null || v === undefined) return '--'

  return Number(v).toLocaleString('zh-CN', { maximumFractionDigits: 2 })

}



const formatYi = (v) => {

  if (v === null || v === undefined) return '--'

  const n = Number(v)

  if (Math.abs(n) >= 1e8) return (n / 1e8).toFixed(2) + '亿'

  if (Math.abs(n) >= 1e4) return (n / 1e4).toFixed(2) + '万'

  return n.toFixed(2)

}



const formatWanYi = (v) => {

  if (v === null || v === undefined) return '--'

  const n = Number(v)

  if (Math.abs(n) >= 1e4) return (n / 1e4).toFixed(2) + '亿'

  return n.toFixed(2) + '万'

}



const formatVol = (v) => {

  if (!v) return '--'

  const n = Number(v)

  if (n >= 1e8) return (n / 1e8).toFixed(1) + '亿'

  if (n >= 1e4) return (n / 1e4).toFixed(1) + '万'

  return n.toFixed(0)

}



const formatAmount = (v) => {

  if (!v) return '--'

  const n = Number(v) * 1000

  if (n >= 1e8) return (n / 1e8).toFixed(1) + '亿'

  if (n >= 1e4) return (n / 1e4).toFixed(1) + '万'

  return n.toFixed(0)

}



// ============ Daily Basic Display ============

const dailyBasicDisplay = computed(() => {

  const d = dailyBasicData.value

  if (!d) return []

  return [

    { label: '收盘价', value: formatNum(d.close) },

    { label: '市盈率(PE)', value: formatNum(d.pe) },

    { label: '市盈率TTM', value: formatNum(d.pe_ttm) },

    { label: '市净率(PB)', value: formatNum(d.pb) },

    { label: '市销率(PS)', value: formatNum(d.ps) },

    { label: '换手率', value: d.turnover_rate ? d.turnover_rate.toFixed(2) + '%' : '--' },

    { label: '股息率', value: d.dv_ratio ? d.dv_ratio.toFixed(2) + '%' : '--' },

    { label: '总市值', value: formatWanYi(d.total_mv) },

    { label: '流通市值', value: formatWanYi(d.circ_mv) },

  ]

})



// ============ Financial Display ============

const balanceDisplay = computed(() => {

  if (!balanceData.value || balanceData.value.length === 0) return []

  const d = balanceData.value[0]

  return [

    { label: '报告期', value: d.end_date || d.ann_date || '--' },

    { label: '总资产', value: formatYi(d.total_assets) },

    { label: '总负债', value: formatYi(d.total_liab) },

    { label: '股东权益', value: formatYi(d.total_hldr_eqy_exc_min_int) },

    { label: '货币资金', value: formatYi(d.money_cap) },

    { label: '应收账款', value: formatYi(d.accounts_receiv) },

    { label: '存货', value: formatYi(d.inventories) },

    { label: '固定资产', value: formatYi(d.fix_assets) },

    { label: '短期借款', value: formatYi(d.st_borr) },

    { label: '长期借款', value: formatYi(d.lt_borr) },

  ]

})



const cashflowDisplay = computed(() => {

  if (!cashflowData_raw.value || cashflowData_raw.value.length === 0) return []

  const d = cashflowData_raw.value[0]

  return [

    { label: '报告期', value: d.end_date || d.ann_date || '--' },

    { label: '经营活动现金流入', value: formatYi(d.c_fr_sale_sg) },

    { label: '经营活动现金流出', value: formatYi(d.c_paid_goods_s) },

    { label: '经营净现金流', value: formatYi(d.n_cashflow_act) },

    { label: '投资净现金流', value: formatYi(d.n_cashflow_inv_act) },

    { label: '筹资净现金流', value: formatYi(d.n_cash_flows_fnc_act) },

    { label: '期末现金余额', value: formatYi(d.c_cash_equ_end_period) },

  ]

})



// ============ Search ============

const loadStocks = async () => {

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

    if (!q) {

      suggestions.value = []

      return

    }

    suggestions.value = allStocks.value

      .filter(s => s.ts_code.toLowerCase().includes(q) || s.symbol?.includes(q) || s.name?.toLowerCase().includes(q))

      .slice(0, 12)

    showSuggestions.value = true

  }, 200)

}



const selectStock = (s) => {

  searchText.value = `${s.name} ${s.ts_code}`

  showSuggestions.value = false

  currentTsCode.value = s.ts_code

  currentStockName.value = s.name

  isIndex.value = false

  selectedIndex.value = ''

  fetchStockData()
  checkAgentCache(s.ts_code)

}



const selectIndex = (idx) => {

  selectedIndex.value = idx.code

  currentTsCode.value = idx.code

  currentStockName.value = idx.name

  isIndex.value = true

  searchText.value = `${idx.name} ${idx.code}`

  showSuggestions.value = false

  agentHasCache.value = false

  fetchIndexKline()

}


// ============ Watchlist ============

const loadWatchlist = async () => {
  try {
    watchlistItems.value = await watchlistApi.list()
  } catch (e) {
    console.error('加载自选股失败:', e)
  }
}

const isInWatchlist = (ts_code) => {
  return watchlistItems.value.some(w => w.ts_code === ts_code)
}

const addToWatchlist = async (s) => {
  if (isInWatchlist(s.ts_code)) return
  try {
    const item = await watchlistApi.add(s.ts_code, s.name)
    watchlistItems.value.push(item)
  } catch (e) {
    console.error('添加自选失败:', e)
  }
}

const removeFromWatchlist = async (ts_code) => {
  try {
    await watchlistApi.remove(ts_code)
    watchlistItems.value = watchlistItems.value.filter(w => w.ts_code !== ts_code)
  } catch (e) {
    console.error('删除自选失败:', e)
  }
}

const jumpToWatchlistStock = (w) => {
  searchText.value = `${w.name} ${w.ts_code}`
  showSuggestions.value = false
  currentTsCode.value = w.ts_code
  currentStockName.value = w.name
  isIndex.value = false
  selectedIndex.value = ''
  fetchStockData()
  checkAgentCache(w.ts_code)
}


// ============ Fetch Data ============

const fetchIndexOverview = async () => {

  const promises = indexList.map(async (idx, i) => {

    try {

      const res = await tushareApi.getIndexDaily(idx.code)

      const data = res.data

      if (data && data.length > 0) {

        const latest = data[data.length - 1]

        indexCards.value[i] = {

          ...indexCards.value[i],

          close: latest.close?.toFixed(2),

          change: latest.change,

          pctChange: latest.pct_chg?.toFixed(2),

          vol: latest.vol,

          amount: latest.amount

        }

      }

    } catch (e) {

      console.error(`获取指数 ${idx.code} 失败:`, e)

    }

  })

  await Promise.all(promises)

}



const fetchStockData = async () => {

  if (!currentTsCode.value) return

  chartLoading.value = true
  basicLoading.value = true
  moneyflowLoading.value = true
  finLoading.value = true

  const code = currentTsCode.value
  const fetchFn = activePeriod.value === 'weekly'
    ? tushareApi.getWeekly
    : activePeriod.value === 'monthly'
      ? tushareApi.getMonthly
      : tushareApi.getDaily

  // 全部并行请求
  const [klineRes, basicRes, mfRes, bRes, cRes] = await Promise.allSettled([
    fetchFn(code),
    tushareApi.getDailyBasic(code),
    tushareApi.getMoneyflow(code),
    tushareApi.getBalancesheet(code),
    tushareApi.getCashflow(code),
  ])

  // K线
  if (klineRes.status === 'fulfilled') {
    klineData.value = klineRes.value.data || []
  } else { console.error('K线:', klineRes.reason) }
  chartLoading.value = false
  await nextTick()
  renderKlineChart()

  // 每日指标
  if (basicRes.status === 'fulfilled') {
    const d = basicRes.value.data
    dailyBasicData.value = (d && d.length > 0) ? d[0] : null
  } else { console.error('指标:', basicRes.reason) }
  basicLoading.value = false

  // 资金流向
  if (mfRes.status === 'fulfilled') {
    moneyflowData.value = mfRes.value.data || []
  } else { console.error('资金流:', mfRes.reason) }
  moneyflowLoading.value = false
  await nextTick()
  renderMoneyflowChart()

  // 财务
  if (bRes.status === 'fulfilled') {
    balanceData.value = bRes.value.data || []
  }
  if (cRes.status === 'fulfilled') {
    cashflowData_raw.value = cRes.value.data || []
  }
  finLoading.value = false

}



const fetchIndexKline = async () => {

  if (!currentTsCode.value) return

  chartLoading.value = true

  try {

    const res = await tushareApi.getIndexDaily(currentTsCode.value)

    klineData.value = res.data || []

    chartLoading.value = false

    await nextTick()

    renderKlineChart()

  } catch (e) {

    console.error(e)

    chartLoading.value = false

  }

  dailyBasicData.value = null

  basicLoading.value = false

  moneyflowData.value = []

  moneyflowLoading.value = false

  balanceData.value = []

  cashflowData_raw.value = []

  finLoading.value = false

}



const changePeriod = (p) => {

  activePeriod.value = p

  if (currentTsCode.value) {

    if (isIndex.value) {

      fetchIndexKline()

    } else {

      fetchStockData()

    }

  }

}



const refreshData = async () => {

  loading.value = true

  await fetchIndexOverview()

  if (currentTsCode.value) {

    if (isIndex.value) await fetchIndexKline()

    else await fetchStockData()

  }

  loading.value = false

}



// ============ Agent Analysis ============

const checkAgentCache = async (tsCode) => {
  if (!tsCode) { agentHasCache.value = false; return }
  try {
    const s = await agentApi.status(tsCode)
    agentHasCache.value = s.state === 'done'
  } catch { agentHasCache.value = false }
}

const stopStream = () => {
  if (streamAbortCtrl) {
    streamAbortCtrl.abort()
    streamAbortCtrl = null
  }
}

const startAgentAnalysis = async () => {
  if (!currentTsCode.value || !currentStockName.value) return

  // 先检查缓存
  try {
    const cached = await agentApi.status(currentTsCode.value)
    if (cached.state === 'done' && cached.result) {
      agentMode.value = true
      agentResult.value = cached.result
      agentStreamContent.value = cached.result.raw || ''
      agentStreamDone.value = true
      agentLoading.value = false
      agentPhase.value = ''
      followupMessages.value = []
      followupInput.value = ''
      await nextTick()
      renderAgentKline()
      return
    }
  } catch (e) { /* ignore, proceed with stream */ }

  // 进入 agent 模式 + SSE 流式分析
  agentMode.value = true
  agentLoading.value = true
  agentResult.value = null
  agentStreamContent.value = ''
  agentStreamDone.value = false
  agentError.value = ''
  agentPhase.value = ''
  followupMessages.value = []
  followupInput.value = ''

  await nextTick()
  renderAgentKline()

  stopStream()
  streamAbortCtrl = agentApi.analyzeStream(
    currentStockName.value,
    currentTsCode.value,
    {
      onPhase: (msg) => {
        agentPhase.value = msg
      },
      onDelta: (chunk) => {
        agentStreamContent.value += chunk
      },
      onDone: () => {
        agentLoading.value = false
        agentStreamDone.value = true
        agentHasCache.value = true
        agentPhase.value = ''
        streamAbortCtrl = null
      },
      onError: (err) => {
        agentError.value = err
        agentLoading.value = false
        agentStreamDone.value = true
        streamAbortCtrl = null
      }
    }
  )
}

const closeAgentMode = () => {
  stopStream()
  agentMode.value = false
  agentError.value = ''
  agentStreamContent.value = ''
  agentPhase.value = ''
  if (agentKlineChart) {
    agentKlineChart.dispose()
    agentKlineChart = null
  }
}

const reAnalyze = async () => {
  if (!currentTsCode.value) return
  stopStream()
  try {
    await agentApi.clearCache(currentTsCode.value)
  } catch (e) {
    console.error('清除缓存失败:', e)
  }
  agentHasCache.value = false
  agentResult.value = null
  agentStreamContent.value = ''
  agentStreamDone.value = false
  agentError.value = ''
  followupMessages.value = []
  startAgentAnalysis()
}

const renderAgentKline = () => {
  if (!agentKlineRef.value || klineData.value.length === 0) return
  if (agentKlineChart) agentKlineChart.dispose()
  agentKlineChart = echarts.init(agentKlineRef.value)

  const dates = klineData.value.map(d => d.trade_date)
  const ohlc = klineData.value.map(d => [d.open, d.close, d.low, d.high])

  agentKlineChart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#f3f4f6',
      borderWidth: 1,
      textStyle: { color: '#1f2937', fontSize: 10 },
      extraCssText: 'box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-radius: 8px;'
    },
    grid: { left: '8%', right: '3%', top: '5%', bottom: '8%' },
    xAxis: {
      type: 'category', data: dates,
      axisLine: { lineStyle: { color: '#e5e7eb' } },
      axisTick: { show: false },
      axisLabel: { color: '#9ca3af', fontSize: 9, interval: 'auto' }
    },
    yAxis: {
      scale: true,
      splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } },
      axisLine: { show: false }, axisTick: { show: false },
      axisLabel: { color: '#9ca3af', fontSize: 9 }
    },
    dataZoom: [{ type: 'inside', start: 70, end: 100 }],
    series: [{
      type: 'candlestick', data: ohlc,
      itemStyle: {
        color: '#ef4444', color0: '#10b981',
        borderColor: '#ef4444', borderColor0: '#10b981'
      }
    }]
  })

  window.addEventListener('resize', () => agentKlineChart?.resize())
}

const askFollowup = async (question) => {
  if (!question || !question.trim()) return
  const q = question.trim()
  followupInput.value = ''
  followupMessages.value.push({ role: 'user', content: q })
  followupLoading.value = true

  try {
    const contextStr = agentStreamContent.value
      ? agentStreamContent.value.slice(0, 2000)
      : ''

    const res = await agentApi.followup(
      currentStockName.value,
      currentTsCode.value,
      q,
      contextStr
    )
    if (res.status === 'ok') {
      followupMessages.value.push({ role: 'assistant', content: res.answer })
    } else {
      followupMessages.value.push({ role: 'assistant', content: `错误: ${res.message}` })
    }
  } catch (e) {
    followupMessages.value.push({ role: 'assistant', content: `请求失败: ${e.message}` })
  } finally {
    followupLoading.value = false
  }
}


// ============ Charts ============

const renderKlineChart = () => {

  if (!klineChartRef.value || klineData.value.length === 0) return

  if (klineChart) klineChart.dispose()

  klineChart = echarts.init(klineChartRef.value)



  const dates = klineData.value.map(d => d.trade_date)

  const volumes = klineData.value.map(d => d.vol)



  if (chartType.value === 'candle') {

    const ohlc = klineData.value.map(d => [d.open, d.close, d.low, d.high])

    const colors = klineData.value.map(d => d.close >= d.open ? '#ef4444' : '#10b981')



    klineChart.setOption({

      tooltip: {

        trigger: 'axis',

        axisPointer: { type: 'cross' },

        backgroundColor: 'rgba(255,255,255,0.95)',

        borderColor: '#f3f4f6',

        borderWidth: 1,

        textStyle: { color: '#1f2937', fontSize: 11 },

        extraCssText: 'box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-radius: 8px;'

      },

      axisPointer: { link: [{ xAxisIndex: 'all' }] },

      grid: [

        { left: '8%', right: '3%', top: '3%', height: '60%' },

        { left: '8%', right: '3%', top: '72%', height: '18%' }

      ],

      xAxis: [

        {

          type: 'category', data: dates, axisLine: { lineStyle: { color: '#e5e7eb' } },

          axisTick: { show: false }, axisLabel: { color: '#9ca3af', fontSize: 10 },

          gridIndex: 0, boundaryGap: true

        },

        {

          type: 'category', data: dates, axisLine: { lineStyle: { color: '#e5e7eb' } },

          axisTick: { show: false }, axisLabel: { show: false },

          gridIndex: 1, boundaryGap: true

        }

      ],

      yAxis: [

        {

          scale: true, splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } },

          axisLine: { show: false }, axisTick: { show: false },

          axisLabel: { color: '#9ca3af', fontSize: 10 }, gridIndex: 0

        },

        {

          scale: true, splitLine: { show: false },

          axisLine: { show: false }, axisTick: { show: false },

          axisLabel: { show: false }, gridIndex: 1

        }

      ],

      dataZoom: [

        { type: 'inside', xAxisIndex: [0, 1], start: 60, end: 100 },

        { type: 'slider', xAxisIndex: [0, 1], start: 60, end: 100, height: 16, bottom: '2%',

          borderColor: '#e5e7eb', fillerColor: 'rgba(245, 158, 11, 0.1)',

          handleStyle: { color: '#f59e0b' },

          textStyle: { color: '#9ca3af', fontSize: 10 }

        }

      ],

      series: [

        {

          type: 'candlestick', data: ohlc, xAxisIndex: 0, yAxisIndex: 0,

          itemStyle: {

            color: '#ef4444', color0: '#10b981',

            borderColor: '#ef4444', borderColor0: '#10b981'

          }

        },

        {

          type: 'bar', data: volumes.map((v, i) => ({

            value: v, itemStyle: { color: colors[i], opacity: 0.35 }

          })),

          xAxisIndex: 1, yAxisIndex: 1, barMaxWidth: 6

        }

      ]

    })

  } else {

    const closes = klineData.value.map(d => d.close)

    klineChart.setOption({

      tooltip: {

        trigger: 'axis',

        backgroundColor: 'rgba(255,255,255,0.95)',

        borderColor: '#f3f4f6',

        borderWidth: 1,

        textStyle: { color: '#1f2937', fontSize: 11 },

        extraCssText: 'box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-radius: 8px;'

      },

      grid: { left: '8%', right: '3%', top: '5%', bottom: '15%' },

      xAxis: {

        type: 'category', data: dates,

        axisLine: { lineStyle: { color: '#e5e7eb' } },

        axisTick: { show: false },

        axisLabel: { color: '#9ca3af', fontSize: 10 }

      },

      yAxis: {

        type: 'value', scale: true,

        splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } },

        axisLine: { show: false }, axisTick: { show: false },

        axisLabel: { color: '#9ca3af', fontSize: 10 }

      },

      dataZoom: [

        { type: 'inside', start: 60, end: 100 },

        { type: 'slider', start: 60, end: 100, height: 16, bottom: '2%',

          borderColor: '#e5e7eb', fillerColor: 'rgba(245, 158, 11, 0.1)',

          handleStyle: { color: '#f59e0b' },

          textStyle: { color: '#9ca3af', fontSize: 10 }

        }

      ],

      series: [{

        type: 'line', data: closes, smooth: true, symbol: 'none',

        lineStyle: { width: 2, color: '#f59e0b' },

        areaStyle: {

          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [

            { offset: 0, color: 'rgba(245, 158, 11, 0.2)' },

            { offset: 1, color: 'rgba(245, 158, 11, 0)' }

          ])

        }

      }]

    })

  }

  window.addEventListener('resize', () => klineChart?.resize())

}



const renderMoneyflowChart = () => {

  if (!moneyflowChartRef.value || moneyflowData.value.length === 0) return

  if (mfChart) mfChart.dispose()

  mfChart = echarts.init(moneyflowChartRef.value)



  const dates = moneyflowData.value.map(d => d.trade_date)

  const netMf = moneyflowData.value.map(d => {

    const inflow = (d.buy_sm_amount || 0) + (d.buy_md_amount || 0) + (d.buy_lg_amount || 0) + (d.buy_elg_amount || 0)

    const outflow = (d.sell_sm_amount || 0) + (d.sell_md_amount || 0) + (d.sell_lg_amount || 0) + (d.sell_elg_amount || 0)

    return +(inflow - outflow).toFixed(2)

  })



  mfChart.setOption({

    tooltip: {

      trigger: 'axis',

      backgroundColor: 'rgba(255,255,255,0.95)',

      borderColor: '#f3f4f6',

      borderWidth: 1,

      textStyle: { color: '#1f2937', fontSize: 11 },

      extraCssText: 'box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-radius: 8px;',

      formatter: (params) => {

        const v = params[0]

        return `${v.name}<br/>净流入: <b style="color:${v.value >= 0 ? '#ef4444' : '#10b981'}">${formatNum(v.value)}万</b>`

      }

    },

    grid: { left: '10%', right: '3%', top: '8%', bottom: '12%' },

    xAxis: {

      type: 'category', data: dates,

      axisLine: { lineStyle: { color: '#e5e7eb' } },

      axisTick: { show: false },

      axisLabel: { color: '#9ca3af', fontSize: 9 }

    },

    yAxis: {

      type: 'value',

      splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } },

      axisLine: { show: false }, axisTick: { show: false },

      axisLabel: { color: '#9ca3af', fontSize: 9 }

    },

    series: [{

      type: 'bar', data: netMf.map(v => ({

        value: v,

        itemStyle: { color: v >= 0 ? '#ef4444' : '#10b981', opacity: 0.75, borderRadius: v >= 0 ? [3, 3, 0, 0] : [0, 0, 3, 3] }

      })),

      barMaxWidth: 10

    }]

  })

  window.addEventListener('resize', () => mfChart?.resize())

}



// Re-render chart when type changes

watch(chartType, () => {

  if (klineData.value.length > 0) renderKlineChart()

})



// ============ Close suggestions on outside click ============

const handleClickOutside = (e) => {

  if (!e.target.closest('.relative')) showSuggestions.value = false

}



// ============ Lifecycle ============

onMounted(async () => {

  document.addEventListener('click', handleClickOutside)

  loading.value = true

  await Promise.all([loadStocks(), loadWatchlist()])

  await fetchIndexOverview()

  loading.value = false



  // 默认展示平安银行

  currentTsCode.value = '000001.SZ'

  currentStockName.value = '平安银行'

  searchText.value = '平安银行 000001.SZ'

  isIndex.value = false

  fetchStockData()
  checkAgentCache('000001.SZ')

})

</script>



<style scoped>

.custom-scrollbar::-webkit-scrollbar {

  width: 4px;

}

.custom-scrollbar::-webkit-scrollbar-track {

  background: transparent;

}

.custom-scrollbar::-webkit-scrollbar-thumb {

  background: #e5e7eb;

  border-radius: 4px;

}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {

  background: #d1d5db;

}

/* Agent overlay transitions */
.agent-fade-enter-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
.agent-fade-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.agent-fade-enter-from {
  opacity: 0;
  transform: scale(0.97);
}
.agent-fade-leave-to {
  opacity: 0;
  transform: scale(0.97);
}

/* K-line shrink animation */
.agent-kline-enter {
  animation: klineShrink 0.6s cubic-bezier(0.4, 0, 0.2, 1) both;
}

@keyframes klineShrink {
  0% {
    opacity: 0;
    transform: scale(1.1) translateY(20px);
  }
  100% {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

</style>

<style>
/* Agent Markdown rendering styles (unscoped for v-html) */
.agent-markdown h3 {
  font-size: 14px;
  font-weight: 700;
  color: #1f2937;
  margin: 16px 0 8px 0;
  padding-bottom: 6px;
  border-bottom: 1px solid #f3f4f6;
}
.agent-markdown h3:first-child {
  margin-top: 0;
}
.agent-markdown h4 {
  font-size: 12px;
  font-weight: 600;
  color: #374151;
  margin: 12px 0 6px 0;
}
.agent-markdown p {
  font-size: 12px;
  line-height: 1.7;
  color: #4b5563;
  margin: 4px 0;
}
.agent-markdown ul, .agent-markdown ol {
  font-size: 12px;
  line-height: 1.7;
  color: #4b5563;
  padding-left: 18px;
  margin: 4px 0 8px 0;
}
.agent-markdown li {
  margin: 2px 0;
}
.agent-markdown strong {
  color: #1f2937;
  font-weight: 600;
}
.agent-markdown table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
  margin: 8px 0;
}
.agent-markdown th {
  background: #f9fafb;
  padding: 6px 8px;
  text-align: left;
  font-weight: 600;
  color: #374151;
  border-bottom: 2px solid #e5e7eb;
}
.agent-markdown td {
  padding: 5px 8px;
  border-bottom: 1px solid #f3f4f6;
  color: #4b5563;
}
.agent-markdown tr:hover td {
  background: #f9fafb;
}
.agent-markdown blockquote {
  border-left: 3px solid #a78bfa;
  padding-left: 12px;
  margin: 8px 0;
  color: #6b7280;
  font-size: 12px;
}
.agent-markdown code {
  background: #f3f4f6;
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 11px;
  color: #7c3aed;
}
.agent-markdown hr {
  border: none;
  border-top: 1px solid #e5e7eb;
  margin: 12px 0;
}
</style>

