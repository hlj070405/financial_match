<template>
  <div class="grid gap-4" :class="gridCols">
    <div 
      v-for="(item, idx) in data.items" :key="idx"
      class="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm hover:shadow-md transition-all group"
    >
      <div class="flex items-center justify-between mb-3">
        <span class="text-sm font-medium text-gray-500">{{ item.label }}</span>
        <div :class="iconBg(idx)" class="w-8 h-8 rounded-lg flex items-center justify-center">
          <component :is="iconFor(idx)" class="w-4 h-4" />
        </div>
      </div>
      <div class="flex items-baseline justify-between">
        <div class="text-2xl font-bold text-gray-900">{{ item.value }}</div>
        <div v-if="item.change" class="flex items-center text-xs font-medium bg-gray-50 px-2 py-1 rounded-full">
          <TrendingUp v-if="item.trend === 'up'" class="w-3 h-3 mr-1 text-emerald-500" />
          <TrendingDown v-else class="w-3 h-3 mr-1 text-rose-500" />
          <span :class="item.trend === 'up' ? 'text-emerald-600' : 'text-rose-600'">{{ item.change }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { TrendingUp, TrendingDown, DollarSign, Wallet, Percent, Scale, BarChart3, Activity } from 'lucide-vue-next'

const props = defineProps({ data: Object })

const icons = [DollarSign, Wallet, Percent, Scale, BarChart3, Activity]
const bgClasses = [
  'bg-blue-50 text-blue-600',
  'bg-emerald-50 text-emerald-600',
  'bg-violet-50 text-violet-600',
  'bg-orange-50 text-orange-600',
  'bg-rose-50 text-rose-600',
  'bg-cyan-50 text-cyan-600'
]

const iconFor = (idx) => icons[idx % icons.length]
const iconBg = (idx) => bgClasses[idx % bgClasses.length]

const gridCols = computed(() => {
  const len = props.data.items?.length || 0
  if (len <= 2) return 'grid-cols-2'
  if (len <= 3) return 'grid-cols-3'
  return 'grid-cols-4'
})
</script>
