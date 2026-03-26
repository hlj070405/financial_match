<template>
  <div class="h-full flex flex-col">
    <!-- Hero -->
    <div class="relative overflow-hidden bg-gradient-to-br from-cyan-50 via-white to-teal-50 border-b border-gray-100">
      <div class="absolute inset-0 opacity-20">
        <div class="absolute top-3 left-16 w-48 h-48 bg-cyan-200 rounded-full blur-3xl animate-pulse"></div>
        <div class="absolute bottom-0 right-10 w-40 h-40 bg-teal-200 rounded-full blur-3xl animate-pulse" style="animation-delay:1s"></div>
      </div>
      <div class="relative px-6 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-500 to-teal-600 flex items-center justify-center shadow-md shadow-cyan-500/20 shrink-0">
              <Network class="w-4.5 h-4.5 text-white" />
            </div>
            <div>
              <h1 class="text-base font-bold text-gray-900">上下游关系图</h1>
              <p class="text-[11px] text-gray-500 mt-0.5">产业链上下游企业映射与价值传导可视化（Sankey图）</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <select v-model="selectedIndustry" @change="loadChain"
              class="px-3 py-2 text-xs border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-cyan-500/20">
              <option v-for="ind in industries" :key="ind" :value="ind">{{ ind }}</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <div class="flex-1 flex min-h-0">
      <!-- Sankey Chart -->
      <div class="flex-1 relative">
        <div ref="sankeyRef" class="w-full h-full"></div>
      </div>

      <!-- Right: Chain Detail -->
      <div class="w-72 border-l border-gray-100 bg-gray-50/50 p-4 flex flex-col gap-3 shrink-0 overflow-y-auto custom-scrollbar">
        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <h4 class="text-[11px] font-bold text-gray-700 mb-3 flex items-center gap-1.5">
            <Layers class="w-3.5 h-3.5 text-cyan-500" /> 产业链层级
          </h4>
          <div class="space-y-2">
            <div v-for="level in chainLevels" :key="level.name" class="p-2.5 rounded-lg" :class="level.bg">
              <div class="flex items-center justify-between mb-1">
                <span :class="['text-[11px] font-bold', level.textClass]">{{ level.name }}</span>
                <span :class="['text-[9px] px-1.5 py-0.5 rounded', level.badgeBg, level.badgeText]">{{ level.count }}家</span>
              </div>
              <p class="text-[10px] text-gray-500">{{ level.desc }}</p>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <h4 class="text-[11px] font-bold text-gray-700 mb-3">核心企业</h4>
          <div class="space-y-1.5">
            <div v-for="co in coreCompanies" :key="co.name"
              class="flex items-center justify-between px-2 py-1.5 rounded-lg hover:bg-cyan-50 transition-colors cursor-pointer">
              <div>
                <span class="text-xs font-medium text-gray-700">{{ co.name }}</span>
                <span class="text-[9px] text-gray-400 ml-1">{{ co.code }}</span>
              </div>
              <span :class="['text-[10px] font-bold px-1.5 py-0.5 rounded',
                co.position === '龙头' ? 'bg-amber-50 text-amber-600' : 'bg-gray-50 text-gray-500']">{{ co.position }}</span>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm flex-1">
          <h4 class="text-[11px] font-bold text-gray-700 mb-3 flex items-center gap-1.5">
            <TrendingUp class="w-3.5 h-3.5 text-emerald-500" /> 价值分布
          </h4>
          <div ref="pieRef" class="w-full h-40"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { Network, Layers, TrendingUp } from 'lucide-vue-next'

const sankeyRef = ref(null)
const pieRef = ref(null)
const selectedIndustry = ref('新能源汽车')
const industries = ['新能源汽车', '半导体', '光伏', '锂电池', '人工智能']

const chainLevels = [
  { name: '上游原材料', count: 12, desc: '锂矿、钴镍、稀土、碳酸锂等', bg: 'bg-sky-50', textClass: 'text-sky-700', badgeBg: 'bg-sky-100', badgeText: 'text-sky-600' },
  { name: '中游制造', count: 18, desc: '电池、电机、电控、车身制造', bg: 'bg-teal-50', textClass: 'text-teal-700', badgeBg: 'bg-teal-100', badgeText: 'text-teal-600' },
  { name: '下游整车', count: 8, desc: '整车制造、品牌运营、销售', bg: 'bg-emerald-50', textClass: 'text-emerald-700', badgeBg: 'bg-emerald-100', badgeText: 'text-emerald-600' },
  { name: '后市场服务', count: 6, desc: '充电桩、维修、电池回收', bg: 'bg-violet-50', textClass: 'text-violet-700', badgeBg: 'bg-violet-100', badgeText: 'text-violet-600' }
]

