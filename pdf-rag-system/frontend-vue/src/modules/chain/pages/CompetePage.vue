<template>
  <div class="h-full flex flex-col">
    <!-- Hero -->
    <div class="relative overflow-hidden bg-gradient-to-br from-indigo-50 via-white to-violet-50 border-b border-gray-100">
      <div class="absolute inset-0 opacity-20">
        <div class="absolute top-3 left-16 w-48 h-48 bg-indigo-200 rounded-full blur-3xl animate-pulse"></div>
        <div class="absolute bottom-0 right-10 w-40 h-40 bg-violet-200 rounded-full blur-3xl animate-pulse" style="animation-delay:1s"></div>
      </div>
      <div class="relative px-6 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-md shadow-indigo-500/20 shrink-0">
              <Target class="w-4.5 h-4.5 text-white" />
            </div>
            <div>
              <h1 class="text-base font-bold text-gray-900">竞争格局对比</h1>
              <p class="text-[11px] text-gray-500 mt-0.5">行业竞争态势分析，市场份额与核心能力雷达对比</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <select v-model="selectedIndustry" @change="loadCompete"
              class="px-3 py-2 text-xs border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500/20">
              <option v-for="ind in industries" :key="ind" :value="ind">{{ ind }}</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <div class="flex-1 flex min-h-0">
      <!-- Main -->
      <div class="flex-1 overflow-y-auto p-5 space-y-4 custom-scrollbar">
        <!-- Market Share -->
        <div class="grid grid-cols-2 gap-4">
          <div class="bg-white border border-gray-100 rounded-xl shadow-sm p-5">
            <h3 class="text-xs font-bold text-gray-800 flex items-center gap-2 mb-3">
              <PieChart class="w-4 h-4 text-indigo-500" /> 市场份额分布
            </h3>
            <div ref="shareRef" class="w-full h-52"></div>
          </div>
          <div class="bg-white border border-gray-100 rounded-xl shadow-sm p-5">
            <h3 class="text-xs font-bold text-gray-800 flex items-center gap-2 mb-3">
              <RadarIcon class="w-4 h-4 text-violet-500" /> 综合能力雷达
            </h3>
            <div ref="radarRef" class="w-full h-52"></div>
          </div>
        </div>

        <!-- Trend -->
        <div class="bg-white border border-gray-100 rounded-xl shadow-sm overflow-hidden">
          <div class="px-5 py-3 border-b border-gray-50">
            <h3 class="text-xs font-bold text-gray-800">市场份额变化趋势</h3>
          </div>
          <div ref="trendRef" class="w-full h-48"></div>
        </div>

        <!-- Company Comparison Table -->
        <div class="bg-white border border-gray-100 rounded-xl shadow-sm overflow-hidden">
          <div class="px-5 py-3 bg-gray-50 border-b border-gray-100">
            <h3 class="text-xs font-bold text-gray-800">龙头企业对比</h3>
          </div>
          <table class="w-full text-xs">
            <thead>
              <tr class="border-b border-gray-100">
                <th class="px-4 py-2.5 text-left font-bold text-gray-700">企业</th>
                <th class="px-4 py-2.5 text-center font-bold text-gray-700">市占率</th>
                <th class="px-4 py-2.5 text-center font-bold text-gray-700">营收(亿)</th>
                <th class="px-4 py-2.5 text-center font-bold text-gray-700">增速</th>
                <th class="px-4 py-2.5 text-center font-bold text-gray-700">毛利率</th>
                <th class="px-4 py-2.5 text-center font-bold text-gray-700">研发占比</th>
                <th class="px-4 py-2.5 text-center font-bold text-gray-700">竞争力</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="co in companies" :key="co.name" class="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
                <td class="px-4 py-2.5">
                  <div class="flex items-center gap-2">
                    <div class="w-2 h-2 rounded-full" :style="{ background: co.color }"></div>
                    <span class="font-medium text-gray-700">{{ co.name }}</span>
                  </div>
                </td>
                <td class="px-4 py-2.5 text-center font-mono font-bold text-gray-800">{{ co.share }}%</td>
                <td class="px-4 py-2.5 text-center font-mono text-gray-600">{{ co.revenue }}</td>
                <td class="px-4 py-2.5 text-center">
                  <span :class="['font-mono', co.growth > 0 ? 'text-rose-600' : 'text-emerald-600']">
                    {{ co.growth > 0 ? '+' : '' }}{{ co.growth }}%
                  </span>
                </td>
                <td class="px-4 py-2.5 text-center font-mono text-gray-600">{{ co.margin }}%</td>
                <td class="px-4 py-2.5 text-center font-mono text-gray-600">{{ co.rnd }}%</td>
                <td class="px-4 py-2.5 text-center">
                  <div class="flex items-center justify-center gap-0.5">
                    <div v-for="s in 5" :key="s" :class="['w-2.5 h-1.5 rounded-sm', s <= co.strength ? 'bg-indigo-500' : 'bg-gray-200']"></div>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Right: Porter's Five Forces -->
      <div class="w-64 border-l border-gray-100 bg-gray-50/50 p-4 flex flex-col gap-3 shrink-0 overflow-y-auto custom-scrollbar">
        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <h4 class="text-[11px] font-bold text-gray-700 flex items-center gap-1.5 mb-3">
            <Shield class="w-3.5 h-3.5 text-indigo-500" /> 波特五力分析
          </h4>
          <div class="space-y-2.5">
            <div v-for="force in porterForces" :key="force.name">
              <div class="flex items-center justify-between mb-1">
                <span class="text-[10px] text-gray-600">{{ force.name }}</span>
                <span :class="['text-[9px] font-bold px-1.5 py-0.5 rounded',
                  force.level === '强' ? 'bg-rose-50 text-rose-600' : force.level === '中' ? 'bg-amber-50 text-amber-600' : 'bg-emerald-50 text-emerald-600']">{{ force.level }}</span>
              </div>
              <div class="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div class="h-full rounded-full transition-all duration-1000"
                  :class="force.score > 70 ? 'bg-rose-500' : force.score > 40 ? 'bg-amber-500' : 'bg-emerald-500'"
                  :style="{ width: force.score + '%' }"></div>
              </div>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm flex-1">
          <h4 class="text-[11px] font-bold text-gray-700 flex items-center gap-1.5 mb-3">
            <Lightbulb class="w-3.5 h-3.5 text-amber-500" /> 竞争要点
          </h4>
          <div class="space-y-2">
            <div v-for="point in keyPoints" :key="point" class="flex items-start gap-2">
              <div class="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-1 shrink-0"></div>
              <p class="text-[10px] text-gray-600 leading-relaxed">{{ point }}</p>
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
import { Target, PieChart, Radar as RadarIcon, Shield, Lightbulb } from 'lucide-vue-next'

