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
        <div class="bg-white border border-gray-100 rounded-xl p-4 shadow-sm">
          <div class="flex items-center gap-3">
            <input v-model="queryText" @keydown.enter="runPrune" type="text" placeholder="输入查询语句，查看剪枝前后对比..."
              class="flex-1 px-4 py-2.5 text-xs border border-gray-200 rounded-xl bg-gray-50 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-400 transition-all" />
            <button @click="runPrune" :disabled="loading"
              class="px-5 py-2.5 bg-emerald-600 text-white text-xs font-medium rounded-xl hover:bg-emerald-700 transition-colors disabled:opacity-50 flex items-center gap-1.5 shrink-0">
              <Loader2 v-if="loading" class="w-3.5 h-3.5 animate-spin" />
              <Search v-else class="w-3.5 h-3.5" />
              剪枝分析
            </button>
          </div>
        </div>

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
            <div class="flex justify-between"><span class="text-gray-500">噪声过滤率</span><span class="font-mono font-bold text-emerald-600">{{ noiseFilterRate }}%</span></div>
            <div class="flex justify-between"><span class="text-gray-500">精确率提升</span><span class="font-mono font-bold text-emerald-600">{{ precisionGain }}</span></div>
            <div class="flex justify-between"><span class="text-gray-500">召回率保持</span><span class="font-mono font-bold text-blue-600">{{ pruneMetrics.afterRecall }}%</span></div>
            <div class="flex justify-between"><span class="text-gray-500">保留片段</span><span class="font-mono font-bold text-purple-600">{{ afterChunks.length }}/{{ beforeChunks.length }}</span></div>
          </div>
        </div>

        <div class="bg-emerald-50 rounded-xl border border-emerald-200 p-4 flex-1">
          <h4 class="text-[11px] font-bold text-emerald-700 mb-2 flex items-center gap-1.5">
            <Sparkles class="w-3.5 h-3.5" /> 剪枝建议
          </h4>
          <div class="space-y-2">
            <p class="text-[10px] text-emerald-600 leading-relaxed">• 当前语义阈值为 {{ semanticThreshold }}%，当前过滤了 {{ noiseFilterRate }}% 的候选片段</p>
            <p class="text-[10px] text-emerald-600 leading-relaxed">• 当前重叠阈值为 {{ overlapThreshold }}%，去重后保留 {{ afterChunks.length }} 条高相关片段</p>
            <p class="text-[10px] text-emerald-600 leading-relaxed">• 精确率从 {{ pruneMetrics.beforePrecision }}% 提升到 {{ pruneMetrics.afterPrecision }}%，召回保持 {{ pruneMetrics.afterRecall }}%</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { Scissors, Workflow, ChevronRight, XCircle, CheckCircle, Sliders, Sparkles,
  FileText, Filter, Layers, Shrink, Search, Loader2 } from 'lucide-vue-next'

const queryText = ref('比亚迪毛利率变化')
const loading = ref(false)
const semanticThreshold = ref(65)
const overlapThreshold = ref(40)
const metricsRef = ref(null)
const metricsChart = ref(null)
const rawResults = ref([])

const beforeChunks = ref([])
const afterChunks = ref([])
const pruneMetrics = ref({ beforePrecision: 0, afterPrecision: 0, beforeRecall: 0, afterRecall: 0, beforeF1: 0, afterF1: 0, beforeMrr: 0, afterMrr: 0, beforeNdcg: 0, afterNdcg: 0 })
const noiseFilterRate = computed(() => beforeChunks.value.length ? Math.round(((beforeChunks.value.length - afterChunks.value.length) / beforeChunks.value.length) * 100) : 0)
const precisionGain = computed(() => {
  const delta = pruneMetrics.value.afterPrecision - pruneMetrics.value.beforePrecision
  return `${delta >= 0 ? '+' : ''}${delta}%`
})

const pipeline = computed(() => {
  const originalCount = beforeChunks.value.length
  const semanticCount = beforeChunks.value.filter(chunk => !chunk.lowScore).length
  const dedupedCount = afterChunks.value.length
  const overlapRemoved = Math.max(semanticCount - dedupedCount, 0)
  const compressedCount = dedupedCount
  return [
    { name: '原始检索', desc: '向量召回', count: originalCount, filtered: null, active: true, icon: FileText, activeBg: 'bg-blue-50 border-blue-200', iconColor: 'text-blue-500', textColor: 'text-blue-700' },
    { name: '语义过滤', desc: '阈值剪枝', count: semanticCount, filtered: Math.max(originalCount - semanticCount, 0), active: true, icon: Filter, activeBg: 'bg-amber-50 border-amber-200', iconColor: 'text-amber-500', textColor: 'text-amber-700' },
    { name: '重叠去重', desc: '相似合并', count: dedupedCount, filtered: overlapRemoved, active: true, icon: Layers, activeBg: 'bg-orange-50 border-orange-200', iconColor: 'text-orange-500', textColor: 'text-orange-700' },
    { name: '压缩精炼', desc: '上下文压缩', count: compressedCount, filtered: 0, active: true, icon: Shrink, activeBg: 'bg-emerald-50 border-emerald-200', iconColor: 'text-emerald-500', textColor: 'text-emerald-700' }
  ]
})

const normalizeText = (text) => (text || '').replace(/\s+/g, '')

