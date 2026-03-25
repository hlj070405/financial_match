<template>
  <div class="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-bold text-gray-900 flex items-center gap-2">
        <Table2 class="w-4 h-4 text-cyan-500" />
        {{ data.title }}
      </h3>
    </div>
    <div class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr>
            <th 
              v-for="col in data.columns" :key="col"
              class="text-left px-4 py-3 bg-gray-50 text-gray-600 font-semibold first:rounded-tl-lg last:rounded-tr-lg border-b border-gray-100"
            >
              {{ col }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="(row, idx) in data.rows" :key="idx"
            class="hover:bg-gray-50/50 transition-colors"
          >
            <td 
              v-for="(cell, cidx) in row" :key="cidx"
              class="px-4 py-3 text-gray-700 border-b border-gray-50"
              :class="{ 'font-medium text-gray-900': cidx === 0 }"
            >
              <span v-if="isRiskTag(cell)" :class="riskTagClass(cell)" class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium">
                {{ cell }}
              </span>
              <span v-else>{{ cell }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { Table2 } from 'lucide-vue-next'

defineProps({ data: Object })

const riskKeywords = ['高', '危险', '警告', '异常', '低', '正常', '良好', '优秀']

const isRiskTag = (cell) => {
  if (typeof cell !== 'string') return false
  return riskKeywords.some(k => cell.includes(k)) || cell.includes('⚠') || cell.includes('🔴') || cell.includes('🟢') || cell.includes('🟡')
}

const riskTagClass = (cell) => {
  if (cell.includes('危险') || cell.includes('🔴') || cell.includes('高')) return 'bg-red-50 text-red-700'
  if (cell.includes('警告') || cell.includes('⚠') || cell.includes('🟡') || cell.includes('异常')) return 'bg-amber-50 text-amber-700'
  if (cell.includes('正常') || cell.includes('良好') || cell.includes('🟢') || cell.includes('优秀') || cell.includes('低')) return 'bg-emerald-50 text-emerald-700'
  return 'bg-gray-50 text-gray-700'
}
</script>
