<template>
  <div class="h-full flex flex-col">
    <!-- Hero - Google-like search bar -->
    <div class="relative overflow-hidden bg-white border-b border-gray-100">
      <div class="px-6 py-5">
        <div class="max-w-2xl mx-auto">
          <div class="flex items-center justify-center gap-2 mb-4">
            <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center">
              <Search class="w-4 h-4 text-white" />
            </div>
            <h1 class="text-base font-bold text-gray-900">语义搜索</h1>
          </div>
          <div class="relative">
            <Search class="w-4 h-4 text-gray-400 absolute left-4 top-1/2 -translate-y-1/2" />
            <input v-model="query" @keydown.enter="doSearch" type="text"
              placeholder="输入自然语言查询，如：比亚迪近三年毛利率变化趋势..."
              class="w-full pl-11 pr-28 py-3 text-sm border border-gray-200 rounded-2xl bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 focus:bg-white transition-all shadow-sm" />
            <button @click="doSearch" :disabled="searching"
              class="absolute right-2 top-1/2 -translate-y-1/2 px-5 py-2 bg-blue-600 text-white text-xs font-medium rounded-xl hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center gap-1.5">
              <Loader2 v-if="searching" class="w-3.5 h-3.5 animate-spin" />
              <Sparkles v-else class="w-3.5 h-3.5" />
              {{ searching ? '检索中' : '智能检索' }}
            </button>
          </div>
          <div class="flex items-center gap-3 mt-2.5 justify-center">
            <span class="text-[10px] text-gray-400">试试：</span>
            <button v-for="ex in examples" :key="ex" @click="query = ex; doSearch()"
              class="text-[10px] text-blue-500 hover:text-blue-700 hover:underline transition-colors">{{ ex }}</button>
          </div>
        </div>
      </div>
    </div>

    <div class="flex-1 flex min-h-0">
      <!-- Results -->
      <div class="flex-1 overflow-y-auto custom-scrollbar">
        <!-- Empty -->
        <div v-if="!searching && results.length === 0 && !hasSearched" class="flex items-center justify-center h-full">
          <div class="text-center max-w-md">
            <div class="flex items-center justify-center gap-4 mb-6">
              <div v-for="(icon, i) in [FileSearch, Database, Brain]" :key="i"
                class="w-14 h-14 rounded-2xl bg-gray-50 flex items-center justify-center">
                <component :is="icon" class="w-6 h-6 text-gray-300" />
              </div>
            </div>
            <h3 class="text-sm font-semibold text-gray-700 mb-1.5">自然语言语义检索</h3>
            <p class="text-xs text-gray-400 leading-relaxed">支持中文自然语言查询，基于向量表征的语义级文档检索，精准匹配相关内容</p>
          </div>
        </div>

        <!-- Loading -->
        <div v-if="searching" class="p-6 space-y-3">
          <div v-for="i in 4" :key="i" class="bg-white border border-gray-100 rounded-xl p-4 animate-pulse">
            <div class="h-3 bg-blue-100 rounded w-1/3 mb-2"></div>
            <div class="h-3 bg-gray-100 rounded w-full mb-1.5"></div>
            <div class="h-3 bg-gray-100 rounded w-4/5"></div>
          </div>
        </div>

        <!-- Results List -->
        <div v-if="!searching && results.length > 0" class="p-6 max-w-3xl">
          <p class="text-[11px] text-gray-400 mb-4">
            找到 <b class="text-gray-700">{{ results.length }}</b> 条相关结果，用时 <b class="text-gray-700">{{ searchTime }}ms</b>
          </p>
          <div class="space-y-4">
            <div v-for="(r, i) in results" :key="i"
              class="group cursor-pointer" @click="selectResult(r)">
              <div class="flex items-center gap-2 mb-1">
                <FileText class="w-3.5 h-3.5 text-blue-500" />
                <span class="text-[10px] text-emerald-700 font-mono">{{ r.source }}</span>
                <span class="text-[10px] text-gray-400">· 第{{ r.page }}页</span>
              </div>
              <h3 class="text-sm font-medium text-blue-700 group-hover:underline mb-1">{{ r.title }}</h3>
              <p class="text-xs text-gray-600 leading-relaxed line-clamp-3" v-html="r.highlight"></p>
              <div class="flex items-center gap-3 mt-1.5">
                <div class="flex items-center gap-1">
                  <span class="text-[9px] text-gray-400">相关度</span>
                  <div class="w-20 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div class="h-full bg-blue-500 rounded-full" :style="{ width: r.score + '%' }"></div>
                  </div>
                  <span class="text-[9px] font-mono text-blue-600">{{ r.score }}%</span>
                </div>
                <span class="text-[9px] text-gray-400">{{ r.type }}</span>
              </div>
            </div>
          </div>

          <!-- No Results -->
          <div v-if="hasSearched && results.length === 0 && !searching" class="text-center py-12">
            <Search class="w-8 h-8 text-gray-300 mx-auto mb-2" />
            <p class="text-sm text-gray-500">未找到相关结果，请尝试更换关键词</p>
          </div>
        </div>
      </div>

      <!-- Right: Detail / Filters -->
      <div class="w-72 border-l border-gray-100 bg-gray-50/50 flex flex-col shrink-0 overflow-hidden">
        <div v-if="!selectedResult" class="flex-1 p-4 flex flex-col gap-3">
          <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
            <h4 class="text-[11px] font-bold text-gray-700 mb-3 flex items-center gap-1.5">
              <Filter class="w-3.5 h-3.5 text-blue-500" /> 检索过滤
            </h4>
            <div class="space-y-3">
              <div>
                <label class="text-[10px] text-gray-500 block mb-1">文档类型</label>
                <div class="flex flex-wrap gap-1.5">
                  <button v-for="ft in fileTypes" :key="ft.value" @click="toggleFilter(ft.value)"
                    :class="['px-2 py-1 text-[10px] font-medium rounded-lg border transition-all',
                      activeFilters.includes(ft.value) ? 'bg-blue-50 border-blue-200 text-blue-700' : 'bg-white border-gray-200 text-gray-500 hover:bg-gray-50']">{{ ft.label }}</button>
                </div>
              </div>
              <div>
                <label class="text-[10px] text-gray-500 block mb-1">相关度阈值</label>
                <input type="range" min="0" max="100" v-model="threshold" class="w-full h-1 accent-blue-500" />
                <span class="text-[10px] text-gray-400 float-right">≥ {{ threshold }}%</span>
              </div>
              <div>
                <label class="text-[10px] text-gray-500 block mb-1">结果数量</label>
                <select v-model="topK" class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded-lg bg-gray-50">
                  <option :value="5">Top 5</option>
                  <option :value="10">Top 10</option>
                  <option :value="20">Top 20</option>
                </select>
              </div>
            </div>
          </div>
          <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm flex-1">
            <h4 class="text-[11px] font-bold text-gray-700 mb-3 flex items-center gap-1.5">
              <Clock class="w-3.5 h-3.5 text-gray-500" /> 最近搜索
            </h4>
            <div class="space-y-1.5">
              <button v-for="h in searchHistory" :key="h" @click="query = h; doSearch()"
                class="w-full text-left px-2.5 py-1.5 text-[11px] text-gray-600 rounded-lg hover:bg-blue-50 hover:text-blue-700 transition-colors truncate">
                {{ h }}
              </button>
            </div>
          </div>
        </div>

        <!-- Selected Doc Detail -->
        <div v-else class="flex-1 overflow-y-auto p-4 custom-scrollbar">
          <button @click="selectedResult = null" class="text-[10px] text-blue-600 hover:underline mb-3 flex items-center gap-1">
            <ArrowLeft class="w-3 h-3" /> 返回列表
          </button>
          <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
            <div class="flex items-center gap-2 mb-2">
              <FileText class="w-4 h-4 text-blue-500" />
              <span class="text-[10px] text-emerald-700 font-mono">{{ selectedResult.source }}</span>
            </div>
            <h3 class="text-sm font-bold text-gray-900 mb-2">{{ selectedResult.title }}</h3>
            <p class="text-xs text-gray-600 leading-relaxed">{{ selectedResult.fullText }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Search, Sparkles, Loader2, FileText, FileSearch, Database, Brain, Filter, Clock, ArrowLeft } from 'lucide-vue-next'

