<template>
  <div class="h-full flex flex-col">
    <!-- Hero -->
    <div class="relative overflow-hidden bg-gradient-to-br from-violet-50 via-white to-purple-50 border-b border-gray-100">
      <div class="absolute inset-0 opacity-20">
        <div class="absolute top-3 left-16 w-48 h-48 bg-violet-200 rounded-full blur-3xl animate-pulse"></div>
        <div class="absolute bottom-0 right-10 w-40 h-40 bg-purple-200 rounded-full blur-3xl animate-pulse" style="animation-delay:1s"></div>
      </div>
      <div class="relative px-6 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-md shadow-violet-500/20 shrink-0">
              <Share2 class="w-4.5 h-4.5 text-white" />
            </div>
            <div>
              <h1 class="text-base font-bold text-gray-900">事件关联图谱</h1>
              <p class="text-[11px] text-gray-500 mt-0.5">事件间因果关系与传导路径可视化，发现隐藏的市场逻辑链</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <input v-model="searchEvent" @keydown.enter="searchGraph" type="text" placeholder="搜索事件关键词..."
              class="px-3 py-2 text-xs border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-400 w-44 transition-all" />
            <button @click="searchGraph"
              class="px-4 py-2 bg-violet-600 text-white text-xs font-medium rounded-lg hover:bg-violet-700 transition-colors flex items-center gap-1.5">
              <Search class="w-3.5 h-3.5" /> 搜索
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="flex-1 flex min-h-0">
      <!-- Graph Canvas -->
      <div class="flex-1 relative">
        <div ref="graphRef" class="w-full h-full"></div>
        <!-- Legend -->
        <div class="absolute top-4 left-4 bg-white/90 backdrop-blur border border-gray-100 rounded-xl p-3 shadow-sm">
          <p class="text-[10px] font-bold text-gray-600 mb-2">节点类型</p>
          <div class="space-y-1.5">
            <div v-for="leg in legends" :key="leg.label" class="flex items-center gap-2">
              <div class="w-3 h-3 rounded-full" :style="{ background: leg.color }"></div>
              <span class="text-[10px] text-gray-600">{{ leg.label }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Event Detail -->
      <div class="w-80 border-l border-gray-100 bg-gray-50/50 flex flex-col shrink-0 overflow-hidden">
        <div class="flex-1 overflow-y-auto p-4 custom-scrollbar">
          <div v-if="!selectedEvent" class="flex flex-col items-center justify-center h-full text-gray-400">
            <Share2 class="w-10 h-10 mb-2 opacity-30" />
            <p class="text-xs">点击图谱节点查看事件详情</p>
          </div>
          <div v-else class="space-y-3">
            <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
              <div class="flex items-center gap-2 mb-2">
                <div class="w-3 h-3 rounded-full" :style="{ background: selectedEvent.color }"></div>
                <span class="text-[10px] font-medium text-gray-500">{{ selectedEvent.category }}</span>
              </div>
              <h3 class="text-sm font-bold text-gray-900">{{ selectedEvent.name }}</h3>
              <p class="text-xs text-gray-500 mt-2 leading-relaxed">{{ selectedEvent.detail }}</p>
            </div>

            <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
              <h4 class="text-[11px] font-bold text-gray-700 mb-2">传导路径</h4>
              <div class="space-y-1.5">
                <div v-for="(path, i) in selectedEvent.paths" :key="i"
                  class="flex items-center gap-2 text-xs text-gray-600">
                  <ArrowRight class="w-3 h-3 text-violet-400 shrink-0" />
                  <span>{{ path }}</span>
                </div>
              </div>
            </div>

            <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
              <h4 class="text-[11px] font-bold text-gray-700 mb-2">受影响标的</h4>
              <div class="flex flex-wrap gap-1.5">
                <span v-for="stock in selectedEvent.stocks" :key="stock"
                  class="px-2 py-1 bg-violet-50 text-violet-700 text-[10px] font-medium rounded-lg border border-violet-100">
                  {{ stock }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Stats -->
        <div class="p-4 border-t border-gray-100 shrink-0">
          <div class="grid grid-cols-3 gap-2">
            <div class="bg-white rounded-lg border border-gray-100 p-2.5 text-center shadow-sm">
              <p class="text-lg font-bold text-violet-600 font-mono">{{ graphNodes.length }}</p>
              <p class="text-[9px] text-gray-500">事件节点</p>
            </div>
            <div class="bg-white rounded-lg border border-gray-100 p-2.5 text-center shadow-sm">
              <p class="text-lg font-bold text-purple-600 font-mono">{{ graphEdges.length }}</p>
              <p class="text-[9px] text-gray-500">关联关系</p>
            </div>
            <div class="bg-white rounded-lg border border-gray-100 p-2.5 text-center shadow-sm">
              <p class="text-lg font-bold text-pink-600 font-mono">5</p>
              <p class="text-[9px] text-gray-500">传导链路</p>
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
import { Share2, Search, ArrowRight } from 'lucide-vue-next'

const graphRef = ref(null)
const searchEvent = ref('')
const selectedEvent = ref(null)

const legends = [
  { label: '宏观政策', color: '#6366f1' },
  { label: '行业事件', color: '#f59e0b' },
  { label: '个股事件', color: '#10b981' },
  { label: '市场表现', color: '#ef4444' },
  { label: '外围因素', color: '#8b5cf6' }
]

const eventDetails = {
  '央行降准': { category: '宏观政策', color: '#6366f1', detail: '央行宣布降准50bp，释放约1.2万亿长期资金，直接利好流动性敏感板块。', paths: ['降准 → 银行间利率下行', '利率下行 → 房企融资成本降低', '融资改善 → 地产板块估值修复', '流动性宽松 → 成长股估值抬升'], stocks: ['招商银行', '万科A', '宁德时代', '贵州茅台'] },
  '美联储暂停加息': { category: '外围因素', color: '#8b5cf6', detail: '美联储FOMC维持利率不变并暗示年内降息3次，美元走弱有利于人民币资产。', paths: ['暂停加息 → 美元指数走弱', '美元走弱 → 人民币升值预期', '汇率预期改善 → 北向资金流入', '外资流入 → A股核心资产获青睐'], stocks: ['贵州茅台', '中国平安', '恒瑞医药'] },
  'AI算力需求爆发': { category: '行业事件', color: '#f59e0b', detail: '英伟达B200发布推动AI算力需求指数级增长，国产替代链受关注。', paths: ['B200发布 → AI训练算力需求↑4x', '算力需求 → GPU/HBM供不应求', '供应紧张 → 国产替代加速', '国产化 → 华为昇腾生态扩大'], stocks: ['中芯国际', '寒武纪', '海光信息', '浪潮信息'] },
  '碳酸锂暴跌': { category: '行业事件', color: '#f59e0b', detail: '碳酸锂期货跌破8万，锂矿企业利润大幅压缩。', paths: ['碳酸锂跌价 → 锂矿企业利润↓', '成本下降 → 电池厂毛利率↑', '电池降价 → 整车成本下降', '整车降价 → 新能源车渗透率↑'], stocks: ['天齐锂业', '赣锋锂业', '宁德时代', '比亚迪'] },
  '新国九条': { category: '宏观政策', color: '#6366f1', detail: '国务院发布新"国九条"强化退市制度改革，利好优质蓝筹。', paths: ['退市新规 → 壳资源价值↓', '监管趋严 → 绩差股承压', '优胜劣汰 → 资金向龙头集中', '龙头溢价 → 蓝筹估值提升'], stocks: ['贵州茅台', '招商银行', '海天味业'] }
}

const graphNodes = ref([
  { name: '央行降准', category: '宏观政策', symbolSize: 55, itemStyle: { color: '#6366f1' } },
  { name: '美联储暂停加息', category: '外围因素', symbolSize: 50, itemStyle: { color: '#8b5cf6' } },
  { name: 'AI算力需求爆发', category: '行业事件', symbolSize: 50, itemStyle: { color: '#f59e0b' } },
  { name: '碳酸锂暴跌', category: '行业事件', symbolSize: 45, itemStyle: { color: '#f59e0b' } },
  { name: '新国九条', category: '宏观政策', symbolSize: 48, itemStyle: { color: '#6366f1' } },
  { name: '银行利率下行', category: '市场表现', symbolSize: 35, itemStyle: { color: '#ef4444' } },
  { name: '地产融资改善', category: '市场表现', symbolSize: 35, itemStyle: { color: '#ef4444' } },
  { name: '北向资金流入', category: '市场表现', symbolSize: 38, itemStyle: { color: '#ef4444' } },
  { name: '国产替代加速', category: '行业事件', symbolSize: 40, itemStyle: { color: '#f59e0b' } },
  { name: '新能源车降价', category: '个股事件', symbolSize: 38, itemStyle: { color: '#10b981' } },
  { name: '成长股估值抬升', category: '市场表现', symbolSize: 36, itemStyle: { color: '#ef4444' } },
  { name: '壳资源价值下降', category: '市场表现', symbolSize: 32, itemStyle: { color: '#ef4444' } }
])

const graphEdges = ref([
  { source: '央行降准', target: '银行利率下行' },
  { source: '银行利率下行', target: '地产融资改善' },
  { source: '央行降准', target: '成长股估值抬升' },
  { source: '美联储暂停加息', target: '北向资金流入' },
  { source: '北向资金流入', target: '成长股估值抬升' },
  { source: 'AI算力需求爆发', target: '国产替代加速' },
  { source: '碳酸锂暴跌', target: '新能源车降价' },
  { source: '新国九条', target: '壳资源价值下降' },
  { source: '美联储暂停加息', target: '银行利率下行' },
  { source: '地产融资改善', target: '成长股估值抬升' }
])

const initGraph = () => {
  if (!graphRef.value) return
  const chart = echarts.init(graphRef.value)
  chart.setOption({
    tooltip: { trigger: 'item', textStyle: { fontSize: 11 },
      formatter: p => p.dataType === 'node' ? `<b>${p.data.name}</b><br/>${p.data.category}` : `${p.data.source} → ${p.data.target}` },
    animationDurationUpdate: 800,
    animationEasingUpdate: 'quinticInOut',
    series: [{
      type: 'graph', layout: 'force', roam: true, draggable: true,
      force: { repulsion: 280, gravity: 0.1, edgeLength: [80, 160], friction: 0.6 },
      label: { show: true, fontSize: 10, color: '#1f2937', formatter: '{b}' },
      edgeLabel: { show: false },
      lineStyle: { color: '#d1d5db', width: 1.5, curveness: 0.15, opacity: 0.8 },
      edgeSymbol: ['none', 'arrow'], edgeSymbolSize: 8,
      emphasis: { focus: 'adjacency', lineStyle: { width: 3, color: '#6366f1' }, label: { fontSize: 12, fontWeight: 'bold' } },
      data: graphNodes.value.map(n => ({ ...n, label: { show: true } })),
      links: graphEdges.value
    }]
  })
  chart.on('click', params => {
    if (params.dataType === 'node' && eventDetails[params.data.name]) {
      selectedEvent.value = { name: params.data.name, ...eventDetails[params.data.name] }
    }
  })
  window.addEventListener('resize', () => chart.resize())
}

const searchGraph = () => { /* TODO: Kimi search to build dynamic graph */ }

onMounted(() => { nextTick(() => initGraph()) })
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }
</style>
