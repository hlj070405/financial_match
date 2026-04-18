<template>
  <aside class="pf-sidebar w-[240px] bg-white border-r border-gray-100 flex flex-col shrink-0 z-20">
    <!-- Brand -->
    <div class="h-14 flex items-center px-4 border-b border-gray-100/50">
      <div class="flex items-center gap-2.5">
        <div class="relative flex items-center justify-center w-7 h-7 rounded-lg shadow-lg shrink-0"
             :class="brandBgClass" :style="brandBgStyle">
          <slot name="brand-icon">
            <svg class="w-4 h-4 text-white" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </slot>
        </div>
        <div>
          <h1 class="text-sm font-bold text-gray-900 leading-none">{{ brandName }}</h1>
          <p v-if="brandSubtitle" class="text-[9px] text-gray-400 font-medium tracking-wide mt-0.5">{{ brandSubtitle }}</p>
        </div>
      </div>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 px-3 py-3 overflow-y-auto pf-scrollbar space-y-0.5">
      <template v-for="item in modules" :key="item.id">
        <!-- Single-feature module: direct click -->
        <template v-if="!hasMultipleFeatures(item)">
          <button
            @click="onModuleClick(item)"
            class="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg transition-all duration-200 group relative overflow-hidden"
            :class="activeModule === item.id
              ? 'bg-gray-900 text-white shadow-sm shadow-gray-900/10'
              : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'"
          >
            <div
              class="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 bg-orange-500 rounded-r-full transition-all duration-300"
              :class="activeModule === item.id ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-full'"
            ></div>
            <component
              :is="item.icon"
              class="w-4 h-4 shrink-0 transition-colors"
              :class="activeModule === item.id ? 'text-orange-400' : 'text-gray-400 group-hover:text-gray-600'"
            />
            <span class="text-[13px] font-medium truncate">{{ item.title }}</span>
          </button>
        </template>

        <!-- Multi-feature module: expandable -->
        <template v-else>
          <button
            @click="toggleExpand(item.id)"
            class="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg transition-all duration-200 group"
            :class="activeModule === item.id
              ? 'bg-gray-50 text-gray-900'
              : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'"
          >
            <component
              :is="item.icon"
              class="w-4 h-4 shrink-0 transition-colors"
              :class="activeModule === item.id ? 'text-orange-500' : 'text-gray-400 group-hover:text-gray-600'"
            />
            <span class="text-[13px] font-medium truncate flex-1 text-left">{{ item.title }}</span>
            <svg
              class="w-3.5 h-3.5 text-gray-400 transition-transform duration-200 shrink-0"
              :class="{ 'rotate-180': isExpanded(item.id) }"
              fill="none" stroke="currentColor" viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
            </svg>
          </button>
          <!-- Sub-features -->
          <div v-if="isExpanded(item.id)" class="ml-4 mb-1 space-y-px">
            <button
              v-for="feat in item.features"
              :key="feat.id"
              @click="onFeatureClick(item.id, feat)"
              class="w-full flex items-center gap-2 py-[6px] px-3 rounded-lg text-[12px] transition-all duration-200 text-left"
              :class="activeFeatureId === feat.id
                ? 'bg-gray-900 text-white shadow-sm shadow-gray-900/10'
                : 'text-gray-500 hover:bg-gray-100 hover:text-gray-800'"
            >
              <div
                class="w-1 h-1 rounded-full shrink-0"
                :class="activeFeatureId === feat.id ? 'bg-orange-400' : 'bg-gray-300'"
              ></div>
              <span class="truncate">{{ feat.name }}</span>
            </button>
          </div>
        </template>
      </template>

      <!-- Divider before extra nav -->
      <div v-if="$slots['nav-extra']" class="mx-1 my-2 h-px bg-gradient-to-r from-transparent via-gray-200 to-transparent"></div>
      <slot name="nav-extra" />
    </nav>

    <!-- Status Panel (optional) -->
    <slot name="status">
      <div class="mx-3 mb-2 p-2.5 rounded-lg bg-gradient-to-br from-gray-900 to-gray-800 space-y-2 relative overflow-hidden shadow-sm">
        <div class="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-orange-500/0 via-orange-500/80 to-orange-500/0"></div>
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-1.5">
            <div class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse shadow-sm shadow-emerald-400/50"></div>
            <span class="text-[10px] font-medium text-gray-300">{{ statusLabel || 'AI Engine' }}</span>
          </div>
          <span class="text-[9px] font-mono text-emerald-400 bg-emerald-400/10 px-1.5 py-0.5 rounded border border-emerald-400/20">RUNNING</span>
        </div>
      </div>
    </slot>

    <!-- User Profile -->
    <div class="p-3 border-t border-gray-100 mt-auto">
      <div class="relative">
        <button
          @click="showUserMenu = !showUserMenu"
          class="w-full flex items-center gap-2.5 p-2 rounded-lg hover:bg-gray-50 transition-colors text-left group"
        >
          <div class="w-8 h-8 rounded-full bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center border border-gray-200 shrink-0">
            <slot name="user-avatar">
              <svg class="w-4 h-4 text-gray-500 group-hover:text-gray-700" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
            </slot>
          </div>
          <div class="flex-1 min-w-0">
            <div class="text-[13px] font-medium text-gray-900 truncate">{{ userName }}</div>
            <div v-if="userEmail" class="text-[11px] text-gray-500 truncate">{{ userEmail }}</div>
          </div>
          <svg class="w-3.5 h-3.5 text-gray-300 group-hover:text-gray-500 shrink-0 transition-transform duration-200"
               :class="{ 'rotate-90': showUserMenu }"
               viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="9 18 15 12 9 6"/>
          </svg>
        </button>

        <!-- User Menu Dropdown -->
        <div
          v-if="showUserMenu"
          class="absolute bottom-full left-0 w-full mb-2 bg-white border border-gray-100 rounded-lg shadow-xl shadow-gray-200/50 py-1 z-30 overflow-hidden"
        >
          <slot name="user-menu" :close="() => showUserMenu = false">
            <button
              @click="emit('logout'); showUserMenu = false"
              class="w-full flex items-center gap-2 px-3 py-2 text-[13px] text-red-600 hover:bg-red-50 transition-colors"
            >
              <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                <polyline points="16 17 21 12 16 7"/>
                <line x1="21" y1="12" x2="9" y2="12"/>
              </svg>
              <span>Logout</span>
            </button>
          </slot>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  modules: { type: Array, default: () => [] },
  activeModule: { type: String, default: '' },
  brandName: { type: String, default: 'Phantom Flow' },
  brandSubtitle: { type: String, default: '' },
  brandBgClass: { type: String, default: 'bg-gray-900 text-white shadow-gray-900/20' },
  brandBgStyle: { type: Object, default: () => ({}) },
  statusLabel: { type: String, default: '' },
  userName: { type: String, default: 'User' },
  userEmail: { type: String, default: '' },
})

