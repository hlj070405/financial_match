<template>
  <div class="h-full flex flex-col">
    <!-- Hero -->
    <div class="relative overflow-hidden bg-gradient-to-br from-amber-50 via-white to-red-50 border-b border-gray-100">
      <div class="absolute inset-0 opacity-20">
        <div class="absolute top-3 left-16 w-48 h-48 bg-amber-200 rounded-full blur-3xl animate-pulse"></div>
        <div class="absolute bottom-0 right-10 w-40 h-40 bg-red-200 rounded-full blur-3xl animate-pulse" style="animation-delay:1s"></div>
      </div>
      <div class="relative px-6 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-amber-500 to-red-600 flex items-center justify-center shadow-md shadow-amber-500/20 shrink-0">
              <ShieldAlert class="w-4.5 h-4.5 text-white" />
            </div>
            <div>
              <h1 class="text-base font-bold text-gray-900">供应链风险评估</h1>
              <p class="text-[11px] text-gray-500 mt-0.5">供应链中断风险识别、影响评估与替代方案分析</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <input v-model="industry" @keydown.enter="assess" type="text" placeholder="输入行业/企业..."
              class="px-3 py-2 text-xs border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-amber-500/20 w-40 transition-all" />
            <button @click="assess" :disabled="loading"
              class="px-4 py-2 bg-amber-600 text-white text-xs font-medium rounded-lg hover:bg-amber-700 transition-colors disabled:opacity-50 flex items-center gap-1.5">
              <Loader2 v-if="loading" class="w-3.5 h-3.5 animate-spin" />
              <Search v-else class="w-3.5 h-3.5" />
              评估
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto p-5 custom-scrollbar">
      <!-- Empty -->
      <div v-if="!loading && !result" class="flex items-center justify-center h-full">
        <div class="text-center max-w-sm">
          <div class="p-3 rounded-xl bg-amber-50 inline-block mb-3">
            <ShieldAlert class="w-10 h-10 text-amber-300" />
          </div>
          <h3 class="text-sm font-semibold text-gray-700 mb-1.5">输入行业或企业名称</h3>
          <p class="text-xs text-gray-400 leading-relaxed mb-4">系统将分析供应链各环节的中断风险、地缘政治影响及替代方案</p>
          <div class="flex flex-wrap gap-2 justify-center">
            <button v-for="ex in examples" :key="ex" @click="industry = ex; assess()"
              class="px-3 py-1.5 text-[11px] text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-amber-50 hover:border-amber-300 hover:text-amber-700 transition-all">{{ ex }}</button>
          </div>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex items-center justify-center h-full">
        <div class="text-center">
          <Loader2 class="w-8 h-8 animate-spin text-amber-500 mx-auto" />
          <p class="text-xs text-gray-500 mt-3">正在评估供应链风险...</p>
        </div>
      </div>

      <!-- Results -->
      <div v-if="result && !loading" class="max-w-5xl mx-auto space-y-5">
        <!-- Overall Risk -->
        <div class="grid grid-cols-4 gap-4">
          <div v-for="card in result.overallCards" :key="card.label"
            :class="['bg-white border rounded-xl p-4 shadow-sm text-center', card.border]">
            <p class="text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-1">{{ card.label }}</p>
            <p :class="['text-xl font-bold font-mono', card.valueColor]">{{ card.value }}</p>
            <p class="text-[9px] text-gray-400 mt-0.5">{{ card.sub }}</p>
          </div>
        </div>

        <!-- Risk Matrix -->
        <div class="grid grid-cols-2 gap-4">
          <div class="bg-white border border-gray-100 rounded-xl shadow-sm p-5">
            <h3 class="text-xs font-bold text-gray-800 flex items-center gap-2 mb-3">
              <AlertTriangle class="w-4 h-4 text-amber-500" /> 风险热力矩阵
            </h3>
            <div ref="heatmapRef" class="w-full h-56"></div>
          </div>
          <div class="bg-white border border-gray-100 rounded-xl shadow-sm p-5">
            <h3 class="text-xs font-bold text-gray-800 flex items-center gap-2 mb-3">
              <MapPin class="w-4 h-4 text-blue-500" /> 地缘风险分布
            </h3>
            <div class="space-y-2">
              <div v-for="geo in result.geoRisks" :key="geo.region" class="flex items-center gap-3">
                <span class="text-xs text-gray-600 w-20 shrink-0">{{ geo.region }}</span>
                <div class="flex-1 h-4 bg-gray-100 rounded-full overflow-hidden relative">
                  <div class="h-full rounded-full transition-all duration-1000"
                    :class="geo.level > 70 ? 'bg-rose-500' : geo.level > 40 ? 'bg-amber-500' : 'bg-emerald-500'"
                    :style="{ width: geo.level + '%' }"></div>
                </div>
                <span :class="['text-[10px] font-bold w-8 text-right',
                  geo.level > 70 ? 'text-rose-600' : geo.level > 40 ? 'text-amber-600' : 'text-emerald-600']">{{ geo.level }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Risk Detail Table -->
        <div class="bg-white border border-gray-100 rounded-xl shadow-sm overflow-hidden">
          <div class="px-5 py-3 bg-gray-50 border-b border-gray-100">
            <h3 class="text-xs font-bold text-gray-800">供应链环节风险明细</h3>
          </div>
          <table class="w-full text-xs">
            <thead>
              <tr class="border-b border-gray-100">
                <th class="px-4 py-2.5 text-left font-bold text-gray-700">环节</th>
                <th class="px-4 py-2.5 text-center font-bold text-gray-700">风险等级</th>
                <th class="px-4 py-2.5 text-left font-bold text-gray-700">主要风险</th>
                <th class="px-4 py-2.5 text-left font-bold text-gray-700">替代方案</th>
                <th class="px-4 py-2.5 text-center font-bold text-gray-700">影响度</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(r, i) in result.risks" :key="i" class="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
                <td class="px-4 py-2.5 font-medium text-gray-700">{{ r.segment }}</td>
                <td class="px-4 py-2.5 text-center">
                  <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold',
                    r.level === '高' ? 'bg-rose-100 text-rose-700' : r.level === '中' ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700']">{{ r.level }}</span>
                </td>
                <td class="px-4 py-2.5 text-gray-600">{{ r.risk }}</td>
                <td class="px-4 py-2.5 text-gray-600">{{ r.alternative }}</td>
                <td class="px-4 py-2.5 text-center">
                  <div class="flex items-center justify-center gap-0.5">
                    <div v-for="s in 5" :key="s" :class="['w-2 h-2 rounded-full', s <= r.impact ? 'bg-amber-500' : 'bg-gray-200']"></div>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- AI Summary -->
        <div class="bg-gradient-to-r from-gray-900 to-gray-800 rounded-xl p-5 text-white">
          <div class="flex items-center gap-2 mb-2">
            <Sparkles class="w-3.5 h-3.5 text-amber-400" />
            <span class="text-[10px] font-bold text-amber-300 uppercase tracking-wider">AI 供应链研判</span>
          </div>
          <p class="text-xs text-gray-300 leading-relaxed">{{ result.aiSummary }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ShieldAlert, Search, Loader2, AlertTriangle, MapPin, Sparkles } from 'lucide-vue-next'

