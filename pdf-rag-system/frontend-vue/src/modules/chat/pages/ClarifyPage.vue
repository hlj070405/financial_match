<template>
  <div class="h-full flex flex-col">
    <!-- Hero Section -->
    <div class="relative overflow-hidden bg-gradient-to-br from-indigo-50 via-white to-violet-50 border-b border-gray-100">
      <div class="absolute inset-0 opacity-30">
        <div class="absolute top-10 left-10 w-72 h-72 bg-indigo-200 rounded-full blur-3xl animate-pulse"></div>
        <div class="absolute bottom-0 right-20 w-56 h-56 bg-violet-200 rounded-full blur-3xl animate-pulse" style="animation-delay: 1s;"></div>
      </div>
      <div class="relative px-6 py-4">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-md shadow-indigo-500/20 shrink-0">
            <MessageSquare class="w-4.5 h-4.5 text-white" />
          </div>
          <div>
            <h1 class="text-base font-bold text-gray-900">多轮需求澄清</h1>
            <p class="text-xs text-gray-500 mt-0.5 max-w-xl">通过智能对话逐步理解您的真实分析意图，为您精准匹配最佳分析方案</p>
            <div class="flex items-center gap-2 mt-2">
              <span class="inline-flex items-center gap-1.5 px-2.5 py-1 bg-indigo-100 text-indigo-700 text-xs font-medium rounded-full">
                <Sparkles class="w-3 h-3" /> AI 驱动
              </span>
              <span class="inline-flex items-center gap-1.5 px-2.5 py-1 bg-emerald-100 text-emerald-700 text-xs font-medium rounded-full">
                <Globe class="w-3 h-3" /> 联网搜索
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Chat Area -->
    <div class="flex-1 flex min-h-0">
      <!-- Main Chat -->
      <div class="flex-1 flex flex-col">
        <div ref="chatArea" class="flex-1 overflow-y-auto px-8 py-6 space-y-6 custom-scrollbar">
          <!-- Stage Indicator -->
          <div class="flex items-center gap-3 justify-center mb-4">
            <div v-for="(stage, idx) in stages" :key="idx"
              class="flex items-center gap-2"
            >
              <div :class="[
                'w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-500',
                currentStage >= idx
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/30 scale-110'
                  : 'bg-gray-100 text-gray-400'
              ]">{{ idx + 1 }}</div>
              <span :class="['text-xs font-medium transition-colors', currentStage >= idx ? 'text-indigo-600' : 'text-gray-400']">{{ stage }}</span>
              <ChevronRight v-if="idx < stages.length - 1" class="w-4 h-4 text-gray-300" />
            </div>
          </div>

          <!-- Messages -->
          <div v-for="(msg, i) in chatMessages" :key="i"
            :class="['flex', msg.role === 'user' ? 'justify-end' : 'justify-start']"
          >
            <div v-if="msg.role === 'assistant'" class="flex items-start gap-3 max-w-[80%]">
              <div class="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center shrink-0">
                <Bot class="w-4 h-4 text-white" />
              </div>
              <div class="bg-white border border-gray-100 rounded-2xl rounded-tl-sm px-5 py-3.5 shadow-sm">
                <div class="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap" v-html="renderMarkdown(msg.content)"></div>
              </div>
            </div>
            <div v-else class="bg-indigo-600 text-white px-5 py-3 rounded-2xl rounded-tr-sm max-w-[70%] text-sm shadow-md shadow-indigo-500/20">
              {{ msg.content }}
            </div>
          </div>

          <!-- Typing indicator -->
          <div v-if="isTyping" class="flex items-start gap-3">
            <div class="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center shrink-0">
              <Bot class="w-4 h-4 text-white" />
            </div>
            <div class="bg-white border border-gray-100 rounded-2xl rounded-tl-sm px-5 py-3.5 shadow-sm">
              <div class="flex items-center gap-1.5">
                <div class="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style="animation-delay: 0ms;"></div>
                <div class="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style="animation-delay: 150ms;"></div>
                <div class="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style="animation-delay: 300ms;"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Input -->
        <div class="p-6 border-t border-gray-100 bg-white">
          <div class="flex gap-3 max-w-3xl mx-auto">
            <div class="flex-1 relative">
              <textarea
                v-model="userInput"
                @keydown.enter.exact.prevent="sendMessage"
                rows="1"
                placeholder="描述您想了解的投资或分析需求..."
                class="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 resize-none transition-all"
                :disabled="isTyping"
                style="min-height: 44px; max-height: 120px;"
              ></textarea>
            </div>
            <button
              @click="sendMessage"
              :disabled="!userInput.trim() || isTyping"
              class="px-5 py-3 bg-indigo-600 text-white rounded-xl font-medium text-sm hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-indigo-500/20 active:scale-95 flex items-center gap-2"
            >
              <Send class="w-4 h-4" />
              发送
            </button>
          </div>
        </div>
      </div>

      <!-- Right: Clarification Summary -->
      <div class="w-72 border-l border-gray-100 bg-gray-50/50 p-5 flex flex-col gap-4 shrink-0 overflow-y-auto custom-scrollbar">
        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <h4 class="text-xs font-bold text-gray-700 flex items-center gap-1.5 mb-3">
            <Target class="w-3.5 h-3.5 text-indigo-500" />
            需求画像
          </h4>
          <div class="space-y-2.5">
            <div v-for="(item, key) in clarifiedProfile" :key="key" class="flex items-start gap-2">
              <div class="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-1.5 shrink-0"></div>
              <div>
                <p class="text-[11px] font-medium text-gray-500">{{ item.label }}</p>
                <p class="text-xs text-gray-800 font-medium">{{ item.value || '待确认' }}</p>
              </div>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <h4 class="text-xs font-bold text-gray-700 flex items-center gap-1.5 mb-3">
            <Lightbulb class="w-3.5 h-3.5 text-amber-500" />
            快捷问题
          </h4>
          <div class="space-y-1.5">
            <button
              v-for="q in quickQuestions"
              :key="q"
              @click="userInput = q; sendMessage()"
              class="w-full text-left px-3 py-2 text-[11px] text-gray-600 bg-gray-50 hover:bg-indigo-50 hover:text-indigo-700 rounded-lg transition-all border border-gray-100 hover:border-indigo-200"
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
  MessageSquare, Sparkles, Globe, Bot, Send, ChevronRight,
  Target, Lightbulb
} from 'lucide-vue-next'

