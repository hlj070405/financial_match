<template>
  <div class="h-full flex flex-col">
    <!-- Hero -->
    <div class="relative overflow-hidden bg-gradient-to-br from-amber-50 via-white to-orange-50 border-b border-gray-100">
      <div class="absolute inset-0 opacity-20">
        <div class="absolute top-5 right-10 w-64 h-64 bg-amber-200 rounded-full blur-3xl animate-pulse"></div>
        <div class="absolute bottom-0 left-20 w-48 h-48 bg-orange-200 rounded-full blur-3xl animate-pulse" style="animation-delay: 1s;"></div>
      </div>
      <div class="relative px-6 py-4">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center shadow-md shadow-amber-500/20 shrink-0">
            <Compass class="w-4.5 h-4.5 text-white" />
          </div>
          <div class="flex-1">
            <h1 class="text-base font-bold text-gray-900">研究建议推荐</h1>
            <p class="text-xs text-gray-500 mt-0.5 max-w-xl">基于AI实时联网搜索，智能推荐当前值得关注的研究方向与热门话题</p>
            <div class="flex items-center gap-2 mt-2">
              <span class="inline-flex items-center gap-1.5 px-2.5 py-1 bg-amber-100 text-amber-700 text-xs font-medium rounded-full">
                <Flame class="w-3 h-3" /> 实时热点
              </span>
              <span class="inline-flex items-center gap-1.5 px-2.5 py-1 bg-orange-100 text-orange-700 text-xs font-medium rounded-full">
                <Globe class="w-3 h-3" /> Kimi联网
              </span>
            </div>
          </div>
          <button @click="fetchSuggestions" :disabled="loading"
            class="px-4 py-2.5 bg-gray-900 text-white text-sm font-medium rounded-xl hover:bg-gray-800 transition-all shadow-lg shadow-gray-900/20 disabled:opacity-60 flex items-center gap-2 shrink-0">
            <RefreshCw :class="['w-4 h-4', loading ? 'animate-spin' : '']" />
            {{ loading ? '搜索中...' : '刷新推荐' }}
          </button>
        </div>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto p-8 custom-scrollbar">
      <div class="max-w-5xl mx-auto space-y-6">
        <!-- Loading Skeleton -->
        <div v-if="loading && topics.length === 0" class="grid grid-cols-2 gap-5">
          <div v-for="i in 6" :key="i" class="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm animate-pulse">
            <div class="h-4 bg-gray-200 rounded w-2/3 mb-3"></div>
            <div class="h-3 bg-gray-100 rounded w-full mb-2"></div>
            <div class="h-3 bg-gray-100 rounded w-4/5"></div>
          </div>
        </div>

        <!-- Topic Cards -->
        <div v-else class="grid grid-cols-2 gap-5">
          <div v-for="(topic, idx) in topics" :key="idx"
            @click="exploreTopic(topic)"
            class="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm hover:shadow-lg hover:border-amber-200 transition-all cursor-pointer group relative overflow-hidden"
          >
            <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-amber-400 to-orange-500 opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <div class="flex items-start gap-3">
              <div class="w-10 h-10 rounded-xl flex items-center justify-center shrink-0 text-lg"
                :class="topicBgs[idx % topicBgs.length]">
                {{ topicEmojis[idx % topicEmojis.length] }}
              </div>
              <div class="flex-1 min-w-0">
                <h3 class="text-sm font-bold text-gray-900 group-hover:text-amber-700 transition-colors line-clamp-2">{{ topic.title }}</h3>
                <p class="text-xs text-gray-500 mt-1.5 line-clamp-3 leading-relaxed">{{ topic.reason }}</p>
                <div class="flex items-center gap-2 mt-3">
                  <span v-for="tag in (topic.tags || []).slice(0, 3)" :key="tag"
                    class="px-2 py-0.5 bg-gray-100 text-gray-600 text-[10px] font-medium rounded">{{ tag }}</span>
                  <ArrowUpRight class="w-4 h-4 text-gray-300 group-hover:text-amber-500 ml-auto transition-colors" />
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Exploration Chat -->
        <div v-if="exploringTopic" class="bg-white border border-amber-200 rounded-2xl shadow-md overflow-hidden">
          <div class="px-5 py-3 bg-amber-50 border-b border-amber-100 flex items-center justify-between">
            <div class="flex items-center gap-2">
              <Sparkles class="w-4 h-4 text-amber-600" />
              <span class="text-sm font-bold text-gray-900">深入探索: {{ exploringTopic.title }}</span>
            </div>
            <button @click="exploringTopic = null" class="text-xs text-gray-500 hover:text-gray-800 px-2 py-1 hover:bg-amber-100 rounded-lg transition-colors">关闭</button>
          </div>
          <div ref="exploreChat" class="max-h-96 overflow-y-auto p-5 space-y-4 custom-scrollbar">
            <div v-for="(msg, i) in exploreMessages" :key="i"
              :class="['flex', msg.role === 'user' ? 'justify-end' : 'justify-start']">
              <div v-if="msg.role === 'assistant'" class="flex items-start gap-3 max-w-[85%]">
                <div class="w-7 h-7 rounded-lg bg-amber-500 flex items-center justify-center shrink-0">
                  <Bot class="w-3.5 h-3.5 text-white" />
                </div>
                <div class="bg-gray-50 rounded-xl rounded-tl-sm px-4 py-3 text-sm text-gray-700 leading-relaxed" v-html="renderMd(msg.content)"></div>
              </div>
              <div v-else class="bg-amber-500 text-white px-4 py-2.5 rounded-xl rounded-tr-sm max-w-[70%] text-sm">{{ msg.content }}</div>
            </div>
            <div v-if="exploreTyping" class="flex items-start gap-3">
              <div class="w-7 h-7 rounded-lg bg-amber-500 flex items-center justify-center shrink-0">
                <Bot class="w-3.5 h-3.5 text-white" />
              </div>
              <div class="bg-gray-50 rounded-xl rounded-tl-sm px-4 py-3">
                <div class="flex gap-1.5">
                  <div class="w-2 h-2 bg-amber-400 rounded-full animate-bounce"></div>
                  <div class="w-2 h-2 bg-amber-400 rounded-full animate-bounce" style="animation-delay:150ms"></div>
                  <div class="w-2 h-2 bg-amber-400 rounded-full animate-bounce" style="animation-delay:300ms"></div>
                </div>
              </div>
            </div>
          </div>
          <div class="px-5 py-3 border-t border-gray-100 flex gap-2">
            <input v-model="exploreInput" @keydown.enter="sendExplore"
              placeholder="继续追问这个话题..."
              class="flex-1 px-3 py-2 text-sm bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500" />
            <button @click="sendExplore" :disabled="!exploreInput.trim() || exploreTyping"
              class="px-4 py-2 bg-amber-500 text-white text-sm font-medium rounded-lg hover:bg-amber-600 disabled:opacity-50 transition-all">发送</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { marked } from 'marked'