const coreCompanies = [
  { name: '宁德时代', code: '300750', position: '龙头' },
  { name: '比亚迪', code: '002594', position: '龙头' },
  { name: '天齐锂业', code: '002466', position: '上游' },
  { name: '汇川技术', code: '300124', position: '中游' },
  { name: '特锐德', code: '300001', position: '后市场' }
]

const initSankey = () => {
  if (!sankeyRef.value) return
  const chart = echarts.init(sankeyRef.value)
  chart.setOption({
    tooltip: { trigger: 'item', textStyle: { fontSize: 11 } },
    series: [{
      type: 'sankey', layout: 'none', emphasis: { focus: 'adjacency' },
      nodeAlign: 'left', nodeGap: 12, nodeWidth: 20,
      lineStyle: { color: 'gradient', curveness: 0.5, opacity: 0.4 },
      label: { fontSize: 10, color: '#374151' },
      data: [
        { name: '锂矿资源', itemStyle: { color: '#0ea5e9' } },
        { name: '钴镍原料', itemStyle: { color: '#06b6d4' } },
        { name: '正极材料', itemStyle: { color: '#14b8a6' } },
        { name: '负极材料', itemStyle: { color: '#14b8a6' } },
        { name: '电解液', itemStyle: { color: '#14b8a6' } },
        { name: '隔膜', itemStyle: { color: '#14b8a6' } },
        { name: '动力电池', itemStyle: { color: '#10b981' } },
        { name: '驱动电机', itemStyle: { color: '#10b981' } },
        { name: '电控系统', itemStyle: { color: '#10b981' } },
        { name: '整车制造', itemStyle: { color: '#059669' } },
        { name: '充电基础设施', itemStyle: { color: '#8b5cf6' } },
        { name: '电池回收', itemStyle: { color: '#8b5cf6' } },
        { name: '稀土永磁', itemStyle: { color: '#0ea5e9' } },
        { name: '铜箔铝箔', itemStyle: { color: '#06b6d4' } }
      ],
      links: [
        { source: '锂矿资源', target: '正极材料', value: 35 },
        { source: '锂矿资源', target: '电解液', value: 15 },
        { source: '钴镍原料', target: '正极材料', value: 20 },
        { source: '稀土永磁', target: '驱动电机', value: 18 },
        { source: '铜箔铝箔', target: '负极材料', value: 12 },
        { source: '正极材料', target: '动力电池', value: 45 },
        { source: '负极材料', target: '动力电池', value: 15 },
        { source: '电解液', target: '动力电池', value: 12 },
        { source: '隔膜', target: '动力电池', value: 10 },
        { source: '动力电池', target: '整车制造', value: 65 },
        { source: '驱动电机', target: '整车制造', value: 18 },
        { source: '电控系统', target: '整车制造', value: 12 },
        { source: '整车制造', target: '充电基础设施', value: 30 },
        { source: '动力电池', target: '电池回收', value: 15 }
      ]
    }]
  })
  window.addEventListener('resize', () => chart.resize())
}

const initPie = () => {
  if (!pieRef.value) return
  const chart = echarts.init(pieRef.value)
  chart.setOption({
    tooltip: { textStyle: { fontSize: 10 } },
    series: [{
      type: 'pie', radius: ['35%', '65%'], center: ['50%', '50%'],
      label: { fontSize: 9, color: '#6b7280' },
      itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
      data: [
        { value: 35, name: '电池', itemStyle: { color: '#10b981' } },
        { value: 25, name: '整车', itemStyle: { color: '#059669' } },
        { value: 18, name: '原材料', itemStyle: { color: '#0ea5e9' } },
        { value: 12, name: '电机电控', itemStyle: { color: '#14b8a6' } },
        { value: 10, name: '后市场', itemStyle: { color: '#8b5cf6' } }
      ]
    }]
  })
}

const loadChain = () => { initSankey() }

onMounted(() => { nextTick(() => { initSankey(); initPie() }) })
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }
</style>
