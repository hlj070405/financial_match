<template>
  <div class="h-screen w-screen overflow-hidden relative flex items-center justify-center">
    <VantaBackground />
    
    <div class="relative z-10 w-full max-w-4xl px-6">
      <!-- Header -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center mb-4">
          <div class="relative">
            <div class="absolute inset-0 bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 rounded-full blur-xl opacity-50"></div>
            <div class="relative w-14 h-14 rounded-full bg-gradient-to-br from-blue-500/20 via-purple-500/20 to-pink-500/20 backdrop-blur-md border border-white/30 flex items-center justify-center">
              <svg class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13 10V3L4 14h7v7l9-11h-7z"/>
              </svg>
            </div>
          </div>
        </div>
        <h1 class="text-2xl font-bold mb-1">
          <span class="bg-gradient-to-r from-blue-200 via-purple-200 to-pink-200 bg-clip-text text-transparent drop-shadow-lg">
            选择您的身份
          </span>
        </h1>
        <p class="text-sm text-white/70 drop-shadow-sm">预设将为您配置最适合的功能模块，您可以随时在设置中调整</p>
      </div>

      <!-- Group Tabs -->
      <div class="flex justify-center mb-6 gap-3">
        <button
          v-for="group in groups"
          :key="group.id"
          @click="activeGroup = group.id"
          class="px-5 py-2 rounded-full text-sm font-medium transition-all duration-300 border"
          :class="activeGroup === group.id
            ? 'bg-white/90 text-gray-900 border-white/60 shadow-lg'
            : 'bg-white/10 text-white/80 border-white/20 hover:bg-white/20'"
        >
          {{ group.label }}
        </button>
      </div>

      <!-- Role Cards -->
      <div class="grid gap-4" :class="currentRoles.length <= 2 ? 'grid-cols-1 sm:grid-cols-2 max-w-2xl mx-auto' : 'grid-cols-1 sm:grid-cols-3'">
        <button
          v-for="role in currentRoles"
          :key="role.id"
          @click="selectedRole = role.id"
          class="glass-panel p-5 text-left transition-all duration-300 group relative overflow-hidden"
          :class="selectedRole === role.id
            ? 'ring-2 ring-white/60 shadow-2xl scale-[1.02]'
            : 'hover:scale-[1.01] hover:shadow-xl'"
        >
          <!-- Selected indicator -->
          <div 
            v-if="selectedRole === role.id"
            class="absolute top-3 right-3 w-6 h-6 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center"
          >
            <svg class="w-3.5 h-3.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/>
            </svg>
          </div>

          <!-- Color accent -->
          <div 
            class="absolute top-0 left-0 w-full h-1 rounded-t-[var(--glass-radius)] transition-opacity duration-300"
            :class="[`bg-${role.color}-500`, selectedRole === role.id ? 'opacity-100' : 'opacity-0 group-hover:opacity-50']"
          ></div>

          <div class="flex items-center gap-3 mb-3">
            <div 
              class="w-10 h-10 rounded-xl flex items-center justify-center"
              :class="`bg-${role.color}-100`"
            >
              <component 
                :is="role.icon" 
                class="w-5 h-5"
                :class="`text-${role.color}-600`"
              />
            </div>
            <div>
              <h3 class="text-base font-semibold text-gray-800">{{ role.name }}</h3>
              <p class="text-[10px] text-gray-500">{{ role.moduleCount }} 个功能模块</p>
            </div>
          </div>
          <p class="text-xs text-gray-600 leading-relaxed">{{ role.description }}</p>
          
          <!-- Module tags -->
          <div class="mt-3 flex flex-wrap gap-1.5">
            <span 
              v-for="mod in role.moduleNames" 
              :key="mod"
              class="text-[10px] px-2 py-0.5 rounded-full bg-gray-100 text-gray-600"
            >{{ mod }}</span>
          </div>
        </button>
      </div>

      <!-- Confirm Button -->
      <div class="flex justify-center mt-6">
        <GlassButton 
          class="min-w-[200px]"
          @click="confirmRole"
          :disabled="!selectedRole"
        >
          <span class="flex items-center justify-center space-x-2 text-sm">
            <span class="font-medium">进入系统</span>
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6"/>
            </svg>
          </span>
        </GlassButton>
      </div>

      <div class="text-center mt-4 text-white/50 text-xs">
        <p>© 2026 幻流 (Phantom Flow). All rights reserved.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import VantaBackground from '../components/VantaBackground.vue'
import GlassButton from '../components/GlassButton.vue'
import { 
  User, Users, Briefcase, Building2, Building,
} from 'lucide-vue-next'
import { ROLES, ALL_MODULES, saveUserRole, saveEnabledModules, saveEnabledFeatures, getDefaultFeaturesForRole } from '../config/modules.js'

const router = useRouter()
const activeGroup = ref('personal')
const selectedRole = ref(null)

const groups = [
  { id: 'personal', label: '个人用户' },
  { id: 'enterprise', label: '企业用户' }
]

const roleIcons = {
  personal_general: User,
  personal_wealthy: Users,
  personal_professional: Briefcase,
  enterprise_small: Building2,
  enterprise_large: Building
}

const currentRoles = computed(() => {
  return Object.values(ROLES)
    .filter(r => r.group === activeGroup.value)
    .map(r => ({
      ...r,
      icon: roleIcons[r.id],
      moduleCount: r.defaultModules.length,
      moduleNames: r.defaultModules.map(id => {
        const mod = ALL_MODULES.find(m => m.id === id)
        return mod ? mod.title : id
      })
    }))
})

const confirmRole = () => {
  if (!selectedRole.value) return
  const role = ROLES[selectedRole.value]
  saveUserRole(selectedRole.value)
  saveEnabledModules(role.defaultModules)
  saveEnabledFeatures(getDefaultFeaturesForRole(selectedRole.value))
  router.push('/dashboard')
}
</script>