const shareRef = ref(null)
const radarRef = ref(null)
const trendRef = ref(null)
const selectedIndustry = ref('动力电池')
const industries = ['动力电池', '新能源汽车', '半导体', '光伏组件', '白酒']

const companies = ref([
  { name: '宁德时代', share: 36.8, revenue: 4009, growth: 22.0, margin: 22.9, rnd: 6.5, strength: 5, color: '#6366f1' },
  { name: '比亚迪电池', share: 16.2, revenue: 1120, growth: 45.3, margin: 18.5, rnd: 5.8, strength: 4, color: '#8b5cf6' },
  { name: 'LG新能源', share: 13.5, revenue: 980, growth: 12.1, margin: 15.2, rnd: 7.2, strength: 4, color: '#a78bfa' },
  { name: '中创新航', share: 7.8, revenue: 420, growth: 68.5, margin: 14.8, rnd: 8.1, strength: 3, color: '#c4b5fd' },
  { name: '国轩高科', share: 5.2, revenue: 316, growth: 35.2, margin: 16.1, rnd: 6.9, strength: 3, color: '#ddd6fe' }
])

const porterForces = [
  { name: '供应商议价能力', level: '中', score: 55 },
  { name: '买方议价能力', level: '强', score: 72 },
  { name: '新进入者威胁', level: '弱', score: 25 },
  { name: '替代品威胁', level: '弱', score: 30 },
  { name: '行业内竞争', level: '强', score: 80 }
]

const keyPoints = [
  '宁德时代以36.8%份额稳居龙头，技术壁垒和规模优势显著',
  '比亚迪垂直整合模式带来成本优势，增速行业领先',
  '二线厂商通过差异化（快充、固态）寻求突破',
  '行业CR5达79.5%，格局趋于稳定但仍有洗牌风险',
  '海外市场成为新增长极，全球化布局是关键竞争力'
]

