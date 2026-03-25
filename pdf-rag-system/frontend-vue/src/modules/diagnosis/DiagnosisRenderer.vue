<template>
  <div class="space-y-6">
    <template v-for="(comp, idx) in components" :key="idx">
      <MetricCards v-if="comp.type === 'metric_cards'" :data="comp" />
      <LineChartRenderer v-else-if="comp.type === 'line_chart'" :data="comp" />
      <BarChartRenderer v-else-if="comp.type === 'bar_chart'" :data="comp" />
      <PieChartRenderer v-else-if="comp.type === 'pie_chart'" :data="comp" />
      <RadarChartRenderer v-else-if="comp.type === 'radar_chart'" :data="comp" />
      <TableRenderer v-else-if="comp.type === 'table'" :data="comp" />
      <TextInsight v-else-if="comp.type === 'text_insight'" :data="comp" />
      <ComparisonRenderer v-else-if="comp.type === 'comparison'" :data="comp" />
      <!-- 未知类型降级为文字卡片 -->
      <div v-else class="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
        <p class="text-sm text-gray-500">未知组件类型: {{ comp.type }}</p>
        <pre class="text-xs text-gray-400 mt-2 overflow-auto">{{ JSON.stringify(comp, null, 2) }}</pre>
      </div>
    </template>
  </div>
</template>

<script setup>
import MetricCards from './renderers/MetricCards.vue'
import LineChartRenderer from './renderers/LineChartRenderer.vue'
import BarChartRenderer from './renderers/BarChartRenderer.vue'
import PieChartRenderer from './renderers/PieChartRenderer.vue'
import RadarChartRenderer from './renderers/RadarChartRenderer.vue'
import TableRenderer from './renderers/TableRenderer.vue'
import TextInsight from './renderers/TextInsight.vue'
import ComparisonRenderer from './renderers/ComparisonRenderer.vue'

defineProps({
  components: {
    type: Array,
    default: () => []
  }
})
</script>
