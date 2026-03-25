<template>
  <div class="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
    <div class="flex items-center gap-2 mb-4">
      <div class="p-2 rounded-lg bg-indigo-50">
        <GitCompare class="w-4 h-4 text-indigo-500" />
      </div>
      <h3 class="text-sm font-bold text-gray-900">{{ data.title }}</h3>
    </div>
    <div class="space-y-3">
      <div 
        v-for="(item, idx) in data.items" :key="idx"
        class="flex items-center gap-4 p-3 rounded-xl bg-gray-50/50"
      >
        <div class="flex-1 min-w-0">
          <div class="text-sm font-medium text-gray-700">{{ item.label }}</div>
        </div>
        <div class="text-right shrink-0 w-24">
          <div class="text-sm font-bold text-gray-900">{{ item.company_value }}</div>
          <div class="text-[10px] text-gray-400">{{ data.company || '公司' }}</div>
        </div>
        <div class="w-px h-8 bg-gray-200"></div>
        <div class="text-right shrink-0 w-24">
          <div class="text-sm font-bold text-gray-500">{{ item.industry_value }}</div>
          <div class="text-[10px] text-gray-400">{{ data.benchmark || '行业均值' }}</div>
        </div>
        <div class="shrink-0 w-16 text-right">
          <span 
            :class="deviationClass(item.deviation)"
            class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium"
          >
            {{ item.deviation }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { GitCompare } from 'lucide-vue-next'

defineProps({ data: Object })

const deviationClass = (val) => {
  if (!val) return 'bg-gray-50 text-gray-600'
  const str = String(val)
  if (str.startsWith('+')) return 'bg-emerald-50 text-emerald-700'
  if (str.startsWith('-')) return 'bg-rose-50 text-rose-700'
  return 'bg-gray-50 text-gray-600'
}
</script>