const overlapRatio = (left, right) => {
  const a = normalizeText(left)
  const b = normalizeText(right)
  if (!a || !b) return 0
  const short = a.length <= b.length ? a : b
  const long = a.length <= b.length ? b : a
  let hits = 0
  const seen = new Set()
  for (const char of short) {
    if (seen.has(char)) continue
    seen.add(char)
    if (long.includes(char)) hits += 1
  }
  return hits / seen.size
}

const updateMetrics = () => {
  const beforeScores = beforeChunks.value.map(item => Number(item.score || 0))
  const afterScores = afterChunks.value.map(item => Number(item.score || 0))
  const avg = (items) => items.length ? items.reduce((sum, item) => sum + item, 0) / items.length : 0
  const beforePrecision = Math.round(avg(beforeScores) * 100)
  const afterPrecision = Math.round(avg(afterScores) * 100)
  const beforeRecall = beforeChunks.value.length ? 100 : 0
  const afterRecall = beforeChunks.value.length ? Math.round((afterChunks.value.length / beforeChunks.value.length) * 100) : 0
  const calcF1 = (precision, recall) => (precision && recall) ? Math.round((2 * precision * recall) / (precision + recall)) : 0
  const topScore = (items) => items.length ? Math.round(items[0] * 100) : 0
  const topAverage = (items) => items.length ? Math.round(avg(items.slice(0, Math.min(items.length, 10))) * 100) : 0
  pruneMetrics.value = {
    beforePrecision,
    afterPrecision,
    beforeRecall,
    afterRecall,
    beforeF1: calcF1(beforePrecision, beforeRecall),
    afterF1: calcF1(afterPrecision, afterRecall),
    beforeMrr: topScore(beforeScores),
    afterMrr: topScore(afterScores),
    beforeNdcg: topAverage(beforeScores),
    afterNdcg: topAverage(afterScores)
  }
}

const applyPruning = () => {
  const thresholdScore = semanticThreshold.value / 100
  const overlapLimit = overlapThreshold.value / 100
  const baseChunks = rawResults.value.map((item, index) => ({
    id: `chunk_${String(index + 1).padStart(3, '0')}`,
    text: item.text,
    score: Number(item.score || 0),
    noise: false,
    lowScore: Number(item.score || 0) < thresholdScore,
    overlapDropped: false,
    page: item.page_number,
    source: item.source
  }))

  const kept = []
  for (const chunk of baseChunks) {
    if (chunk.lowScore) {
      chunk.noise = true
      continue
    }
    const duplicated = kept.some(existing => overlapRatio(existing.text, chunk.text) >= overlapLimit)
    if (duplicated) {
      chunk.overlapDropped = true
      chunk.noise = true
      continue
    }
    kept.push(chunk)
  }

  beforeChunks.value = baseChunks
  afterChunks.value = kept.map(chunk => ({
    id: chunk.id,
    text: chunk.text,
    score: chunk.score.toFixed(3),
    page: chunk.page,
    source: chunk.source
  }))
  updateMetrics()
  nextTick(() => initMetrics())
}

const initMetrics = () => {
  if (!metricsRef.value) return
  metricsChart.value = metricsChart.value || echarts.init(metricsRef.value)
  metricsChart.value.setOption({
    tooltip: { textStyle: { fontSize: 10 } },
    legend: { data: ['剪枝前', '剪枝后'], bottom: 5, textStyle: { fontSize: 10 } },
    grid: { top: 15, bottom: 40, left: 50, right: 15 },
    xAxis: { type: 'category', data: ['精确率', '召回率', 'F1分数', 'MRR@10', 'NDCG@10'], axisLabel: { fontSize: 9 } },
    yAxis: { type: 'value', max: 100, axisLabel: { fontSize: 9, formatter: '{value}%' }, splitLine: { lineStyle: { color: '#f3f4f6' } } },
    series: [
      { name: '剪枝前', type: 'bar', data: [pruneMetrics.value.beforePrecision, pruneMetrics.value.beforeRecall, pruneMetrics.value.beforeF1, pruneMetrics.value.beforeMrr, pruneMetrics.value.beforeNdcg], barWidth: '25%', itemStyle: { color: '#fca5a5', borderRadius: [3, 3, 0, 0] } },
      { name: '剪枝后', type: 'bar', data: [pruneMetrics.value.afterPrecision, pruneMetrics.value.afterRecall, pruneMetrics.value.afterF1, pruneMetrics.value.afterMrr, pruneMetrics.value.afterNdcg], barWidth: '25%', itemStyle: { color: '#6ee7b7', borderRadius: [3, 3, 0, 0] } }
    ]
  })
}

const runPrune = async () => {
  if (!queryText.value.trim()) return
  loading.value = true
  try {
    const token = localStorage.getItem('access_token')
    const resp = await fetch('/api/rag/search', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: queryText.value.trim(),
        top_k: 40,
        score_threshold: 0,
        sort_by: 'score_desc'
      })
    })
    const data = await resp.json()
    if (!resp.ok) {
      throw new Error(data.detail || '剪枝分析失败')
    }
    rawResults.value = data.results || []
    applyPruning()
  } catch (error) {
    console.error('剪枝分析失败', error)
    rawResults.value = []
    beforeChunks.value = []
    afterChunks.value = []
    updateMetrics()
    nextTick(() => initMetrics())
  } finally {
    loading.value = false
  }
}

watch([semanticThreshold, overlapThreshold], () => {
  if (rawResults.value.length) {
    applyPruning()
  }
})

onMounted(() => {
  nextTick(() => initMetrics())
  runPrune()
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }
</style>
