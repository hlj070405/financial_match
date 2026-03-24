<template>
  <div class="h-screen w-screen overflow-hidden relative flex items-center justify-center">
    <VantaBackground />
    
    <div class="relative z-10 w-full max-w-6xl px-8">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 items-center">
        
        <div class="hidden lg:block space-y-5">
          <div class="glass-panel p-5">
            <h3 class="text-base font-semibold text-gray-800 mb-3 flex items-center">
              <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500/30 to-purple-500/30 flex items-center justify-center mr-2">
                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
                </svg>
              </div>
              金融分析核心能力
            </h3>
            <div class="space-y-2 text-sm">
              <div class="flex items-start">
                <span class="text-blue-500 mr-2">•</span>
                <span class="text-gray-700">多维财报金融分析与风险预警</span>
              </div>
              <div class="flex items-start">
                <span class="text-purple-500 mr-2">•</span>
                <span class="text-gray-700">行业对标与量化金融评估</span>
              </div>
              <div class="flex items-start">
                <span class="text-pink-500 mr-2">•</span>
                <span class="text-gray-700">实时金融舆情感知与关联</span>
              </div>
            </div>
          </div>
          
          <div class="glass-panel p-5">
            <h3 class="text-base font-semibold text-gray-800 mb-3 flex items-center">
              <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500/30 to-pink-500/30 flex items-center justify-center mr-2">
                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
                </svg>
              </div>
              金融应用场景
            </h3>
            <div class="space-y-2 text-sm">
              <div class="flex items-start">
                <span class="text-blue-600 font-medium mr-2">1</span>
                <span class="text-gray-700">机构金融投资决策分析</span>
              </div>
              <div class="flex items-start">
                <span class="text-purple-600 font-medium mr-2">2</span>
                <span class="text-gray-700">企业财务战略诊断分析</span>
              </div>
              <div class="flex items-start">
                <span class="text-pink-600 font-medium mr-2">3</span>
                <span class="text-gray-700">信贷金融风控智能评估</span>
              </div>
            </div>
          </div>
        </div>

        <div class="lg:col-span-1">
          <div class="text-center mb-6">
            <div class="inline-flex items-center justify-center mb-4">
              <div class="relative">
                <div class="absolute inset-0 bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 rounded-full blur-xl opacity-50"></div>
                <div class="relative w-16 h-16 rounded-full bg-gradient-to-br from-blue-500/20 via-purple-500/20 to-pink-500/20 backdrop-blur-md border border-white/30 flex items-center justify-center">
                  <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                  </svg>
                </div>
              </div>
            </div>
            
            <h1 class="text-3xl font-bold mb-1">
              <span class="bg-gradient-to-r from-blue-200 via-purple-200 to-pink-200 bg-clip-text text-transparent drop-shadow-lg">
                幻流
              </span>
            </h1>
            <p class="text-lg text-white/90 font-light mb-1 drop-shadow-md">Phantom Flow</p>
            <p class="text-xs text-white/70 drop-shadow-sm">多源金融数据驱动的决策进化智能体</p>
          </div>

          <div class="glass-panel p-6">
            <h2 class="text-xl font-semibold text-gray-800 mb-5 text-center">金融分析系统登录</h2>
            
            <div v-if="errorMessage" class="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg text-sm">
              {{ errorMessage }}
            </div>
            
            <form @submit.prevent="handleLogin" class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  <span class="flex items-center">
                    <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                    </svg>
                    用户名
                  </span>
                </label>
                <input 
                  v-model="username"
                  type="text" 
                  class="glass-input text-sm"
                  placeholder="请输入用户名"
                  required
                />
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  <span class="flex items-center">
                    <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                    </svg>
                    密码
                  </span>
                </label>
                <input 
                  v-model="password"
                  type="password" 
                  class="glass-input text-sm"
                  placeholder="请输入密码"
                  required
                />
              </div>

              <div class="flex items-center justify-between text-sm">
                <label class="flex items-center cursor-pointer">
                  <input 
                    v-model="rememberMe"
                    type="checkbox" 
                    class="w-4 h-4 rounded border-gray-300 text-purple-500 focus:ring-purple-400 focus:ring-offset-0 mr-2"
                  />
                  <span class="text-gray-700">记住登录</span>
                </label>
                <a href="#" class="text-gray-600 hover:text-gray-800 transition">忘记密码？</a>
              </div>

              <GlassButton 
                class="w-full"
                @click="handleLogin"
                :disabled="isLoading"
              >
                <span class="flex items-center justify-center space-x-2 text-sm">
                  <svg v-if="isLoading" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span class="font-medium">{{ isLoading ? '验证中...' : '登录' }}</span>
                </span>
              </GlassButton>
            </form>

            <div class="relative my-5">
              <div class="absolute inset-0 flex items-center">
                <div class="w-full border-t border-gray-300/50"></div>
              </div>
              <div class="relative flex justify-center text-xs">
                <span class="px-3 bg-white/50 text-gray-600">企业级单点登录</span>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-3">
              <button class="flex items-center justify-center px-3 py-2 bg-white/30 hover:bg-white/50 border border-gray-200 rounded-[var(--glass-radius)] transition text-xs text-gray-700">
                <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                </svg>
                GitHub
              </button>
              <button class="flex items-center justify-center px-3 py-2 bg-white/30 hover:bg-white/50 border border-gray-200 rounded-[var(--glass-radius)] transition text-xs text-gray-700">
                <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M23.954 4.569c-.885.389-1.83.654-2.825.775 1.014-.611 1.794-1.574 2.163-2.723-.951.555-2.005.959-3.127 1.184-.896-.959-2.173-1.559-3.591-1.559-2.717 0-4.92 2.203-4.92 4.917 0 .39.045.765.127 1.124C7.691 8.094 4.066 6.13 1.64 3.161c-.427.722-.666 1.561-.666 2.475 0 1.71.87 3.213 2.188 4.096-.807-.026-1.566-.248-2.228-.616v.061c0 2.385 1.693 4.374 3.946 4.827-.413.111-.849.171-1.296.171-.314 0-.615-.03-.916-.086.631 1.953 2.445 3.377 4.604 3.417-1.68 1.319-3.809 2.105-6.102 2.105-.39 0-.779-.023-1.17-.067 2.189 1.394 4.768 2.209 7.557 2.209 9.054 0 13.999-7.496 13.999-13.986 0-.209 0-.42-.015-.63.961-.689 1.8-1.56 2.46-2.548l-.047-.02z"/>
                </svg>
                企业微信
              </button>
            </div>

            <div class="text-center mt-4 text-xs text-gray-600">
              需要申请试用权限？
              <a href="#" class="text-gray-800 font-medium hover:text-gray-900 transition">联系我们</a>
            </div>
          </div>
        </div>

        <div class="hidden lg:block space-y-5">
          <div class="glass-panel p-5">
            <div class="text-center mb-3">
              <div class="inline-flex items-center justify-center w-12 h-12 rounded-full bg-gradient-to-br from-blue-500/20 to-purple-500/20 mb-2">
                <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
                </svg>
              </div>
              <h3 class="text-base font-semibold text-gray-800">金融数据实时流</h3>
            </div>
            <div class="space-y-2 text-sm text-gray-600">
              <div class="flex justify-between items-center">
                <span>财报金融分析引擎</span>
                <span class="text-green-600">● 在线</span>
              </div>
              <div class="flex justify-between items-center">
                <span>金融风险监测系统</span>
                <span class="text-green-600">● 在线</span>
              </div>
              <div class="flex justify-between items-center">
                <span>金融舆情追踪模块</span>
                <span class="text-green-600">● 在线</span>
              </div>
            </div>
          </div>
          
          <div class="glass-panel p-5">
            <div class="text-center">
              <p class="text-xs text-gray-600 mb-2">服务全球金融机构</p>
              <div class="flex justify-center space-x-5 text-sm">
                <div>
                  <div class="text-xl font-bold text-gray-800">1000+</div>
                  <div class="text-gray-600 text-xs mt-1">金融企业</div>
                </div>
                <div>
                  <div class="text-xl font-bold text-gray-800">50K+</div>
                  <div class="text-gray-600 text-xs mt-1">分析报告</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="text-center mt-6 text-white/60 text-xs">
        <p>© 2026 幻流 (Phantom Flow). All rights reserved.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import VantaBackground from '../components/VantaBackground.vue'
import GlassButton from '../components/GlassButton.vue'

const router = useRouter()
const username = ref('')
const password = ref('')
const rememberMe = ref(false)
const isLoading = ref(false)
const errorMessage = ref('')

const API_BASE_URL = 'http://localhost:8000'

const handleLogin = async () => {
  if (!username.value || !password.value) {
    errorMessage.value = '请输入用户名和密码'
    return
  }

  isLoading.value = true
  errorMessage.value = ''
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: username.value,
        password: password.value,
      }),
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.detail || '登录失败')
    }

    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('user', JSON.stringify(data.user))
    
    if (rememberMe.value) {
      localStorage.setItem('remember_me', 'true')
    }

    router.push('/dashboard')
    
  } catch (error) {
    errorMessage.value = error.message || '登录失败，请检查网络连接'
    console.error('登录错误:', error)
  } finally {
    isLoading.value = false
  }
}
</script>
