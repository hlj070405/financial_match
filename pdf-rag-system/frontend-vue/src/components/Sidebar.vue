<template>
  <aside class="w-[280px] bg-white border-r border-gray-100 flex flex-col shrink-0 z-20 transition-all duration-300">
    <!-- Brand -->
    <div class="h-16 flex items-center px-6 border-b border-gray-100/50">
      <div class="flex items-center gap-3">
        <div class="relative flex items-center justify-center w-8 h-8 rounded-xl bg-gray-900 text-white shadow-lg shadow-gray-900/20">
          <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <div>
          <h1 class="text-base font-bold text-gray-900 leading-none">Phantom Flow</h1>
          <p class="text-[10px] text-gray-400 font-medium tracking-wide mt-0.5">幻流智能</p>
        </div>
      </div>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 p-4 space-y-1 overflow-y-auto custom-scrollbar">
      <div class="px-3 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">核心功能</div>
      
      <button
        v-for="item in menuItems"
        :key="item.id"
        @click="$emit('change-module', item.id)"
        :class="cn(
          'w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group relative overflow-hidden',
          activeModule === item.id
            ? 'bg-gray-900 text-white shadow-md shadow-gray-900/10'
            : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
        )"
      >
        <!-- Orange Accent Line -->
        <div 
          class="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-orange-500 rounded-r-full transition-all duration-300"
          :class="activeModule === item.id ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-full'"
        ></div>

        <component 
          :is="item.icon" 
          :class="cn(
            'w-5 h-5 transition-colors relative z-10',
            activeModule === item.id ? 'text-white' : 'text-gray-400 group-hover:text-gray-600'
          )" 
        />
        <div class="flex-1 text-left relative z-10">
          <div class="text-sm font-medium">{{ item.title }}</div>
          <div class="text-[10px] opacity-60">{{ item.subtitle }}</div>
        </div>
      </button>

      <div class="mt-8 px-3 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">系统监控</div>
      <div class="mx-3 p-4 rounded-xl bg-gray-50 border border-gray-100 space-y-3 relative overflow-hidden">
        <div class="absolute top-0 left-0 w-full h-0.5 bg-gradient-to-r from-orange-500/0 via-orange-500/50 to-orange-500/0 opacity-50"></div>
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <div class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
            <span class="text-xs font-medium text-gray-700">AI 引擎</span>
          </div>
          <span class="text-[10px] font-mono text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded">RUNNING</span>
        </div>
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <div class="w-2 h-2 rounded-full bg-emerald-500"></div>
            <span class="text-xs font-medium text-gray-700">数据流</span>
          </div>
          <span class="text-[10px] font-mono text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded">ONLINE</span>
        </div>
      </div>
    </nav>

    <!-- User Profile (Bottom) -->
    <div class="p-4 border-t border-gray-100 mt-auto">
      <div class="relative">
        <button 
          @click="showUserMenu = !showUserMenu"
          class="w-full flex items-center gap-3 p-2 rounded-xl hover:bg-gray-50 transition-colors text-left group border border-transparent hover:border-orange-100 relative overflow-hidden"
        >
          <!-- Accent Line on Hover -->
          <div class="absolute bottom-0 left-1/2 -translate-x-1/2 w-0 h-0.5 bg-orange-500 transition-all duration-300 group-hover:w-full"></div>
          
          <div class="w-9 h-9 rounded-full bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center border border-gray-200 shrink-0">
            <User class="w-5 h-5 text-gray-500 group-hover:text-gray-700" />
          </div>
          <div class="flex-1 min-w-0">
            <div class="text-sm font-medium text-gray-900 truncate">Admin User</div>
            <div class="text-xs text-gray-500 truncate">admin@phantom.ai</div>
          </div>
          <ChevronRight class="w-4 h-4 text-gray-300 group-hover:text-gray-500 shrink-0 transition-transform duration-200" :class="{ 'rotate-90': showUserMenu }" />
        </button>

        <!-- User Menu Dropdown -->
        <div 
          v-if="showUserMenu"
          class="absolute bottom-full left-0 w-full mb-2 bg-white border border-gray-100 rounded-xl shadow-xl shadow-gray-200/50 py-1 z-30 overflow-hidden"
        >
          <button class="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-gray-600 hover:bg-gray-50 hover:text-gray-900 transition-colors relative group">
            <div class="absolute left-0 top-0 bottom-0 w-1 bg-orange-500 opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <Settings class="w-4 h-4" />
            <span>设置</span>
          </button>
          <div class="h-px bg-gray-100 my-1"></div>
          <button 
            @click="$emit('logout')"
            class="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 transition-colors relative group"
          >
            <div class="absolute left-0 top-0 bottom-0 w-1 bg-red-500 opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <LogOut class="w-4 h-4" />
            <span>退出登录</span>
          </button>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, defineProps, defineEmits } from 'vue'
import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { 
  MessageSquare, 
  GitMerge, 
  BarChart3, 
  Activity,
  User,
  ChevronRight,
  LogOut,
  Settings
} from 'lucide-vue-next'

const cn = (...inputs) => twMerge(clsx(inputs))
const showUserMenu = ref(false)

defineProps({
  activeModule: {
    type: String,
    default: 'chat'
  }
})

defineEmits(['change-module', 'logout'])

const menuItems = [
  {
    id: 'chat',
    title: '幻思·智能咨询',
    subtitle: '认知进化',
    icon: MessageSquare
  },
  {
    id: 'logic',
    title: '逻辑流·可视化',
    subtitle: '决策链路',
    icon: GitMerge
  },
  {
    id: 'data',
    title: '幻诊·运营评估',
    subtitle: '透视真相',
    icon: BarChart3
  },
  {
    id: 'sentiment',
    title: '舆情溯源·感知',
    subtitle: '实时共振',
    icon: Activity
  }
]
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
