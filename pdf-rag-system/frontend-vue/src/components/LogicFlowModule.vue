<template>
  <div class="h-full flex flex-col gap-6 p-2 font-sans overflow-hidden">
    <!-- Header Section -->
    <div class="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm shrink-0 flex items-center justify-between">
      <div>
        <h2 class="text-xl font-bold text-gray-900 flex items-center gap-3">
          <div class="p-2.5 rounded-xl bg-violet-50 text-violet-600">
            <GitMerge class="w-6 h-6" />
          </div>
          全息决策链·逻辑流
        </h2>
        <p class="text-sm text-gray-500 mt-1.5 ml-1">决策终局的"骨" — AI 决策推理链路全景展示</p>
      </div>
      
      <div class="flex items-center gap-3">
        <div class="flex items-center bg-gray-50 rounded-xl p-1 border border-gray-100">
           <button class="p-2 hover:bg-white hover:shadow-sm rounded-lg text-gray-500 transition-all relative group overflow-hidden" title="放大" @click="zoomIn">
             <div class="absolute bottom-0 left-0 w-full h-0.5 bg-orange-500 opacity-0 group-hover:opacity-100 transition-opacity"></div>
             <ZoomIn class="w-4 h-4" />
           </button>
           <button class="p-2 hover:bg-white hover:shadow-sm rounded-lg text-gray-500 transition-all relative group overflow-hidden" title="缩小" @click="zoomOut">
             <div class="absolute bottom-0 left-0 w-full h-0.5 bg-orange-500 opacity-0 group-hover:opacity-100 transition-opacity"></div>
             <ZoomOut class="w-4 h-4" />
           </button>
           <button class="p-2 hover:bg-white hover:shadow-sm rounded-lg text-gray-500 transition-all relative group overflow-hidden" title="适应屏幕" @click="fitView">
             <div class="absolute bottom-0 left-0 w-full h-0.5 bg-orange-500 opacity-0 group-hover:opacity-100 transition-opacity"></div>
             <Maximize class="w-4 h-4" />
           </button>
        </div>
        <button class="flex items-center gap-2 px-4 py-2 bg-gray-900 text-white text-sm font-medium rounded-xl hover:bg-gray-800 transition-all shadow-lg shadow-gray-900/20 relative group overflow-hidden">
          <div class="absolute bottom-0 left-0 w-full h-0.5 bg-orange-500 opacity-0 group-hover:opacity-100 transition-opacity"></div>
          <Download class="w-4 h-4" />
          导出图谱
        </button>
      </div>
    </div>

    <!-- Main Content -->
    <div class="flex-1 relative bg-white border border-gray-100 rounded-2xl shadow-sm overflow-hidden group">
      <!-- VueFlow Container -->
      <VueFlow
        v-model="elements"
        :default-zoom="1"
        :min-zoom="0.2"
        :max-zoom="4"
        class="h-full w-full bg-slate-50/50"
        @pane-ready="onPaneReady"
      >
        <Background pattern-color="#e2e8f0" :gap="20" />
        <Controls :show-interactive="false" class="!bg-white !border !border-gray-100 !shadow-sm !rounded-lg !m-4" />
        <MiniMap class="!bg-white !border !border-gray-100 !shadow-sm !rounded-lg !bottom-4 !right-4" />
      </VueFlow>

      <!-- Floating Stats Panel -->
      <div class="absolute top-6 right-6 w-72 bg-white/90 backdrop-blur-md border border-gray-100 rounded-2xl shadow-lg p-5 space-y-5 transition-all duration-300 translate-x-0">
        <div>
          <h3 class="text-sm font-bold text-gray-900 mb-3 flex items-center gap-2">
            <Activity class="w-4 h-4 text-violet-500" />
            推理统计
          </h3>
          <div class="space-y-3">
            <div class="flex items-center justify-between p-2.5 bg-gray-50 rounded-xl">
              <span class="text-xs text-gray-500">推理节点</span>
              <span class="text-sm font-bold text-gray-900">{{ nodeCount }}</span>
            </div>
            <div class="flex items-center justify-between p-2.5 bg-gray-50 rounded-xl">
              <span class="text-xs text-gray-500">数据源调用</span>
              <span class="text-sm font-bold text-gray-900">{{ dataSourceCount }}</span>
            </div>
            <div class="flex items-center justify-between p-2.5 bg-gray-50 rounded-xl">
              <span class="text-xs text-gray-500">推理深度</span>
              <span class="text-sm font-bold text-gray-900">{{ reasoningDepth }} 层</span>
            </div>
          </div>
        </div>

        <div class="border-t border-gray-100 pt-4">
          <h3 class="text-sm font-bold text-gray-900 mb-3 flex items-center gap-2">
            <Layers class="w-4 h-4 text-blue-500" />
            节点类型图例
          </h3>
          <div class="grid grid-cols-2 gap-2">
            <div class="flex items-center gap-2 text-xs text-gray-600">
              <div class="w-2.5 h-2.5 rounded-full bg-blue-500"></div>
              <span>数据检索</span>
            </div>
            <div class="flex items-center gap-2 text-xs text-gray-600">
              <div class="w-2.5 h-2.5 rounded-full bg-violet-500"></div>
              <span>逻辑推理</span>
            </div>
            <div class="flex items-center gap-2 text-xs text-gray-600">
              <div class="w-2.5 h-2.5 rounded-full bg-emerald-500"></div>
              <span>结果生成</span>
            </div>
            <div class="flex items-center gap-2 text-xs text-gray-600">
              <div class="w-2.5 h-2.5 rounded-full bg-orange-500"></div>
              <span>风险评估</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { VueFlow, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import { 
  GitMerge, 
  ZoomIn, 
  ZoomOut, 
  Maximize, 
  Download,
  Activity,
  Layers
} from 'lucide-vue-next'

const { zoomIn, zoomOut, fitView } = useVueFlow()
defineEmits(['logout'])

const elements = ref([
  {
    id: '1',
    type: 'input',
    label: '用户查询\n分析比亚迪财务状况',
    position: { x: 250, y: 50 },
    style: {
      background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
      color: 'white',
      border: 'none',
      borderRadius: '12px',
      padding: '16px',
      fontSize: '13px',
      fontWeight: '600',
      boxShadow: '0 4px 6px -1px rgba(124, 58, 237, 0.3)',
      width: '180px',
      textAlign: 'center'
    }
  },
  {
    id: '2',
    label: '检索财报数据\n2023年年报',
    position: { x: 100, y: 180 },
    style: {
      background: '#fff',
      color: '#1e293b',
      border: '1px solid #e2e8f0',
      borderRadius: '12px',
      padding: '12px',
      fontSize: '12px',
      borderLeft: '4px solid #3b82f6',
      width: '160px',
      boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
    }
  },
  {
    id: '3',
    label: '检索行业数据\n新能源汽车行业',
    position: { x: 400, y: 180 },
    style: {
      background: '#fff',
      color: '#1e293b',
      border: '1px solid #e2e8f0',
      borderRadius: '12px',
      padding: '12px',
      fontSize: '12px',
      borderLeft: '4px solid #3b82f6',
      width: '160px',
      boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
    }
  },
  {
    id: '4',
    label: '财务指标计算\nROE, 毛利率等',
    position: { x: 100, y: 300 },
    style: {
      background: '#fff',
      color: '#1e293b',
      border: '1px solid #e2e8f0',
      borderRadius: '12px',
      padding: '12px',
      fontSize: '12px',
      borderLeft: '4px solid #8b5cf6',
      width: '160px',
      boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
    }
  },
  {
    id: '5',
    label: '行业对标分析\n与竞品对比',
    position: { x: 400, y: 300 },
    style: {
      background: '#fff',
      color: '#1e293b',
      border: '1px solid #e2e8f0',
      borderRadius: '12px',
      padding: '12px',
      fontSize: '12px',
      borderLeft: '4px solid #8b5cf6',
      width: '160px',
      boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
    }
  },
  {
    id: '6',
    label: '风险评估\n识别潜在风险',
    position: { x: 250, y: 420 },
    style: {
      background: '#fff',
      color: '#1e293b',
      border: '1px solid #e2e8f0',
      borderRadius: '12px',
      padding: '12px',
      fontSize: '12px',
      borderLeft: '4px solid #f97316',
      width: '160px',
      boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
    }
  },
  {
    id: '7',
    type: 'output',
    label: '生成分析报告\n综合评估结果',
    position: { x: 250, y: 540 },
    style: {
      background: '#10b981',
      color: 'white',
      border: 'none',
      borderRadius: '12px',
      padding: '14px',
      fontSize: '13px',
      fontWeight: '600',
      width: '180px',
      textAlign: 'center',
      boxShadow: '0 4px 6px -1px rgba(16, 185, 129, 0.3)'
    }
  },
  { id: 'e1-2', source: '1', target: '2', animated: true, style: { stroke: '#94a3b8', strokeWidth: 2 } },
  { id: 'e1-3', source: '1', target: '3', animated: true, style: { stroke: '#94a3b8', strokeWidth: 2 } },
  { id: 'e2-4', source: '2', target: '4', animated: true, style: { stroke: '#94a3b8', strokeWidth: 2 } },
  { id: 'e3-5', source: '3', target: '5', animated: true, style: { stroke: '#94a3b8', strokeWidth: 2 } },
  { id: 'e4-6', source: '4', target: '6', animated: true, style: { stroke: '#94a3b8', strokeWidth: 2 } },
  { id: 'e5-6', source: '5', target: '6', animated: true, style: { stroke: '#94a3b8', strokeWidth: 2 } },
  { id: 'e6-7', source: '6', target: '7', animated: true, style: { stroke: '#10b981', strokeWidth: 2 } }
])

const nodeCount = computed(() => {
  return elements.value.filter(el => !el.source).length
})

const dataSourceCount = computed(() => {
  return elements.value.filter(el => el.label && el.label.includes('检索')).length
})

const reasoningDepth = computed(() => {
  return 4
})

const onPaneReady = (instance) => {
  instance.fitView()
}
</script>

<style>
@import '@vue-flow/core/dist/style.css';
@import '@vue-flow/core/dist/theme-default.css';
@import '@vue-flow/controls/dist/style.css';
@import '@vue-flow/minimap/dist/style.css';

/* Override VueFlow Controls & MiniMap Styles to match theme */
.vue-flow__controls-button {
  border: 1px solid #e2e8f0 !important;
  background-color: white !important;
  color: #64748b !important;
}
.vue-flow__controls-button:hover {
  background-color: #f8fafc !important;
  color: #0f172a !important;
}
</style>
