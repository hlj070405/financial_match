<template>
  <div class="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm flex flex-col min-h-0">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-bold text-gray-900 flex items-center gap-2">
        <RadarIcon class="w-4 h-4 text-orange-500" />
        {{ data.title }}
      </h3>
    </div>
    <div ref="chartEl" class="flex-1 w-full min-h-[260px]"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as echarts from 'echarts'
import { Radar as RadarIcon } from 'lucide-vue-next'

const props = defineProps({ data: Object })
const chartEl = ref(null)
let chart = null

const COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b']

const render = () => {
  if (!chartEl.value) return
  if (chart) chart.dispose()
  chart = echarts.init(chartEl.value)

  const indicators = (props.data.indicators || []).map(name => ({
    name,
    max: props.data.max || 100
  }))

  // Support single array or multiple series
  let seriesData = []
  if (props.data.series && Array.isArray(props.data.series)) {
    seriesData = props.data.series.map((s, i) => ({
      value: s.data,
      name: s.name,
      areaStyle: { color: COLORS[i % COLORS.length] + '33' },
      lineStyle: { color: COLORS[i % COLORS.length], width: 2, type: i === 0 ? 'solid' : 'dashed' },
      itemStyle: { color: COLORS[i % COLORS.length] },
      symbol: i === 0 ? 'circle' : 'none',
      symbolSize: 6
    }))
  } else if (props.data.data && Array.isArray(props.data.data)) {
    seriesData = [{
      value: props.data.data,
      name: props.data.title || '评分',
      areaStyle: { color: 'rgba(59, 130, 246, 0.2)' },
      lineStyle: { color: '#3b82f6', width: 2 },
      itemStyle: { color: '#3b82f6' },
      symbol: 'circle',
      symbolSize: 6
    }]
  }

  chart.setOption({
    tooltip: {
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#f3f4f6',
      borderWidth: 1,
      textStyle: { color: '#1f2937', fontSize: 12 },
      extraCssText: 'box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); border-radius: 8px;'
    },
    legend: {
      data: seriesData.map(s => s.name),
      bottom: 0,
      icon: 'circle',
      textStyle: { fontSize: 12, color: '#6b7280' }
    },
    radar: {
      indicator: indicators,
      radius: '60%',
      center: ['50%', '48%'],
      splitArea: { show: true, areaStyle: { color: ['#f9fafb', '#ffffff'] } },
      axisLine: { lineStyle: { color: '#e5e7eb' } },
      splitLine: { lineStyle: { color: '#e5e7eb' } },
      axisName: { color: '#6b7280', fontSize: 11 }
    },
    series: [{ type: 'radar', data: seriesData }]
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
