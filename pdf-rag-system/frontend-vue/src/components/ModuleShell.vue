<template>
  <div class="h-full flex flex-col font-sans overflow-hidden">
    <!-- Module Header -->
    <div class="bg-white border-b border-gray-100 px-6 py-4 shrink-0">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="p-2.5 rounded-xl" :style="{ backgroundColor: iconBgColor }">
            <component :is="icon" class="w-5 h-5" :style="{ color: iconColor }" />
          </div>
          <div>
            <h2 class="text-lg font-bold text-gray-900 leading-tight">{{ title }}</h2>
            <p class="text-xs text-gray-400 mt-0.5">{{ subtitle }}</p>
          </div>
        </div>
        <!-- Feature Tabs -->
        <div v-if="features.length > 1" class="flex items-center gap-1 bg-gray-50 rounded-xl p-1 border border-gray-100">
          <button
            v-for="feat in features"
            :key="feat.id"
            @click="switchFeature(feat.id)"
            :class="[
              'px-3.5 py-1.5 text-xs font-medium rounded-lg transition-all duration-200 relative overflow-hidden whitespace-nowrap',
              activeFeatureId === feat.id
                ? 'bg-gray-900 text-white shadow-sm'
                : 'text-gray-500 hover:text-gray-800 hover:bg-white/60'
            ]"
          >
            {{ feat.name }}
          </button>
        </div>
        <!-- Slot: extra header actions -->
        <slot name="header-actions" />
      </div>
    </div>

    <!-- Sub-page Content with Transition -->
    <div class="flex-1 overflow-hidden relative">
      <Transition :name="transitionName" mode="out-in">
        <div :key="activeFeatureId" class="absolute inset-0 overflow-y-auto custom-scrollbar">
          <slot :activeFeature="activeFeatureId" />
        </div>
      </Transition>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  icon: { type: [Object, Function], required: true },
  iconBgColor: { type: String, default: '#f5f3ff' },
  iconColor: { type: String, default: '#7c3aed' },
  features: { type: Array, default: () => [] },
  activeFeature: { type: String, default: '' }
})

const emit = defineEmits(['update:activeFeature'])

const activeFeatureId = ref(props.activeFeature || (props.features[0]?.id ?? ''))
const transitionName = ref('page-slide-right')
let prevIndex = 0

watch(() => props.activeFeature, (val) => {
  if (val && val !== activeFeatureId.value) {
    const newIdx = props.features.findIndex(f => f.id === val)
    transitionName.value = newIdx > prevIndex ? 'page-slide-right' : 'page-slide-left'
    prevIndex = newIdx >= 0 ? newIdx : prevIndex
    activeFeatureId.value = val
  }
})

const switchFeature = (id) => {
  const newIdx = props.features.findIndex(f => f.id === id)
  transitionName.value = newIdx > prevIndex ? 'page-slide-right' : 'page-slide-left'
  prevIndex = newIdx >= 0 ? newIdx : prevIndex
  activeFeatureId.value = id
  emit('update:activeFeature', id)
}
</script>

<style scoped>
/* Slide Right (new page enters from right) */
.page-slide-right-enter-active,
.page-slide-right-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.page-slide-right-enter-from {
  opacity: 0;
  transform: translateX(30px);
}
.page-slide-right-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

/* Slide Left (new page enters from left) */
.page-slide-left-enter-active,
.page-slide-left-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.page-slide-left-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}
.page-slide-left-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #d1d5db; }
</style>
