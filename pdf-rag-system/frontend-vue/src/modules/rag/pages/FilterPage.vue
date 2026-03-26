<template>
  <div class="h-full flex flex-col">
    <!-- Hero -->
    <div class="relative overflow-hidden bg-gradient-to-br from-emerald-50 via-white to-green-50 border-b border-gray-100">
      <div class="absolute inset-0 opacity-20">
        <div class="absolute top-3 left-16 w-48 h-48 bg-emerald-200 rounded-full blur-3xl animate-pulse"></div>
        <div class="absolute bottom-0 right-10 w-40 h-40 bg-green-200 rounded-full blur-3xl animate-pulse" style="animation-delay:1s"></div>
      </div>
      <div class="relative px-6 py-4">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-500 to-green-600 flex items-center justify-center shadow-md shadow-emerald-500/20 shrink-0">
            <Scissors class="w-4.5 h-4.5 text-white" />
          </div>
          <div>
            <h1 class="text-base font-bold text-gray-900">噪声过滤与剪枝</h1>
            <p class="text-[11px] text-gray-500 mt-0.5">语义剪枝去除无关内容，可视化过滤过程与精度提升</p>
          </div>
        </div>
      </div>
    </div>

    <div class="flex-1 flex min-h-0">
      <!-- Main -->
      <div class="flex-1 overflow-y-auto p-5 space-y-4 custom-scrollbar">
        <!-- Pipeline Visualization -->
        <div class="bg-white border border-gray-100 rounded-xl p-5 shadow-sm">
          <h3 class="text-xs font-bold text-gray-800 mb-4 flex items-center gap-2">
            <Workflow class="w-4 h-4 text-emerald-500" /> 剪枝处理流水线
          </h3>
          <div class="flex items-center gap-2">
            <div v-for="(step, i) in pipeline" :key="i" class="flex items-center gap-2">
              <div :class="['p-3 rounded-xl border transition-all', step.active ? step.activeBg : 'bg-gray-50 border-gray-200']">
                <div class="flex items-center gap-2 mb-1">
                  <component :is="step.icon" :class="['w-3.5 h-3.5', step.active ? step.iconColor : 'text-gray-400']" />
                  <span :class="['text-[11px] font-bold', step.active ? step.textColor : 'text-gray-500']">{{ step.name }}</span>
                </div>
                <p class="text-[9px] text-gray-400">{{ step.desc }}</p>
                <div class="mt-1.5 flex items-center gap-1.5">
                  <span class="text-[10px] font-mono font-bold" :class="step.active ? step.textColor : 'text-gray-500'">{{ step.count }}条</span>
                  <span v-if="step.filtered" class="text-[9px] text-rose-500 font-mono">-{{ step.filtered }}</span>
                </div>
              </div>
              <ChevronRight v-if="i < pipeline.length - 1" class="w-4 h-4 text-gray-300 shrink-0" />
            </div>
          </div>
        </div>

        <!-- Before/After Comparison -->
        <div class="grid grid-cols-2 gap-4">
          <div class="bg-white border border-gray-100 rounded-xl shadow-sm overflow-hidden">
            <div class="px-4 py-2.5 bg-rose-50 border-b border-rose-100 flex items-center gap-2">
              <XCircle class="w-3.5 h-3.5 text-rose-500" />
              <h3 class="text-[11px] font-bold text-rose-700">剪枝前（含噪声）</h3>
              <span class="ml-auto text-[10px] font-mono text-rose-500">{{ beforeChunks.length }}条</span>
            </div>
            <div class="p-3 space-y-2 max-h-64 overflow-y-auto custom-scrollbar">
              <div v-for="(chunk, i) in beforeChunks" :key="i"
                :class="['p-2.5 rounded-lg text-[11px] border transition-all',
                  chunk.noise ? 'bg-rose-50/50 border-rose-200 text-rose-600 line-through opacity-60' : 'bg-white border-gray-100 text-gray-700']">
                <div class="flex items-center justify-between mb-1">
                  <span class="text-[9px] font-mono" :class="chunk.noise ? 'text-rose-400' : 'text-gray-400'">{{ chunk.id }}</span>
                  <span v-if="chunk.noise" class="text-[9px] px-1.5 py-0.5 bg-rose-100 text-rose-600 rounded font-bold">噪声</span>
                  <span v-else class="text-[9px] px-1.5 py-0.5 bg-emerald-100 text-emerald-600 rounded font-bold">相关</span>
                </div>
                {{ chunk.text }}
              </div>
            </div>
          </div>
          <div class="bg-white border border-gray-100 rounded-xl shadow-sm overflow-hidden">
            <div class="px-4 py-2.5 bg-emerald-50 border-b border-emerald-100 flex items-center gap-2">
              <CheckCircle class="w-3.5 h-3.5 text-emerald-500" />
              <h3 class="text-[11px] font-bold text-emerald-700">剪枝后（精准结果）</h3>
              <span class="ml-auto text-[10px] font-mono text-emerald-500">{{ afterChunks.length }}条</span>
            </div>
            <div class="p-3 space-y-2 max-h-64 overflow-y-auto custom-scrollbar">
              <div v-for="(chunk, i) in afterChunks" :key="i"
                class="p-2.5 rounded-lg text-[11px] bg-white border border-emerald-100 text-gray-700">
                <div class="flex items-center justify-between mb-1">
                  <span class="text-[9px] font-mono text-gray-400">{{ chunk.id }}</span>
                  <span class="text-[9px] font-mono text-emerald-600 font-bold">{{ chunk.score }}</span>
                </div>
                {{ chunk.text }}
              </div>
            </div>
          </div>
        </div>

        <!-- Metrics -->
        <div class="bg-white border border-gray-100 rounded-xl shadow-sm overflow-hidden">
          <div class="px-5 py-3 border-b border-gray-50">
            <h3 class="text-xs font-bold text-gray-800">剪枝效果对比</h3>
          </div>
          <div ref="metricsRef" class="w-full h-48"></div>
        </div>
      </div>

      <!-- Right: Config -->
      <div class="w-64 border-l border-gray-100 bg-gray-50/50 p-4 flex flex-col gap-3 shrink-0 overflow-y-auto custom-scrollbar">
        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <h4 class="text-[11px] font-bold text-gray-700 mb-3 flex items-center gap-1.5">
            <Sliders class="w-3.5 h-3.5 text-emerald-500" /> 剪枝策略
          </h4>
          <div class="space-y-3">
            <div>
              <label class="text-[10px] text-gray-500 block mb-1">语义阈值</label>
              <input type="range" min="0" max="100" v-model="semanticThreshold" class="w-full h-1 accent-emerald-500" />
              <span class="text-[10px] text-gray-400 float-right">{{ semanticThreshold }}%</span>
            </div>
            <div>
              <label class="text-[10px] text-gray-500 block mb-1">重叠度阈值</label>
              <input type="range" min="0" max="100" v-model="overlapThreshold" class="w-full h-1 accent-emerald-500" />
              <span class="text-[10px] text-gray-400 float-right">{{ overlapThreshold }}%</span>
            </div>
            <div>
              <label class="text-[10px] text-gray-500 block mb-1">剪枝模式</label>
              <select class="w-full px-2 py-1.5 text-[11px] border border-gray-200 rounded-lg bg-gray-50">
                <option>语义剪枝（推荐）</option>
                <option>关键词剪枝</option>
                <option>混合模式</option>
              </select>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <h4 class="text-[11px] font-bold text-gray-700 mb-3">效果指标</h4>
          <div class="space-y-2 text-[11px]">
            <div class="flex justify-between"><span class="text-gray-500">噪声过滤率</span><span class="font-mono font-bold text-emerald-600">62.5%</span></div>
            <div class="flex justify-between"><span class="text-gray-500">精确率提升</span><span class="font-mono font-bold text-emerald-600">+28.3%</span></div>
            <div class="flex justify-between"><span class="text-gray-500">召回率保持</span><span class="font-mono font-bold text-blue-600">97.1%</span></div>
            <div class="flex justify-between"><span class="text-gray-500">响应速度提升</span><span class="font-mono font-bold text-purple-600">+45%</span></div>
          </div>
        </div>

        <div class="bg-emerald-50 rounded-xl border border-emerald-200 p-4 flex-1">
          <h4 class="text-[11px] font-bold text-emerald-700 mb-2 flex items-center gap-1.5">
            <Sparkles class="w-3.5 h-3.5" /> 剪枝建议
          </h4>
          <div class="space-y-2">
            <p class="text-[10px] text-emerald-600 leading-relaxed">• 当前语义阈值设置合理，过滤了62.5%的噪声内容</p>
            <p class="text-[10px] text-emerald-600 leading-relaxed">• 建议开启重叠去重，可进一步减少15%冗余</p>
            <p class="text-[10px] text-emerald-600 leading-relaxed">• 召回率保持在97%以上，未丢失关键信息</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { Scissors, Workflow, ChevronRight, XCircle, CheckCircle, Sliders, Sparkles,
  FileText, Filter, Layers, Shrink } from 'lucide-vue-next'

