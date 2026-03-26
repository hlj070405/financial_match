<template>
  <div class="h-full flex flex-col">
    <!-- Hero -->
    <div class="relative overflow-hidden bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 border-b border-gray-700">
      <div class="absolute inset-0 opacity-30">
        <div class="absolute top-5 left-20 w-64 h-64 bg-violet-500 rounded-full blur-3xl animate-pulse"></div>
        <div class="absolute bottom-0 right-10 w-48 h-48 bg-indigo-500 rounded-full blur-3xl animate-pulse" style="animation-delay: 1s;"></div>
      </div>
      <div class="relative px-6 py-4">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center shadow-md shadow-violet-500/30 shrink-0 ring-1 ring-violet-400/30">
            <Zap class="w-4.5 h-4.5 text-white" />
          </div>
          <div>
            <h1 class="text-base font-bold text-white">专业直达模式</h1>
            <p class="text-xs text-gray-400 mt-0.5 max-w-xl">跳过澄清流程，直接进入专业级深度分析，面向资深投资者</p>
            <div class="flex items-center gap-2 mt-2">
              <span class="inline-flex items-center gap-1.5 px-2.5 py-1 bg-violet-500/20 text-violet-300 text-xs font-medium rounded-full border border-violet-500/30">
                <Sparkles class="w-3 h-3" /> 专业级
              </span>
              <span class="inline-flex items-center gap-1.5 px-2.5 py-1 bg-indigo-500/20 text-indigo-300 text-xs font-medium rounded-full border border-indigo-500/30">
                <Globe class="w-3 h-3" /> 联网深度搜索
              </span>
              <span class="inline-flex items-center gap-1.5 px-2.5 py-1 bg-amber-500/20 text-amber-300 text-xs font-medium rounded-full border border-amber-500/30">
                <Shield class="w-3 h-3" /> 专业投资者
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="flex-1 flex min-h-0 bg-gray-950">
      <!-- Main Chat -->
      <div class="flex-1 flex flex-col min-h-0">
        <div ref="chatArea" class="flex-1 overflow-y-auto px-8 py-6 space-y-6 custom-scrollbar-dark">
          <div v-for="(msg, i) in chatMessages" :key="i"
            :class="['flex', msg.role === 'user' ? 'justify-end' : 'justify-start']"
          >
            <div v-if="msg.role === 'assistant'" class="flex items-start gap-3 max-w-[85%]">
              <div class="w-8 h-8 rounded-lg bg-violet-600 flex items-center justify-center shrink-0 ring-1 ring-violet-500/50">
                <Bot class="w-4 h-4 text-white" />
              </div>
              <div class="bg-gray-900 border border-gray-800 rounded-2xl rounded-tl-sm px-5 py-4 shadow-lg">
                <div class="prose-dark text-sm text-gray-300 leading-relaxed" v-html="renderMd(msg.content)"></div>
              </div>
            </div>
            <div v-else class="bg-violet-600 text-white px-5 py-3 rounded-2xl rounded-tr-sm max-w-[70%] text-sm shadow-lg shadow-violet-500/20">
              {{ msg.content }}
            </div>
          </div>

          <div v-if="isTyping" class="flex items-start gap-3">
            <div class="w-8 h-8 rounded-lg bg-violet-600 flex items-center justify-center shrink-0">
              <Bot class="w-4 h-4 text-white" />
            </div>
            <div class="bg-gray-900 border border-gray-800 rounded-2xl rounded-tl-sm px-5 py-4">
              <div class="flex items-center gap-2">
                <Loader2 class="w-4 h-4 text-violet-400 animate-spin" />
                <span class="text-xs text-violet-400 font-medium">{{ typingPhase }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Input -->
        <div class="p-6 border-t border-gray-800 bg-gray-900/80 backdrop-blur">
          <div class="flex gap-3 max-w-3xl mx-auto">
            <textarea
              v-model="userInput"
              @keydown.enter.exact.prevent="sendMessage"
              rows="1"
              placeholder="直接输入专业分析需求，如：分析贵州茅台的DCF估值模型..."
              class="flex-1 px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-violet-500/30 focus:border-violet-500 resize-none transition-all"
              :disabled="isTyping"
              style="min-height: 44px; max-height: 120px;"
            ></textarea>
            <button @click="sendMessage" :disabled="!userInput.trim() || isTyping"
              class="px-5 py-3 bg-violet-600 text-white rounded-xl font-medium text-sm hover:bg-violet-700 disabled:opacity-40 transition-all shadow-lg shadow-violet-500/30 active:scale-95 flex items-center gap-2">
              <Send class="w-4 h-4" /> 分析
            </button>
          </div>
        </div>
      </div>

      <!-- Right: Pro Tools -->
      <div class="w-72 border-l border-gray-800 bg-gray-900/50 p-5 flex flex-col gap-4 shrink-0 overflow-y-auto custom-scrollbar-dark">
        <div class="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <h4 class="text-xs font-bold text-gray-400 flex items-center gap-1.5 mb-3 uppercase tracking-wider">
            <Terminal class="w-3.5 h-3.5 text-violet-400" />
            专业分析模板
          </h4>
          <div class="space-y-1.5">
            <button v-for="tmpl in templates" :key="tmpl.label"
              @click="userInput = tmpl.prompt; sendMessage()"
              class="w-full text-left px-3 py-2.5 text-[11px] text-gray-400 bg-gray-800/50 hover:bg-violet-500/10 hover:text-violet-300 rounded-lg transition-all border border-gray-800 hover:border-violet-500/30">
              <span class="font-medium text-gray-300">{{ tmpl.label }}</span>
              <p class="text-[10px] text-gray-500 mt-0.5">{{ tmpl.desc }}</p>
            </button>
          </div>
        </div>

        <div class="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <h4 class="text-xs font-bold text-gray-400 flex items-center gap-1.5 mb-3 uppercase tracking-wider">
            <Activity class="w-3.5 h-3.5 text-emerald-400" />
            会话统计
          </h4>
          <div class="space-y-2">
            <div class="flex items-center justify-between text-xs">
              <span class="text-gray-500">消息数</span>
              <span class="text-gray-300 font-mono">{{ chatMessages.length }}</span>
            </div>
            <div class="flex items-center justify-between text-xs">
              <span class="text-gray-500">搜索调用</span>
              <span class="text-emerald-400 font-mono">{{ searchCount }}</span>
            </div>
            <div class="flex items-center justify-between text-xs">
              <span class="text-gray-500">响应字数</span>
              <span class="text-gray-300 font-mono">{{ totalChars.toLocaleString() }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, computed } from 'vue'
import { marked } from 'marked'
import { Zap, Sparkles, Globe, Shield, Bot, Send, Loader2, Terminal, Activity } from 'lucide-vue-next'

const chatMessages = ref([])
const userInput = ref('')
const isTyping = ref(false)
const typingPhase = ref('深度分析中...')
const chatArea = ref(null)
const searchCount = ref(0)

const totalChars = computed(() => chatMessages.value.filter(m => m.role === 'assistant').reduce((s, m) => s + (m.content?.length || 0), 0))

const templates = [
  { label: 'DCF估值分析', desc: '现金流折现模型', prompt: '请对贵州茅台进行DCF估值分析，给出关键假设和目标价' },
  { label: '行业竞争格局', desc: '波特五力模型', prompt: '请用波特五力模型分析半导体行业的竞争格局' },
  { label: '财务造假筛查', desc: 'Beneish M-Score', prompt: '请用Beneish M-Score模型筛查最近财报是否存在财务操纵风险' },
  { label: '量化因子分析', desc: '多因子选股', prompt: '请分析当前A股市场中价值因子和动量因子的有效性' },
  { label: '宏观经济研判', desc: '美林时钟框架', prompt: '基于当前经济数据，用美林时钟分析当前所处的经济周期阶段' }
]

const renderMd = (t) => { try { return marked.parse(t) } catch { return t } }

const scrollToBottom = () => {
  nextTick(() => { if (chatArea.value) chatArea.value.scrollTop = chatArea.value.scrollHeight })
}

const sendMessage = async () => {
  const text = userInput.value.trim()
  if (!text || isTyping.value) return
  chatMessages.value.push({ role: 'user', content: text })
  userInput.value = ''
  isTyping.value = true
  typingPhase.value = '联网搜索中...'
  scrollToBottom()

  try {
    const token = localStorage.getItem('access_token')
    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, style: '专业直达模式' })
    })
    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = '', content = ''
    chatMessages.value.push({ role: 'assistant', content: '' })
    const idx = chatMessages.value.length - 1
    let gotContent = false

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
            if (p.type === 'text') {
              if (!gotContent) { typingPhase.value = '生成分析报告...'; gotContent = true }
              content += p.text
              chatMessages.value[idx].content = content
              scrollToBottom()
            }
          } catch {}
        }
      }
    }
    searchCount.value++
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
    content: '**专业直达模式已激活** ⚡\n\n跳过常规澄清流程，直接进行深度分析。请输入具体分析需求：\n\n- 输入股票名称/代码 → 直接获取全维度分析\n- 使用右侧专业模板 → 快速启动特定分析框架\n- 自由提问 → AI联网搜索并生成专业报告\n\n> *本模式面向专业投资者，输出包含完整的专业术语和量化指标。*'
  })
})
</script>