const query = ref('')
const searching = ref(false)
const hasSearched = ref(false)
const results = ref([])
const selectedResult = ref(null)
const searchTime = ref(0)
const threshold = ref(60)
const topK = ref(10)
const activeFilters = ref(['pdf', 'excel'])

const examples = ['比亚迪毛利率变化', '宁德时代海外布局', '光伏行业产能过剩']
const fileTypes = [
  { label: 'PDF', value: 'pdf' },
  { label: 'Excel', value: 'excel' },
  { label: 'Word', value: 'word' },
  { label: '网页', value: 'web' }
]
const fileTypeLabels = {
  pdf: 'PDF文档',
  excel: 'Excel文档',
  word: 'Word文档',
  web: '网页内容'
}
const searchHistory = ref(['贵州茅台2023年报分析', '新能源补贴政策', '银行不良贷款率'])

const toggleFilter = (v) => {
  const idx = activeFilters.value.indexOf(v)
  if (idx >= 0) activeFilters.value.splice(idx, 1)
  else activeFilters.value.push(v)
}

const selectResult = (r) => { selectedResult.value = r }

const highlightText = (text, q) => {
  if (!text || !q) return text || ''
  const snippet = text.length > 200 ? '...' + text.slice(0, 200) + '...' : text
  const words = q.split(/\s+/).filter(Boolean)
  let html = snippet
  for (const w of words) {
    html = html.replace(new RegExp(w, 'gi'), `<b class="text-blue-700">${w}</b>`)
  }
  return html
}

const doSearch = async () => {
  if (!query.value.trim() || searching.value) return
  searching.value = true
  hasSearched.value = true
  selectedResult.value = null
  try {
    const token = localStorage.getItem('access_token')
    const minScore = threshold.value / 100
    const resp = await fetch('/api/rag/search', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: query.value.trim(),
        top_k: topK.value,
        score_threshold: minScore,
        file_types: activeFilters.value
      })
    })
    const data = await resp.json()
    searchTime.value = data.elapsed_ms || 0
    results.value = (data.results || [])
      .filter(r => r.score >= minScore)
      .map(r => ({
        title: `${r.source} · 第${r.page_number}页`,
        source: r.source,
        page: r.page_number,
        score: Math.round(r.score * 100),
        type: fileTypeLabels[r.file_type] || r.file_type || '文档',
        highlight: highlightText(r.text, query.value.trim()),
        fullText: r.text
      }))
    if (!searchHistory.value.includes(query.value.trim())) {
      searchHistory.value.unshift(query.value.trim())
      if (searchHistory.value.length > 5) searchHistory.value.pop()
    }
  } catch (e) {
    console.error('搜索失败', e)
    results.value = []
  } finally { searching.value = false }
}
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }
</style>
