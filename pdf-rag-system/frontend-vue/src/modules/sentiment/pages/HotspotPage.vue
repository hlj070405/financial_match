<template>
  <div class="h-full flex flex-col">
    <!-- Hero -->
    <div class="relative overflow-hidden bg-gradient-to-br from-rose-50 via-white to-pink-50 border-b border-gray-100">
      <div class="absolute inset-0 opacity-20">
        <div class="absolute top-3 left-16 w-48 h-48 bg-rose-200 rounded-full blur-3xl animate-pulse"></div>
        <div class="absolute bottom-0 right-10 w-40 h-40 bg-pink-200 rounded-full blur-3xl animate-pulse" style="animation-delay:1s"></div>
      </div>
      <div class="relative px-6 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-rose-500 to-pink-600 flex items-center justify-center shadow-md shadow-rose-500/20 shrink-0">
              <Flame class="w-4.5 h-4.5 text-white" />
            </div>
            <div>
              <h1 class="text-base font-bold text-gray-900">热点追踪</h1>
              <p class="text-[11px] text-gray-500 mt-0.5">实时金融热点事件监测，AI联网搜索最新市场动态</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <div class="flex items-center bg-gray-50 rounded-lg p-0.5 border border-gray-100">
              <button v-for="cat in categories" :key="cat.value" @click="activeCategory = cat.value"
                :class="['px-2.5 py-1.5 text-[11px] font-medium rounded-md transition-all',
                  activeCategory === cat.value ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700']"
              >{{ cat.label }}</button>
            </div>
            <button @click="refreshNews" :disabled="loading"
              class="px-3 py-2 bg-rose-600 text-white text-xs font-medium rounded-lg hover:bg-rose-700 transition-colors disabled:opacity-50 flex items-center gap-1.5">
              <RefreshCw :class="['w-3.5 h-3.5', loading ? 'animate-spin' : '']" />
              {{ loading ? '搜索中' : '刷新' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="flex-1 flex min-h-0">
      <!-- News Feed -->
      <div class="flex-1 overflow-y-auto p-5 custom-scrollbar">
        <div v-if="loading && newsList.length === 0" class="space-y-4">
          <div v-for="i in 5" :key="i" class="bg-white border border-gray-100 rounded-xl p-5 shadow-sm animate-pulse">
            <div class="h-4 bg-gray-200 rounded w-3/4 mb-3"></div>
            <div class="h-3 bg-gray-100 rounded w-full mb-2"></div>
            <div class="h-3 bg-gray-100 rounded w-2/3"></div>
          </div>
        </div>

        <div v-else class="space-y-3">
          <div v-for="(news, idx) in filteredNews" :key="idx"
            @click="selectNews(news)"
            :class="[
              'bg-white border rounded-xl p-4 shadow-sm cursor-pointer transition-all group hover:shadow-md',
              selectedNews === news ? 'border-rose-300 ring-1 ring-rose-200' : 'border-gray-100 hover:border-rose-200'
            ]">
            <div class="flex items-start gap-3">
              <div class="flex flex-col items-center gap-1 shrink-0 mt-0.5">
                <span :class="[
                  'w-7 h-7 rounded-lg flex items-center justify-center text-[10px] font-bold',
                  idx < 3 ? 'bg-rose-500 text-white' : 'bg-gray-100 text-gray-500'
                ]">{{ idx + 1 }}</span>
                <div class="flex items-center gap-0.5">
                  <Flame :class="['w-3 h-3', news.heat > 80 ? 'text-rose-500' : news.heat > 50 ? 'text-amber-500' : 'text-gray-300']" />
                  <span class="text-[9px] text-gray-400">{{ news.heat }}</span>
                </div>
              </div>
              <div class="flex-1 min-w-0">
                <h3 class="text-sm font-bold text-gray-900 group-hover:text-rose-700 transition-colors line-clamp-2">{{ news.title }}</h3>
                <p class="text-xs text-gray-500 mt-1.5 line-clamp-2 leading-relaxed">{{ news.summary }}</p>
                <div class="flex items-center gap-3 mt-2.5">
                  <span class="text-[10px] text-gray-400 flex items-center gap-1">
                    <Clock class="w-3 h-3" /> {{ news.time }}
                  </span>
                  <span class="text-[10px] text-gray-400">{{ news.source }}</span>
                  <span v-for="tag in news.tags" :key="tag"
                    :class="['px-1.5 py-0.5 rounded text-[9px] font-medium',
                      tag === '利好' ? 'bg-rose-50 text-rose-600' :
                      tag === '利空' ? 'bg-emerald-50 text-emerald-600' :
                      'bg-gray-50 text-gray-500']">{{ tag }}</span>
                </div>
              </div>
              <ChevronRight class="w-4 h-4 text-gray-300 group-hover:text-rose-400 shrink-0 mt-1 transition-colors" />
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Detail & Stats -->
      <div class="w-80 border-l border-gray-100 bg-gray-50/50 flex flex-col shrink-0 overflow-hidden">
        <!-- Selected Detail -->
        <div class="flex-1 overflow-y-auto p-4 custom-scrollbar">
          <div v-if="!selectedNews" class="flex flex-col items-center justify-center h-full text-gray-400">
            <Newspaper class="w-10 h-10 mb-2 opacity-30" />
            <p class="text-xs">点击左侧新闻查看详情</p>
          </div>
          <div v-else class="space-y-4">
            <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
              <h3 class="text-sm font-bold text-gray-900 mb-2">{{ selectedNews.title }}</h3>
              <div class="flex items-center gap-2 mb-3">
                <span class="text-[10px] text-gray-400">{{ selectedNews.source }}</span>
                <span class="text-[10px] text-gray-400">{{ selectedNews.time }}</span>
              </div>
              <p class="text-xs text-gray-600 leading-relaxed">{{ selectedNews.detail }}</p>
            </div>
            <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
              <h4 class="text-[11px] font-bold text-gray-700 mb-2 flex items-center gap-1.5">
                <TrendingUp class="w-3.5 h-3.5 text-rose-500" /> 影响评估
              </h4>
              <div class="space-y-2">
                <div v-for="imp in selectedNews.impacts" :key="imp.sector" class="flex items-center justify-between">
                  <span class="text-xs text-gray-600">{{ imp.sector }}</span>
                  <span :class="['text-[10px] font-bold px-2 py-0.5 rounded',
                    imp.direction === 'up' ? 'bg-rose-50 text-rose-600' : 'bg-emerald-50 text-emerald-600']">
                    {{ imp.direction === 'up' ? '↑ 利好' : '↓ 利空' }} {{ imp.degree }}
                  </span>
                </div>
              </div>
            </div>
            <button @click="deepAnalyze" :disabled="analyzing"
              class="w-full py-2.5 bg-gray-900 text-white text-xs font-medium rounded-xl hover:bg-gray-800 disabled:opacity-50 transition-all flex items-center justify-center gap-2">
              <Sparkles class="w-3.5 h-3.5" />
              {{ analyzing ? 'AI 深度解读中...' : 'AI 深度解读' }}
            </button>
            <div v-if="aiAnalysis" class="bg-white rounded-xl border border-rose-200 p-4 shadow-sm">
              <div class="flex items-center gap-1.5 mb-2">
                <Bot class="w-3.5 h-3.5 text-rose-500" />
                <span class="text-[10px] font-bold text-rose-600">AI 深度解读</span>
              </div>
              <div class="text-xs text-gray-600 leading-relaxed prose-sm" v-html="aiAnalysis"></div>
            </div>
          </div>
        </div>

        <!-- Heat Stats -->
        <div class="p-4 border-t border-gray-100 shrink-0">
          <div class="bg-white rounded-xl border border-gray-100 p-3 shadow-sm">
            <h4 class="text-[10px] font-bold text-gray-600 mb-2">今日热度分布</h4>
            <div ref="heatChartRef" class="w-full h-24"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { marked } from 'marked'
