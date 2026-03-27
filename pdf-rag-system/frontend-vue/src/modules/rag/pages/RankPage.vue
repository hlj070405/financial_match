<template>
  <div class="h-full flex flex-col">
    <!-- Hero -->
    <div class="relative overflow-hidden bg-gradient-to-br from-purple-50 via-white to-indigo-50 border-b border-gray-100">
      <div class="absolute inset-0 opacity-20">
        <div class="absolute top-3 left-16 w-48 h-48 bg-purple-200 rounded-full blur-3xl animate-pulse"></div>
        <div class="absolute bottom-0 right-10 w-40 h-40 bg-indigo-200 rounded-full blur-3xl animate-pulse" style="animation-delay:1s"></div>
      </div>
      <div class="relative px-6 py-4">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center shadow-md shadow-purple-500/20 shrink-0">
            <ArrowUpDown class="w-4.5 h-4.5 text-white" />
          </div>
          <div>
            <h1 class="text-base font-bold text-gray-900">向量相似度排序</h1>
            <p class="text-[11px] text-gray-500 mt-0.5">余弦相似度 + ANN近似最近邻，可视化向量空间距离与排序</p>
          </div>
        </div>
      </div>
    </div>

    <div class="flex-1 flex min-h-0">
      <!-- Main -->
      <div class="flex-1 overflow-y-auto p-5 space-y-4 custom-scrollbar">
        <!-- Query Input -->
        <div class="bg-white border border-gray-100 rounded-xl p-4 shadow-sm">
          <div class="flex items-center gap-3">
            <input v-model="queryText" @keydown.enter="runRank" type="text" placeholder="输入查询语句，可视化向量匹配排序..."
              class="flex-1 px-4 py-2.5 text-xs border border-gray-200 rounded-xl bg-gray-50 focus:outline-none focus:ring-2 focus:ring-purple-500/20 focus:border-purple-400 transition-all" />
            <button @click="runRank" :disabled="loading"
              class="px-5 py-2.5 bg-purple-600 text-white text-xs font-medium rounded-xl hover:bg-purple-700 transition-colors disabled:opacity-50 flex items-center gap-1.5 shrink-0">
              <Loader2 v-if="loading" class="w-3.5 h-3.5 animate-spin" />
              <Zap v-else class="w-3.5 h-3.5" />
              向量检索
            </button>
          </div>
        </div>

        <!-- Vector Space Visualization -->
        <div class="bg-white border border-gray-100 rounded-xl shadow-sm overflow-hidden">
          <div class="px-5 py-3 border-b border-gray-50 flex items-center justify-between">
            <h3 class="text-xs font-bold text-gray-800 flex items-center gap-2">
              <Atom class="w-4 h-4 text-purple-500" /> 向量空间分布（t-SNE降维）
            </h3>
            <span class="text-[10px] text-gray-400">每个点代表一个文档分块</span>
          </div>
          <div ref="scatterRef" class="w-full h-64"></div>
        </div>

        <!-- Ranking Results -->
        <div class="bg-white border border-gray-100 rounded-xl shadow-sm overflow-hidden">
          <div class="px-5 py-3 border-b border-gray-50">
            <h3 class="text-xs font-bold text-gray-800">相似度排序结果</h3>
          </div>
          <div class="divide-y divide-gray-50">
            <div v-for="(item, i) in rankResults" :key="i"
              class="px-5 py-3 flex items-center gap-4 hover:bg-purple-50/30 transition-colors">
              <div :class="['w-8 h-8 rounded-lg flex items-center justify-center text-[11px] font-bold shrink-0',
                i < 3 ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-500']">{{ i + 1 }}</div>
              <div class="flex-1 min-w-0">
                <p class="text-xs font-medium text-gray-800 truncate">{{ item.title }}</p>
                <p class="text-[10px] text-gray-500 truncate">{{ item.source }} · {{ item.chunk }}</p>
              </div>
              <!-- Score bar -->
              <div class="w-32 shrink-0">
                <div class="flex items-center gap-2">
                  <div class="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div class="h-full rounded-full transition-all duration-700"
                      :class="item.cosine > 0.9 ? 'bg-purple-500' : item.cosine > 0.7 ? 'bg-indigo-400' : 'bg-gray-300'"
                      :style="{ width: (item.cosine * 100) + '%' }"></div>
                  </div>
                  <span class="text-[10px] font-mono font-bold w-10 text-right"
                    :class="item.cosine > 0.9 ? 'text-purple-600' : item.cosine > 0.7 ? 'text-indigo-500' : 'text-gray-500'">
                    {{ item.cosine.toFixed(3) }}
                  </span>
                </div>
              </div>
              <div class="text-[9px] text-gray-400 font-mono w-14 text-right shrink-0">{{ item.latency }}ms</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Config & Stats -->
      <div class="w-64 border-l border-gray-100 bg-gray-50/50 p-4 flex flex-col gap-3 shrink-0 overflow-y-auto custom-scrollbar">
        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <h4 class="text-[11px] font-bold text-gray-700 mb-3 flex items-center gap-1.5">
            <Settings class="w-3.5 h-3.5 text-purple-500" /> 检索参数
          </h4>
          <div class="space-y-3">
            <div>
              <label class="text-[10px] text-gray-500 block mb-1">Embedding模型</label>
              <select class="w-full px-2 py-1.5 text-[11px] border border-gray-200 rounded-lg bg-gray-50">
                <option>text-embedding-3-small</option>
                <option>text-embedding-3-large</option>
                <option>bge-large-zh-v1.5</option>
              </select>
            </div>
            <div>
              <label class="text-[10px] text-gray-500 block mb-1">向量维度</label>
              <span class="text-xs font-mono text-purple-600 font-bold">1536</span>
            </div>
            <div>
              <label class="text-[10px] text-gray-500 block mb-1">ANN算法</label>
              <select class="w-full px-2 py-1.5 text-[11px] border border-gray-200 rounded-lg bg-gray-50">
                <option>HNSW (默认)</option>
                <option>IVF-PQ</option>
                <option>Flat (暴力搜索)</option>
              </select>
            </div>
            <div>
              <label class="text-[10px] text-gray-500 block mb-1">Top-K</label>
              <input type="range" min="1" max="50" v-model="topK" class="w-full h-1 accent-purple-500" />
              <span class="text-[10px] text-gray-400 float-right">{{ topK }}</span>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <h4 class="text-[11px] font-bold text-gray-700 mb-3">检索统计</h4>
          <div class="space-y-2 text-[11px]">
            <div class="flex justify-between"><span class="text-gray-500">索引文档数</span><span class="font-mono text-gray-800">{{ rankStats.documentCount }}</span></div>
            <div class="flex justify-between"><span class="text-gray-500">向量总数</span><span class="font-mono text-gray-800">{{ rankStats.totalChunks }}</span></div>
            <div class="flex justify-between"><span class="text-gray-500">最近检索延迟</span><span class="font-mono text-purple-600">{{ rankStats.lastLatency }}</span></div>
            <div class="flex justify-between"><span class="text-gray-500">返回结果数</span><span class="font-mono text-emerald-600">{{ rankStats.resultCount }}</span></div>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm flex-1">
          <h4 class="text-[11px] font-bold text-gray-700 mb-3">相似度分布</h4>
          <div ref="histRef" class="w-full h-28"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ArrowUpDown, Zap, Loader2, Atom, Settings } from 'lucide-vue-next'

