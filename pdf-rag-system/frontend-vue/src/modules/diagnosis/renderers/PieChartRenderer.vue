<template>
  <div class="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm flex flex-col min-h-0">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-bold text-gray-900 flex items-center gap-2">
        <PieChartIcon class="w-4 h-4 text-violet-500" />
        {{ data.title }}
      </h3>
    </div>
    <div ref="chartEl" class="flex-1 w-full min-h-[260px]"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as echarts from 'echarts'
import { PieChart as PieChartIcon } from 'lucide-vue-next'

const props = defineProps({ data: Object })
const chartEl = ref(null)
let chart = null

const COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#ec4899', '#84cc16']

const render = () => {
  if (!chartEl.value) return
  if (chart) chart.dispose()
  chart = echarts.init(chartEl.value)

  const pieData = (props.data.data || []).map((d, i) => ({
    value: d.value,
    name: d.name,
    itemStyle: { color: COLORS[i % COLORS.length] }
  }))

  chart.setOption({
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#f3f4f6',
      borderWidth: 1,
      textStyle: { color: '#1f2937', fontSize: 12 },
      extraCssText: 'box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); border-radius: 8px;'
    },
    legend: {
      orient: 'vertical',
      right: '0%',
      top: 'center',
      icon: 'circle',
      textStyle: { fontSize: 12, color: '#6b7280' },
      itemGap: 14
    },
    series: [{
      type: 'pie',
      radius: ['45%', '75%'],
      center: ['35%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { show: false },
      emphasis: {
        label: { show: true, fontSize: 14, fontWeight: 'bold', color: '#1f2937' },
        scale: true,
        scaleSize: 8
      },
      data: pieData
    }]
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
