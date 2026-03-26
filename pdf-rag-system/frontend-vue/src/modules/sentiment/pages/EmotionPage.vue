<template>
  <div class="h-full flex flex-col">
    <!-- Hero -->
    <div class="relative overflow-hidden bg-gradient-to-br from-orange-50 via-white to-amber-50 border-b border-gray-100">
      <div class="absolute inset-0 opacity-20">
        <div class="absolute top-3 left-16 w-48 h-48 bg-orange-200 rounded-full blur-3xl animate-pulse"></div>
        <div class="absolute bottom-0 right-10 w-40 h-40 bg-amber-200 rounded-full blur-3xl animate-pulse" style="animation-delay:1s"></div>
      </div>
      <div class="relative px-6 py-4">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-orange-500 to-amber-600 flex items-center justify-center shadow-md shadow-orange-500/20 shrink-0">
            <Gauge class="w-4.5 h-4.5 text-white" />
          </div>
          <div>
            <h1 class="text-base font-bold text-gray-900">情绪指数</h1>
            <p class="text-[11px] text-gray-500 mt-0.5">市场情绪量化指标与趋势变化，恐惧/贪婪指数实时监测</p>
          </div>
        </div>
      </div>
    </div>

    <div class="flex-1 flex min-h-0">
      <!-- Main Charts -->
      <div class="flex-1 overflow-y-auto p-5 space-y-4 custom-scrollbar">
        <!-- Top Cards -->
        <div class="grid grid-cols-4 gap-3">
          <div v-for="card in emotionCards" :key="card.label"
            :class="['bg-white border rounded-xl p-4 shadow-sm text-center transition-all hover:shadow-md', card.borderClass]">
            <div class="flex items-center justify-center gap-1.5 mb-2">
              <component :is="card.icon" :class="['w-4 h-4', card.iconClass]" />
              <span class="text-[10px] font-bold text-gray-500 uppercase tracking-wider">{{ card.label }}</span>
            </div>
            <p :class="['text-2xl font-bold font-mono', card.valueClass]">{{ card.value }}</p>
            <p class="text-[10px] text-gray-400 mt-1">{{ card.desc }}</p>
          </div>
        </div>

        <!-- Main Gauge -->
        <div class="bg-white border border-gray-100 rounded-xl shadow-sm p-5">
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-xs font-bold text-gray-800 flex items-center gap-2">
              <Gauge class="w-4 h-4 text-orange-500" /> 综合市场情绪仪表盘
            </h3>
            <span class="text-[10px] text-gray-400">更新于 {{ lastUpdate }}</span>
          </div>
          <div class="flex items-center gap-6">
            <div ref="mainGaugeRef" class="w-64 h-48 shrink-0"></div>
            <div class="flex-1">
              <div class="grid grid-cols-2 gap-3">
                <div v-for="factor in emotionFactors" :key="factor.name" class="p-3 bg-gray-50 rounded-lg">
                  <div class="flex items-center justify-between mb-1.5">
                    <span class="text-[11px] font-medium text-gray-700">{{ factor.name }}</span>
                    <span :class="['text-[10px] font-bold px-1.5 py-0.5 rounded',
                      factor.score > 60 ? 'bg-rose-50 text-rose-600' : factor.score > 40 ? 'bg-amber-50 text-amber-600' : 'bg-emerald-50 text-emerald-600']">
                      {{ factor.score }}
                    </span>
                  </div>
                  <div class="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden">
                    <div class="h-full rounded-full transition-all duration-1000"
                      :class="factor.score > 60 ? 'bg-rose-500' : factor.score > 40 ? 'bg-amber-500' : 'bg-emerald-500'"
                      :style="{ width: factor.score + '%' }"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Emotion Trend -->
        <div class="bg-white border border-gray-100 rounded-xl shadow-sm overflow-hidden">
          <div class="px-5 py-3 border-b border-gray-50 flex items-center justify-between">
            <h3 class="text-xs font-bold text-gray-800">情绪指数趋势</h3>
            <div class="flex items-center gap-1 bg-gray-50 rounded-lg p-0.5 border border-gray-100">
              <button v-for="p in ['7日','30日','90日']" :key="p" @click="trendPeriod = p"
                :class="['px-2 py-1 text-[10px] font-medium rounded transition-all',
                  trendPeriod === p ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500']">{{ p }}</button>
            </div>
          </div>
          <div ref="trendChartRef" class="w-full h-56"></div>
        </div>

        <!-- Sector Emotion Heatmap -->
        <div class="bg-white border border-gray-100 rounded-xl shadow-sm overflow-hidden">
          <div class="px-5 py-3 border-b border-gray-50">
            <h3 class="text-xs font-bold text-gray-800">板块情绪热力图</h3>
          </div>
          <div class="p-4 grid grid-cols-5 gap-2">
            <div v-for="sector in sectorEmotions" :key="sector.name"
              :class="['rounded-xl p-3 text-center transition-all hover:scale-105 cursor-default', sector.bg]">
              <p class="text-[11px] font-bold" :class="sector.textClass">{{ sector.name }}</p>
              <p class="text-lg font-bold font-mono mt-0.5" :class="sector.textClass">{{ sector.score }}</p>
              <p class="text-[9px] mt-0.5" :class="sector.subClass">{{ sector.label }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Alerts -->
      <div class="w-64 border-l border-gray-100 bg-gray-50/50 p-4 flex flex-col gap-3 shrink-0 overflow-y-auto custom-scrollbar">
        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <h4 class="text-[11px] font-bold text-gray-700 flex items-center gap-1.5 mb-3">
            <AlertTriangle class="w-3.5 h-3.5 text-amber-500" /> 情绪异常警报
          </h4>
          <div class="space-y-2">
            <div v-for="alert in alerts" :key="alert.text" class="p-2.5 rounded-lg border" :class="alert.bg">
              <p :class="['text-[10px] font-bold', alert.titleClass]">{{ alert.title }}</p>
              <p :class="['text-[9px] mt-0.5', alert.textClass]">{{ alert.text }}</p>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm flex-1">
          <h4 class="text-[11px] font-bold text-gray-700 flex items-center gap-1.5 mb-3">
            <History class="w-3.5 h-3.5 text-blue-500" /> 历史极值参考
          </h4>
          <div class="space-y-2">
            <div class="flex justify-between text-xs">
              <span class="text-gray-500">极度恐惧(&lt;20)</span>
              <span class="font-mono text-emerald-600">2022-10-31</span>
            </div>
            <div class="flex justify-between text-xs">
              <span class="text-gray-500">极度贪婪(&gt;80)</span>
              <span class="font-mono text-rose-600">2021-02-18</span>
            </div>
            <div class="flex justify-between text-xs">
              <span class="text-gray-500">当前位置</span>
              <span class="font-mono font-bold text-amber-600">55 中性偏贪</span>
            </div>
            <div class="mt-3 p-2.5 bg-amber-50 rounded-lg">
              <p class="text-[10px] text-amber-700 leading-relaxed">当前情绪处于中性偏贪区间，历史上该区间后续30日平均收益率+2.3%，但波动率偏高。</p>
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
import { Gauge, TrendingUp, TrendingDown, Activity, BarChart3, AlertTriangle, History } from 'lucide-vue-next'

const trendPeriod = ref('30日')
const mainGaugeRef = ref(null)
const trendChartRef = ref(null)
const lastUpdate = ref('2024-03-15 15:00')

const emotionCards = [
  { label: '恐贪指数', value: '55', desc: '中性偏贪婪', icon: Gauge, iconClass: 'text-amber-500', valueClass: 'text-amber-600', borderClass: 'border-amber-200' },
  { label: '多空比', value: '1.32', desc: '多头占优', icon: TrendingUp, iconClass: 'text-rose-500', valueClass: 'text-rose-600', borderClass: 'border-rose-200' },
  { label: '波动率VIX', value: '18.5', desc: '正常区间', icon: Activity, iconClass: 'text-blue-500', valueClass: 'text-blue-600', borderClass: 'border-blue-200' },
  { label: '融资余额变化', value: '+86亿', desc: '资金流入', icon: BarChart3, iconClass: 'text-emerald-500', valueClass: 'text-emerald-600', borderClass: 'border-emerald-200' }
]

const emotionFactors = [
  { name: '市场动量', score: 62 },
  { name: '成交量异动', score: 48 },
  { name: '涨跌家数比', score: 58 },
  { name: '融资融券情绪', score: 65 },
  { name: '期权隐含波动', score: 42 },
  { name: '社交媒体热度', score: 71 }
]

const sectorEmotions = [
  { name: '新能源', score: 72, label: '贪婪', bg: 'bg-rose-50', textClass: 'text-rose-700', subClass: 'text-rose-400' },
  { name: '半导体', score: 68, label: '偏贪', bg: 'bg-orange-50', textClass: 'text-orange-700', subClass: 'text-orange-400' },
  { name: '消费', score: 45, label: '中性', bg: 'bg-gray-50', textClass: 'text-gray-700', subClass: 'text-gray-400' },
  { name: '医药', score: 35, label: '偏恐', bg: 'bg-emerald-50', textClass: 'text-emerald-700', subClass: 'text-emerald-400' },
  { name: '银行', score: 52, label: '中性', bg: 'bg-blue-50', textClass: 'text-blue-700', subClass: 'text-blue-400' },
  { name: '军工', score: 61, label: '偏贪', bg: 'bg-orange-50', textClass: 'text-orange-700', subClass: 'text-orange-400' },
  { name: '地产', score: 28, label: '恐惧', bg: 'bg-emerald-100', textClass: 'text-emerald-800', subClass: 'text-emerald-500' },
  { name: '传媒', score: 75, label: '贪婪', bg: 'bg-rose-100', textClass: 'text-rose-800', subClass: 'text-rose-500' },
  { name: '白酒', score: 58, label: '中性', bg: 'bg-amber-50', textClass: 'text-amber-700', subClass: 'text-amber-400' },
  { name: '券商', score: 50, label: '中性', bg: 'bg-gray-100', textClass: 'text-gray-700', subClass: 'text-gray-400' }
]

const alerts = [
  { title: '传媒板块情绪过热', text: '情绪指数75，连续3日上升，建议关注回调风险', bg: 'bg-rose-50 border-rose-200', titleClass: 'text-rose-700', textClass: 'text-rose-500' },
  { title: '地产板块极度恐慌', text: '情绪指数28，处于历史低位，可能存在超跌反弹机会', bg: 'bg-emerald-50 border-emerald-200', titleClass: 'text-emerald-700', textClass: 'text-emerald-500' },
  { title: '融资余额快速攀升', text: '近5日融资净买入+320亿，杠杆情绪升温', bg: 'bg-amber-50 border-amber-200', titleClass: 'text-amber-700', textClass: 'text-amber-500' }
]

const initGauge = () => {
  if (!mainGaugeRef.value) return
  const chart = echarts.init(mainGaugeRef.value)
  chart.setOption({
    series: [{
      type: 'gauge', startAngle: 200, endAngle: -20, min: 0, max: 100,
      axisLine: { lineStyle: { width: 20, color: [[0.2, '#22c55e'], [0.4, '#86efac'], [0.6, '#fbbf24'], [0.8, '#f97316'], [1, '#ef4444']] } },
      pointer: { itemStyle: { color: '#1f2937' }, length: '60%', width: 5 },
      axisTick: { distance: -20, length: 6, lineStyle: { color: '#fff', width: 1.5 } },
      splitLine: { distance: -22, length: 10, lineStyle: { color: '#fff', width: 2.5 } },
      axisLabel: { color: '#6b7280', distance: 28, fontSize: 10,
        formatter: v => { if (v === 0) return '极恐'; if (v === 25) return '恐惧'; if (v === 50) return '中性'; if (v === 75) return '贪婪'; if (v === 100) return '极贪'; return '' } },
      detail: { valueAnimation: true, fontSize: 26, fontWeight: 'bold', offsetCenter: [0, '70%'], color: '#f59e0b',
        formatter: v => v + '\n中性偏贪' },
      title: { show: false },
      data: [{ value: 55 }]
    }]
  })
}

const initTrend = () => {
  if (!trendChartRef.value) return
  const chart = echarts.init(trendChartRef.value)
  const dates = [], values = []
  const d = new Date(2024, 0, 1)
  let v = 50
  for (let i = 0; i < 30; i++) {
    d.setDate(d.getDate() + 1)
    dates.push(d.toISOString().slice(5, 10))
    v += (Math.random() - 0.48) * 8
    v = Math.max(10, Math.min(90, v))
    values.push(+v.toFixed(1))
  }
  chart.setOption({
    tooltip: { trigger: 'axis', textStyle: { fontSize: 10 } },
    grid: { top: 25, bottom: 25, left: 45, right: 15 },
    xAxis: { type: 'category', data: dates, axisLabel: { fontSize: 9 } },
    yAxis: { min: 0, max: 100, axisLabel: { fontSize: 9 }, splitLine: { lineStyle: { color: '#f3f4f6' } } },
    visualMap: { show: false, pieces: [{ gt: 75, color: '#ef4444' }, { gt: 60, lte: 75, color: '#f97316' }, { gt: 40, lte: 60, color: '#f59e0b' }, { gt: 25, lte: 40, color: '#86efac' }, { lte: 25, color: '#22c55e' }] },
    series: [{ type: 'line', data: values, smooth: true, symbol: 'none', lineStyle: { width: 2.5 },
      markArea: { silent: true, data: [
        [{ yAxis: 75, itemStyle: { color: '#fef2f210' } }, { yAxis: 100 }],
        [{ yAxis: 0 }, { yAxis: 25, itemStyle: { color: '#f0fdf410' } }]
      ] },
      markLine: { silent: true, lineStyle: { type: 'dashed' }, data: [
        { yAxis: 75, label: { formatter: '贪婪', fontSize: 9, color: '#ef4444' }, lineStyle: { color: '#ef444440' } },
        { yAxis: 25, label: { formatter: '恐惧', fontSize: 9, color: '#22c55e' }, lineStyle: { color: '#22c55e40' } }
      ] }
    }]
  })
}

onMounted(() => { nextTick(() => { initGauge(); initTrend() }) })
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }
</style>
