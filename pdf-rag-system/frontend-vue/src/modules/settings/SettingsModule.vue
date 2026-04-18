<template>
  <div class="h-full overflow-y-auto bg-gray-50 p-6">
    <div class="max-w-3xl mx-auto">
      <!-- Header -->
      <div class="mb-6">
        <h2 class="text-xl font-bold text-gray-900">功能模块设置</h2>
        <p class="text-sm text-gray-500 mt-1">
          当前身份：<span class="font-medium text-gray-700">{{ currentRoleName }}</span>
          <button @click="goRoleSelect" class="ml-2 text-blue-600 hover:text-blue-800 text-xs underline">切换身份</button>
        </p>
        <p class="text-xs text-gray-400 mt-1">勾选模块启用/关闭，点击展开可调整子功能</p>
      </div>

      <!-- Modules -->
      <div class="space-y-2">
          <div
            v-for="mod in ALL_MODULES"
            :key="mod.id"
            class="bg-white rounded-xl border transition-all duration-200"
            :class="isModuleEnabled(mod.id) ? 'border-blue-200 shadow-sm' : 'border-gray-100'"
          >
            <!-- Module header row -->
            <div class="flex items-center gap-3 px-4 py-3 cursor-pointer" @click="toggleModule(mod.id)">
              <div 
                class="w-[18px] h-[18px] rounded border-2 flex items-center justify-center transition-colors shrink-0"
                :class="isModuleEnabled(mod.id) ? 'bg-blue-600 border-blue-600' : 'border-gray-300 bg-white'"
              >
                <svg v-if="isModuleEnabled(mod.id)" class="w-2.5 h-2.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/>
                </svg>
              </div>
              <component :is="mod.icon" class="w-4 h-4 text-gray-400 shrink-0" />
              <span class="text-[13px] font-medium text-gray-900 flex-1">{{ mod.title }}</span>
              <span class="text-[10px] text-gray-400">{{ mod.features.length }} 个子功能</span>
              <button 
                @click.stop="toggleExpand(mod.id)"
                class="text-gray-400 hover:text-gray-600 transition-colors p-0.5"
              >
                <svg 
                  class="w-4 h-4 transition-transform duration-200" 
                  :class="{ 'rotate-180': isExpanded(mod.id) }"
                  fill="none" stroke="currentColor" viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                </svg>
              </button>
            </div>

            <!-- Expandable features -->
            <div v-if="isExpanded(mod.id)" class="border-t border-gray-100 px-4 py-2.5 space-y-1">
              <div
                v-for="feat in mod.features"
                :key="feat.id"
                class="flex items-start gap-3 py-2 px-2 rounded-lg transition-colors hover:bg-gray-50"
              >
                <div class="mt-0.5">
                  <button
                    @click="toggleFeature(feat.id)"
                    class="w-4 h-4 rounded border flex items-center justify-center transition-colors"
                    :class="isFeatureEnabled(feat.id) ? 'bg-blue-600 border-blue-600' : 'border-gray-300 bg-white hover:border-gray-400'"
                  >
                    <svg v-if="isFeatureEnabled(feat.id)" class="w-2.5 h-2.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/>
                    </svg>
                  </button>
                </div>
                <div class="flex-1 min-w-0">
                  <div class="text-[12px] font-medium text-gray-800">{{ feat.name }}</div>
                  <div class="text-[11px] text-gray-500 leading-relaxed mt-0.5">{{ feat.desc }}</div>
                </div>
              </div>
            </div>
          </div>
      </div>

      <!-- Save -->
      <div class="flex items-center gap-3 pt-2 pb-8">
        <button
          @click="saveSettings"
          class="px-5 py-2 bg-gray-900 text-white text-[13px] font-medium rounded-lg hover:bg-gray-800 transition-colors shadow-md shadow-gray-900/10"
        >
          保存设置
        </button>
        <button
          @click="resetToPreset"
          class="px-5 py-2 bg-white text-gray-700 text-[13px] font-medium rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
        >
          恢复身份预设
        </button>
        <Transition name="fade">
          <span v-if="showSaved" class="text-[13px] text-emerald-600 font-medium">已保存</span>
        </Transition>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { 
  ALL_MODULES, ROLES, 
  getEnabledModules, saveEnabledModules,
  getEnabledFeatures, saveEnabledFeatures, getDefaultFeaturesForRole,
  getUserRole 
} from '../../config/modules.js'

const emit = defineEmits(['modules-changed'])
const router = useRouter()

const enabledModuleIds = ref([])
const enabledFeatureIds = ref([])
const expandedModules = ref(new Set())
const showSaved = ref(false)

const currentRoleId = computed(() => getUserRole())

const currentRoleName = computed(() => {
  const roleId = currentRoleId.value
  if (!roleId || !ROLES[roleId]) return '未选择'
  return ROLES[roleId].name
})

const isModuleEnabled = (id) => enabledModuleIds.value.includes(id)
const isFeatureEnabled = (id) => enabledFeatureIds.value.includes(id)
const isExpanded = (id) => expandedModules.value.has(id)

const toggleModule = (id) => {
  const idx = enabledModuleIds.value.indexOf(id)
  if (idx >= 0) {
    enabledModuleIds.value.splice(idx, 1)
  } else {
    enabledModuleIds.value.push(id)
  }
}

const toggleFeature = (id) => {
  const idx = enabledFeatureIds.value.indexOf(id)
  if (idx >= 0) {
    enabledFeatureIds.value.splice(idx, 1)
  } else {
    enabledFeatureIds.value.push(id)
  }
}

const toggleExpand = (id) => {
  if (expandedModules.value.has(id)) {
    expandedModules.value.delete(id)
  } else {
    expandedModules.value.add(id)
  }
}

const saveSettings = () => {
  saveEnabledModules([...enabledModuleIds.value])
  saveEnabledFeatures([...enabledFeatureIds.value])
  showSaved.value = true
  emit('modules-changed', [...enabledModuleIds.value])
  setTimeout(() => { showSaved.value = false }, 2000)
}

const resetToPreset = () => {
  const roleId = getUserRole()
  if (roleId && ROLES[roleId]) {
    enabledModuleIds.value = [...ROLES[roleId].defaultModules]
    enabledFeatureIds.value = [...getDefaultFeaturesForRole(roleId)]
  }
}

const goRoleSelect = () => {
  router.push('/role-select')
}

onMounted(() => {
  const savedMods = getEnabledModules()
  const savedFeats = getEnabledFeatures()
  const roleId = getUserRole()

  if (savedMods) {
    enabledModuleIds.value = savedMods
  } else if (roleId && ROLES[roleId]) {
    enabledModuleIds.value = [...ROLES[roleId].defaultModules]
  } else {
    enabledModuleIds.value = ALL_MODULES.slice(0, 5).map(m => m.id)
  }

  if (savedFeats) {
    enabledFeatureIds.value = savedFeats
  } else {
    enabledFeatureIds.value = [...getDefaultFeaturesForRole(roleId)]
  }
})
</script>

<style scoped>
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