const queryText = ref('')
const loading = ref(false)
const topK = ref(10)
const scatterRef = ref(null)
const histRef = ref(null)
const scatterChart = ref(null)
const histChart = ref(null)
const totalChunks = ref(0)
const documentCount = ref(0)
const lastLatency = ref(0)

const rankResults = ref([])

const rankStats = computed(() => ({
  documentCount: documentCount.value,
  totalChunks: totalChunks.value,
  lastLatency: `${lastLatency.value}ms`,
  resultCount: rankResults.value.length
}))

const buildScatterData = () => {
  const points = rankResults.value.map((item, index) => ([
    (index % 4) * 1.6 + item.cosine * 2,
    Math.floor(index / 4) * 1.25 + (1 - item.cosine) * 4,
    12 + item.cosine * 18,
    1,
    item.title
  ]))
  points.push([1.5, 1.2, 28, 2, '查询向量'])
  return points
}

const buildHistogram = () => {
  const bins = [0, 0, 0, 0, 0]
  rankResults.value.forEach((item) => {
    const score = item.cosine
    if (score < 0.6) bins[0] += 1
    else if (score < 0.7) bins[1] += 1
    else if (score < 0.8) bins[2] += 1
    else if (score < 0.9) bins[3] += 1
    else bins[4] += 1
  })
  return bins
}

