<template>
  <div class="h-full flex flex-col">
    <!-- Hero -->
    <div class="relative overflow-hidden bg-gradient-to-br from-rose-50 via-white to-orange-50 border-b border-gray-100">
      <div class="absolute inset-0 opacity-20">
        <div class="absolute top-3 left-16 w-48 h-48 bg-rose-200 rounded-full blur-3xl animate-pulse"></div>
        <div class="absolute bottom-0 right-10 w-40 h-40 bg-orange-200 rounded-full blur-3xl animate-pulse" style="animation-delay: 1s;"></div>
      </div>
      <div class="relative px-6 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-rose-500 to-orange-600 flex items-center justify-center shadow-md shadow-rose-500/20 shrink-0">
              <ShieldAlert class="w-4.5 h-4.5 text-white" />
            </div>
            <div>
              <h1 class="text-base font-bold text-gray-900">风险预警评分</h1>
              <p class="text-[11px] text-gray-500 mt-0.5">基于财务数据的风险量化评分与预警，识别潜在财务危机</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <input v-model="companyInput" @keydown.enter="runRiskCheck" type="text" placeholder="输入公司名称..."
              class="px-3 py-2 text-xs border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-rose-500/20 focus:border-rose-400 w-40 transition-all" />
            <button @click="runRiskCheck" :disabled="loading"
              class="px-4 py-2 bg-rose-600 text-white text-xs font-medium rounded-lg hover:bg-rose-700 transition-colors disabled:opacity-50 flex items-center gap-1.5">
              <Loader2 v-if="loading" class="w-3.5 h-3.5 animate-spin" />
              <Search v-else class="w-3.5 h-3.5" />
              {{ loading ? '检测中...' : '风险检测' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto p-6 custom-scrollbar">
      <!-- Empty -->
      <div v-if="!loading && !result" class="flex items-center justify-center h-full">
        <div class="text-center max-w-sm">
          <div class="p-3 rounded-xl bg-rose-50 inline-block mb-3">
            <ShieldAlert class="w-10 h-10 text-rose-300" />
          </div>
          <h3 class="text-sm font-semibold text-gray-700 mb-1.5">输入公司名称进行风险检测</h3>
          <p class="text-xs text-gray-400 leading-relaxed mb-4">系统将从财务造假风险、偿债能力、经营风险等多维度进行量化评分</p>
          <div class="flex flex-wrap gap-2 justify-center">
            <button v-for="ex in examples" :key="ex" @click="companyInput = ex; runRiskCheck()"
              class="px-3 py-1.5 text-[11px] text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-rose-50 hover:border-rose-300 hover:text-rose-700 transition-all">{{ ex }}</button>
          </div>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex items-center justify-center h-full">
        <div class="text-center">
          <Loader2 class="w-8 h-8 animate-spin text-rose-500 mx-auto" />
          <p class="text-xs text-gray-500 mt-3">AI 正在量化风险因子...</p>
        </div>
      </div>

      <!-- Results -->
      <div v-if="result && !loading" class="max-w-5xl mx-auto space-y-5">
        <!-- Overall Score -->
        <div class="grid grid-cols-4 gap-4">
          <div class="col-span-1 bg-white border border-gray-100 rounded-xl p-5 shadow-sm flex flex-col items-center justify-center">
            <div ref="gaugeRef" class="w-full h-36"></div>
            <p class="text-xs font-bold text-gray-700 mt-1">综合风险评分</p>
            <p class="text-[10px] text-gray-400">{{ result.riskLevel }}</p>
          </div>
          <div class="col-span-3 grid grid-cols-3 gap-4">
            <div v-for="cat in result.categories" :key="cat.name"
              class="bg-white border rounded-xl p-4 shadow-sm transition-all hover:shadow-md"
              :class="cat.score > 70 ? 'border-rose-200' : cat.score > 40 ? 'border-amber-200' : 'border-emerald-200'">
              <div class="flex items-center justify-between mb-3">
                <h4 class="text-xs font-bold text-gray-800">{{ cat.name }}</h4>
                <span :class="[
                  'px-2 py-0.5 rounded-full text-[10px] font-bold',
                  cat.score > 70 ? 'bg-rose-100 text-rose-700' : cat.score > 40 ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'
                ]">{{ cat.score }}分</span>
              </div>
              <div class="w-full h-2 bg-gray-100 rounded-full overflow-hidden mb-2">
                <div class="h-full rounded-full transition-all duration-1000"
                  :class="cat.score > 70 ? 'bg-rose-500' : cat.score > 40 ? 'bg-amber-500' : 'bg-emerald-500'"
                  :style="{ width: cat.score + '%' }"></div>
              </div>
              <p class="text-[10px] text-gray-500 leading-relaxed">{{ cat.detail }}</p>
            </div>
          </div>
        </div>

        <!-- Risk Factors -->
        <div class="bg-white border border-gray-100 rounded-xl shadow-sm overflow-hidden">
          <div class="px-5 py-3 bg-gray-50 border-b border-gray-100">
            <h3 class="text-xs font-bold text-gray-800 flex items-center gap-2">
              <AlertTriangle class="w-3.5 h-3.5 text-amber-500" /> 风险因子明细
            </h3>
          </div>
          <div class="divide-y divide-gray-50">
            <div v-for="(f, i) in result.factors" :key="i" class="px-5 py-3 flex items-center gap-4 hover:bg-gray-50/50 transition-colors">
              <div :class="[
                'w-2 h-2 rounded-full shrink-0',
                f.level === 'high' ? 'bg-rose-500' : f.level === 'medium' ? 'bg-amber-500' : 'bg-emerald-500'
              ]"></div>
              <div class="flex-1 min-w-0">
                <p class="text-xs font-medium text-gray-800">{{ f.name }}</p>
                <p class="text-[10px] text-gray-500">{{ f.desc }}</p>
              </div>
              <span :class="[
                'px-2 py-0.5 rounded text-[10px] font-bold shrink-0',
                f.level === 'high' ? 'bg-rose-50 text-rose-600' : f.level === 'medium' ? 'bg-amber-50 text-amber-600' : 'bg-emerald-50 text-emerald-600'
              ]">{{ f.level === 'high' ? '高风险' : f.level === 'medium' ? '中风险' : '低风险' }}</span>
            </div>
          </div>
        </div>

        <!-- AI Summary -->
        <div class="bg-gradient-to-r from-gray-900 to-gray-800 rounded-xl p-5 text-white">
          <div class="flex items-center gap-2 mb-2">
            <Sparkles class="w-3.5 h-3.5 text-orange-400" />
            <span class="text-[10px] font-bold text-orange-300 uppercase tracking-wider">AI 风险研判</span>
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
import { ShieldAlert, Search, Loader2, Sparkles, AlertTriangle } from 'lucide-vue-next'

