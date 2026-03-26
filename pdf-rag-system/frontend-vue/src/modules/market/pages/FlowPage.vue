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
            <input v-model="stockCode" @keydown.enter="loadFlow" type="text" placeholder="股票代码..."
              class="px-3 py-2 text-xs border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 focus:border-cyan-400 w-32 transition-all" />
            <button @click="loadFlow"
              class="px-4 py-2 bg-cyan-600 text-white text-xs font-medium rounded-lg hover:bg-cyan-700 transition-colors flex items-center gap-1.5">
              <Search class="w-3.5 h-3.5" /> 查询
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="flex-1 flex min-h-0">
      <!-- Charts -->
      <div class="flex-1 flex flex-col min-h-0 p-5 gap-4">
        <!-- Main Flow Chart -->
        <div class="bg-white border border-gray-100 rounded-xl shadow-sm flex-[2] overflow-hidden">
          <div class="px-4 py-2.5 border-b border-gray-50 flex items-center justify-between">
            <h3 class="text-xs font-bold text-gray-800">主力资金流向</h3>
            <div class="flex items-center gap-1 bg-gray-50 rounded-lg p-0.5 border border-gray-100">
              <button v-for="p in ['5日','20日','60日']" :key="p" @click="flowPeriod = p"
                :class="['px-2 py-1 text-[10px] font-medium rounded transition-all',
                  flowPeriod === p ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500']"
              >{{ p }}</button>
            </div>
          </div>
          <div ref="flowChartRef" class="w-full" style="height: calc(100% - 38px);"></div>
        </div>

        <!-- Sector Flow -->
        <div class="bg-white border border-gray-100 rounded-xl shadow-sm flex-1 overflow-hidden">
          <div class="px-4 py-2.5 border-b border-gray-50">
            <h3 class="text-xs font-bold text-gray-800">行业板块资金流入排行</h3>
          </div>
          <div ref="sectorRef" class="w-full" style="height: calc(100% - 38px);"></div>
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

        <!-- Top Inflow -->
        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <h4 class="text-[11px] font-bold text-gray-700 mb-3 flex items-center gap-1.5">
            <TrendingUp class="w-3.5 h-3.5 text-rose-500" /> 主力净流入 TOP5
          </h4>
          <div class="space-y-1.5">
            <div v-for="(s, i) in topInflow" :key="i" class="flex items-center justify-between px-2 py-1.5 rounded-lg hover:bg-rose-50/50 transition-colors">
              <div class="flex items-center gap-2">
                <span class="w-4 h-4 rounded bg-rose-100 text-rose-600 text-[10px] font-bold flex items-center justify-center">{{ i + 1 }}</span>
                <span class="text-xs font-medium text-gray-700">{{ s.name }}</span>
              </div>
              <span class="text-[11px] font-mono text-rose-600">+{{ s.amount }}亿</span>
            </div>
          </div>
        </div>

        <!-- Top Outflow -->
        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <h4 class="text-[11px] font-bold text-gray-700 mb-3 flex items-center gap-1.5">
            <TrendingDown class="w-3.5 h-3.5 text-emerald-500" /> 主力净流出 TOP5
          </h4>
          <div class="space-y-1.5">
            <div v-for="(s, i) in topOutflow" :key="i" class="flex items-center justify-between px-2 py-1.5 rounded-lg hover:bg-emerald-50/50 transition-colors">
              <div class="flex items-center gap-2">
                <span class="w-4 h-4 rounded bg-emerald-100 text-emerald-600 text-[10px] font-bold flex items-center justify-center">{{ i + 1 }}</span>
                <span class="text-xs font-medium text-gray-700">{{ s.name }}</span>
              </div>
              <span class="text-[11px] font-mono text-emerald-600">-{{ s.amount }}亿</span>
            </div>
          </div>
        </div>

        <!-- North Flow -->
        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm flex-1">
          <h4 class="text-[11px] font-bold text-gray-700 mb-3 flex items-center gap-1.5">
            <Globe class="w-3.5 h-3.5 text-blue-500" /> 北向资金
          </h4>
          <div class="space-y-2">
            <div class="flex justify-between text-xs">
              <span class="text-gray-500">今日净买入</span>
              <span class="font-mono font-bold text-rose-600">+52.3亿</span>
            </div>
            <div class="flex justify-between text-xs">
              <span class="text-gray-500">沪股通</span>
              <span class="font-mono font-medium text-rose-500">+31.8亿</span>
            </div>
            <div class="flex justify-between text-xs">
              <span class="text-gray-500">深股通</span>
              <span class="font-mono font-medium text-rose-500">+20.5亿</span>
            </div>
            <div class="flex justify-between text-xs">
              <span class="text-gray-500">本周累计</span>
              <span class="font-mono font-medium text-rose-600">+186.7亿</span>
            </div>
            <div class="flex justify-between text-xs">
              <span class="text-gray-500">本月累计</span>
              <span class="font-mono font-medium text-emerald-600">-42.1亿</span>
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
import { ArrowLeftRight, Search, TrendingUp, TrendingDown, Globe } from 'lucide-vue-next'

