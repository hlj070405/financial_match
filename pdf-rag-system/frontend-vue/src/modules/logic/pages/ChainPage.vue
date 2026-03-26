<template>
  <div class="h-full flex flex-col">
    <!-- Hero -->
    <div class="relative overflow-hidden bg-gradient-to-br from-violet-50 via-white to-indigo-50 border-b border-gray-100">
      <div class="absolute inset-0 opacity-20">
        <div class="absolute top-5 left-20 w-64 h-64 bg-violet-200 rounded-full blur-3xl animate-pulse"></div>
        <div class="absolute bottom-0 right-10 w-48 h-48 bg-indigo-200 rounded-full blur-3xl animate-pulse" style="animation-delay: 1s;"></div>
      </div>
      <div class="relative px-6 py-3">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center shadow-md shadow-violet-500/20 shrink-0">
              <GitMerge class="w-4.5 h-4.5 text-white" />
            </div>
            <div>
              <h1 class="text-base font-bold text-gray-900">决策链路展示</h1>
              <p class="text-[11px] text-gray-500 mt-0.5">可视化 Agent 推理过程与决策依据，全景展示 AI 的思考链路</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <div class="flex items-center bg-gray-50 rounded-xl p-1 border border-gray-100">
              <button @click="zoomIn" class="p-2 hover:bg-white hover:shadow-sm rounded-lg text-gray-500 transition-all"><ZoomIn class="w-4 h-4" /></button>
              <button @click="zoomOut" class="p-2 hover:bg-white hover:shadow-sm rounded-lg text-gray-500 transition-all"><ZoomOut class="w-4 h-4" /></button>
              <button @click="fitView" class="p-2 hover:bg-white hover:shadow-sm rounded-lg text-gray-500 transition-all"><Maximize class="w-4 h-4" /></button>
            </div>
            <button @click="replayAnimation" class="flex items-center gap-2 px-4 py-2 bg-violet-600 text-white text-sm font-medium rounded-xl hover:bg-violet-700 transition-all shadow-lg shadow-violet-500/20">
              <Play class="w-4 h-4" /> 回放推理
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="flex-1 flex min-h-0">
      <!-- Flow Canvas -->
      <div class="flex-1 relative bg-slate-50/50 overflow-hidden">
        <VueFlow
          v-model="elements"
          :default-zoom="0.9"
          :min-zoom="0.2"
          :max-zoom="4"
          class="h-full w-full"
          @pane-ready="onPaneReady"
        >
          <Background pattern-color="#e2e8f0" :gap="20" />
          <Controls :show-interactive="false" class="!bg-white !border !border-gray-100 !shadow-sm !rounded-lg !m-4" />
          <MiniMap class="!bg-white !border !border-gray-100 !shadow-sm !rounded-lg !bottom-4 !right-4" />
        </VueFlow>

        <!-- Replay overlay -->
        <Transition name="fade">
          <div v-if="isReplaying" class="absolute top-4 left-1/2 -translate-x-1/2 z-20 px-4 py-2 bg-violet-600 text-white text-xs font-medium rounded-full shadow-lg flex items-center gap-2">
            <Loader2 class="w-3.5 h-3.5 animate-spin" />
            推理回放中... 步骤 {{ replayStep }}/{{ totalSteps }}
          </div>
        </Transition>
      </div>

      <!-- Right Panel -->
      <div class="w-80 border-l border-gray-100 bg-white flex flex-col shrink-0 overflow-hidden">
        <!-- Stats -->
        <div class="p-5 border-b border-gray-100 space-y-4">
          <h3 class="text-sm font-bold text-gray-900 flex items-center gap-2">
            <Activity class="w-4 h-4 text-violet-500" />
            推理统计
          </h3>
          <div class="grid grid-cols-2 gap-3">
            <div class="p-3 bg-violet-50 rounded-xl text-center">
              <p class="text-2xl font-bold text-violet-600">{{ nodeCount }}</p>
              <p class="text-[10px] text-violet-500 font-medium">推理节点</p>
            </div>
            <div class="p-3 bg-blue-50 rounded-xl text-center">
              <p class="text-2xl font-bold text-blue-600">{{ dataSourceCount }}</p>
              <p class="text-[10px] text-blue-500 font-medium">数据源</p>
            </div>
            <div class="p-3 bg-emerald-50 rounded-xl text-center">
              <p class="text-2xl font-bold text-emerald-600">{{ reasoningDepth }}</p>
              <p class="text-[10px] text-emerald-500 font-medium">推理深度</p>
            </div>
            <div class="p-3 bg-amber-50 rounded-xl text-center">
              <p class="text-2xl font-bold text-amber-600">{{ edgeCount }}</p>
              <p class="text-[10px] text-amber-500 font-medium">逻辑连接</p>
            </div>
          </div>
        </div>

        <!-- Legend -->
        <div class="p-5 border-b border-gray-100">
          <h3 class="text-sm font-bold text-gray-900 flex items-center gap-2 mb-3">
            <Layers class="w-4 h-4 text-blue-500" />
            节点类型
          </h3>
          <div class="grid grid-cols-2 gap-2">
            <div v-for="legend in legends" :key="legend.label" class="flex items-center gap-2 text-xs text-gray-600">
              <div class="w-3 h-3 rounded-full" :class="legend.color"></div>
              <span>{{ legend.label }}</span>
            </div>
          </div>
        </div>

        <!-- Node Detail -->
        <div class="flex-1 overflow-y-auto p-5 custom-scrollbar">
          <h3 class="text-sm font-bold text-gray-900 flex items-center gap-2 mb-3">
            <FileText class="w-4 h-4 text-gray-500" />
            节点详情
          </h3>
          <div v-if="!selectedNode" class="text-center py-8 text-gray-400">
            <MousePointer class="w-8 h-8 mx-auto mb-2 opacity-30" />
            <p class="text-xs">点击节点查看详情</p>
          </div>
          <div v-else class="space-y-3">
            <div class="p-3 bg-gray-50 rounded-xl">
              <p class="text-xs text-gray-500 mb-1">节点名称</p>
              <p class="text-sm font-bold text-gray-900">{{ selectedNode.label }}</p>
            </div>
            <div class="p-3 bg-gray-50 rounded-xl">
              <p class="text-xs text-gray-500 mb-1">节点类型</p>
              <p class="text-sm font-medium text-gray-700">{{ selectedNode.nodeType || '推理节点' }}</p>
            </div>
            <div v-if="selectedNode.detail" class="p-3 bg-gray-50 rounded-xl">
              <p class="text-xs text-gray-500 mb-1">详细描述</p>
              <p class="text-xs text-gray-600 leading-relaxed">{{ selectedNode.detail }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { VueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import {
  GitMerge, ZoomIn, ZoomOut, Maximize, Play, Loader2,
  Activity, Layers, FileText, MousePointer
} from 'lucide-vue-next'

let flowInstance = null
const zoomIn = () => flowInstance?.zoomIn()
const zoomOut = () => flowInstance?.zoomOut()
const fitView = () => flowInstance?.fitView()
const selectedNode = ref(null)
const isReplaying = ref(false)
const replayStep = ref(0)
const totalSteps = ref(7)

const nodeStyle = (borderColor, bg = '#fff') => ({
  background: bg,
  color: bg === '#fff' ? '#1e293b' : 'white',
  border: bg === '#fff' ? '1px solid #e2e8f0' : 'none',
  borderRadius: '14px',
  padding: '14px 18px',
  fontSize: '12px',
  fontWeight: bg === '#fff' ? '500' : '600',
  borderLeft: bg === '#fff' ? `4px solid ${borderColor}` : 'none',
  width: '180px',
  boxShadow: bg === '#fff' ? '0 2px 8px rgba(0,0,0,0.04)' : `0 4px 12px ${borderColor}40`,
  textAlign: bg === '#fff' ? 'left' : 'center'
})

const elements = ref([
  { id: '1', type: 'input', label: '用户查询\n分析比亚迪财务状况', position: { x: 300, y: 30 },
    style: { background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)', color: 'white', border: 'none', borderRadius: '14px', padding: '16px', fontSize: '13px', fontWeight: '600', boxShadow: '0 4px 12px rgba(124, 58, 237, 0.3)', width: '200px', textAlign: 'center' },
    data: { detail: '用户发起查询请求，系统开始解析意图' } },
  { id: '2', label: '意图识别\n财务分析 + 个股', position: { x: 300, y: 140 }, style: nodeStyle('#8b5cf6'),
    data: { detail: 'NLP引擎识别：分析类型=财务分析，标的=比亚迪(002594.SZ)', nodeType: '意图理解' } },
  { id: '3', label: '检索财报数据\n2023年年报', position: { x: 100, y: 260 }, style: nodeStyle('#3b82f6'),
    data: { detail: '调用Tushare API获取比亚迪最新财报数据，包含资产负债表、现金流量表', nodeType: '数据检索' } },
  { id: '4', label: '联网搜索\n最新新闻与分析', position: { x: 500, y: 260 }, style: nodeStyle('#3b82f6'),
    data: { detail: '调用Kimi $web_search搜索"比亚迪 最新新闻 行情分析"', nodeType: '联网搜索' } },
  { id: '5', label: '行业对标\n新能源汽车行业', position: { x: 100, y: 380 }, style: nodeStyle('#8b5cf6'),
    data: { detail: '与同行业企业（特斯拉、蔚来、理想等）进行横向财务指标对比', nodeType: '逻辑推理' } },
  { id: '6', label: '财务指标计算\nROE/毛利率/现金流', position: { x: 500, y: 380 }, style: nodeStyle('#8b5cf6'),
    data: { detail: '计算核心指标：ROE=17.2%, 毛利率=20.3%, 经营现金流同比+35%', nodeType: '指标计算' } },
  { id: '7', label: '风险评估\n识别潜在风险', position: { x: 300, y: 500 }, style: nodeStyle('#f97316'),
    data: { detail: '综合评估：行业竞争加剧(中风险)、原材料成本波动(低风险)、海外扩张不确定性(中风险)', nodeType: '风险评估' } },
  { id: '8', type: 'output', label: '生成分析报告\n综合评估结果', position: { x: 300, y: 620 },
    style: { background: 'linear-gradient(135deg, #059669 0%, #10b981 100%)', color: 'white', border: 'none', borderRadius: '14px', padding: '16px', fontSize: '13px', fontWeight: '600', width: '200px', textAlign: 'center', boxShadow: '0 4px 12px rgba(16, 185, 129, 0.3)' },
    data: { detail: '整合所有分析结果，生成结构化Markdown分析报告，评级：看好，置信度：中高' } },
  // Edges
  { id: 'e1-2', source: '1', target: '2', animated: true, style: { stroke: '#94a3b8', strokeWidth: 2 } },
  { id: 'e2-3', source: '2', target: '3', animated: true, style: { stroke: '#3b82f6', strokeWidth: 2 } },
  { id: 'e2-4', source: '2', target: '4', animated: true, style: { stroke: '#3b82f6', strokeWidth: 2 } },
  { id: 'e3-5', source: '3', target: '5', animated: true, style: { stroke: '#94a3b8', strokeWidth: 2 } },
  { id: 'e4-6', source: '4', target: '6', animated: true, style: { stroke: '#94a3b8', strokeWidth: 2 } },
  { id: 'e5-7', source: '5', target: '7', animated: true, style: { stroke: '#f97316', strokeWidth: 2 } },
  { id: 'e6-7', source: '6', target: '7', animated: true, style: { stroke: '#f97316', strokeWidth: 2 } },
  { id: 'e7-8', source: '7', target: '8', animated: true, style: { stroke: '#10b981', strokeWidth: 2 } }
])

const legends = [
  { label: '用户输入', color: 'bg-violet-500' },
  { label: '数据检索', color: 'bg-blue-500' },
  { label: '逻辑推理', color: 'bg-purple-500' },
  { label: '风险评估', color: 'bg-orange-500' },
  { label: '结果生成', color: 'bg-emerald-500' }
]

const nodeCount = computed(() => elements.value.filter(el => !el.source).length)
const edgeCount = computed(() => elements.value.filter(el => el.source).length)
const dataSourceCount = computed(() => elements.value.filter(el => el.label && (el.label.includes('检索') || el.label.includes('搜索'))).length)
const reasoningDepth = ref(5)

const onPaneReady = (instance) => {
  flowInstance = instance
  instance.fitView()
  instance.onNodeClick(({ node }) => {
    selectedNode.value = { label: node.label, ...(node.data || {}) }
  })
}

const replayAnimation = async () => {
  isReplaying.value = true
  replayStep.value = 0
  const nodes = elements.value.filter(el => !el.source)
  const edges = elements.value.filter(el => el.source)

  // Hide all first
  const origStyles = nodes.map(n => ({ ...n.style }))
  nodes.forEach(n => { n.style = { ...n.style, opacity: 0.15 } })
  edges.forEach(e => { e.style = { ...e.style, opacity: 0.1 } })

  // Reveal one by one
  for (let i = 0; i < nodes.length; i++) {
    await new Promise(r => setTimeout(r, 600))
    replayStep.value = i + 1
    nodes[i].style = { ...origStyles[i], opacity: 1, transition: 'all 0.5s' }
    // Reveal edges connected to this node
    edges.forEach(e => {
      if (e.target === nodes[i].id || e.source === nodes[i].id) {
        e.style = { ...e.style, opacity: 1, transition: 'all 0.5s' }
      }
    })
  }

  isReplaying.value = false
}
</script>

<style>
@import '@vue-flow/core/dist/style.css';
@import '@vue-flow/core/dist/theme-default.css';
@import '@vue-flow/controls/dist/style.css';
@import '@vue-flow/minimap/dist/style.css';

.vue-flow__controls-button {
  border: 1px solid #e2e8f0 !important;
  background-color: white !important;
  color: #64748b !important;
}
.vue-flow__controls-button:hover {
  background-color: #f8fafc !important;
  color: #0f172a !important;
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }
</style>
