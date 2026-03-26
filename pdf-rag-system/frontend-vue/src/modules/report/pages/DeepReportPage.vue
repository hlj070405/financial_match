<template>
  <div class="h-full flex flex-col">
    <!-- Hero -->
    <div class="relative overflow-hidden bg-gradient-to-br from-slate-800 via-gray-900 to-slate-900 border-b border-gray-700">
      <div class="absolute inset-0 opacity-20">
        <div class="absolute top-3 left-16 w-48 h-48 bg-blue-500 rounded-full blur-3xl animate-pulse"></div>
        <div class="absolute bottom-0 right-10 w-40 h-40 bg-indigo-500 rounded-full blur-3xl animate-pulse" style="animation-delay:1s"></div>
      </div>
      <div class="relative px-6 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-md shrink-0">
              <BookOpen class="w-4.5 h-4.5 text-white" />
            </div>
            <div>
              <h1 class="text-base font-bold text-white">深度行业报告</h1>
              <p class="text-[11px] text-gray-400 mt-0.5">整合多源数据生成专业级行业研究报告，覆盖全产业链</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <input v-model="industry" type="text" placeholder="输入行业名称..."
              class="px-3 py-2 text-xs border border-gray-600 rounded-lg bg-gray-800 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40 w-40 transition-all" />
            <button @click="generateDeep" :disabled="generating"
              class="px-4 py-2 bg-blue-600 text-white text-xs font-medium rounded-lg hover:bg-blue-500 transition-colors disabled:opacity-50 flex items-center gap-1.5">
              <Loader2 v-if="generating" class="w-3.5 h-3.5 animate-spin" />
              <Sparkles v-else class="w-3.5 h-3.5" />
              {{ generating ? '生成中...' : '深度生成' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="flex-1 flex min-h-0 bg-gray-950">
      <!-- Outline Left -->
      <div class="w-56 border-r border-gray-800 bg-gray-900 p-4 flex flex-col gap-2 shrink-0 overflow-y-auto custom-scrollbar-dark">
        <p class="text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-2">报告大纲</p>
        <div v-for="(ch, i) in chapters" :key="i"
          @click="scrollToChapter(i)"
          :class="['px-3 py-2 rounded-lg cursor-pointer transition-all text-xs',
            activeChapter === i ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30' : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200 border border-transparent']">
          <div class="flex items-center gap-2">
            <span class="w-5 h-5 rounded bg-gray-800 text-[10px] font-bold flex items-center justify-center shrink-0"
              :class="activeChapter === i ? 'bg-blue-600/30 text-blue-300' : ''">{{ i + 1 }}</span>
            <span class="truncate">{{ ch.title }}</span>
          </div>
          <div v-if="generating" class="mt-1.5 ml-7">
            <div class="w-full h-1 bg-gray-800 rounded-full overflow-hidden">
              <div class="h-full bg-blue-500 rounded-full transition-all duration-500"
                :style="{ width: ch.progress + '%' }"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Main Content -->
      <div class="flex-1 overflow-y-auto custom-scrollbar-dark p-6">
        <div v-if="!generating && !reportContent" class="flex items-center justify-center h-full">
          <div class="text-center max-w-sm">
            <div class="p-4 rounded-2xl bg-gray-800 inline-block mb-4">
              <BookOpen class="w-12 h-12 text-gray-600" />
            </div>
            <h3 class="text-sm font-semibold text-gray-300 mb-2">输入行业主题开始生成</h3>
            <p class="text-xs text-gray-500 leading-relaxed mb-4">深度报告将包含行业规模、竞争格局、产业链、政策环境、投资逻辑等专业章节</p>
            <div class="flex flex-wrap gap-2 justify-center">
              <button v-for="ex in examples" :key="ex" @click="industry = ex; generateDeep()"
                class="px-3 py-1.5 text-[11px] text-gray-400 bg-gray-800 border border-gray-700 rounded-lg hover:bg-blue-900/30 hover:border-blue-600/50 hover:text-blue-300 transition-all">{{ ex }}</button>
            </div>
          </div>
        </div>

        <div v-else class="max-w-3xl mx-auto">
          <div class="prose prose-invert prose-sm max-w-none
            prose-headings:text-gray-100 prose-headings:font-bold
            prose-h2:text-base prose-h2:border-b prose-h2:border-gray-800 prose-h2:pb-2 prose-h2:mt-8
            prose-h3:text-sm prose-h3:mt-4 prose-h3:text-gray-300
            prose-p:text-xs prose-p:text-gray-400 prose-p:leading-relaxed
            prose-strong:text-gray-200
            prose-li:text-xs prose-li:text-gray-400
            prose-table:text-xs prose-table:border-gray-800
            prose-th:bg-gray-800 prose-th:text-gray-300 prose-th:px-3 prose-th:py-2
            prose-td:px-3 prose-td:py-2 prose-td:border-gray-800 prose-td:text-gray-400
            prose-code:text-blue-400 prose-code:bg-gray-800 prose-code:px-1 prose-code:rounded"
            v-html="renderedContent">
          </div>
          <div v-if="generating" class="mt-4 flex items-center gap-2 text-xs text-gray-500">
            <Loader2 class="w-3.5 h-3.5 animate-spin text-blue-500" />
            <span>{{ generateStatus }}</span>
          </div>
        </div>
      </div>

      <!-- Right: Meta -->
      <div class="w-56 border-l border-gray-800 bg-gray-900 p-4 flex flex-col gap-3 shrink-0 overflow-y-auto custom-scrollbar-dark">
        <div class="bg-gray-800/50 rounded-xl border border-gray-700/50 p-3">
          <h4 class="text-[10px] font-bold text-gray-500 mb-2">报告元数据</h4>
          <div class="space-y-2 text-[11px]">
            <div class="flex justify-between"><span class="text-gray-500">类型</span><span class="text-gray-300">深度行业报告</span></div>
            <div class="flex justify-between"><span class="text-gray-500">字数</span><span class="text-blue-400 font-mono">{{ wordCount }}</span></div>
            <div class="flex justify-between"><span class="text-gray-500">章节</span><span class="text-gray-300">{{ chapters.length }}</span></div>
            <div class="flex justify-between"><span class="text-gray-500">数据源</span><span class="text-gray-300">联网实时</span></div>
          </div>
        </div>
        <div class="bg-gray-800/50 rounded-xl border border-gray-700/50 p-3">
          <h4 class="text-[10px] font-bold text-gray-500 mb-2">分析框架</h4>
          <div class="space-y-1">
            <div v-for="fw in frameworks" :key="fw" class="flex items-center gap-2 text-[10px] text-gray-400">
              <div class="w-1.5 h-1.5 rounded-full bg-blue-500"></div>
              <span>{{ fw }}</span>
            </div>
          </div>
        </div>
        <div class="bg-gray-800/50 rounded-xl border border-gray-700/50 p-3 flex-1">
          <h4 class="text-[10px] font-bold text-gray-500 mb-2">操作</h4>
          <div class="space-y-2">
            <button class="w-full py-2 text-[10px] font-medium text-gray-300 bg-gray-700/50 rounded-lg hover:bg-gray-700 transition-all flex items-center justify-center gap-1.5">
              <Download class="w-3 h-3" /> 导出 Word
            </button>
            <button class="w-full py-2 text-[10px] font-medium text-gray-300 bg-gray-700/50 rounded-lg hover:bg-gray-700 transition-all flex items-center justify-center gap-1.5">
              <Download class="w-3 h-3" /> 导出 PDF
            </button>
            <button class="w-full py-2 text-[10px] font-medium text-blue-400 bg-blue-600/10 border border-blue-600/30 rounded-lg hover:bg-blue-600/20 transition-all flex items-center justify-center gap-1.5">
              <RefreshCw class="w-3 h-3" /> 重新生成
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { marked } from 'marked'
import { BookOpen, Sparkles, Loader2, Download, RefreshCw } from 'lucide-vue-next'

const industry = ref('')
const generating = ref(false)
const reportContent = ref('')
const generateStatus = ref('')
const activeChapter = ref(0)

const examples = ['人工智能', '新能源汽车', '创新药', '半导体', '机器人']
const frameworks = ['PEST分析', 'Porter五力模型', '产业链价值分析', 'SWOT分析', '估值模型']

const chapters = ref([
  { title: '行业概况与定义', progress: 0 },
  { title: '市场规模与增速', progress: 0 },
  { title: '产业链全景', progress: 0 },
  { title: '竞争格局分析', progress: 0 },
  { title: '技术发展趋势', progress: 0 },
  { title: '政策与监管', progress: 0 },
  { title: '投资逻辑与建议', progress: 0 },
  { title: '风险提示', progress: 0 }
])

const wordCount = computed(() => reportContent.value.length)
const renderedContent = computed(() => reportContent.value ? marked.parse(reportContent.value) : '')

const scrollToChapter = (i) => { activeChapter.value = i }

const generateDeep = async () => {
  if (!industry.value.trim() || generating.value) return
  generating.value = true
  reportContent.value = ''
  generateStatus.value = '正在联网搜索行业数据...'
  chapters.value.forEach(c => { c.progress = 0 })

  try {
    const token = localStorage.getItem('access_token')
    const prompt = `请搜索"${industry.value}"行业最新数据，生成一份专业级深度行业研究报告（不少于2000字）。报告结构：
## 1. 行业概况与定义
## 2. 市场规模与增速（含数据表格）
## 3. 产业链全景分析（上游/中游/下游）
## 4. 竞争格局分析（含市场份额表格和龙头企业对比）
## 5. 技术发展趋势
## 6. 政策与监管环境
## 7. 投资逻辑与标的推荐（含估值对比表格）
## 8. 风险提示
请使用Markdown格式，引用具体数据和来源。`

    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: prompt, style: '深度研报', user_role: localStorage.getItem('user_role') || null })
    })
    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = '', charCount = 0
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
              reportContent.value += p.text
              charCount += p.text.length
              const chIdx = Math.min(Math.floor(charCount / 300), chapters.value.length - 1)
              for (let i = 0; i <= chIdx; i++) chapters.value[i].progress = 100
              if (chIdx < chapters.value.length - 1) chapters.value[chIdx + 1].progress = Math.min(90, (charCount % 300) / 3)
              activeChapter.value = chIdx
              const statuses = ['正在搜索行业数据...', '正在分析市场规模...', '正在梳理产业链...', '正在对比竞争格局...', '正在分析技术趋势...', '正在整合政策环境...', '正在形成投资建议...', '正在完善风险提示...']
              generateStatus.value = statuses[Math.min(chIdx, statuses.length - 1)]
            }
          } catch {}
        }
      }
    }
    chapters.value.forEach(c => { c.progress = 100 })
  } catch {
    reportContent.value = '## 生成失败\n\n暂时无法生成报告，请稍后再试。'
  } finally {
    setTimeout(() => { generating.value = false }, 500)
  }
}
</script>

<style scoped>
.custom-scrollbar-dark::-webkit-scrollbar { width: 4px; }
.custom-scrollbar-dark::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar-dark::-webkit-scrollbar-thumb { background: #374151; border-radius: 4px; }
</style>
