<template>
  <div class="h-full flex flex-col">
    <!-- Hero -->
    <div class="relative overflow-hidden bg-gradient-to-br from-blue-50 via-white to-cyan-50 border-b border-gray-100">
      <div class="absolute inset-0 opacity-20">
        <div class="absolute top-5 left-20 w-64 h-64 bg-blue-200 rounded-full blur-3xl animate-pulse"></div>
        <div class="absolute bottom-0 right-10 w-48 h-48 bg-cyan-200 rounded-full blur-3xl animate-pulse" style="animation-delay: 1s;"></div>
      </div>
      <div class="relative px-6 py-3">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-600 flex items-center justify-center shadow-md shadow-blue-500/20 shrink-0">
              <ListOrdered class="w-4.5 h-4.5 text-white" />
            </div>
            <div>
              <h1 class="text-base font-bold text-gray-900">推理步骤日志</h1>
              <p class="text-[11px] text-gray-500 mt-0.5">完整记录AI分析的每一步推理过程，支持时间轴回溯与步骤展开</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button @click="expandAll" class="px-3 py-2 text-xs font-medium text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-all">全部展开</button>
            <button @click="collapseAll" class="px-3 py-2 text-xs font-medium text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-all">全部折叠</button>
          </div>
        </div>
      </div>
    </div>

    <div class="flex-1 flex min-h-0">
      <!-- Timeline -->
      <div class="flex-1 overflow-y-auto px-8 py-6 custom-scrollbar">
        <div class="max-w-3xl mx-auto relative">
          <!-- Vertical timeline line -->
          <div class="absolute left-6 top-0 bottom-0 w-0.5 bg-gradient-to-b from-blue-300 via-blue-200 to-transparent"></div>

          <div v-for="(step, idx) in steps" :key="idx" class="relative pl-16 pb-8 group">
            <!-- Timeline dot -->
            <div :class="[
              'absolute left-4 w-5 h-5 rounded-full border-[3px] transition-all duration-500 z-10',
              step.status === 'done' ? 'bg-blue-500 border-blue-200 shadow-md shadow-blue-500/30' :
              step.status === 'running' ? 'bg-amber-400 border-amber-200 shadow-md shadow-amber-400/30 animate-pulse' :
              'bg-gray-200 border-gray-100'
            ]"></div>

            <!-- Step card -->
            <div :class="[
              'bg-white border rounded-2xl overflow-hidden transition-all duration-300',
              step.status === 'running' ? 'border-amber-200 shadow-md shadow-amber-100/50' :
              step.status === 'done' ? 'border-gray-100 shadow-sm hover:shadow-md' :
              'border-gray-100 opacity-60'
            ]">
              <!-- Header -->
              <div @click="toggleStep(idx)" class="px-5 py-4 cursor-pointer flex items-center gap-3 hover:bg-gray-50/50 transition-colors">
                <div :class="[
                  'w-9 h-9 rounded-xl flex items-center justify-center shrink-0 text-xs font-bold',
                  step.status === 'done' ? 'bg-blue-100 text-blue-600' :
                  step.status === 'running' ? 'bg-amber-100 text-amber-600' :
                  'bg-gray-100 text-gray-400'
                ]">{{ idx + 1 }}</div>
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <h3 class="text-sm font-bold text-gray-900">{{ step.title }}</h3>
                    <span v-if="step.status === 'running'" class="flex items-center gap-1 px-2 py-0.5 bg-amber-100 text-amber-700 text-[10px] font-medium rounded-full">
                      <Loader2 class="w-3 h-3 animate-spin" /> 进行中
                    </span>
                    <span v-if="step.status === 'done' && step.duration" class="text-[10px] text-gray-400 font-mono">{{ step.duration }}</span>
                  </div>
                  <p class="text-xs text-gray-500 mt-0.5">{{ step.summary }}</p>
                </div>
                <component :is="step.icon" class="w-4 h-4 text-gray-400 shrink-0" />
                <ChevronDown :class="['w-4 h-4 text-gray-400 transition-transform shrink-0', step.expanded ? 'rotate-180' : '']" />
              </div>

              <!-- Expanded Detail -->
              <Transition name="expand">
                <div v-if="step.expanded" class="px-5 pb-4 border-t border-gray-50">
                  <!-- Input/Output -->
                  <div class="grid grid-cols-2 gap-3 mt-4">
                    <div class="p-3 bg-blue-50/50 rounded-xl">
                      <p class="text-[10px] font-bold text-blue-600 uppercase tracking-wider mb-1.5">输入</p>
                      <p class="text-xs text-gray-600 leading-relaxed">{{ step.input }}</p>
                    </div>
                    <div class="p-3 bg-emerald-50/50 rounded-xl">
                      <p class="text-[10px] font-bold text-emerald-600 uppercase tracking-wider mb-1.5">输出</p>
                      <p class="text-xs text-gray-600 leading-relaxed">{{ step.output }}</p>
                    </div>
                  </div>
                  <!-- Metadata -->
                  <div v-if="step.metadata" class="mt-3 flex flex-wrap gap-2">
                    <span v-for="(val, key) in step.metadata" :key="key"
                      class="px-2.5 py-1 bg-gray-100 text-gray-600 text-[10px] font-medium rounded-lg">
                      {{ key }}: <span class="text-gray-900">{{ val }}</span>
                    </span>
                  </div>
                </div>
              </Transition>
            </div>
          </div>

          <!-- End marker -->
          <div class="relative pl-16">
            <div class="absolute left-4 w-5 h-5 rounded-full bg-emerald-500 border-[3px] border-emerald-200 shadow-md shadow-emerald-500/30 z-10 flex items-center justify-center">
              <Check class="w-3 h-3 text-white" />
            </div>
            <div class="bg-emerald-50 border border-emerald-200 rounded-2xl px-5 py-4 text-center">
              <p class="text-sm font-bold text-emerald-700">分析完成</p>
              <p class="text-xs text-emerald-500 mt-1">全部 {{ steps.length }} 个推理步骤已完成，耗时 {{ totalDuration }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Summary Panel -->
      <div class="w-72 border-l border-gray-100 bg-gray-50/50 p-5 flex flex-col gap-4 shrink-0 overflow-y-auto custom-scrollbar">
        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <h4 class="text-xs font-bold text-gray-700 flex items-center gap-1.5 mb-3">
            <BarChart3 class="w-3.5 h-3.5 text-blue-500" />
            推理概览
          </h4>
          <div class="space-y-3">
            <div>
              <div class="flex justify-between text-xs mb-1">
                <span class="text-gray-500">完成度</span>
                <span class="font-bold text-blue-600">{{ completionPct }}%</span>
              </div>
              <div class="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                <div class="h-full bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full transition-all duration-700" :style="{ width: completionPct + '%' }"></div>
              </div>
            </div>
            <div class="flex justify-between text-xs">
              <span class="text-gray-500">总步骤数</span>
              <span class="font-mono text-gray-900">{{ steps.length }}</span>
            </div>
            <div class="flex justify-between text-xs">
              <span class="text-gray-500">已完成</span>
              <span class="font-mono text-emerald-600">{{ doneCount }}</span>
            </div>
            <div class="flex justify-between text-xs">
              <span class="text-gray-500">总耗时</span>
              <span class="font-mono text-gray-900">{{ totalDuration }}</span>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <h4 class="text-xs font-bold text-gray-700 flex items-center gap-1.5 mb-3">
            <Gauge class="w-3.5 h-3.5 text-amber-500" />
            置信度评估
          </h4>
          <div ref="gaugeRef" class="w-full h-40"></div>
        </div>

        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <h4 class="text-xs font-bold text-gray-700 flex items-center gap-1.5 mb-3">
            <PieChartIcon class="w-3.5 h-3.5 text-purple-500" />
            数据源占比
          </h4>
          <div ref="pieRef" class="w-full h-40"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import {
  ListOrdered, ChevronDown, Loader2, Check,
  BarChart3, Gauge, PieChart as PieChartIcon,
  Search, Database, Brain, Shield, FileOutput, Lightbulb, Globe
} from 'lucide-vue-next'

const gaugeRef = ref(null)
const pieRef = ref(null)

const steps = ref([
  {
    title: '意图解析',
    summary: '理解用户查询意图，识别分析类型与标的',
    icon: Brain,
    status: 'done',
    duration: '0.3s',
    expanded: false,
    input: '用户输入：分析比亚迪最近的经营状况和投资价值',
    output: '分析类型：综合分析\n标的：比亚迪(002594.SZ)\n关键词：经营状况、投资价值',
    metadata: { '模型': 'Kimi k2.5', '置信度': '95%' }
  },
  {
    title: '数据检索',
    summary: '从Tushare获取股票行情与财务数据',
    icon: Database,
    status: 'done',
    duration: '1.2s',
    expanded: false,
    input: '股票代码：002594.SZ\n数据范围：最近12个月',
    output: '获取到 245 条日K数据\n获取到最新财报(2023Q4)\n获取到资金流向数据',
    metadata: { 'API': 'Tushare', '数据量': '245条', '时间跨度': '12个月' }
  },
  {
    title: '联网搜索',
    summary: '通过Kimi搜索最新市场新闻与分析师观点',
    icon: Globe,
    status: 'done',
    duration: '2.8s',
    expanded: false,
    input: '搜索关键词：比亚迪 最新新闻 行情分析 2024',
    output: '获取到 12 条相关新闻\n3条分析师研报摘要\n2条行业政策动态',
    metadata: { '来源': 'Kimi $web_search', '结果数': '17条', '时效': '最近7天' }
  },
  {
    title: '财务指标计算',
    summary: '计算核心财务指标并进行趋势分析',
    icon: Lightbulb,
    status: 'done',
    duration: '0.5s',
    expanded: false,
    input: '原始财报数据：资产负债表、利润表、现金流量表',
    output: 'ROE: 17.2% (同比+2.1pp)\n毛利率: 20.3% (同比+1.8pp)\n经营现金流: 同比+35%\n资产负债率: 65.8%',
    metadata: { '指标数': '12项', '计算方法': 'TTM' }
  },
  {
    title: '行业对标分析',
    summary: '与新能源汽车行业同行企业对比',
    icon: Search,
    status: 'done',
    duration: '0.8s',
    expanded: false,
    input: '对标企业：特斯拉、蔚来、理想、小鹏',
    output: 'ROE排名：第2位\n营收增速排名：第1位\nP/E估值：低于行业均值15%\n市占率：国内新能源第1',
    metadata: { '对标企业': '4家', '对标维度': '8维' }
  },
  {
    title: '风险因子评估',
    summary: '识别并量化潜在风险因子',
    icon: Shield,
    status: 'done',
    duration: '0.6s',
    expanded: false,
    input: '综合财务数据、新闻情报、行业环境',
    output: '竞争加剧风险：中(60分)\n原材料价格风险：低(35分)\n政策变动风险：低(25分)\n海外扩张风险：中(55分)',
    metadata: { '风险因子': '4项', '综合评分': '43.8/100' }
  },
  {
    title: '生成分析报告',
    summary: '综合所有分析结果生成结构化报告',
    icon: FileOutput,
    status: 'done',
    duration: '3.1s',
    expanded: false,
    input: '意图解析结果 + 数据检索结果 + 联网搜索结果 + 指标计算 + 对标分析 + 风险评估',
    output: '生成Markdown格式分析报告\n包含：概述、财务分析、行业对比、风险提示、投资建议\n综合评级：看好\n置信度：中高(78%)',
    metadata: { '报告字数': '约2500字', '评级': '看好', '置信度': '78%' }
  }
])

const doneCount = computed(() => steps.value.filter(s => s.status === 'done').length)
const completionPct = computed(() => Math.round(doneCount.value / steps.value.length * 100))
const totalDuration = computed(() => {
  const total = steps.value.reduce((s, step) => s + parseFloat(step.duration || '0'), 0)
  return total.toFixed(1) + 's'
})

const toggleStep = (idx) => { steps.value[idx].expanded = !steps.value[idx].expanded }
const expandAll = () => { steps.value.forEach(s => s.expanded = true) }
const collapseAll = () => { steps.value.forEach(s => s.expanded = false) }

const initCharts = () => {
  if (gaugeRef.value) {
    const gauge = echarts.init(gaugeRef.value)
    gauge.setOption({
      series: [{
        type: 'gauge',
        startAngle: 200, endAngle: -20,
        min: 0, max: 100,
        progress: { show: true, width: 12, roundCap: true, itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 0, colorStops: [{ offset: 0, color: '#f59e0b' }, { offset: 1, color: '#10b981' }] } } },
        pointer: { show: false },
        axisLine: { lineStyle: { width: 12, color: [[1, '#f3f4f6']] } },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        title: { show: false },
        detail: {
          valueAnimation: true, offsetCenter: [0, '10%'],
          fontSize: 24, fontWeight: 'bold', color: '#1f2937',
          formatter: '{value}%'
        },
        data: [{ value: 78, name: '置信度' }]
      }]
    })
  }

  if (pieRef.value) {
    const pie = echarts.init(pieRef.value)
    pie.setOption({
      tooltip: { trigger: 'item', textStyle: { fontSize: 11 } },
      series: [{
        type: 'pie', radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        label: { show: true, fontSize: 10 },
        data: [
          { value: 40, name: 'Tushare', itemStyle: { color: '#3b82f6' } },
          { value: 30, name: 'Kimi搜索', itemStyle: { color: '#8b5cf6' } },
          { value: 20, name: '计算指标', itemStyle: { color: '#f59e0b' } },
          { value: 10, name: '模型推理', itemStyle: { color: '#10b981' } }
        ]
      }]
    })
  }
}

onMounted(() => { nextTick(() => initCharts()) })
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }

.expand-enter-active, .expand-leave-active { transition: all 0.3s ease; overflow: hidden; }
.expand-enter-from, .expand-leave-to { max-height: 0; opacity: 0; }
.expand-enter-to, .expand-leave-from { max-height: 500px; opacity: 1; }
</style>
