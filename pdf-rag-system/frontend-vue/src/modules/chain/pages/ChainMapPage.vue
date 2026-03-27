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
            <input v-model="industryInput" @keydown.enter="loadChain" type="text" placeholder="输入行业名称..."
              class="px-3 py-2 text-xs border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 focus:border-cyan-400 w-36 transition-all" />
            <button @click="loadChain" :disabled="loading"
              class="px-4 py-2 bg-cyan-600 text-white text-xs font-medium rounded-lg hover:bg-cyan-700 transition-colors disabled:opacity-50 flex items-center gap-1.5">
              <Loader2 v-if="loading" class="w-3.5 h-3.5 animate-spin" />
              <Network v-else class="w-3.5 h-3.5" />
              {{ loading ? '分析中...' : '生成图谱' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="flex-1 flex min-h-0">
      <!-- Empty State -->
      <div v-if="!loading && !result" class="flex-1 flex items-center justify-center">
        <div class="text-center max-w-sm">
          <div class="p-3 rounded-xl bg-cyan-50 inline-block mb-3">
            <Network class="w-10 h-10 text-cyan-300" />
          </div>
          <h3 class="text-sm font-semibold text-gray-700 mb-1.5">输入行业名称生成产业链图谱</h3>
          <p class="text-xs text-gray-400 leading-relaxed mb-4">AI 将分析行业上下游关系，生成 Sankey 图与核心企业映射</p>
          <div class="flex flex-wrap gap-2 justify-center">
            <button v-for="ex in examples" :key="ex" @click="industryInput = ex; loadChain()"
              class="px-3 py-1.5 text-[11px] text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-cyan-50 hover:border-cyan-300 hover:text-cyan-700 transition-all">{{ ex }}</button>
          </div>
        </div>
      </div>

      <!-- Loading -->
      <div v-else-if="loading" class="flex-1 flex flex-col items-center justify-center">
        <div class="text-center">
          <Loader2 class="w-8 h-8 animate-spin text-cyan-500 mx-auto" />
          <p class="text-xs text-gray-500 mt-3">AI 正在分析产业链结构...</p>
        </div>
        <div v-if="streamText" class="mt-4 max-w-2xl w-full bg-gray-50 border border-gray-100 rounded-xl p-4 max-h-48 overflow-y-auto">
          <p class="text-[10px] font-bold text-gray-400 mb-1 uppercase tracking-wider">实时生成中</p>
          <pre class="text-[11px] text-gray-600 whitespace-pre-wrap font-mono leading-relaxed">{{ streamText.slice(-800) }}</pre>
        </div>
      </div>

      <!-- Results -->
      <template v-else>
        <!-- Demo Banner -->
        <div v-if="isDemo" class="absolute top-2 left-2 right-2 z-10 bg-cyan-50 border border-cyan-200 rounded-xl px-4 py-2.5 flex items-center justify-between">
          <p class="text-[11px] text-cyan-600"><span class="font-bold">示例数据</span> — 当前展示的是新能源汽车产业链示例，输入行业名称可获取实时分析</p>
          <button @click="clearDemo" class="text-[10px] text-cyan-500 hover:text-cyan-700 font-medium">清除示例</button>
        </div>
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
      </template>

      <!-- Error overlay -->
      <div v-if="error" class="absolute bottom-4 left-4 right-4 bg-red-50 border border-red-100 rounded-xl p-4 text-xs text-red-600 z-10">{{ error }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import { Network, Layers, TrendingUp, Loader2 } from 'lucide-vue-next'
import { useSSE } from '../../../composables/useSSE'
import { EXAMPLE_CHAIN_MAP } from '../../../composables/exampleData'

const sankeyRef = ref(null)
const pieRef = ref(null)
const industryInput = ref('')
const chainLevels = ref([])
const coreCompanies = ref([])
const isDemo = ref(false)
let sankeyChart = null
let pieChart = null
const { loading, error, streamText, result, fetchSSE } = useSSE()

const applyData = (data) => {
  chainLevels.value = (data.levels || []).map((l, i) => ({
    ...l, ...LEVEL_STYLES[i % LEVEL_STYLES.length]
  }))
  coreCompanies.value = data.coreCompanies || []
  initSankey(data)
  initPie(data)
  window.addEventListener('resize', handleResize)
}

onMounted(() => {
  result.value = EXAMPLE_CHAIN_MAP
  isDemo.value = true
  nextTick(() => applyData(EXAMPLE_CHAIN_MAP))
})

const LEVEL_STYLES = [
  { bg: 'bg-sky-50', textClass: 'text-sky-700', badgeBg: 'bg-sky-100', badgeText: 'text-sky-600' },
  { bg: 'bg-teal-50', textClass: 'text-teal-700', badgeBg: 'bg-teal-100', badgeText: 'text-teal-600' },
  { bg: 'bg-emerald-50', textClass: 'text-emerald-700', badgeBg: 'bg-emerald-100', badgeText: 'text-emerald-600' },
  { bg: 'bg-violet-50', textClass: 'text-violet-700', badgeBg: 'bg-violet-100', badgeText: 'text-violet-600' },
  { bg: 'bg-amber-50', textClass: 'text-amber-700', badgeBg: 'bg-amber-100', badgeText: 'text-amber-600' },
]

const examples = ['新能源汽车', '半导体', '光伏', '人工智能']

const initSankey = (data) => {
  nextTick(() => {
    if (!sankeyRef.value) return
    if (sankeyChart) sankeyChart.dispose()
    sankeyChart = echarts.init(sankeyRef.value)
    sankeyChart.setOption({
      tooltip: { trigger: 'item', textStyle: { fontSize: 11 } },
      series: [{
        type: 'sankey', layout: 'none', emphasis: { focus: 'adjacency' },
        nodeAlign: 'left', nodeGap: 12, nodeWidth: 20,
        lineStyle: { color: 'gradient', curveness: 0.5, opacity: 0.4 },
        label: { fontSize: 10, color: '#374151' },
        data: (data.sankeyNodes || []).map(n => ({ name: n.name, itemStyle: { color: n.color || '#10b981' } })),
        links: (data.sankeyLinks || []).map(l => ({ source: l.source, target: l.target, value: l.value }))
      }]
    })
  })
}

const initPie = (data) => {
  nextTick(() => {
    if (!pieRef.value) return
    if (pieChart) pieChart.dispose()
    pieChart = echarts.init(pieRef.value)
    const COLORS = ['#10b981', '#059669', '#0ea5e9', '#14b8a6', '#8b5cf6', '#f59e0b']
    pieChart.setOption({
      tooltip: { textStyle: { fontSize: 10 } },
      series: [{
        type: 'pie', radius: ['35%', '65%'], center: ['50%', '50%'],
        label: { fontSize: 9, color: '#6b7280' },
        itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
        data: (data.valueDistribution || []).map((d, i) => ({ value: d.value, name: d.name, itemStyle: { color: COLORS[i % COLORS.length] } }))
      }]
    })
  })
}

const handleResize = () => { sankeyChart?.resize(); pieChart?.resize() }

const clearDemo = () => { result.value = null; isDemo.value = false; chainLevels.value = []; coreCompanies.value = [] }

const loadChain = () => {
  if (!industryInput.value.trim()) return
  isDemo.value = false
  chainLevels.value = []
  coreCompanies.value = []
  fetchSSE('/api/chain/map', { industry: industryInput.value.trim() }, {
    onDone: (data) => applyData(data)
  })
}

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  sankeyChart?.dispose()
  pieChart?.dispose()
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }
</style>
