<template>
  <div class="h-full flex flex-col">
    <!-- Hero -->
    <div class="relative overflow-hidden bg-gradient-to-br from-blue-50 via-white to-indigo-50 border-b border-gray-100">
      <div class="absolute inset-0 opacity-20">
        <div class="absolute top-3 left-16 w-48 h-48 bg-blue-200 rounded-full blur-3xl animate-pulse"></div>
        <div class="absolute bottom-0 right-10 w-40 h-40 bg-indigo-200 rounded-full blur-3xl animate-pulse" style="animation-delay:1s"></div>
      </div>
      <div class="relative px-6 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-md shadow-blue-500/20 shrink-0">
              <FolderUp class="w-4.5 h-4.5 text-white" />
            </div>
            <div>
              <h1 class="text-base font-bold text-gray-900">批量导入</h1>
              <p class="text-[11px] text-gray-500 mt-0.5">大批量文档一键导入与自动处理，支持文件夹递归扫描</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <input
              ref="fileInputRef"
              type="file"
              multiple
              accept=".pdf"
              class="hidden"
              @change="onFilesSelected"
            />
            <button @click="triggerBatchPicker" :disabled="batchRunning"
              class="px-4 py-2 bg-blue-600 text-white text-xs font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center gap-1.5">
              <Loader2 v-if="batchRunning" class="w-3.5 h-3.5 animate-spin" />
              <Play v-else class="w-3.5 h-3.5" />
              {{ batchRunning ? '处理中...' : '开始批量导入' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="flex-1 flex min-h-0">
      <!-- Main -->
      <div class="flex-1 overflow-y-auto p-5 space-y-4 custom-scrollbar">
        <!-- Stats Overview -->
        <div class="grid grid-cols-5 gap-3">
          <div v-for="stat in batchStats" :key="stat.label"
            class="bg-white border border-gray-100 rounded-xl p-3.5 shadow-sm text-center">
            <p class="text-[10px] text-gray-500 mb-1">{{ stat.label }}</p>
            <p :class="['text-lg font-bold font-mono', stat.color]">{{ stat.value }}</p>
          </div>
        </div>

        <!-- Batch Job List -->
        <div class="bg-white border border-gray-100 rounded-xl shadow-sm overflow-hidden">
          <div class="px-5 py-3 bg-gray-50 border-b border-gray-100 flex items-center justify-between">
            <h3 class="text-xs font-bold text-gray-800 flex items-center gap-2">
              <ListChecks class="w-4 h-4 text-blue-500" /> 批量任务列表
            </h3>
            <div class="flex items-center gap-2">
              <span class="text-[10px] text-gray-400">{{ completedJobs }}/{{ batchJobs.length }} 已完成</span>
              <div class="w-24 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                <div class="h-full bg-blue-500 rounded-full transition-all duration-300"
                  :style="{ width: (batchJobs.length ? (completedJobs / batchJobs.length * 100) : 0) + '%' }"></div>
              </div>
            </div>
          </div>
          <div class="divide-y divide-gray-50">
            <div v-for="(job, i) in batchJobs" :key="i"
              class="px-5 py-3 flex items-center gap-4 hover:bg-gray-50/50 transition-colors">
              <div :class="['w-8 h-8 rounded-lg flex items-center justify-center shrink-0',
                job.status === 'done' ? 'bg-emerald-100' : job.status === 'processing' ? 'bg-blue-100' : job.status === 'error' ? 'bg-rose-100' : 'bg-gray-100']">
                <CheckCircle v-if="job.status === 'done'" class="w-4 h-4 text-emerald-600" />
                <Loader2 v-else-if="job.status === 'processing'" class="w-4 h-4 text-blue-600 animate-spin" />
                <AlertCircle v-else-if="job.status === 'error'" class="w-4 h-4 text-rose-600" />
                <Clock v-else class="w-4 h-4 text-gray-400" />
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-xs font-medium text-gray-800 truncate">{{ job.name }}</p>
                <p class="text-[10px] text-gray-400">{{ job.files }}个文件 · {{ job.size }}</p>
              </div>
              <div class="w-40 shrink-0">
                <div class="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden mb-0.5">
                  <div class="h-full rounded-full transition-all duration-500"
                    :class="job.status === 'done' ? 'bg-emerald-500' : job.status === 'error' ? 'bg-rose-500' : 'bg-blue-500'"
                    :style="{ width: job.progress + '%' }"></div>
                </div>
                <div class="flex justify-between">
                  <span class="text-[9px] text-gray-400">{{ job.progress }}%</span>
                  <span class="text-[9px] text-gray-400">{{ job.eta }}</span>
                </div>
              </div>
              <span :class="['text-[10px] font-bold px-2 py-0.5 rounded shrink-0',
                job.status === 'done' ? 'bg-emerald-50 text-emerald-600' :
                job.status === 'processing' ? 'bg-blue-50 text-blue-600' :
                job.status === 'error' ? 'bg-rose-50 text-rose-600' : 'bg-gray-50 text-gray-500']">
                {{ statusLabel(job.status) }}
              </span>
            </div>
          </div>
        </div>

        <!-- Processing Log -->
        <div class="bg-gray-900 rounded-xl p-4 shadow-sm overflow-hidden">
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-[11px] font-bold text-gray-400 flex items-center gap-2">
              <Terminal class="w-3.5 h-3.5 text-emerald-500" /> 处理日志
            </h3>
            <span class="text-[9px] text-gray-600 font-mono">{{ logs.length }} entries</span>
          </div>
          <div class="h-36 overflow-y-auto custom-scrollbar-dark font-mono text-[10px] space-y-0.5">
            <p v-for="(log, i) in logs" :key="i" :class="log.color">
              <span class="text-gray-600">[{{ log.time }}]</span> {{ log.text }}
            </p>
          </div>
        </div>
      </div>

      <!-- Right -->
      <div class="w-64 border-l border-gray-100 bg-gray-50/50 p-4 flex flex-col gap-3 shrink-0 overflow-y-auto custom-scrollbar">
        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <h4 class="text-[11px] font-bold text-gray-700 mb-3 flex items-center gap-1.5">
            <Settings class="w-3.5 h-3.5 text-blue-500" /> 导入设置
          </h4>
          <div class="space-y-3">
            <div>
              <label class="text-[10px] text-gray-500 block mb-1">并发数</label>
              <select class="w-full px-2 py-1.5 text-[11px] border border-gray-200 rounded-lg bg-gray-50">
                <option>2 (稳定)</option>
                <option>4 (平衡)</option>
                <option>8 (高速)</option>
              </select>
            </div>
            <div>
              <label class="text-[10px] text-gray-500 block mb-1">分块策略</label>
              <select class="w-full px-2 py-1.5 text-[11px] border border-gray-200 rounded-lg bg-gray-50">
                <option>按段落 (推荐)</option>
                <option>按页面</option>
                <option>固定长度 512</option>
                <option>固定长度 1024</option>
              </select>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-[10px] text-gray-500">自动OCR</span>
              <div class="w-8 h-4 bg-blue-500 rounded-full relative cursor-pointer">
                <div class="w-3 h-3 bg-white rounded-full absolute right-0.5 top-0.5 shadow-sm"></div>
              </div>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-[10px] text-gray-500">错误重试</span>
              <div class="w-8 h-4 bg-blue-500 rounded-full relative cursor-pointer">
                <div class="w-3 h-3 bg-white rounded-full absolute right-0.5 top-0.5 shadow-sm"></div>
              </div>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm flex-1">
          <h4 class="text-[11px] font-bold text-gray-700 mb-3">处理统计</h4>
          <div ref="donutRef" class="w-full h-32"></div>
          <div class="space-y-1.5 mt-2">
            <div class="flex items-center gap-2 text-[10px]">
              <div class="w-2.5 h-2.5 rounded bg-emerald-500"></div>
              <span class="text-gray-600">成功</span>
              <span class="ml-auto font-mono font-bold text-gray-800">156</span>
            </div>
            <div class="flex items-center gap-2 text-[10px]">
              <div class="w-2.5 h-2.5 rounded bg-blue-500"></div>
              <span class="text-gray-600">处理中</span>
              <span class="ml-auto font-mono font-bold text-gray-800">12</span>
            </div>
            <div class="flex items-center gap-2 text-[10px]">
              <div class="w-2.5 h-2.5 rounded bg-rose-500"></div>
              <span class="text-gray-600">失败</span>
              <span class="ml-auto font-mono font-bold text-gray-800">3</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { FolderUp, Play, Loader2, ListChecks, CheckCircle, AlertCircle, Clock, Terminal, Settings } from 'lucide-vue-next'

