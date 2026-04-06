<template>
  <aside class="w-[240px] bg-white border-r border-gray-100 flex flex-col shrink-0 z-20">
    <!-- Brand -->
    <div class="h-14 flex items-center px-4 border-b border-gray-100/50">
      <div class="flex items-center gap-2.5">
        <div class="relative flex items-center justify-center w-7 h-7 rounded-lg bg-gray-900 text-white shadow-lg shadow-gray-900/20">
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <div>
          <h1 class="text-sm font-bold text-gray-900 leading-none">Phantom Flow</h1>
          <p class="text-[9px] text-gray-400 font-medium tracking-wide mt-0.5">幻流智能</p>
        </div>
      </div>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 px-3 py-3 overflow-y-auto custom-scrollbar space-y-0.5">
      <template v-for="item in visibleMenuItems" :key="item.id">
        <!-- Single-feature module: direct click, no expand -->
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

      <!-- Divider -->
      <div class="mx-1 my-2 h-px bg-gradient-to-r from-transparent via-gray-200 to-transparent"></div>

      <!-- Settings -->
      <button
        @click="$emit('change-module', 'settings')"
        class="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg transition-all duration-200 group relative overflow-hidden"
        :class="activeModule === 'settings'
          ? 'bg-gray-900 text-white shadow-sm shadow-gray-900/10'
          : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'"
      >
        <Settings class="w-4 h-4 shrink-0 transition-colors" :class="activeModule === 'settings' ? 'text-white' : 'text-gray-400 group-hover:text-gray-600'" />
        <span class="text-[13px] font-medium">功能设置</span>
      </button>
    </nav>

    <!-- System Monitor -->
    <div class="mx-3 mb-2 p-2.5 rounded-lg bg-gradient-to-br from-gray-900 to-gray-800 space-y-2 relative overflow-hidden shadow-sm">
      <div class="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-orange-500/0 via-orange-500/80 to-orange-500/0"></div>
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-1.5">
          <div class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse shadow-sm shadow-emerald-400/50"></div>
          <span class="text-[10px] font-medium text-gray-300">AI 引擎</span>
        </div>
        <span class="text-[9px] font-mono text-emerald-400 bg-emerald-400/10 px-1.5 py-0.5 rounded border border-emerald-400/20">RUNNING</span>
      </div>
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-1.5">
          <div class="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400/50"></div>
          <span class="text-[10px] font-medium text-gray-300">数据流</span>
        </div>
        <span class="text-[9px] font-mono text-emerald-400 bg-emerald-400/10 px-1.5 py-0.5 rounded border border-emerald-400/20">ONLINE</span>
      </div>
    </div>

    <!-- User Profile (Bottom) -->
    <div class="p-3 border-t border-gray-100 mt-auto">
      <div class="relative">
        <button
          @click="showUserMenu = !showUserMenu"
          class="w-full flex items-center gap-2.5 p-2 rounded-lg hover:bg-gray-50 transition-colors text-left group"
        >
          <div class="w-8 h-8 rounded-full bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center border border-gray-200 shrink-0">
            <User class="w-4 h-4 text-gray-500 group-hover:text-gray-700" />
          </div>
          <div class="flex-1 min-w-0">
            <div class="text-[13px] font-medium text-gray-900 truncate">{{ displayName }}</div>
            <div class="text-[11px] text-gray-500 truncate">{{ displayEmail }}</div>
          </div>
          <ChevronRight class="w-3.5 h-3.5 text-gray-300 group-hover:text-gray-500 shrink-0 transition-transform duration-200" :class="{ 'rotate-90': showUserMenu }" />
        </button>

        <!-- User Menu Dropdown -->
        <div
          v-if="showUserMenu"
          class="absolute bottom-full left-0 w-full mb-2 bg-white border border-gray-100 rounded-lg shadow-xl shadow-gray-200/50 py-1 z-30 overflow-hidden"
        >
          <button
            @click="$emit('change-module', 'settings'); showUserMenu = false"
            class="w-full flex items-center gap-2 px-3 py-2 text-[13px] text-gray-600 hover:bg-gray-50 hover:text-gray-900 transition-colors"
          >
            <Settings class="w-3.5 h-3.5" />
            <span>功能设置</span>
          </button>
          <div class="h-px bg-gray-100 my-0.5"></div>
          <button
            @click="$emit('logout')"
            class="w-full flex items-center gap-2 px-3 py-2 text-[13px] text-red-600 hover:bg-red-50 transition-colors"
          >
            <LogOut class="w-3.5 h-3.5" />
            <span>退出登录</span>
          </button>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed } from 'vue'
import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
import {
  User,
  ChevronRight,
  LogOut,
  Settings
} from 'lucide-vue-next'
import { ROLES, getUserRole, getActiveModuleDefinitions } from '../config/modules.js'

const cn = (...inputs) => twMerge(clsx(inputs))
const showUserMenu = ref(false)
const expandedModules = ref(new Set())
const activeFeatureId = ref(null)

const props = defineProps({
  activeModule: {
    type: String,
    default: 'chat'
  },
  menuItems: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['change-module', 'change-feature', 'logout'])

const visibleMenuItems = computed(() => {
  return props.menuItems.length > 0 ? props.menuItems : getActiveModuleDefinitions()
})

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

const currentRoleName = computed(() => {
  const roleId = getUserRole()
  if (!roleId || !ROLES[roleId]) return ''
  return ROLES[roleId].name
})

const displayName = computed(() => {
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    return user.full_name || user.username || 'User'
  } catch { return 'User' }
})

const displayEmail = computed(() => {
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    return user.email || ''
  } catch { return '' }
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #f3f4f6;
  border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #e5e7eb;
}
</style>
