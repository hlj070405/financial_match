<template>
  <div class="h-full flex flex-col">
    <!-- Hero -->
    <div class="relative overflow-hidden bg-gradient-to-br from-purple-50 via-white to-fuchsia-50 border-b border-gray-100">
      <div class="absolute inset-0 opacity-20">
        <div class="absolute top-5 right-20 w-64 h-64 bg-purple-200 rounded-full blur-3xl animate-pulse"></div>
        <div class="absolute bottom-0 left-10 w-48 h-48 bg-fuchsia-200 rounded-full blur-3xl animate-pulse" style="animation-delay: 1.5s;"></div>
      </div>
      <div class="relative px-6 py-4">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-purple-500 to-fuchsia-600 flex items-center justify-center shadow-md shadow-purple-500/20 shrink-0">
            <UserCircle class="w-4.5 h-4.5 text-white" />
          </div>
          <div>
            <h1 class="text-base font-bold text-gray-900">用户画像分析</h1>
            <p class="text-xs text-gray-500 mt-0.5 max-w-xl">智能分析您的投资偏好、风险承受能力与关注领域，提供个性化服务</p>
          </div>
        </div>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto p-8 custom-scrollbar">
      <div class="max-w-5xl mx-auto space-y-6">
        <!-- Profile Cards Grid -->
        <div class="grid grid-cols-3 gap-5">
          <div v-for="card in profileCards" :key="card.title"
            class="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm hover:shadow-md transition-all group relative overflow-hidden"
          >
            <div class="absolute top-0 left-0 w-full h-1 transition-all duration-300 opacity-0 group-hover:opacity-100"
              :class="card.barColor"></div>
            <div class="flex items-center gap-3 mb-4">
              <div class="w-10 h-10 rounded-xl flex items-center justify-center" :class="card.iconBg">
                <component :is="card.icon" class="w-5 h-5" :class="card.iconColor" />
              </div>
              <div>
                <h3 class="text-sm font-bold text-gray-900">{{ card.title }}</h3>
                <p class="text-[11px] text-gray-400">{{ card.subtitle }}</p>
              </div>
            </div>
            <div class="space-y-3">
              <div v-for="item in card.items" :key="item.label">
                <div class="flex items-center justify-between mb-1">
                  <span class="text-xs text-gray-500">{{ item.label }}</span>
                  <span class="text-xs font-bold" :class="item.valueColor || 'text-gray-900'">{{ item.value }}</span>
                </div>
                <div v-if="item.progress !== undefined" class="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div class="h-full rounded-full transition-all duration-1000" :class="item.progressColor || 'bg-purple-500'"
                    :style="{ width: item.progress + '%' }"></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Radar Chart + AI Summary -->
        <div class="grid grid-cols-2 gap-5">
          <div class="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
            <h3 class="text-sm font-bold text-gray-900 flex items-center gap-2 mb-4">
              <Radar class="w-4 h-4 text-purple-500" />
              投资能力雷达
            </h3>
            <div ref="radarChartRef" class="w-full h-64"></div>
          </div>

          <div class="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
            <h3 class="text-sm font-bold text-gray-900 flex items-center gap-2 mb-4">
              <Brain class="w-4 h-4 text-fuchsia-500" />
              AI 个性化建议
            </h3>
            <div class="space-y-3">
              <div v-for="(tip, i) in aiTips" :key="i"
                class="flex items-start gap-3 p-3 bg-gray-50 rounded-xl hover:bg-purple-50 transition-colors"
              >
                <div class="w-6 h-6 rounded-full bg-gradient-to-br from-purple-500 to-fuchsia-500 flex items-center justify-center shrink-0 text-white text-[10px] font-bold">{{ i + 1 }}</div>
                <p class="text-xs text-gray-700 leading-relaxed">{{ tip }}</p>
              </div>
            </div>
            <button
              @click="refreshProfile"
              :disabled="loading"
              class="mt-4 w-full py-2.5 bg-gradient-to-r from-purple-600 to-fuchsia-600 text-white text-xs font-medium rounded-xl hover:from-purple-700 hover:to-fuchsia-700 transition-all shadow-lg shadow-purple-500/20 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              <RefreshCw :class="['w-3.5 h-3.5', loading ? 'animate-spin' : '']" />
              {{ loading ? '分析中...' : '重新分析画像' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import {
  UserCircle, Radar, Brain, RefreshCw,
  TrendingUp, Shield, Target, Clock, BarChart3, Layers
} from 'lucide-vue-next'

const loading = ref(false)
const radarChartRef = ref(null)
let radarChart = null

const profileCards = ref([
  {
    title: '风险偏好',
    subtitle: '基于历史行为评估',
    icon: Shield,
    iconBg: 'bg-blue-50',
    iconColor: 'text-blue-600',
    barColor: 'bg-blue-500',
    items: [
      { label: '风险承受等级', value: '稳健型', valueColor: 'text-blue-600' },
      { label: '波动容忍度', value: '68%', progress: 68, progressColor: 'bg-blue-500' },
      { label: '最大回撤容忍', value: '15%', progress: 30, progressColor: 'bg-blue-400' }
    ]
  },
  {
    title: '投资偏好',
    subtitle: '关注领域与风格',
    icon: TrendingUp,
    iconBg: 'bg-emerald-50',
    iconColor: 'text-emerald-600',
    barColor: 'bg-emerald-500',
    items: [
      { label: '偏好板块', value: '新能源 / 科技', valueColor: 'text-emerald-600' },
      { label: '投资周期', value: '中长期', progress: 75, progressColor: 'bg-emerald-500' },
      { label: '分散度评分', value: '72分', progress: 72, progressColor: 'bg-emerald-400' }
    ]
  },
  {
    title: '分析深度',
    subtitle: '专业程度偏好',
    icon: Layers,
    iconBg: 'bg-purple-50',
    iconColor: 'text-purple-600',
    barColor: 'bg-purple-500',
    items: [
      { label: '专业程度', value: '进阶', valueColor: 'text-purple-600' },
      { label: '数据敏感度', value: '高', progress: 85, progressColor: 'bg-purple-500' },
      { label: '术语接受度', value: '中等', progress: 55, progressColor: 'bg-purple-400' }
    ]
  }
])

const aiTips = ref([
  '根据您的稳健型风险偏好，建议重点关注低波动蓝筹股和高股息率标的。',
  '您对新能源板块关注较多，建议搭配防御性板块（如公用事业）平衡风险。',
  '中长期投资风格适合使用基本面分析，建议多关注财报诊断模块的多维对标功能。',
  '当前市场波动加大，建议适当降低仓位并关注舆情分析模块的热点追踪。'
])

const initRadarChart = () => {
  if (!radarChartRef.value) return
  radarChart = echarts.init(radarChartRef.value)
  radarChart.setOption({
    color: ['#a855f7'],
    radar: {
      indicator: [
        { name: '风险意识', max: 100 },
        { name: '市场敏锐', max: 100 },
        { name: '数据分析', max: 100 },
        { name: '行业认知', max: 100 },
        { name: '择时能力', max: 100 },
        { name: '资产配置', max: 100 }
      ],
      shape: 'polygon',
      splitArea: { show: true, areaStyle: { color: ['#faf5ff', '#f3e8ff', '#e9d5ff', '#d8b4fe'].reverse() } },
      axisName: { color: '#6b7280', fontSize: 11 }
    },
    series: [{
      type: 'radar',
      data: [{
        value: [78, 65, 82, 70, 55, 73],
        name: '投资能力',
        areaStyle: { color: 'rgba(168, 85, 247, 0.15)' },
        lineStyle: { color: '#a855f7', width: 2 },
        itemStyle: { color: '#a855f7' }
      }]
    }]
  })
}

const refreshProfile = () => {
  loading.value = true
  setTimeout(() => { loading.value = false }, 2000)
}

onMounted(() => {
  nextTick(() => initRadarChart())
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }
</style>
