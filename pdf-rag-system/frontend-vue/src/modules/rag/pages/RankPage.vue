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
            <div class="flex justify-between"><span class="text-gray-500">索引文档数</span><span class="font-mono text-gray-800">2,847</span></div>
            <div class="flex justify-between"><span class="text-gray-500">向量总数</span><span class="font-mono text-gray-800">18,523</span></div>
            <div class="flex justify-between"><span class="text-gray-500">平均检索延迟</span><span class="font-mono text-purple-600">23ms</span></div>
            <div class="flex justify-between"><span class="text-gray-500">召回率@10</span><span class="font-mono text-emerald-600">94.2%</span></div>
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
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ArrowUpDown, Zap, Loader2, Atom, Settings } from 'lucide-vue-next'

const queryText = ref('')
const loading = ref(false)
const topK = ref(10)
const scatterRef = ref(null)
const histRef = ref(null)

const rankResults = ref([
  { title: '比亚迪2023年年报 - 盈利能力分析', source: '年报.pdf', chunk: 'chunk_042', cosine: 0.956, latency: 18 },
  { title: '新能源汽车行业毛利率对比', source: '行业研究.pdf', chunk: 'chunk_015', cosine: 0.923, latency: 21 },
  { title: '动力电池成本结构分析', source: '电池报告.pdf', chunk: 'chunk_088', cosine: 0.891, latency: 19 },
  { title: '整车企业财务指标汇总表', source: '数据汇总.xlsx', chunk: 'chunk_003', cosine: 0.867, latency: 22 },
  { title: '碳酸锂价格与电池成本关系', source: '供应链.pdf', chunk: 'chunk_051', cosine: 0.845, latency: 20 },
  { title: '特斯拉 vs 比亚迪盈利模式', source: '竞争分析.pdf', chunk: 'chunk_027', cosine: 0.812, latency: 24 },
  { title: '新能源补贴退坡影响评估', source: '政策分析.pdf', chunk: 'chunk_064', cosine: 0.778, latency: 23 },
  { title: '光伏与新能源车协同效应', source: '跨行业.pdf', chunk: 'chunk_012', cosine: 0.734, latency: 26 }
])

const initScatter = () => {
  if (!scatterRef.value) return
  const chart = echarts.init(scatterRef.value)
  const data = []
  for (let i = 0; i < 80; i++) {
    data.push([
      (Math.random() - 0.5) * 10 + (i < 8 ? 3 : 0),
      (Math.random() - 0.5) * 10 + (i < 8 ? 2 : 0),
      i < 8 ? 20 : 8,
      i < 8 ? 1 : 0
    ])
  }
  data.push([3, 2, 30, 2]) // query point
  chart.setOption({
    tooltip: { textStyle: { fontSize: 10 }, formatter: p => p.data[3] === 2 ? '查询向量' : p.data[3] === 1 ? `匹配结果 (Top ${rankResults.value.length})` : '文档向量' },
    grid: { top: 10, bottom: 25, left: 30, right: 10 },
    xAxis: { axisLabel: { fontSize: 9 }, splitLine: { lineStyle: { color: '#f3f4f6' } } },
    yAxis: { axisLabel: { fontSize: 9 }, splitLine: { lineStyle: { color: '#f3f4f6' } } },
    series: [{
      type: 'scatter', data,
      symbolSize: d => d[2],
      itemStyle: { color: d => d[3] === 2 ? '#ef4444' : d[3] === 1 ? '#8b5cf6' : '#d1d5db', opacity: d => d[3] === 0 ? 0.4 : 0.9 }
    }]
  })
}

const initHist = () => {
  if (!histRef.value) return
  const chart = echarts.init(histRef.value)
  chart.setOption({
    grid: { top: 5, bottom: 20, left: 5, right: 5, containLabel: false },
    xAxis: { type: 'category', data: ['0.5-0.6', '0.6-0.7', '0.7-0.8', '0.8-0.9', '0.9-1.0'], axisLabel: { fontSize: 8 }, axisLine: { show: false }, axisTick: { show: false } },
    yAxis: { show: false },
    series: [{ type: 'bar', data: [
      { value: 3, itemStyle: { color: '#d1d5db', borderRadius: [3, 3, 0, 0] } },
      { value: 8, itemStyle: { color: '#a5b4fc', borderRadius: [3, 3, 0, 0] } },
      { value: 12, itemStyle: { color: '#818cf8', borderRadius: [3, 3, 0, 0] } },
      { value: 5, itemStyle: { color: '#7c3aed', borderRadius: [3, 3, 0, 0] } },
      { value: 2, itemStyle: { color: '#6d28d9', borderRadius: [3, 3, 0, 0] } }
    ], barWidth: '55%' }]
  })
}

const runRank = async () => {
  if (!queryText.value.trim()) return
  loading.value = true
  await new Promise(r => setTimeout(r, 600))
  loading.value = false
}

onMounted(() => { nextTick(() => { initScatter(); initHist() }) })
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }
</style>