import { Compass, Flame, Globe, RefreshCw, ArrowUpRight, Sparkles, Bot } from 'lucide-vue-next'

const loading = ref(false)
const topics = ref([])
const exploringTopic = ref(null)
const exploreMessages = ref([])
const exploreInput = ref('')
const exploreTyping = ref(false)
const exploreChat = ref(null)

const topicBgs = ['bg-amber-50', 'bg-blue-50', 'bg-emerald-50', 'bg-purple-50', 'bg-rose-50', 'bg-cyan-50']
const topicEmojis = ['📊', '🔥', '💡', '🏭', '📈', '🌐']

const renderMd = (t) => { try { return marked.parse(t) } catch { return t } }

const defaultTopics = [
  { title: '新能源汽车产业链最新动态', reason: '碳酸锂价格持续波动，固态电池技术突破在即，产业格局可能迎来重大变化', tags: ['新能源', '产业链', '技术突破'] },
  { title: '人工智能算力需求爆发', reason: '大模型训练对算力需求指数级增长，GPU供应链与国产替代成为关键投资主线', tags: ['AI', '算力', '半导体'] },
  { title: '央行货币政策走向', reason: '降准降息预期叠加地方债化险，流动性宽松对A股市场的影响值得深入研究', tags: ['宏观', '货币政策', '利率'] },
  { title: '医药创新出海趋势', reason: '创新药license-out交易频繁，国产创新药逐步获得国际认可，出海管线密集', tags: ['医药', '创新', '出海'] },
  { title: '消费复苏与结构分化', reason: '高端消费与大众消费呈现分化态势，关注消费升级与降级并存的投资机会', tags: ['消费', '复苏', '分化'] },
  { title: '地缘政治对供应链的影响', reason: '全球供应链重构加速，关注半导体、稀土等关键领域的国产替代进程', tags: ['地缘', '供应链', '国产替代'] }
]

