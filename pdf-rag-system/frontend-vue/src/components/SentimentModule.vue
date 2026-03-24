<template>
  <div class="h-full flex flex-col gap-6 p-2 font-sans overflow-hidden">
    <!-- Header Section -->
    <div class="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm shrink-0 flex items-center justify-between">
      <div>
        <h2 class="text-xl font-bold text-gray-900 flex items-center gap-3">
          <div class="p-2.5 rounded-xl bg-violet-50 text-violet-600">
            <Activity class="w-6 h-6" />
          </div>
          舆情溯源引擎
        </h2>
        <p class="text-sm text-gray-500 mt-1.5 ml-1">全网实时舆情监测与热点事件追踪系统</p>
      </div>
      
      <div class="flex items-center gap-3">
        <div class="relative group">
          <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search class="w-4 h-4 text-gray-400" />
          </div>
          <input
            v-model="searchQuery"
            @input="onSearchInput"
            placeholder="搜索全球热点..."
            class="pl-10 pr-4 py-2.5 w-64 text-sm bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 transition-all placeholder-gray-400"
          />
        </div>

        <button
          type="button"
          @click="syncNews"
          :disabled="syncing"
          class="flex items-center gap-2 px-4 py-2 bg-gray-900 text-white text-sm font-medium rounded-xl hover:bg-gray-800 active:scale-95 transition-all disabled:opacity-70 disabled:cursor-not-allowed shadow-lg shadow-gray-900/20 relative group overflow-hidden"
        >
          <div class="absolute bottom-0 left-0 w-full h-0.5 bg-orange-500 opacity-0 group-hover:opacity-100 transition-opacity"></div>
          <RefreshCw :class="['w-4 h-4', syncing ? 'animate-spin' : '']" />
          {{ syncing ? '同步中...' : '同步' }}
        </button>
      </div>
    </div>

    <!-- Stats Grid -->
    <div class="grid grid-cols-3 gap-6 shrink-0">
      <div class="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm relative overflow-hidden group hover:shadow-md transition-all">
        <div class="flex items-center justify-between mb-4 relative z-10">
          <span class="text-sm font-medium text-gray-500">今日热点追踪</span>
          <div class="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
            <TrendingUp class="w-5 h-5" />
          </div>
        </div>
        <div class="flex items-baseline gap-2">
          <span class="text-3xl font-bold text-gray-900">{{ totalNews }}</span>
          <span class="text-xs text-emerald-600 font-medium bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-100">+{{ todayNewCount }} 新增</span>
        </div>
      </div>

      <div class="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm relative overflow-hidden group hover:shadow-md transition-all">
        <div class="flex items-center justify-between mb-4 relative z-10">
          <span class="text-sm font-medium text-gray-500">覆盖数据源</span>
          <div class="w-8 h-8 rounded-lg bg-violet-50 text-violet-600 flex items-center justify-center">
            <Layers class="w-5 h-5" />
          </div>
        </div>
        <div class="flex items-baseline gap-2">
          <span class="text-3xl font-bold text-gray-900">{{ categoryCount }}</span>
          <span class="text-xs text-gray-500">个平台 / {{ categories.length - 1 }} 个分类</span>
        </div>
      </div>

      <div class="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm relative overflow-hidden group hover:shadow-md transition-all">
        <div class="flex items-center justify-between mb-4 relative z-10">
          <span class="text-sm font-medium text-gray-500">系统状态</span>
          <div class="w-8 h-8 rounded-lg bg-pink-50 text-pink-600 flex items-center justify-center">
            <Server class="w-5 h-5" />
          </div>
        </div>
        <div class="flex items-baseline gap-2">
          <span class="text-sm font-medium text-gray-500">最后更新</span>
          <span class="text-xl font-bold text-gray-900">{{ lastUpdateTime }}</span>
        </div>
      </div>
    </div>

    <!-- Main Content Area -->
    <div class="flex-1 flex gap-6 min-h-0">
      <!-- News List -->
      <div class="flex-1 bg-white border border-gray-100 rounded-2xl shadow-sm flex flex-col min-h-0 relative overflow-hidden">
        <!-- Filter Tabs -->
        <div class="px-5 pt-4 pb-2 border-b border-gray-100 flex gap-2 overflow-x-auto no-scrollbar">
          <button
            v-for="cat in categories"
            :key="cat"
            @click="selectedCategory = cat"
            :class="cn(
              'px-4 py-1.5 text-sm font-medium rounded-lg transition-all whitespace-nowrap relative group overflow-hidden',
              selectedCategory === cat
                ? 'bg-gray-100 text-gray-900'
                : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700'
            )"
          >
            <div class="absolute bottom-0 left-0 w-full h-0.5 bg-orange-500 opacity-0 group-hover:opacity-100 transition-opacity"></div>
            {{ cat }}
          </button>
        </div>

        <!-- News Grid -->
        <div class="flex-1 overflow-y-auto p-5 scroll-smooth custom-scrollbar">
          <div v-if="loading" class="h-full flex flex-col items-center justify-center text-gray-400">
            <Loader2 class="w-8 h-8 animate-spin mb-3 text-violet-500" />
            <p class="text-sm">正在聚合全网数据...</p>
          </div>

          <div v-else-if="filteredNews.length === 0" class="h-full flex flex-col items-center justify-center text-gray-400">
            <Inbox class="w-12 h-12 mb-4 text-gray-200" />
            <p class="text-sm">暂无相关热点数据</p>
          </div>

          <div v-else class="space-y-3">
            <div 
              v-for="(item, index) in filteredNews" 
              :key="item.id || index"
              @click="openNews(item)"
              class="group bg-white hover:bg-gray-50/80 border border-gray-100 hover:border-violet-200 rounded-xl p-4 transition-all cursor-pointer relative"
            >
              <div class="flex items-start gap-4">
                <div class="flex-shrink-0 w-10 text-center pt-1">
                  <span :class="cn(
                    'text-xl font-bold font-mono block leading-none',
                    index < 3 ? 'text-violet-600' : 'text-gray-300'
                  )">
                    {{ String(item.rank).padStart(2, '0') }}
                  </span>
                </div>

                <div class="flex-1 min-w-0">
                  <h3 class="text-base font-medium text-gray-900 group-hover:text-violet-600 transition-colors line-clamp-2 mb-2">
                    {{ item.title }}
                  </h3>
                  
                  <div class="flex items-center gap-3 text-xs text-gray-500">
                    <span class="flex items-center gap-1 bg-gray-100 px-2 py-0.5 rounded text-gray-600 font-medium">
                      <Globe class="w-3 h-3" />
                      {{ item.source_name }}
                    </span>
                    
                    <span class="flex items-center gap-1">
                      <Tag class="w-3 h-3" />
                      {{ item.category }}
                    </span>

                    <span class="flex items-center gap-1 ml-auto text-gray-400">
                      <Clock class="w-3 h-3" />
                      {{ formatTime(item.first_seen) }}
                    </span>
                  </div>
                </div>

                <div class="flex-shrink-0 self-center opacity-0 group-hover:opacity-100 transition-opacity transform translate-x-2 group-hover:translate-x-0">
                  <ArrowUpRight class="w-5 h-5 text-gray-400 group-hover:text-violet-500" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Panel -->
      <div class="w-80 flex flex-col gap-6 shrink-0">
        <!-- Category Distribution -->
        <div class="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm">
          <h3 class="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <PieChart class="w-4 h-4 text-violet-500" />
            热点分布
          </h3>
          <div class="space-y-4">
            <div v-for="(count, cat) in categoryStats" :key="cat" class="group">
              <div class="flex items-center justify-between mb-1.5">
                <span class="text-xs font-medium text-gray-600">{{ cat }}</span>
                <span class="text-xs font-medium text-gray-900">{{ count }}</span>
              </div>
              <div class="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div 
                  class="h-full bg-violet-500 rounded-full transition-all duration-1000 group-hover:bg-violet-600"
                  :style="{ width: `${(count / totalNews) * 100}%` }"
                ></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Source Status -->
        <div class="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm flex-1 flex flex-col min-h-0">
          <h3 class="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Radio class="w-4 h-4 text-emerald-500" />
            数据源监控
          </h3>
          <div class="flex-1 overflow-y-auto pr-1 space-y-2 custom-scrollbar">
            <div v-for="(count, source) in sourceStats" :key="source" 
              class="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div class="flex items-center gap-3">
                <div class="relative">
                  <div class="w-2 h-2 rounded-full bg-emerald-500"></div>
                  <div class="absolute inset-0 rounded-full bg-emerald-500 animate-ping opacity-20"></div>
                </div>
                <span class="text-xs font-medium text-gray-700">{{ source }}</span>
              </div>
              <span class="text-xs text-gray-500 bg-white px-2 py-0.5 rounded border border-gray-200">{{ count }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { 
  Activity, 
  Search, 
  RefreshCw, 
  TrendingUp, 
  Layers, 
  Server, 
  Loader2, 
  Inbox, 
  Globe, 
  Tag, 
  Clock, 
  ArrowUpRight,
  PieChart,
  Radio
} from 'lucide-vue-next'
defineEmits(['logout'])

const cn = (...inputs) => twMerge(clsx(inputs))

const loading = ref(false)
const syncing = ref(false)
const allNews = ref([])
const selectedCategory = ref('全部')
const searchQuery = ref('')
const todayNewCount = ref(0)
let searchTimer = null

const categories = computed(() => {
  const cats = new Set(['全部'])
  allNews.value.forEach(item => {
    if (item.category) cats.add(item.category)
  })
  return Array.from(cats)
})

const filteredNews = computed(() => {
  let result = allNews.value

  if (selectedCategory.value !== '全部') {
    result = result.filter(item => item.category === selectedCategory.value)
  }

  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(item => 
      item.title.toLowerCase().includes(query)
    )
  }

  return result.slice(0, 100)
})