import { Flame, RefreshCw, Clock, ChevronRight, Newspaper, TrendingUp, Sparkles, Bot } from 'lucide-vue-next'

const loading = ref(false)
const analyzing = ref(false)
const aiAnalysis = ref('')
const activeCategory = ref('all')
const selectedNews = ref(null)
const heatChartRef = ref(null)

const categories = [
  { label: '全部', value: 'all' },
  { label: '宏观', value: 'macro' },
  { label: '行业', value: 'industry' },
  { label: '个股', value: 'stock' },
  { label: '政策', value: 'policy' }
]

const newsList = ref([
  { title: '央行宣布降准50个基点，释放长期资金约1.2万亿', summary: '中国人民银行决定下调金融机构存款准备金率0.5个百分点，预计释放长期资金约1.2万亿元。', time: '2小时前', source: '新华社', heat: 98, category: 'macro', tags: ['利好', '宏观'],
    detail: '中国人民银行决定于2024年3月15日下调金融机构存款准备金率0.5个百分点。此次降准后，金融机构加权平均存款准备金率约为7.0%。此次降准共计释放长期资金约1.2万亿元，有助于保持银行体系流动性合理充裕。',
    impacts: [{ sector: '银行板块', direction: 'up', degree: '中等' }, { sector: '房地产', direction: 'up', degree: '较强' }, { sector: '债券市场', direction: 'up', degree: '较强' }] },
  { title: '英伟达发布新一代AI芯片B200，算力提升4倍', summary: '英伟达GTC大会发布Blackwell架构B200芯片，推理性能较H100提升4倍，训练效率提升3倍。', time: '3小时前', source: '36氪', heat: 95, category: 'industry', tags: ['利好', '科技'],
    detail: '英伟达CEO黄仁勋在GTC 2024大会上发布了新一代Blackwell架构GPU B200。该芯片采用台积电4nm定制工艺，拥有2080亿晶体管，FP8性能达到20 PFLOPS。',
    impacts: [{ sector: 'AI算力', direction: 'up', degree: '强烈' }, { sector: '半导体设备', direction: 'up', degree: '中等' }, { sector: '消费电子', direction: 'up', degree: '轻微' }] },
  { title: '比亚迪第四代DM技术发布，百公里油耗2.9L', summary: '比亚迪发布第四代DM超级混动技术，实现全球量产车最低油耗2.9L/100km。', time: '5小时前', source: '证券时报', heat: 88, category: 'stock', tags: ['利好', '新能源'],
    detail: '比亚迪正式发布第四代DM超级混动技术平台。新平台采用全新混动专用发动机，热效率达46.06%，搭配全新EHS电混系统。',
    impacts: [{ sector: '比亚迪(002594)', direction: 'up', degree: '较强' }, { sector: '传统燃油车', direction: 'down', degree: '中等' }] },
  { title: '美联储维持利率不变，暗示年内降息3次', summary: 'FOMC会议决定维持联邦基金利率在5.25%-5.50%不变，点阵图显示年内降息75个基点。', time: '6小时前', source: '华尔街见闻', heat: 92, category: 'macro', tags: ['利好', '宏观'],
    detail: '美联储3月FOMC会议如期按兵不动，将联邦基金利率目标区间维持在5.25%-5.50%。最新经济预测和点阵图显示年内仍将降息三次。',
    impacts: [{ sector: 'A股市场', direction: 'up', degree: '中等' }, { sector: '黄金', direction: 'up', degree: '较强' }, { sector: '美元指数', direction: 'down', degree: '中等' }] },
  { title: '国务院发布新"国九条"，强化退市制度改革', summary: '国务院印发《关于加强监管防范风险推动资本市场高质量发展的若干意见》。', time: '8小时前', source: '中国证券报', heat: 85, category: 'policy', tags: ['政策', '监管'],
    detail: '新"国九条"从投资者保护、上市公司质量、退市制度、交易监管等多方面提出改革举措，是继2004年、2014年后第三个资本市场指导性文件。',
    impacts: [{ sector: '绩优蓝筹', direction: 'up', degree: '中等' }, { sector: 'ST板块', direction: 'down', degree: '强烈' }, { sector: '券商', direction: 'up', degree: '中等' }] },
  { title: '宁德时代发布神行超充电池，充电10分钟续航400km', summary: '宁德时代正式推出神行超充电池2.0版本，实现磷酸铁锂体系4C超充。', time: '10小时前', source: '第一财经', heat: 80, category: 'stock', tags: ['利好', '新能源'],
    detail: '宁德时代神行超充电池2.0采用全新超电子网正极技术和第二代快离子环石墨负极，实现磷酸铁锂电池4C超充。',
    impacts: [{ sector: '宁德时代(300750)', direction: 'up', degree: '较强' }, { sector: '充电桩', direction: 'up', degree: '中等' }] },
  { title: '碳酸锂期货跌破8万元/吨，创历史新低', summary: '碳酸锂主力合约跌破8万元关口，锂电产业链利润进一步压缩。', time: '12小时前', source: '上海有色网', heat: 75, category: 'industry', tags: ['利空', '新能源'],
    detail: '广期所碳酸锂主力合约LC2407跌破8万元/吨，日跌幅2.8%，创上市以来新低。',
    impacts: [{ sector: '锂矿企业', direction: 'down', degree: '强烈' }, { sector: '电池制造', direction: 'up', degree: '轻微' }] }
])

