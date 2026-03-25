<template>
  <div class="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm flex flex-col min-h-0">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-bold text-gray-900 flex items-center gap-2">
        <BarChart2 class="w-4 h-4 text-emerald-500" />
        {{ data.title }}
      </h3>
    </div>
    <div ref="chartEl" class="flex-1 w-full min-h-[260px]"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as echarts from 'echarts'
import { BarChart2 } from 'lucide-vue-next'

const props = defineProps({ data: Object })
const chartEl = ref(null)
let chart = null

const COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4']

const render = () => {
  if (!chartEl.value) return
  if (chart) chart.dispose()
  chart = echarts.init(chartEl.value)

  const series = (props.data.series || []).map((s, i) => ({
    name: s.name,
    type: 'bar',
    barWidth: 14,
    barGap: '20%',
    data: s.data,
    itemStyle: { color: COLORS[i % COLORS.length], borderRadius: [4, 4, 0, 0] }
  }))

  chart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#f3f4f6',
      borderWidth: 1,
      textStyle: { color: '#1f2937', fontSize: 12 },
      extraCssText: 'box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); border-radius: 8px;'
    },
    legend: {
      data: series.map(s => s.name),
      bottom: 0,
      icon: 'circle',
      textStyle: { fontSize: 12, color: '#6b7280' }
    },
    grid: { left: '2%', right: '4%', bottom: '12%', top: '5%', containLabel: true },
    xAxis: {
      type: 'category',
      data: props.data.x_axis || [],
      axisLine: { lineStyle: { color: '#f3f4f6' } },
      axisTick: { show: false },
      axisLabel: { color: '#9ca3af', fontSize: 11, margin: 12 }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } },
      axisLabel: { color: '#9ca3af', fontSize: 11 }
    },
    series
  })
}

const handleResize = () => chart?.resize()

onMounted(() => {
  render()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
})

watch(() => props.data, render, { deep: true })
</script>