const semanticThreshold = ref(65)
const overlapThreshold = ref(40)
const metricsRef = ref(null)

const pipeline = [
  { name: '原始检索', desc: '向量召回', count: 40, filtered: null, active: true, icon: FileText, activeBg: 'bg-blue-50 border-blue-200', iconColor: 'text-blue-500', textColor: 'text-blue-700' },
  { name: '语义过滤', desc: '阈值剪枝', count: 25, filtered: 15, active: true, icon: Filter, activeBg: 'bg-amber-50 border-amber-200', iconColor: 'text-amber-500', textColor: 'text-amber-700' },
  { name: '重叠去重', desc: '相似合并', count: 18, filtered: 7, active: true, icon: Layers, activeBg: 'bg-orange-50 border-orange-200', iconColor: 'text-orange-500', textColor: 'text-orange-700' },
  { name: '压缩精炼', desc: '上下文压缩', count: 15, filtered: 3, active: true, icon: Shrink, activeBg: 'bg-emerald-50 border-emerald-200', iconColor: 'text-emerald-500', textColor: 'text-emerald-700' }
]

const beforeChunks = [
  { id: 'chunk_001', text: '比亚迪2023年营收6023亿，同比增长42%，毛利率20.31%', noise: false },
  { id: 'chunk_002', text: '公司办公地址位于深圳市坪山区比亚迪路3009号', noise: true },
  { id: 'chunk_003', text: '新能源汽车销量302.4万辆，市占率提升至35%', noise: false },
  { id: 'chunk_004', text: '本报告中的数据来源于公开资料整理', noise: true },
  { id: 'chunk_005', text: '免责声明：本报告仅供参考，不构成投资建议', noise: true },
  { id: 'chunk_006', text: '研发费用投入396亿元，同比增长97%，研发人员超10万', noise: false },
  { id: 'chunk_007', text: '目录：一、公司概况 二、财务分析 三、行业分析...', noise: true },
  { id: 'chunk_008', text: '动力电池出货量全球第二，市占率16.2%', noise: false }
]