const companyInput = ref('')
const loading = ref(false)
const result = ref(null)
const gaugeRef = ref(null)
const examples = ['贵州茅台', '比亚迪', '恒大地产', '招商银行']

const mockResult = (company) => ({
  overallScore: 35,
  riskLevel: '风险可控',
  categories: [
    { name: '财务造假风险', score: 22, detail: 'Beneish M-Score为-2.8，低于阈值-1.78，财务造假概率极低' },
    { name: '偿债能力风险', score: 38, detail: '流动比率2.1，速动比率1.6，短期偿债能力良好' },
    { name: '经营持续风险', score: 28, detail: '经营现金流连续5年为正，营收复合增长率15.2%，经营稳健' },
    { name: '市场情绪风险', score: 45, detail: '近期负面舆情较少，但行业竞争加剧，市场关注度上升' },
    { name: '估值泡沫风险', score: 52, detail: '当前P/E为32.5x，高于行业均值25.1x，存在一定估值压力' },
    { name: '治理结构风险', score: 18, detail: '独立董事占比超50%，股权结构清晰，关联交易占比低' }
  ],
  factors: [
    { name: '估值偏高', desc: 'P/E高于行业均值29.5%，PB高于行业均值45.2%', level: 'medium' },
    { name: '行业竞争加剧', desc: '近半年行业新进入者增加，市场份额面临挤压', level: 'medium' },
    { name: '原材料价格波动', desc: '主要原材料价格近3月波动幅度达12.3%', level: 'low' },
    { name: '现金流充裕', desc: '经营现金流/净利润比率达1.35，现金质量优秀', level: 'low' },
    { name: '负债率健康', desc: '资产负债率21.3%，远低于行业均值45.6%', level: 'low' }
  ],
  aiSummary: `${company}整体风险评分35分（满分100，越低越安全），处于"风险可控"区间。主要关注点为估值偏高和行业竞争加剧，但公司财务基本面稳健、偿债能力充足、治理结构良好。建议关注估值回调机会，当前阶段不建议追高，可在P/E回落至28x以下时择机布局。`
})

const initGauge = (score) => {
  nextTick(() => {
    if (!gaugeRef.value) return
    const chart = echarts.init(gaugeRef.value)
    chart.setOption({
      series: [{
        type: 'gauge', startAngle: 200, endAngle: -20, min: 0, max: 100,
        progress: { show: true, width: 14, roundCap: true, itemStyle: { color: score > 70 ? '#f43f5e' : score > 40 ? '#f59e0b' : '#10b981' } },
        pointer: { show: false },
        axisLine: { lineStyle: { width: 14, color: [[1, '#f3f4f6']] } },
        axisTick: { show: false }, splitLine: { show: false }, axisLabel: { show: false }, title: { show: false },
        detail: { valueAnimation: true, offsetCenter: [0, '10%'], fontSize: 28, fontWeight: 'bold', color: score > 70 ? '#f43f5e' : score > 40 ? '#f59e0b' : '#10b981', formatter: '{value}' },
        data: [{ value: score }]
      }]
    })
  })
}

const runRiskCheck = async () => {
  if (!companyInput.value.trim()) return
  loading.value = true
  result.value = null
  try {
    await new Promise(r => setTimeout(r, 1200))
    result.value = mockResult(companyInput.value.trim())
    initGauge(result.value.overallScore)
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }
</style>