const initCharts = () => {
  nextTick(() => {
    if (shareRef.value) {
      const chart = echarts.init(shareRef.value)
      chart.setOption({
        tooltip: { textStyle: { fontSize: 10 } },
        series: [{
          type: 'pie', radius: ['30%', '65%'], center: ['50%', '50%'],
          label: { fontSize: 9, formatter: '{b}\n{d}%' },
          itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
          emphasis: { scaleSize: 8 },
          data: [
            ...companies.value.map(c => ({ value: c.share, name: c.name, itemStyle: { color: c.color } })),
            { value: 20.5, name: '其他', itemStyle: { color: '#e5e7eb' } }
          ]
        }]
      })
    }
    if (radarRef.value) {
      const chart = echarts.init(radarRef.value)
      chart.setOption({
        legend: { data: companies.value.slice(0, 3).map(c => c.name), bottom: 0, textStyle: { fontSize: 9 } },
        radar: {
          indicator: [{ name: '市占率', max: 50 }, { name: '增速', max: 80 }, { name: '毛利率', max: 30 }, { name: '研发', max: 10 }, { name: '品牌力', max: 100 }],
          axisName: { color: '#6b7280', fontSize: 9 }, shape: 'polygon',
          splitArea: { areaStyle: { color: ['#f5f3ff', '#ede9fe', '#ddd6fe'].reverse() } }
        },
        series: [{
          type: 'radar',
          data: [
            { value: [36.8, 22, 22.9, 6.5, 95], name: '宁德时代', lineStyle: { color: '#6366f1', width: 2 }, areaStyle: { color: '#6366f120' }, itemStyle: { color: '#6366f1' } },
            { value: [16.2, 45.3, 18.5, 5.8, 85], name: '比亚迪电池', lineStyle: { color: '#8b5cf6', width: 2 }, areaStyle: { color: '#8b5cf620' }, itemStyle: { color: '#8b5cf6' } },
            { value: [13.5, 12.1, 15.2, 7.2, 75], name: 'LG新能源', lineStyle: { color: '#a78bfa', width: 2 }, areaStyle: { color: '#a78bfa20' }, itemStyle: { color: '#a78bfa' } }
          ]
        }]
      })
    }
    if (trendRef.value) {
      const chart = echarts.init(trendRef.value)
      const years = ['2020', '2021', '2022', '2023', '2024E']
      chart.setOption({
        tooltip: { trigger: 'axis', textStyle: { fontSize: 10 } },
        legend: { data: companies.value.slice(0, 4).map(c => c.name), bottom: 5, textStyle: { fontSize: 9 } },
        grid: { top: 10, bottom: 40, left: 45, right: 15 },
        xAxis: { type: 'category', data: years, axisLabel: { fontSize: 9 } },
        yAxis: { type: 'value', axisLabel: { fontSize: 9, formatter: '{value}%' }, max: 50, splitLine: { lineStyle: { color: '#f3f4f6' } } },
        series: [
          { name: '宁德时代', type: 'line', data: [25, 32, 35, 36, 36.8], smooth: true, symbol: 'circle', symbolSize: 5, lineStyle: { width: 2.5, color: '#6366f1' }, itemStyle: { color: '#6366f1' } },
          { name: '比亚迪电池', type: 'line', data: [6, 8, 12, 14.5, 16.2], smooth: true, symbol: 'circle', symbolSize: 5, lineStyle: { width: 2, color: '#8b5cf6' }, itemStyle: { color: '#8b5cf6' } },
          { name: 'LG新能源', type: 'line', data: [22, 20, 16, 14, 13.5], smooth: true, symbol: 'circle', symbolSize: 5, lineStyle: { width: 2, color: '#a78bfa' }, itemStyle: { color: '#a78bfa' } },
          { name: '中创新航', type: 'line', data: [1, 2, 4, 6, 7.8], smooth: true, symbol: 'circle', symbolSize: 5, lineStyle: { width: 2, color: '#c4b5fd' }, itemStyle: { color: '#c4b5fd' } }
        ]
      })
    }
  })
}

const loadCompete = () => initCharts()
onMounted(() => initCharts())
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }
</style>