const initScatter = () => {
  if (!scatterRef.value) return
  scatterChart.value = scatterChart.value || echarts.init(scatterRef.value)
  scatterChart.value.setOption({
    tooltip: { textStyle: { fontSize: 10 }, formatter: p => p.data[3] === 2 ? '查询向量' : p.data[4] || `匹配结果 (Top ${rankResults.value.length})` },
    grid: { top: 10, bottom: 25, left: 30, right: 10 },
    xAxis: { axisLabel: { fontSize: 9 }, splitLine: { lineStyle: { color: '#f3f4f6' } } },
    yAxis: { axisLabel: { fontSize: 9 }, splitLine: { lineStyle: { color: '#f3f4f6' } } },
    series: [{
      type: 'scatter', data: buildScatterData(),
      symbolSize: d => d[2],
      itemStyle: { color: d => d[3] === 2 ? '#ef4444' : d[3] === 1 ? '#8b5cf6' : '#d1d5db', opacity: d => d[3] === 0 ? 0.4 : 0.9 }
    }]
  })
}

const initHist = () => {
  if (!histRef.value) return
  histChart.value = histChart.value || echarts.init(histRef.value)
  histChart.value.setOption({
    grid: { top: 5, bottom: 20, left: 5, right: 5, containLabel: false },
    xAxis: { type: 'category', data: ['0.5-0.6', '0.6-0.7', '0.7-0.8', '0.8-0.9', '0.9-1.0'], axisLabel: { fontSize: 8 }, axisLine: { show: false }, axisTick: { show: false } },
    yAxis: { show: false },
    series: [{
      type: 'bar',
      data: buildHistogram().map((value, index) => ({
        value,
        itemStyle: {
          color: ['#d1d5db', '#a5b4fc', '#818cf8', '#7c3aed', '#6d28d9'][index],
          borderRadius: [3, 3, 0, 0]
        }
      })),
      barWidth: '55%'
    }]
  })
}

const loadRankStats = async () => {
  try {
    const token = localStorage.getItem('access_token')
    const [statsResp, indexedResp] = await Promise.all([
      fetch('/api/rag/stats', { headers: { 'Authorization': `Bearer ${token}` } }),
      fetch('/api/rag/indexed', { headers: { 'Authorization': `Bearer ${token}` } })
    ])
    const statsData = await statsResp.json()
    const indexedData = await indexedResp.json()
    totalChunks.value = statsData.total_chunks || 0
    documentCount.value = (indexedData.sources || []).length
  } catch (error) {
    console.error('加载排序页统计失败', error)
  }
}

const runRank = async () => {
  if (!queryText.value.trim()) return
  loading.value = true
  try {
    const token = localStorage.getItem('access_token')
    const resp = await fetch('/api/rag/search', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: queryText.value.trim(),
        top_k: topK.value,
        score_threshold: 0,
        sort_by: 'score_desc'
      })
    })
    const data = await resp.json()
    if (!resp.ok) {
      throw new Error(data.detail || '向量检索失败')
    }
    lastLatency.value = data.elapsed_ms || 0
    rankResults.value = (data.results || []).map((item) => ({
      title: `${item.source} · 第${item.page_number}页`,
      source: item.source,
      chunk: `chunk_${String(item.chunk_index).padStart(3, '0')}`,
      cosine: Number(item.score || 0),
      latency: data.elapsed_ms || 0
    }))
    await nextTick()
    initScatter()
    initHist()
  } catch (error) {
    console.error('向量排序检索失败', error)
    rankResults.value = []
    lastLatency.value = 0
    await nextTick()
    initScatter()
    initHist()
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadRankStats()
  nextTick(() => { initScatter(); initHist() })
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }
</style>