const batchRunning = ref(false)
const donutRef = ref(null)
const fileInputRef = ref(null)

const statusLabel = (s) => ({ done: '已完成', processing: '处理中', error: '失败', pending: '等待中' })[s] || s

const batchSummary = ref({ total: 0, success: 0, failed: 0, chunks: 0 })

const batchStats = computed(() => [
  { label: '总文件数', value: String(batchSummary.value.total), color: 'text-gray-800' },
  { label: '已完成', value: String(batchSummary.value.success), color: 'text-emerald-600' },
  { label: '处理中', value: batchRunning.value ? '1' : '0', color: 'text-blue-600' },
  { label: '失败', value: String(batchSummary.value.failed), color: 'text-rose-600' },
  { label: '总向量数', value: String(batchSummary.value.chunks), color: 'text-purple-600' }
])

const completedJobs = computed(() => batchJobs.value.filter(j => j.status === 'done').length)

const batchJobs = ref([])

const logs = ref([])

const nowTime = () => new Date().toLocaleTimeString('zh-CN', { hour12: false })

const pushLog = (text, color = 'text-gray-400') => {
  logs.value.unshift({ time: nowTime(), text, color })
  if (logs.value.length > 50) logs.value = logs.value.slice(0, 50)
}

const formatBytes = (bytes) => {
  if (!bytes || bytes <= 0) return '0 B'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`
  return `${(bytes / 1024 / 1024).toFixed(1)}MB`
}

const triggerBatchPicker = () => {
  if (batchRunning.value) return
  fileInputRef.value?.click()
}

const onFilesSelected = async (event) => {
  const files = Array.from(event.target?.files || [])
  if (!files.length) return

  batchRunning.value = true
  batchSummary.value = { total: files.length, success: 0, failed: 0, chunks: 0 }
  batchJobs.value = files.map(file => ({
    name: file.name,
    files: 1,
    size: formatBytes(file.size),
    progress: 10,
    status: 'processing',
    eta: '上传中'
  }))
  pushLog(`[INFO] 批量导入任务启动，共 ${files.length} 个文件`, 'text-emerald-400')

  const formData = new FormData()
  files.forEach(file => formData.append('files', file))

  try {
    const token = localStorage.getItem('access_token')
    const resp = await fetch('/api/rag/ingest/batch-upload', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    })
    const data = await resp.json()
    if (!resp.ok) {
      throw new Error(data.detail || '批量导入失败')
    }

    const resultMap = Object.fromEntries((data.results || []).map(item => [item.filename, item]))
    batchSummary.value = data.summary || batchSummary.value
    batchJobs.value = files.map(file => {
      const result = resultMap[file.name]
      if (!result) {
        return {
          name: file.name,
          files: 1,
          size: formatBytes(file.size),
          progress: 0,
          status: 'error',
          eta: '无返回结果'
        }
      }

      const success = result.status === 'ok'
      pushLog(
        success
          ? `[OK] ${result.filename} 处理完成，生成 ${result.chunks || 0} 个向量`
          : `[ERROR] ${result.filename} 处理失败: ${result.message || '未知错误'}`,
        success ? 'text-emerald-400' : 'text-rose-400'
      )

      return {
        name: result.filename,
        files: 1,
        size: formatBytes(file.size),
        progress: success ? 100 : 100,
        status: success ? 'done' : 'error',
        eta: success ? `+${result.chunks || 0} 向量` : (result.message || '失败')
      }
    })
  } catch (error) {
    pushLog(`[ERROR] 批量导入失败: ${error.message}`, 'text-rose-400')
    batchJobs.value = files.map(file => ({
      name: file.name,
      files: 1,
      size: formatBytes(file.size),
      progress: 100,
      status: 'error',
      eta: error.message
    }))
    batchSummary.value = { total: files.length, success: 0, failed: files.length, chunks: 0 }
  } finally {
    batchRunning.value = false
    if (event.target) event.target.value = ''
    nextTick(() => initDonut())
  }
}

const initDonut = () => {
  if (!donutRef.value) return
  const chart = echarts.init(donutRef.value)
  chart.setOption({
    series: [{
      type: 'pie', radius: ['45%', '70%'], center: ['50%', '50%'],
      label: { show: false },
      itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
      data: [
        { value: batchSummary.value.success, itemStyle: { color: '#10b981' } },
        { value: batchRunning.value ? 1 : 0, itemStyle: { color: '#3b82f6' } },
        { value: batchSummary.value.failed, itemStyle: { color: '#ef4444' } }
      ]
    }]
  })
}

onMounted(() => {
  pushLog('[INFO] 等待选择批量导入文件', 'text-gray-400')
  nextTick(() => initDonut())
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }
.custom-scrollbar-dark::-webkit-scrollbar { width: 4px; }
.custom-scrollbar-dark::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar-dark::-webkit-scrollbar-thumb { background: #374151; border-radius: 4px; }
</style>