const stages = ['理解意图', '信息收集', '需求确认', '方案匹配']
const currentStage = ref(0)
const chatMessages = ref([])
const userInput = ref('')
const isTyping = ref(false)
const chatArea = ref(null)

const clarifiedProfile = ref({
  target: { label: '分析对象', value: '' },
  type: { label: '分析类型', value: '' },
  period: { label: '时间范围', value: '' },
  risk: { label: '风险偏好', value: '' },
  depth: { label: '分析深度', value: '' }
})

const quickQuestions = [
  '帮我分析比亚迪的投资价值',
  '新能源行业未来趋势如何？',
  '最近有什么值得关注的金融热点？',
  '帮我对比几家银行股的估值'
]

const renderMarkdown = (text) => {
  try { return marked.parse(text) } catch { return text }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (chatArea.value) chatArea.value.scrollTop = chatArea.value.scrollHeight
  })
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
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message: text,
        style: '多轮需求澄清'
      })
    })

    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let assistantContent = ''
    chatMessages.value.push({ role: 'assistant', content: '' })
    const msgIdx = chatMessages.value.length - 1

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
            const parsed = JSON.parse(data)
            if (parsed.type === 'text') {
              assistantContent += parsed.text
              chatMessages.value[msgIdx].content = assistantContent
              scrollToBottom()
            }
          } catch {}
        }
      }
    }

    if (currentStage.value < stages.length - 1) currentStage.value++
  } catch (e) {
    chatMessages.value.push({ role: 'assistant', content: '抱歉，服务暂时不可用，请稍后再试。' })
  } finally {
    isTyping.value = false
    scrollToBottom()
  }
}

onMounted(() => {
  chatMessages.value.push({
    role: 'assistant',
    content: '您好！我是幻流智能咨询助手。\n\n请告诉我您想分析什么？我会通过几轮对话逐步了解您的需求，为您匹配最佳的分析方案。\n\n例如：\n- 某只股票的投资价值分析\n- 行业趋势与竞争格局\n- 宏观经济形势研判'
  })
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }
</style>