const fetchSuggestions = async () => {
  loading.value = true
  try {
    const token = localStorage.getItem('access_token')
    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: '请搜索当前最值得关注的6个金融投资研究方向，每个给出标题、推荐原因和标签，输出JSON数组格式：[{"title":"","reason":"","tags":[]}]', style: '研究建议推荐' })
    })
    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = '', content = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const d = line.slice(6)
          if (d === '[DONE]') break
          try { const p = JSON.parse(d); if (p.type === 'text') content += p.text } catch {}
        }
      }
    }
    try {
      const jsonMatch = content.match(/\[[\s\S]*\]/)
      if (jsonMatch) topics.value = JSON.parse(jsonMatch[0])
    } catch { topics.value = defaultTopics }
  } catch {
    topics.value = defaultTopics
  } finally {
    loading.value = false
  }
}

const exploreTopic = async (topic) => {
  exploringTopic.value = topic
  exploreMessages.value = []
  exploreTyping.value = true
  await nextTick()

  try {
    const token = localStorage.getItem('access_token')
    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: `请搜索并深入分析这个研究方向：${topic.title}。给出详细的分析框架、当前市场现状和投资建议。`, style: '研究建议推荐' })
    })
    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = '', content = ''
    exploreMessages.value.push({ role: 'assistant', content: '' })
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const d = line.slice(6)
          if (d === '[DONE]') break
          try {
            const p = JSON.parse(d)
            if (p.type === 'text') { content += p.text; exploreMessages.value[0].content = content }
          } catch {}
        }
      }
    }
  } catch {
    exploreMessages.value.push({ role: 'assistant', content: '暂时无法获取分析，请稍后再试。' })
  } finally {
    exploreTyping.value = false
  }
}

const sendExplore = async () => {
  const text = exploreInput.value.trim()
  if (!text || exploreTyping.value) return
  exploreMessages.value.push({ role: 'user', content: text })
  exploreInput.value = ''
  exploreTyping.value = true

  try {
    const token = localStorage.getItem('access_token')
    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, style: '研究建议推荐' })
    })
    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = '', content = ''
    exploreMessages.value.push({ role: 'assistant', content: '' })
    const idx = exploreMessages.value.length - 1
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const d = line.slice(6)
          if (d === '[DONE]') break
          try { const p = JSON.parse(d); if (p.type === 'text') { content += p.text; exploreMessages.value[idx].content = content } } catch {}
        }
      }
    }
  } catch {
    exploreMessages.value.push({ role: 'assistant', content: '暂时无法回答，请稍后再试。' })
  } finally {
    exploreTyping.value = false
    nextTick(() => { if (exploreChat.value) exploreChat.value.scrollTop = exploreChat.value.scrollHeight })
  }
}

onMounted(() => {
  topics.value = defaultTopics
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }
</style>
