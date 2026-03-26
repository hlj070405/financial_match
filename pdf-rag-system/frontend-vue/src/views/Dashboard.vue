<template>
  <div class="h-screen w-screen overflow-hidden bg-gray-50 flex font-sans">
    <Sidebar 
      :activeModule="activeModule" 
      :menuItems="currentMenuItems"
      @change-module="changeModule"
      @change-feature="changeFeature"
      @logout="handleLogout"
    />

    <div class="flex-1 flex flex-col overflow-hidden relative">
      <main class="flex-1 overflow-hidden relative">
        <div v-show="activeModule === 'chat'" class="h-full w-full">
          <ChatWrapper :activeFeature="activeFeature" />
        </div>
        <div v-show="activeModule === 'logic'" class="h-full w-full">
          <LogicWrapper :activeFeature="activeFeature" />
        </div>
        <div v-show="activeModule === 'data'" class="h-full w-full">
          <DataWrapper :activeFeature="activeFeature" />
        </div>
        <div v-show="activeModule === 'sentiment'" class="h-full w-full">
          <SentimentWrapper :activeFeature="activeFeature" />
        </div>
        <div v-show="activeModule === 'market'" class="h-full w-full">
          <MarketWrapper :activeFeature="activeFeature" />
        </div>
        <div v-show="activeModule === 'report'" class="h-full w-full">
          <ReportWrapper :activeFeature="activeFeature" />
        </div>
        <div v-show="activeModule === 'chain'" class="h-full w-full">
          <ChainWrapper :activeFeature="activeFeature" />
        </div>
        <div v-show="activeModule === 'rag'" class="h-full w-full">
          <RagWrapper :activeFeature="activeFeature" />
        </div>
        <div v-show="activeModule === 'datasource'" class="h-full w-full">
          <DsWrapper :activeFeature="activeFeature" />
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
import ChatWrapper from '../modules/chat/ChatWrapper.vue'
import LogicWrapper from '../modules/logic/LogicWrapper.vue'
import DataWrapper from '../modules/analysis/DataWrapper.vue'
import SentimentWrapper from '../modules/sentiment/SentimentWrapper.vue'
import MarketWrapper from '../modules/market/MarketWrapper.vue'
import ReportWrapper from '../modules/report/ReportWrapper.vue'
import ChainWrapper from '../modules/chain/ChainWrapper.vue'
import RagWrapper from '../modules/rag/RagWrapper.vue'
import DsWrapper from '../modules/datasource/DsWrapper.vue'
import SettingsModule from '../modules/settings/SettingsModule.vue'
import { getActiveModuleDefinitions } from '../config/modules.js'

const router = useRouter()
const activeModule = ref('chat')
const activeFeature = ref('')
const currentMenuItems = ref([])

const loadModules = () => {
  currentMenuItems.value = getActiveModuleDefinitions()
}

const changeModule = (module) => {
  activeModule.value = module
}

const changeFeature = (moduleId, featureId) => {
  activeModule.value = moduleId
  activeFeature.value = featureId
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