const afterChunks = beforeChunks.filter(c => !c.noise).map(c => ({ ...c, score: (0.85 + Math.random() * 0.12).toFixed(3) }))

const initMetrics = () => {
  if (!metricsRef.value) return
  const chart = echarts.init(metricsRef.value)
  chart.setOption({
    tooltip: { textStyle: { fontSize: 10 } },
    legend: { data: ['剪枝前', '剪枝后'], bottom: 5, textStyle: { fontSize: 10 } },
    grid: { top: 15, bottom: 40, left: 50, right: 15 },
    xAxis: { type: 'category', data: ['精确率', '召回率', 'F1分数', 'MRR@10', 'NDCG@10'], axisLabel: { fontSize: 9 } },
    yAxis: { type: 'value', max: 100, axisLabel: { fontSize: 9, formatter: '{value}%' }, splitLine: { lineStyle: { color: '#f3f4f6' } } },
    series: [
      { name: '剪枝前', type: 'bar', data: [58, 95, 72, 65, 68], barWidth: '25%', itemStyle: { color: '#fca5a5', borderRadius: [3, 3, 0, 0] } },
      { name: '剪枝后', type: 'bar', data: [86, 93, 89, 82, 85], barWidth: '25%', itemStyle: { color: '#6ee7b7', borderRadius: [3, 3, 0, 0] } }
    ]
  })
}

onMounted(() => { nextTick(() => initMetrics()) })
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }
</style>
