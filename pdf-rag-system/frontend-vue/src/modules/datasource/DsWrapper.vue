<template>
  <div class="h-full w-full">
    <div v-if="showTabs" class="bg-white border-b border-gray-100 px-6 py-2.5 flex items-center justify-between shrink-0">
      <div class="flex items-center gap-2">
        <div class="p-2 rounded-xl bg-gray-100">
          <Database class="w-4 h-4 text-gray-600" />
        </div>
        <span class="text-sm font-bold text-gray-900">数据源管理</span>
      </div>
      <div class="flex items-center gap-1 bg-gray-50 rounded-xl p-1 border border-gray-100">
        <button v-for="feat in features" :key="feat.id" @click="switchTo(feat.id)"
          :class="['px-3.5 py-1.5 text-xs font-medium rounded-lg transition-all duration-200 whitespace-nowrap',
            currentFeature === feat.id ? 'bg-gray-900 text-white shadow-sm' : 'text-gray-500 hover:text-gray-800 hover:bg-white/60']"
        >{{ feat.name }}</button>
      </div>
    </div>
    <div :class="['w-full overflow-hidden', showTabs ? 'h-[calc(100%-52px)]' : 'h-full']">
      <Transition :name="transitionName" mode="out-in">
        <component :is="currentComponent" :key="currentFeature" />
      </Transition>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Database } from 'lucide-vue-next'
import { ALL_MODULES } from '../../config/modules.js'
import UploadPage from './pages/UploadPage_naive.vue'
import BatchPage from './pages/BatchPage.vue'
import MultiSourcePage from './pages/MultiSourcePage.vue'

const props = defineProps({ activeFeature: { type: String, default: '' } })
const moduleDef = ALL_MODULES.find(m => m.id === 'datasource')
const features = moduleDef?.features || []
const featureMap = { 'ds_upload': UploadPage, 'ds_batch': BatchPage, 'ds_multi': MultiSourcePage }
const currentFeature = ref(props.activeFeature || 'ds_upload')
const transitionName = ref('page-slide-right')
let prevIndex = 0
const showTabs = computed(() => false)
const currentComponent = computed(() => featureMap[currentFeature.value] || UploadPage)
const switchTo = (id) => {
  const newIdx = features.findIndex(f => f.id === id)
  transitionName.value = newIdx > prevIndex ? 'page-slide-right' : 'page-slide-left'
  prevIndex = newIdx >= 0 ? newIdx : prevIndex
  currentFeature.value = id
}
watch(() => props.activeFeature, (val) => { if (val && val.startsWith('ds_') && val !== currentFeature.value) switchTo(val) })
</script>

<style scoped>
.page-slide-right-enter-active, .page-slide-right-leave-active { transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1); }
.page-slide-right-enter-from { opacity: 0; transform: translateX(20px); }
.page-slide-right-leave-to { opacity: 0; transform: translateX(-20px); }
.page-slide-left-enter-active, .page-slide-left-leave-active { transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1); }
.page-slide-left-enter-from { opacity: 0; transform: translateX(-20px); }
.page-slide-left-leave-to { opacity: 0; transform: translateX(20px); }
</style>