const stockCode = ref('600519')
const flowPeriod = ref('5日')
const flowChartRef = ref(null)
const sectorRef = ref(null)

const summaryCards = ref([
  { label: '今日主力净流入', value: '+3.8亿', sub: '较昨日 +1.2亿', color: 'text-rose-600' },
  { label: '超大单净流入', value: '+2.1亿', sub: '占比 55.3%', color: 'text-rose-600' },
  { label: '大单净流入', value: '+1.7亿', sub: '占比 44.7%', color: 'text-rose-500' },
  { label: '散户净流出', value: '-3.8亿', sub: '小单+中单', color: 'text-emerald-600' }
])

const topInflow = ref([
  { name: '贵州茅台', amount: '8.5' },
  { name: '宁德时代', amount: '6.2' },
  { name: '招商银行', amount: '4.8' },
  { name: '比亚迪', amount: '3.5' },
  { name: '中国平安', amount: '2.9' }
])

const topOutflow = ref([
  { name: '东方财富', amount: '5.2' },
  { name: '中信证券', amount: '3.8' },
  { name: '隆基绿能', amount: '2.6' },
  { name: '三一重工', amount: '2.1' },
  { name: '海天味业', amount: '1.8' }
])

const initFlowChart = () => {
  if (!flowChartRef.value) return
  const chart = echarts.init(flowChartRef.value)
  const dates = []
  const d = new Date(2024, 0, 1)
  for (let i = 0; i < 20; i++) { d.setDate(d.getDate() + 1); dates.push(d.toISOString().slice(5, 10)) }

  const mainFlow = dates.map(() => +(Math.random() * 10 - 3).toFixed(1))
  const retailFlow = mainFlow.map(v => +(-v + (Math.random() - 0.5) * 2).toFixed(1))

  chart.setOption({
    tooltip: { trigger: 'axis', textStyle: { fontSize: 10 } },
    legend: { data: ['主力净流入', '散户净流入'], bottom: 5, textStyle: { fontSize: 10 } },
    grid: { top: 15, bottom: 40, left: 55, right: 15 },
    xAxis: { type: 'category', data: dates, axisLabel: { fontSize: 9 } },
    yAxis: { type: 'value', axisLabel: { fontSize: 9, formatter: '{value}亿' }, splitLine: { lineStyle: { color: '#f3f4f6' } } },
    series: [
      {
        name: '主力净流入', type: 'bar', data: mainFlow.map(v => ({
          value: v, itemStyle: { color: v >= 0 ? '#ef4444' : '#22c55e', borderRadius: v >= 0 ? [3, 3, 0, 0] : [0, 0, 3, 3] }
        })), barWidth: '35%'
      },
      {
        name: '散户净流入', type: 'line', data: retailFlow,
        lineStyle: { width: 1.5, color: '#f59e0b', type: 'dashed' }, symbol: 'none',
        areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#fef3c710' }, { offset: 1, color: '#fef3c700' }] } }
      }
    ]
  })
  window.addEventListener('resize', () => chart.resize())
}

const initSectorChart = () => {
  if (!sectorRef.value) return
  const chart = echarts.init(sectorRef.value)
  const sectors = ['新能源', '半导体', '医药生物', '白酒', '银行', '军工', '房地产', '传媒']
  const values = sectors.map(() => +(Math.random() * 20 - 5).toFixed(1))

  chart.setOption({
    tooltip: { trigger: 'axis', textStyle: { fontSize: 10 } },
    grid: { top: 10, bottom: 25, left: 65, right: 15 },
    xAxis: { type: 'value', axisLabel: { fontSize: 9, formatter: '{value}亿' }, splitLine: { lineStyle: { color: '#f3f4f6' } } },
    yAxis: { type: 'category', data: sectors, axisLabel: { fontSize: 10 } },
    series: [{
      type: 'bar', data: values.map(v => ({
        value: v, itemStyle: { color: v >= 0 ? '#ef4444' : '#22c55e', borderRadius: v >= 0 ? [0, 4, 4, 0] : [4, 0, 0, 4] }
      })), barWidth: '50%'
    }]
  })
  window.addEventListener('resize', () => chart.resize())
}

const loadFlow = () => { initFlowChart(); initSectorChart() }

onMounted(() => { nextTick(() => { initFlowChart(); initSectorChart() }) })
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }
</style>
