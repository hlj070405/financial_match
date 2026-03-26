<template>
  <aside class="w-[260px] bg-white border-r border-gray-100 flex flex-col shrink-0 z-20 transition-all duration-300">
    <!-- Brand -->
    <div class="h-14 flex items-center px-5 border-b border-gray-100/50">
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

    <!-- Role Badge -->
    <div v-if="currentRoleName" class="mx-3 mt-2.5 mb-0.5 px-2.5 py-1.5 rounded-lg bg-gray-50 border border-gray-100 flex items-center justify-between">
      <div class="flex items-center gap-1.5 min-w-0">
        <div class="w-1.5 h-1.5 rounded-full bg-blue-500 shrink-0"></div>
        <span class="text-[11px] font-medium text-gray-600 truncate">{{ currentRoleName }}</span>
      </div>
      <button 
        @click="$emit('change-module', 'settings')"
        class="text-[10px] text-gray-400 hover:text-gray-600 shrink-0 ml-2"
      >切换</button>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 px-3 py-2 overflow-y-auto custom-scrollbar">
      <template v-for="group in groupedMenuItems" :key="group.label">
        <div 
          class="mx-1 mt-4 mb-1.5 px-2.5 py-[6px] rounded-lg cursor-pointer select-none flex items-center gap-2 transition-colors relative overflow-hidden"
          :style="{ backgroundColor: groupBgColor(group), color: groupTextColor(group) }"
          @click="toggleGroup(group)"
        >
          <div class="absolute left-0 top-0 bottom-0 w-[3px] rounded-r-sm" :style="{ backgroundColor: groupTextColor(group) }"></div>
          <svg class="w-3.5 h-3.5 transition-transform duration-200" :class="{ '-rotate-90': isGroupCollapsed(group) }" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7"/></svg>
          <span class="text-[12px] font-bold tracking-wide">{{ group.label }}</span>
        </div>
        <div v-for="item in group.items" :key="item.id" v-show="!isGroupCollapsed(group)">
          <!-- Module title row - always normal style, never black -->
          <div
            class="w-full flex items-center gap-2.5 ml-2 px-2.5 py-[7px] rounded-lg transition-all duration-200 group relative overflow-hidden cursor-pointer text-gray-600 hover:bg-gray-50 hover:text-gray-900"
            :class="{ 'bg-gray-50': isSidebarExpanded(item.id) || activeModule === item.id }"
          >
            <div class="flex items-center gap-2.5 flex-1 min-w-0" @click="$emit('change-module', item.id)">
              <component 
                :is="item.icon" 
                :class="cn(
                  'w-4 h-4 transition-colors relative z-10 shrink-0',
                  activeModule === item.id ? 'text-orange-500' : 'text-gray-400 group-hover:text-gray-600'
                )" 
              />
              <span 
                class="text-[13px] font-medium relative z-10 truncate"
                :class="activeModule === item.id ? 'text-gray-900' : ''"
              >{{ item.title }}</span>
            </div>
            <button
              v-if="item.features && item.features.length"
              @click.stop="toggleSidebarExpand(item.id)"
              class="relative z-10 shrink-0 p-0.5 rounded transition-colors hover:bg-gray-200"
            >
              <svg 
                class="w-3.5 h-3.5 transition-transform duration-200 text-gray-400"
                :class="{ 'rotate-180': isSidebarExpanded(item.id) }"
                fill="none" stroke="currentColor" viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
              </svg>
            </button>
          </div>
          <!-- Sub-features - these get the dark highlight -->
          <div v-if="isSidebarExpanded(item.id) && item.features" class="mb-1 space-y-px">
            <div
              v-for="feat in item.features"
              :key="feat.id"
              @click="onFeatureClick(item.id, feat)"
              class="flex items-center gap-2 py-[6px] pl-9 pr-2 rounded-lg text-[12px] transition-all duration-200 cursor-pointer"
              :class="activeFeatureId === feat.id
                ? 'bg-gray-900 text-white shadow-sm shadow-gray-900/10'
                : isFeatureAvailableForRole(feat)
                  ? 'text-gray-600 hover:bg-gray-100 hover:text-gray-800'
                  : 'text-gray-400 hover:bg-gray-50'"
            >
              <div 
                class="w-1.5 h-1.5 rounded-full shrink-0"
                :class="activeFeatureId === feat.id 
                  ? 'bg-orange-400'
                  : isFeatureAvailableForRole(feat) ? 'bg-emerald-400' : 'bg-gray-300'"
              ></div>
              <span class="truncate">{{ feat.name }}</span>
              <span v-if="!isFeatureAvailableForRole(feat)" class="text-[9px] shrink-0 ml-auto" :class="activeFeatureId === feat.id ? 'text-amber-300' : 'text-amber-500'">面向{{ feat.targetLabel }}</span>
            </div>
          </div>
        </div>
      </template>

      <!-- Divider -->
      <div class="mx-2 my-3 h-px bg-gradient-to-r from-transparent via-gray-200 to-transparent"></div>

      <!-- System group -->
      <button
        @click="$emit('change-module', 'settings')"
        :class="cn(
          'w-full flex items-center gap-2.5 mx-1 px-3 py-2 rounded-lg transition-all duration-200 group relative overflow-hidden border',
          activeModule === 'settings'
            ? 'bg-gray-900 text-white shadow-sm shadow-gray-900/10 border-gray-900'
            : 'bg-gray-50 text-gray-600 hover:bg-gray-100 hover:text-gray-900 border-gray-150'
        )"
        style="width: calc(100% - 8px)"
      >
        <div 
          class="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 bg-orange-500 rounded-r-full transition-all duration-300"
          :class="activeModule === 'settings' ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-full'"
        ></div>
        <Settings :class="cn('w-4 h-4 transition-colors relative z-10 shrink-0', activeModule === 'settings' ? 'text-white' : 'text-gray-400 group-hover:text-gray-600')" />
        <span class="text-[13px] font-medium relative z-10 flex-1 text-left">功能设置</span>
        <ChevronRight :class="cn('w-3.5 h-3.5 relative z-10 shrink-0', activeModule === 'settings' ? 'text-white/50' : 'text-gray-300')" />
      </button>

      <!-- System Monitor -->
      <div class="mx-1 mt-3 p-3 rounded-lg bg-gradient-to-br from-gray-900 to-gray-800 space-y-2.5 relative overflow-hidden shadow-sm">
        <div class="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-orange-500/0 via-orange-500/80 to-orange-500/0"></div>
        <div class="flex items-center gap-1.5 mb-1">
          <svg class="w-3 h-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>
          <span class="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">系统监控</span>
        </div>
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-1.5">
            <div class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse shadow-sm shadow-emerald-400/50"></div>
            <span class="text-[11px] font-medium text-gray-300">AI 引擎</span>
          </div>
          <span class="text-[9px] font-mono text-emerald-400 bg-emerald-400/10 px-1.5 py-0.5 rounded border border-emerald-400/20">RUNNING</span>
        </div>
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-1.5">
            <div class="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400/50"></div>
            <span class="text-[11px] font-medium text-gray-300">数据流</span>
          </div>
          <span class="text-[9px] font-mono text-emerald-400 bg-emerald-400/10 px-1.5 py-0.5 rounded border border-emerald-400/20">ONLINE</span>
        </div>
      </div>
    </nav>

    <!-- User Profile (Bottom) -->
    <div class="p-3 border-t border-gray-100 mt-auto">
      <div class="relative">
        <button 
          @click="showUserMenu = !showUserMenu"
          class="w-full flex items-center gap-2.5 p-2 rounded-lg hover:bg-gray-50 transition-colors text-left group border border-transparent hover:border-orange-100 relative overflow-hidden"
        >
          <div class="absolute bottom-0 left-1/2 -translate-x-1/2 w-0 h-0.5 bg-orange-500 transition-all duration-300 group-hover:w-full"></div>
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
            class="w-full flex items-center gap-2 px-3 py-2 text-[13px] text-gray-600 hover:bg-gray-50 hover:text-gray-900 transition-colors relative group"
          >
            <div class="absolute left-0 top-0 bottom-0 w-1 bg-orange-500 opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <Settings class="w-3.5 h-3.5" />
            <span>功能设置</span>
          </button>
          <div class="h-px bg-gray-100 my-0.5"></div>
          <button 
            @click="$emit('logout')"
            class="w-full flex items-center gap-2 px-3 py-2 text-[13px] text-red-600 hover:bg-red-50 transition-colors relative group"
          >
            <div class="absolute left-0 top-0 bottom-0 w-1 bg-red-500 opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <LogOut class="w-3.5 h-3.5" />
            <span>退出登录</span>
          </button>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { 
  User,
  ChevronRight,
  LogOut,
  Settings
} from 'lucide-vue-next'
import { CATEGORIES, ROLES, getUserRole, getActiveModuleDefinitions } from '../config/modules.js'