<style scoped>
.custom-scrollbar-dark::-webkit-scrollbar { width: 4px; }
.custom-scrollbar-dark::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar-dark::-webkit-scrollbar-thumb { background: #374151; border-radius: 4px; }
.custom-scrollbar-dark::-webkit-scrollbar-thumb:hover { background: #4b5563; }

.prose-dark :deep(h1), .prose-dark :deep(h2), .prose-dark :deep(h3) { color: #e5e7eb; }
.prose-dark :deep(strong) { color: #d1d5db; }
.prose-dark :deep(code) { color: #a78bfa; background: #1f2937; padding: 2px 6px; border-radius: 4px; font-size: 12px; }
.prose-dark :deep(pre) { background: #111827; border: 1px solid #1f2937; border-radius: 8px; padding: 12px; overflow-x: auto; }
.prose-dark :deep(pre code) { background: none; padding: 0; }
.prose-dark :deep(blockquote) { border-left: 3px solid #6d28d9; padding-left: 12px; color: #9ca3af; font-style: italic; }
.prose-dark :deep(table) { width: 100%; border-collapse: collapse; }
.prose-dark :deep(th) { background: #1f2937; color: #d1d5db; padding: 8px; text-align: left; font-size: 12px; }
.prose-dark :deep(td) { border-top: 1px solid #1f2937; padding: 8px; font-size: 12px; }
.prose-dark :deep(a) { color: #a78bfa; text-decoration: underline; }
.prose-dark :deep(ul), .prose-dark :deep(ol) { padding-left: 1.5em; }
.prose-dark :deep(li) { margin-bottom: 4px; }
</style>
