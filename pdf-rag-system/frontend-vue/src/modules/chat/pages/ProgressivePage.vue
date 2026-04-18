<template>
  <div class="h-full flex flex-col">
    <!-- Hero -->
    <div class="relative overflow-hidden bg-gradient-to-br from-emerald-50 via-white to-teal-50 border-b border-gray-100">
      <div class="absolute inset-0 opacity-20">
        <div class="absolute top-5 left-20 w-64 h-64 bg-emerald-200 rounded-full blur-3xl animate-pulse"></div>
        <div class="absolute bottom-0 right-10 w-48 h-48 bg-teal-200 rounded-full blur-3xl animate-pulse" style="animation-delay: 1.2s;"></div>
      </div>
      <div class="relative px-6 py-4">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center shadow-md shadow-emerald-500/20 shrink-0">
            <Layers class="w-4.5 h-4.5 text-white" />
          </div>
          <div class="flex-1">
            <h1 class="text-base font-bold text-gray-900">渐进式引导分析</h1>
            <p class="text-xs text-gray-500 mt-0.5 max-w-xl">多源数据渐进式分析，让普通人也能获得专业分析师级服务</p>
            <div class="flex items-center gap-2 mt-2">
              <span class="inline-flex items-center gap-1.5 px-2.5 py-1 bg-emerald-100 text-emerald-700 text-xs font-medium rounded-full">
                <Sparkles class="w-3 h-3" /> 渐进式深入
              </span>
              <span class="inline-flex items-center gap-1.5 px-2.5 py-1 bg-teal-100 text-teal-700 text-xs font-medium rounded-full">
                <BookOpen class="w-3 h-3" /> 零门槛
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="flex-1 flex min-h-0">
      <!-- Main Content -->
      <div class="flex-1 flex flex-col min-h-0">
        <div ref="contentArea" class="flex-1 overflow-y-auto px-8 py-6 space-y-5 custom-scrollbar">
          <!-- Analysis Depth Steps -->
          <div class="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm">
            <h3 class="text-sm font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Layers class="w-4 h-4 text-emerald-500" />
              分析深度层级
            </h3>
            <div class="flex items-center gap-2">
              <div v-for="(level, idx) in analysisLevels" :key="idx"
                @click="selectLevel(idx)"
                :class="[
                  'flex-1 p-3 rounded-xl border-2 cursor-pointer transition-all duration-300 text-center group relative overflow-hidden',
                  currentLevel === idx
                    ? 'border-emerald-500 bg-emerald-50 shadow-md shadow-emerald-500/10'
                    : currentLevel > idx
                      ? 'border-emerald-200 bg-emerald-50/50'
                      : 'border-gray-100 bg-gray-50 hover:border-emerald-200 hover:bg-emerald-50/30'
                ]"
              >
                <div :class="[
                  'w-8 h-8 rounded-full mx-auto mb-2 flex items-center justify-center text-xs font-bold transition-all',
                  currentLevel >= idx ? 'bg-emerald-500 text-white' : 'bg-gray-200 text-gray-500'
                ]">{{ idx + 1 }}</div>
                <p class="text-xs font-semibold" :class="currentLevel >= idx ? 'text-emerald-700' : 'text-gray-500'">{{ level.name }}</p>
                <p class="text-[10px] mt-0.5" :class="currentLevel >= idx ? 'text-emerald-500' : 'text-gray-400'">{{ level.desc }}</p>
              </div>
            </div>
          </div>

          <!-- Chat messages -->
          <div v-for="(msg, i) in chatMessages" :key="i"
            :class="['flex', msg.role === 'user' ? 'justify-end' : 'justify-start']"
          >
            <div v-if="msg.role === 'assistant'" class="flex items-start gap-3 max-w-[85%]">
              <div class="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center shrink-0">
                <Bot class="w-4 h-4 text-white" />
              </div>
              <div class="bg-white border border-gray-100 rounded-2xl rounded-tl-sm px-5 py-3.5 shadow-sm">
                <div class="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap" v-html="renderMd(msg.content)"></div>
              </div>
            </div>
            <div v-else class="bg-emerald-600 text-white px-5 py-3 rounded-2xl rounded-tr-sm max-w-[70%] text-sm shadow-md shadow-emerald-500/20">
              {{ msg.content }}
            </div>
          </div>

          <div v-if="isTyping" class="flex items-start gap-3">
            <div class="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center shrink-0">
              <Bot class="w-4 h-4 text-white" />
            </div>
            <div class="bg-white border border-gray-100 rounded-2xl rounded-tl-sm px-5 py-3.5 shadow-sm">
              <div class="flex items-center gap-1.5">
                <div class="w-2 h-2 bg-emerald-400 rounded-full animate-bounce"></div>
                <div class="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style="animation-delay: 150ms;"></div>
                <div class="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style="animation-delay: 300ms;"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Input -->
        <div class="p-6 border-t border-gray-100 bg-white">
          <div class="flex gap-3 max-w-3xl mx-auto">
            <textarea
              v-model="userInput"
              @keydown.enter.exact.prevent="sendMessage"
              rows="1"
              placeholder="输入您想分析的话题，系统会渐进式深入..."
              class="flex-1 px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 resize-none transition-all"
              :disabled="isTyping"
              style="min-height: 44px; max-height: 120px;"
            ></textarea>
            <button @click="sendMessage" :disabled="!userInput.trim() || isTyping"
              class="px-5 py-3 bg-emerald-600 text-white rounded-xl font-medium text-sm hover:bg-emerald-700 disabled:opacity-50 transition-all shadow-lg shadow-emerald-500/20 active:scale-95 flex items-center gap-2">
              <Send class="w-4 h-4" /> 分析
            </button>
          </div>
        </div>
      </div>

      <!-- Right: Analysis Progress -->
      <div class="w-72 border-l border-gray-100 bg-gray-50/50 p-5 flex flex-col gap-4 shrink-0 overflow-y-auto custom-scrollbar">
        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <h4 class="text-xs font-bold text-gray-700 flex items-center gap-1.5 mb-3">
            <BarChart3 class="w-3.5 h-3.5 text-emerald-500" />
            当前分析进度
          </h4>
          <div class="space-y-3">
            <div v-for="(step, idx) in progressSteps" :key="idx">
              <div class="flex items-center justify-between mb-1">
                <span class="text-[11px] text-gray-500 flex items-center gap-1.5">
                  <component :is="step.done ? CheckCircle : Circle" :class="['w-3 h-3', step.done ? 'text-emerald-500' : 'text-gray-300']" />
                  {{ step.label }}
                </span>
                <span class="text-[10px] font-mono" :class="step.done ? 'text-emerald-600' : 'text-gray-400'">{{ step.done ? '✓' : '--' }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm flex-1">
          <h4 class="text-xs font-bold text-gray-700 flex items-center gap-1.5 mb-3">
            <Lightbulb class="w-3.5 h-3.5 text-amber-500" />
            可深入方向
          </h4>
          <div class="space-y-1.5">
            <button v-for="q in suggestions" :key="q"
              @click="userInput = q; sendMessage()"
              class="w-full text-left px-3 py-2 text-[11px] text-gray-600 bg-gray-50 hover:bg-emerald-50 hover:text-emerald-700 rounded-lg transition-all border border-gray-100 hover:border-emerald-200"
            >{{ q }}</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { marked } from 'marked'
import {
  Layers, Sparkles, BookOpen, Bot, Send, BarChart3, Lightbulb,
  CheckCircle, Circle
} from 'lucide-vue-next'

const analysisLevels = [
  { name: '概览', desc: '快速了解大局' },
  { name: '基础分析', desc: '核心指标解读' },
  { name: '深度对比', desc: '横向纵向对比' },
  { name: '风险评估', desc: '量化风险评分' },
  { name: '综合研判', desc: '全面投资建议' }
]

const currentLevel = ref(0)
const chatMessages = ref([])
const userInput = ref('')
const isTyping = ref(false)
const contentArea = ref(null)

const progressSteps = ref([
  { label: '数据收集', done: false },
  { label: '指标分析', done: false },
  { label: '行业对标', done: false },
  { label: '风险评估', done: false },
  { label: '综合建议', done: false }
])

const suggestions = ref([
  '这个行业的竞争格局如何？',
  '帮我对比同行业龙头企业',
  '有哪些潜在风险需要注意？',
  '给出具体的操作建议'
])

const renderMd = (t) => { try { return marked.parse(t) } catch { return t } }

const scrollToBottom = () => {
  nextTick(() => { if (contentArea.value) contentArea.value.scrollTop = contentArea.value.scrollHeight })
}

const selectLevel = (idx) => {
  if (idx <= currentLevel.value + 1) currentLevel.value = idx
}

const sendMessage = async () => {
  const text = userInput.value.trim()
  if (!text || isTyping.value) return
  chatMessages.value.push({ role: 'user', content: text })
  userInput.value = ''
  isTyping.value = true
  scrollToBottom()

  try {
    const token = localStorage.getItem('access_token')
    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, style: '渐进式引导分析' })
    })
    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = '', content = ''
    chatMessages.value.push({ role: 'assistant', content: '' })
    const idx = chatMessages.value.length - 1

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') break
          try {
            const p = JSON.parse(data)
            if (p.type === 'text') { content += p.text; chatMessages.value[idx].content = content; scrollToBottom() }
          } catch {}
        }
      }
    }
    if (currentLevel.value < analysisLevels.length - 1) currentLevel.value++
    progressSteps.value.forEach((s, i) => { if (i <= currentLevel.value) s.done = true })
  } catch {
    chatMessages.value.push({ role: 'assistant', content: '服务暂时不可用，请稍后再试。' })
  } finally {
    isTyping.value = false
    scrollToBottom()
  }
}

onMounted(() => {
  chatMessages.value.push({
    role: 'assistant',
    content: '欢迎使用渐进式引导分析！🌱\n\n我会从**概览**开始，逐步深入到**基础分析 → 深度对比 → 风险评估 → 综合研判**，每一步都会用通俗易懂的语言为您解读。\n\n请输入您感兴趣的股票、行业或话题，我们开始吧！'
  })
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }
</style>