const filteredNews = computed(() => {
  if (activeCategory.value === 'all') return newsList.value
  return newsList.value.filter(n => n.category === activeCategory.value)
})

const selectNews = (news) => { selectedNews.value = news; aiAnalysis.value = '' }

const deepAnalyze = async () => {
  if (!selectedNews.value || analyzing.value) return
  analyzing.value = true
  aiAnalysis.value = ''
  try {
    const token = localStorage.getItem('access_token')
    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: `请搜索并深度解读这条金融新闻的市场影响：${selectedNews.value.title}。分析对相关板块和个股的影响，给出投资建议。`, style: '舆情深度分析' })
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
          try { const p = JSON.parse(d); if (p.type === 'text') { content += p.text; aiAnalysis.value = marked.parse(content) } } catch {}
        }
      }
    }
  } catch { aiAnalysis.value = '<p>暂时无法获取分析，请稍后再试。</p>' }
  finally { analyzing.value = false }
}

const refreshNews = async () => {
  loading.value = true
  try {
    const token = localStorage.getItem('access_token')
    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: '请搜索今天最新的7条金融市场重要新闻，每条给出标题、摘要、来源、热度评分(0-100)、分类(macro/industry/stock/policy)、标签数组，输出JSON数组', style: '热点搜索' })
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
      const m = content.match(/\[[\s\S]*\]/)
      if (m) { const parsed = JSON.parse(m[0]); if (parsed.length) newsList.value = parsed }
    } catch {}
  } catch {}
  finally { loading.value = false }
}

const initHeatChart = () => {
  if (!heatChartRef.value) return
  const chart = echarts.init(heatChartRef.value)
  chart.setOption({
    grid: { top: 5, bottom: 20, left: 5, right: 5, containLabel: false },
    xAxis: { type: 'category', data: ['09:00', '10:00', '11:00', '13:00', '14:00', '15:00'], axisLabel: { fontSize: 9 }, axisLine: { show: false }, axisTick: { show: false } },
    yAxis: { show: false },
    series: [{ type: 'line', data: [45, 68, 92, 85, 72, 88], smooth: true, symbol: 'none',
      lineStyle: { color: '#f43f5e', width: 2 },
      areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#f43f5e30' }, { offset: 1, color: '#f43f5e05' }] } }
    }]
  })
}

onMounted(() => { nextTick(() => initHeatChart()) })
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }
</style>
