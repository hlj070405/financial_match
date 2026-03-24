<template>
  <div ref="chartRef" class="w-full h-96"></div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  chartData: Object
})

const chartRef = ref(null)
let chartInstance = null

const renderChart = () => {
  if (!chartRef.value || !props.chartData) return

  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  const option = {
    title: {
      text: props.chartData.title || '数据分析图表'
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: props.chartData.legend || []
    },
    xAxis: {
      type: 'category',
      data: props.chartData.xAxis || []
    },
    yAxis: {
      type: 'value'
    },
    series: props.chartData.series || []
  }

  chartInstance.setOption(option)
}

onMounted(() => {
  renderChart()
  
  window.addEventListener('resize', () => {
    chartInstance?.resize()
  })
})

watch(() => props.chartData, () => {
  renderChart()
}, { deep: true })
</script>