const cn = (...inputs) => twMerge(clsx(inputs))
const showUserMenu = ref(false)
const sidebarExpanded = ref(new Set())
const collapsedGroups = ref(new Set())
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

const onFeatureClick = (moduleId, feat) => {
  activeFeatureId.value = feat.id
  emit('change-module', moduleId)
  emit('change-feature', moduleId, feat.id)
}

const toggleSidebarExpand = (id) => {
  if (sidebarExpanded.value.has(id)) {
    sidebarExpanded.value.delete(id)
  } else {
    sidebarExpanded.value.add(id)
  }
}
const isSidebarExpanded = (id) => sidebarExpanded.value.has(id)

const colorMap = {
  blue:    { bg: '#dbeafe', text: '#1d4ed8' },
  emerald: { bg: '#d1fae5', text: '#047857' },
  amber:   { bg: '#fef3c7', text: '#b45309' },
  purple:  { bg: '#ede9fe', text: '#6d28d9' },
  orange:  { bg: '#ffedd5', text: '#c2410c' }
}
const groupBgColor = (group) => (colorMap[group.color] || colorMap.blue).bg
const groupTextColor = (group) => (colorMap[group.color] || colorMap.blue).text

const toggleGroup = (group) => {
  if (collapsedGroups.value.has(group.label)) {
    collapsedGroups.value.delete(group.label)
  } else {
    collapsedGroups.value.add(group.label)
  }
}
const isGroupCollapsed = (group) => collapsedGroups.value.has(group.label)

const isFeatureAvailableForRole = (feat) => {
  const roleId = getUserRole()
  if (!roleId) return true
  return feat.roles.includes(roleId)
}

const visibleMenuItems = computed(() => {
  return props.menuItems.length > 0 ? props.menuItems : getActiveModuleDefinitions()
})

watch(visibleMenuItems, (items) => {
  if (sidebarExpanded.value.size === 0 && items.length > 0) {
    items.forEach(m => sidebarExpanded.value.add(m.id))
  }
}, { immediate: true })

const groupedMenuItems = computed(() => {
  const items = visibleMenuItems.value
  const groups = []
  for (const cat of CATEGORIES) {
    const catItems = items.filter(m => m.category === cat.id)
    if (catItems.length > 0) {
      groups.push({ label: cat.label, color: cat.color, items: catItems })
    }
  }
  return groups
})

const currentRoleName = computed(() => {
  const roleId = getUserRole()
  if (!roleId || !ROLES[roleId]) return ''
  return `${ROLES[roleId].groupName} · ${ROLES[roleId].name}`
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