const industry = ref('')
const loading = ref(false)
const result = ref(null)
const heatmapRef = ref(null)
const examples = ['新能源汽车', '半导体', '光伏产业', '消费电子']

const mockResult = (name) => ({
  overallCards: [
    { label: '综合风险', value: '中等', sub: '评分 52/100', valueColor: 'text-amber-600', border: 'border-amber-200' },
    { label: '高风险环节', value: '3', sub: '需重点关注', valueColor: 'text-rose-600', border: 'border-rose-200' },
    { label: '供应商集中度', value: 'CR3 68%', sub: '集中度偏高', valueColor: 'text-orange-600', border: 'border-orange-200' },
    { label: '替代可行性', value: '良好', sub: '72%可替代', valueColor: 'text-emerald-600', border: 'border-emerald-200' }
  ],
  geoRisks: [
    { region: '东南亚', level: 45 },
    { region: '欧洲', level: 30 },
    { region: '北美', level: 25 },
    { region: '非洲', level: 72 },
    { region: '南美', level: 55 },
    { region: '中东', level: 60 }
  ],
  risks: [
    { segment: '锂矿开采', level: '高', risk: '产能集中于澳洲/南美，地缘风险大', alternative: '盐湖提锂、固态锂', impact: 5 },
    { segment: '正极材料', level: '中', risk: '镍钴价格波动，供应链较长', alternative: '磷酸铁锂替代三元', impact: 3 },
    { segment: '隔膜生产', level: '低', risk: '国产化率高，技术成熟', alternative: '多家供应商可选', impact: 2 },
    { segment: '电芯制造', level: '低', risk: '龙头产能充足，技术壁垒高', alternative: '二线厂商备份', impact: 2 },
    { segment: '半导体芯片', level: '高', risk: '高端芯片依赖进口，制裁风险', alternative: '国产替代加速中', impact: 5 },
    { segment: '稀土永磁', level: '高', risk: '资源集中度极高，出口管控', alternative: '减量设计/无稀土电机', impact: 4 }
  ],
  aiSummary: `${name}产业链综合供应链风险评分52分（满分100），处于中等风险水平。核心风险集中在上游原材料环节（锂矿、稀土）和关键芯片环节。建议企业采取多元化供应商策略、适度增加安全库存、加速国产替代验证。中长期来看，随着盐湖提锂技术成熟和国产芯片替代推进，供应链风险有望逐步下降。`
})

const initHeatmap = () => {
  if (!heatmapRef.value) return
  const chart = echarts.init(heatmapRef.value)
  const segments = ['锂矿', '正极', '隔膜', '电芯', '芯片', '稀土']
  const dimensions = ['中断概率', '影响程度', '恢复时间']
  const data = []
  segments.forEach((s, si) => {
    dimensions.forEach((d, di) => {
      data.push([di, si, Math.floor(Math.random() * 60 + 20)])
    })
  })
  chart.setOption({
    tooltip: { textStyle: { fontSize: 10 }, formatter: p => `${segments[p.data[1]]} - ${dimensions[p.data[0]]}: ${p.data[2]}` },
    grid: { top: 5, bottom: 30, left: 55, right: 10 },
    xAxis: { type: 'category', data: dimensions, axisLabel: { fontSize: 9 }, splitArea: { show: true } },
    yAxis: { type: 'category', data: segments, axisLabel: { fontSize: 9 }, splitArea: { show: true } },
    visualMap: { min: 0, max: 100, show: false, inRange: { color: ['#dcfce7', '#fef9c3', '#fecaca', '#fca5a5'] } },
    series: [{ type: 'heatmap', data, label: { show: true, fontSize: 10, color: '#374151' }, emphasis: { itemStyle: { shadowBlur: 10 } } }]
  })
}

const assess = async () => {
  if (!industry.value.trim()) return
  loading.value = true
  result.value = null
  try {
    await new Promise(r => setTimeout(r, 1200))
    result.value = mockResult(industry.value.trim())
    nextTick(() => initHeatmap())
  } finally { loading.value = false }
}
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }
</style>
