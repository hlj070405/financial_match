<template>
  <div class="h-full flex flex-col">
    <!-- Hero -->
    <div class="relative overflow-hidden bg-gradient-to-br from-sky-50 via-white to-blue-50 border-b border-gray-100">
      <div class="absolute inset-0 opacity-20">
        <div class="absolute top-3 left-16 w-48 h-48 bg-sky-200 rounded-full blur-3xl animate-pulse"></div>
        <div class="absolute bottom-0 right-10 w-40 h-40 bg-blue-200 rounded-full blur-3xl animate-pulse" style="animation-delay:1s"></div>
      </div>
      <div class="relative px-6 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-sky-500 to-blue-600 flex items-center justify-center shadow-md shadow-sky-500/20 shrink-0">
              <FileText class="w-4.5 h-4.5 text-white" />
            </div>
            <div>
              <h1 class="text-base font-bold text-gray-900">摘要报告</h1>
              <p class="text-[11px] text-gray-500 mt-0.5">一键生成行业或个股分析摘要，AI联网搜索最新数据</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <select v-model="reportType" class="px-3 py-2 text-xs border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-sky-500/20">
              <option value="stock">个股分析</option>
              <option value="industry">行业分析</option>
              <option value="macro">宏观研判</option>
            </select>
            <input v-model="topic" @keydown.enter="generateReport" type="text" placeholder="输入分析主题..."
              class="px-3 py-2 text-xs border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-400 w-40 transition-all" />
            <button @click="generateReport" :disabled="generating"
              class="px-4 py-2 bg-sky-600 text-white text-xs font-medium rounded-lg hover:bg-sky-700 transition-colors disabled:opacity-50 flex items-center gap-1.5">
              <Loader2 v-if="generating" class="w-3.5 h-3.5 animate-spin" />
              <Sparkles v-else class="w-3.5 h-3.5" />
              {{ generating ? '生成中...' : '生成报告' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="flex-1 flex min-h-0">
      <!-- Document Preview -->
      <div class="flex-1 overflow-y-auto custom-scrollbar bg-gray-100/60">
        <!-- Empty -->
        <div v-if="!generating && !reportContent" class="flex items-center justify-center h-full">
          <div class="text-center max-w-sm">
            <div class="p-4 rounded-2xl bg-white shadow-sm inline-block mb-4">
              <FileText class="w-12 h-12 text-gray-300" />
            </div>
            <h3 class="text-sm font-semibold text-gray-700 mb-2">选择主题生成分析报告</h3>
            <p class="text-xs text-gray-400 leading-relaxed mb-4">AI将联网搜索最新数据，自动生成结构化分析报告</p>
            <div class="flex flex-wrap gap-2 justify-center">
              <button v-for="ex in examples" :key="ex" @click="topic = ex; generateReport()"
                class="px-3 py-1.5 text-[11px] text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-sky-50 hover:border-sky-300 hover:text-sky-700 transition-all shadow-sm">{{ ex }}</button>
            </div>
          </div>
        </div>

        <!-- Document -->
        <div v-else class="max-w-3xl mx-auto my-8">
          <div class="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
            <!-- Doc Header -->
            <div class="bg-gradient-to-r from-sky-600 to-blue-600 px-8 py-6 text-white">
              <div class="flex items-center gap-2 mb-2">
                <FileText class="w-4 h-4 text-sky-200" />
                <span class="text-[10px] font-bold text-sky-200 uppercase tracking-wider">AI 研究报告</span>
              </div>
              <h2 class="text-lg font-bold">{{ topic || '分析报告' }}</h2>
              <div class="flex items-center gap-3 mt-2 text-xs text-sky-200">
                <span>{{ reportType === 'stock' ? '个股分析' : reportType === 'industry' ? '行业分析' : '宏观研判' }}</span>
                <span>·</span>
                <span>{{ new Date().toLocaleDateString('zh-CN') }}</span>
                <span>·</span>
                <span>AI自动生成</span>
              </div>
            </div>

            <!-- Progress Bar -->
            <div v-if="generating" class="px-8 pt-4">
              <div class="flex items-center gap-3 mb-2">
                <Loader2 class="w-4 h-4 animate-spin text-sky-500" />
                <span class="text-xs text-gray-500">{{ generateStatus }}</span>
              </div>
              <div class="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div class="h-full bg-sky-500 rounded-full transition-all duration-500"
                  :style="{ width: generateProgress + '%' }"></div>
              </div>
            </div>

            <!-- Content -->
            <div class="px-8 py-6 prose prose-sm max-w-none
              prose-headings:text-gray-900 prose-headings:font-bold
              prose-h2:text-base prose-h2:border-b prose-h2:border-gray-100 prose-h2:pb-2 prose-h2:mt-6
              prose-h3:text-sm prose-h3:mt-4
              prose-p:text-xs prose-p:text-gray-600 prose-p:leading-relaxed
              prose-strong:text-gray-800
              prose-li:text-xs prose-li:text-gray-600
              prose-table:text-xs
              prose-th:bg-gray-50 prose-th:text-gray-700 prose-th:font-bold prose-th:px-3 prose-th:py-2
              prose-td:px-3 prose-td:py-2 prose-td:border-gray-100"
              v-html="renderedContent">
            </div>

            <!-- Footer -->
            <div v-if="reportContent && !generating" class="px-8 py-4 bg-gray-50 border-t border-gray-100 flex items-center justify-between">
              <span class="text-[10px] text-gray-400">本报告由AI自动生成，仅供参考，不构成投资建议</span>
              <div class="flex items-center gap-2">
                <button class="px-3 py-1.5 text-[10px] font-medium text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-all flex items-center gap-1">
                  <Copy class="w-3 h-3" /> 复制
                </button>
                <button class="px-3 py-1.5 text-[10px] font-medium text-white bg-gray-900 rounded-lg hover:bg-gray-800 transition-all flex items-center gap-1">
                  <Download class="w-3 h-3" /> 导出PDF
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: History -->
      <div class="w-64 border-l border-gray-100 bg-gray-50/50 p-4 flex flex-col gap-3 shrink-0 overflow-y-auto custom-scrollbar">
        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <h4 class="text-[11px] font-bold text-gray-700 flex items-center gap-1.5 mb-3">
            <Clock class="w-3.5 h-3.5 text-sky-500" /> 最近报告
          </h4>
          <div class="space-y-2">
            <div v-for="h in history" :key="h.title"
              class="p-2.5 rounded-lg border border-gray-100 hover:bg-sky-50 hover:border-sky-200 cursor-pointer transition-all group">
              <p class="text-[11px] font-medium text-gray-700 group-hover:text-sky-700 line-clamp-1">{{ h.title }}</p>
              <div class="flex items-center gap-2 mt-1">
                <span class="text-[9px] text-gray-400">{{ h.date }}</span>
                <span class="text-[9px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-500">{{ h.type }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm flex-1">
          <h4 class="text-[11px] font-bold text-gray-700 flex items-center gap-1.5 mb-3">
            <TrendingUp class="w-3.5 h-3.5 text-amber-500" /> 热门主题
          </h4>
          <div class="flex flex-wrap gap-1.5">
            <button v-for="hot in hotTopics" :key="hot" @click="topic = hot"
              class="px-2.5 py-1 text-[10px] text-gray-600 bg-gray-50 border border-gray-100 rounded-lg hover:bg-amber-50 hover:border-amber-200 hover:text-amber-700 transition-all">{{ hot }}</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { marked } from 'marked'
import { FileText, Sparkles, Loader2, Copy, Download, Clock, TrendingUp } from 'lucide-vue-next'

const topic = ref('')
const reportType = ref('stock')
const generating = ref(false)
const reportContent = ref('')
const generateProgress = ref(0)
const generateStatus = ref('')

const examples = ['贵州茅台2024年投资价值', '新能源汽车行业前景', '2024宏观经济展望', 'AI算力产业链']
const hotTopics = ['半导体国产替代', '低空经济', '人形机器人', '量化交易', '碳中和', '跨境电商', '创新药出海', '数据要素']

const history = ref([
  { title: '比亚迪竞争力分析', date: '2024-03-14', type: '个股' },
  { title: '光伏行业过剩周期', date: '2024-03-12', type: '行业' },
  { title: 'A股市场风格切换', date: '2024-03-10', type: '宏观' }
])

const renderedContent = computed(() => reportContent.value ? marked.parse(reportContent.value) : '')

const generateReport = async () => {
  if (!topic.value.trim() || generating.value) return
  generating.value = true
  reportContent.value = ''
  generateProgress.value = 0
  generateStatus.value = '正在联网搜索最新数据...'

  try {
    const token = localStorage.getItem('access_token')
    const prompt = reportType.value === 'stock'
      ? `请搜索"${topic.value}"的最新数据，生成一份完整的个股分析报告。报告应包含：## 公司概况、## 财务分析（含关键指标表格）、## 行业地位与竞争优势、## 近期重大事件、## 风险提示、## 投资建议与目标价。使用Markdown格式，数据尽量引用具体数字。`
      : reportType.value === 'industry'
        ? `请搜索"${topic.value}"最新行业数据，生成行业深度分析报告。包含：## 行业概况与规模、## 产业链分析、## 竞争格局（含市场份额表格）、## 技术发展趋势、## 政策环境、## 投资机会与风险、## 重点公司推荐。Markdown格式。`
        : `请搜索最新宏观经济数据，围绕"${topic.value}"生成宏观研判报告。包含：## 经济指标综述、## 货币政策分析、## 财政政策展望、## 全球经济联动、## 大类资产配置建议。Markdown格式。`

    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: prompt, style: '研报生成' })
    })

    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = '', charCount = 0
    const statusSteps = [
      [50, '正在整合分析框架...'],
      [200, '正在撰写核心章节...'],
      [500, '正在完善数据论据...'],
      [800, '正在生成结论建议...']
    ]

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
              generateProgress.value = Math.min(95, Math.floor(charCount / 15))
              for (const [threshold, status] of statusSteps) {
                if (charCount >= threshold) generateStatus.value = status
              }
            }
          } catch {}
        }
      }
    }
    generateProgress.value = 100
    generateStatus.value = '报告生成完成'
    history.value.unshift({ title: topic.value, date: new Date().toLocaleDateString('zh-CN'), type: reportType.value === 'stock' ? '个股' : reportType.value === 'industry' ? '行业' : '宏观' })
  } catch {
    reportContent.value = '## 生成失败\n\n暂时无法生成报告，请稍后再试。'
  } finally {
    setTimeout(() => { generating.value = false }, 500)
  }
}
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }
</style>