const emit = defineEmits(['change-module', 'change-feature', 'logout'])

const showUserMenu = ref(false)
const expandedModules = ref(new Set())
const activeFeatureId = ref(null)

const hasMultipleFeatures = (item) => item.features && item.features.length > 1

const isExpanded = (id) => expandedModules.value.has(id)
const toggleExpand = (id) => {
  if (expandedModules.value.has(id)) {
    expandedModules.value.delete(id)
  } else {
    expandedModules.value.add(id)
  }
}

const onModuleClick = (item) => {
  emit('change-module', item.id)
  if (item.features && item.features.length === 1) {
    activeFeatureId.value = item.features[0].id
    emit('change-feature', item.id, item.features[0].id)
  }
}

const onFeatureClick = (moduleId, feat) => {
  activeFeatureId.value = feat.id
  emit('change-module', moduleId)
  emit('change-feature', moduleId, feat.id)
}
</script>

<style scoped>
.pf-scrollbar::-webkit-scrollbar { width: 4px; }
.pf-scrollbar::-webkit-scrollbar-track { background: transparent; }
.pf-scrollbar::-webkit-scrollbar-thumb { background: #f3f4f6; border-radius: 4px; }
.pf-scrollbar::-webkit-scrollbar-thumb:hover { background: #e5e7eb; }
</style>
