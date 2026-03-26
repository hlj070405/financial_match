<template>
  <div class="h-screen w-screen overflow-hidden bg-gray-50 flex font-sans">
    <Sidebar 
      :activeModule="activeModule" 
      :menuItems="currentMenuItems"
      @change-module="changeModule" 
      @logout="handleLogout"
    />

    <div class="flex-1 flex flex-col overflow-hidden relative">
      <main class="flex-1 overflow-hidden relative">
        <div v-show="activeModule === 'chat'" class="h-full w-full">
          <ChatModule @logout="handleLogout" />
        </div>
        <div v-show="activeModule === 'logic'" class="h-full w-full p-6">
          <LogicFlowModule @logout="handleLogout" />
        </div>
        <div v-show="activeModule === 'data'" class="h-full w-full p-6">
          <DataVisualization @logout="handleLogout" />
        </div>
        <div v-show="activeModule === 'sentiment'" class="h-full w-full">
          <SentimentModule @logout="handleLogout" />
        </div>
        <div v-show="activeModule === 'market'" class="h-full w-full p-6">
          <MarketModule @logout="handleLogout" />
        </div>
        <div v-show="activeModule === 'report'" class="h-full w-full p-6">
          <PlaceholderModule title="一键研报" description="基于公开实时行情和可靠资料，整合当下热点，一键生成领域分析报告" />
        </div>
        <div v-show="activeModule === 'chain'" class="h-full w-full p-6">
          <PlaceholderModule title="产业链分析" description="深入分析上下游产业链关系、供应链风险与行业竞争格局" />
        </div>
        <div v-show="activeModule === 'rag'" class="h-full w-full p-6">
          <PlaceholderModule title="智能检索" description="非结构化文本语义剪枝、噪声过滤、向量表征、自然语言意图检索全链路闭环" />
        </div>
        <div v-show="activeModule === 'datasource'" class="h-full w-full p-6">
          <PlaceholderModule title="数据源管理" description="面向庞大金融多源异构大数据，统一数据接入与管理" />
        </div>
        <div v-show="activeModule === 'settings'" class="h-full w-full">
          <SettingsModule @modules-changed="refreshModules" />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Sidebar from '../layouts/Sidebar.vue'
import ChatModule from '../modules/chat/ChatModule.vue'
import LogicFlowModule from '../modules/logic/LogicFlowModule.vue'
import DataVisualization from '../modules/analysis/DataVisualization.vue'
import SentimentModule from '../modules/sentiment/SentimentModule.vue'
import MarketModule from '../modules/market/MarketModule.vue'
import SettingsModule from '../modules/settings/SettingsModule.vue'
import PlaceholderModule from '../modules/PlaceholderModule.vue'
import { getActiveModuleDefinitions } from '../config/modules.js'

const router = useRouter()
const activeModule = ref('chat')
const currentMenuItems = ref([])

const loadModules = () => {
  currentMenuItems.value = getActiveModuleDefinitions()
}

const changeModule = (module) => {
  activeModule.value = module
}

const refreshModules = () => {
  loadModules()
}

const handleLogout = () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('user')
  localStorage.removeItem('user_role')
  localStorage.removeItem('user_modules')
  localStorage.removeItem('user_features')
  router.push('/')
}

onMounted(() => {
  loadModules()
})
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
  font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif;
}
</style>

