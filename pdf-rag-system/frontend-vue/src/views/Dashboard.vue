<template>
  <div class="h-screen w-screen overflow-hidden bg-gray-50 flex font-sans">
    <Sidebar 
      :activeModule="activeModule" 
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
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import Sidebar from '../components/Sidebar.vue'
import ChatModule from '../components/ChatModule.vue'
import LogicFlowModule from '../components/LogicFlowModule.vue'
import DataVisualization from '../components/DataVisualization.vue'
import SentimentModule from '../components/SentimentModule.vue'

const router = useRouter()
const activeModule = ref('chat')

const changeModule = (module) => {
  activeModule.value = module
}

const handleLogout = () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('user')
  router.push('/')
}
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
  font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif;
}
</style>