const totalNews = computed(() => allNews.value.length)
const categoryCount = computed(() => categories.value.length - 1)

const lastUpdateTime = computed(() => {
  if (allNews.value.length === 0) return '--'
  const now = new Date()
  return `${now.getHours()}:${String(now.getMinutes()).padStart(2, '0')}`
})

const categoryStats = computed(() => {
  const stats = {}
  allNews.value.forEach(item => {
    if (item.category) {
      stats[item.category] = (stats[item.category] || 0) + 1
    }
  })
  return stats
})

const sourceStats = computed(() => {
  const stats = {}
  allNews.value.forEach(item => {
    if (item.source_name) {
      stats[item.source_name] = (stats[item.source_name] || 0) + 1
    }
  })
  return stats
})

const fetchNews = async () => {
  loading.value = true
  try {
    const token = localStorage.getItem('access_token')
    if (!token) {
      console.error('未找到访问令牌')
      allNews.value = []
      return
    }

    const response = await fetch('http://localhost:8000/api/hotspot/news?limit=200', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    
    if (data.success && Array.isArray(data.news)) {
      allNews.value = data.news
      todayNewCount.value = data.news.length 
    } else {
      allNews.value = []
    }
  } catch (error) {
    console.error('获取热点新闻失败:', error)
    allNews.value = []
  } finally {
    loading.value = false
  }
}

const syncNews = async () => {
  if (syncing.value) return
  
  syncing.value = true
  try {
    const token = localStorage.getItem('access_token')
    if (!token) {
      console.error('未找到访问令牌')
      return
    }

    const response = await fetch('http://localhost:8000/api/hotspot/sync', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    todayNewCount.value = data.synced || 0
    
    await fetchNews()
  } catch (error) {
    console.error('同步热点新闻失败:', error)
  } finally {
    syncing.value = false
  }
}

const onSearchInput = () => {
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
  searchTimer = setTimeout(() => {
    // 搜索逻辑已在 computed 中处理
  }, 300)
}

const openNews = (item) => {
  const url = item.url?.trim()
  if (!url) return
  window.open(url, '_blank', 'noopener,noreferrer')
}

const formatTime = (timeStr) => {
  if (!timeStr) return ''
  try {
    const date = new Date(timeStr)
    if (isNaN(date.getTime())) return timeStr
    
    const now = new Date()
    const diff = now - date
    
    if (diff < 0) return '刚刚'
    
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(minutes / 60)
    const days = Math.floor(hours / 24)
    
    if (minutes < 1) return '刚刚'
    if (minutes < 60) return `${minutes}分钟前`
    if (hours < 24) return `${hours}小时前`
    if (days < 3) return `${days}天前`
    
    return `${date.getMonth() + 1}月${date.getDate()}日`
  } catch {
    return timeStr
  }
}

onMounted(() => {
  fetchNews()
})
</script>

<style scoped>
.no-scrollbar::-webkit-scrollbar {
  display: none;
}
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #e5e7eb;
  border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #d1d5db;
}
</style>