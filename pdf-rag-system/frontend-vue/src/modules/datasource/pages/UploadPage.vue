<template>
  <div class="h-full flex flex-col">
    <!-- Hero -->
    <div class="relative overflow-hidden bg-gradient-to-br from-slate-50 via-white to-gray-50 border-b border-gray-100">
      <div class="absolute inset-0 opacity-20">
        <div class="absolute top-3 left-16 w-48 h-48 bg-slate-200 rounded-full blur-3xl animate-pulse"></div>
        <div class="absolute bottom-0 right-10 w-40 h-40 bg-gray-200 rounded-full blur-3xl animate-pulse" style="animation-delay:1s"></div>
      </div>
      <div class="relative px-6 py-4">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-slate-600 to-gray-700 flex items-center justify-center shadow-md shadow-slate-500/20 shrink-0">
            <Upload class="w-4.5 h-4.5 text-white" />
          </div>
          <div>
            <h1 class="text-base font-bold text-gray-900">单文件上传</h1>
            <p class="text-[11px] text-gray-500 mt-0.5">支持PDF、Excel、Word等文件上传与自动解析入库</p>
          </div>
        </div>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto p-6 custom-scrollbar">
      <div class="max-w-4xl mx-auto space-y-5">
        <!-- Drop Zone -->
        <div @dragover.prevent="dragOver = true" @dragleave.prevent="dragOver = false"
          @drop.prevent="onDrop"
          :class="['border-2 border-dashed rounded-2xl p-10 text-center transition-all cursor-pointer',
            dragOver ? 'border-blue-400 bg-blue-50/50' : 'border-gray-200 bg-gray-50/30 hover:border-gray-300 hover:bg-gray-50']"
          @click="$refs.fileInput.click()">
          <input ref="fileInput" type="file" class="hidden" @change="onFileSelect"
            accept=".pdf,.xlsx,.xls,.docx,.doc,.csv,.txt" />
          <div class="flex flex-col items-center">
            <div :class="['w-16 h-16 rounded-2xl flex items-center justify-center mb-4 transition-all',
              dragOver ? 'bg-blue-100' : 'bg-gray-100']">
              <Upload :class="['w-7 h-7 transition-all', dragOver ? 'text-blue-500' : 'text-gray-400']" />
            </div>
            <p class="text-sm font-medium text-gray-700 mb-1">拖拽文件到此处，或点击上传</p>
            <p class="text-[11px] text-gray-400">支持 PDF、Excel、Word、CSV、TXT，单文件最大 50MB</p>
          </div>
        </div>

        <!-- Upload Queue -->
        <div v-if="uploadQueue.length > 0" class="space-y-3">
          <h3 class="text-xs font-bold text-gray-700 flex items-center gap-2">
            <FileUp class="w-4 h-4 text-blue-500" /> 上传队列
          </h3>
          <div v-for="(file, i) in uploadQueue" :key="i"
            class="bg-white border border-gray-100 rounded-xl p-4 shadow-sm flex items-center gap-4">
            <div :class="['w-10 h-10 rounded-xl flex items-center justify-center shrink-0', fileIconBg(file.type)]">
              <component :is="fileIcon(file.type)" :class="['w-5 h-5', fileIconColor(file.type)]" />
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center justify-between mb-1">
                <p class="text-xs font-medium text-gray-800 truncate">{{ file.name }}</p>
                <span :class="['text-[10px] px-2 py-0.5 rounded-full font-bold',
                  file.status === 'done' ? 'bg-emerald-100 text-emerald-700' :
                  file.status === 'parsing' ? 'bg-blue-100 text-blue-700' :
                  file.status === 'uploading' ? 'bg-amber-100 text-amber-700' :
                  file.status === 'error' ? 'bg-rose-100 text-rose-700' : 'bg-gray-100 text-gray-500']">
                  {{ statusLabel(file.status) }}
                </span>
              </div>
              <div class="flex items-center gap-3">
                <div class="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div class="h-full rounded-full transition-all duration-500"
                    :class="file.status === 'done' ? 'bg-emerald-500' : file.status === 'error' ? 'bg-rose-500' : 'bg-blue-500'"
                    :style="{ width: file.progress + '%' }"></div>
                </div>
                <span class="text-[10px] text-gray-400 font-mono shrink-0">{{ file.size }}</span>
              </div>
            </div>
            <button @click="uploadQueue.splice(i, 1)" class="p-1.5 hover:bg-gray-100 rounded-lg transition-colors text-gray-400 hover:text-rose-500 shrink-0">
              <X class="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        <!-- Recent Files -->
        <div class="bg-white border border-gray-100 rounded-xl shadow-sm overflow-hidden">
          <div class="px-5 py-3 bg-gray-50 border-b border-gray-100 flex items-center justify-between">
            <h3 class="text-xs font-bold text-gray-800 flex items-center gap-2">
              <FolderOpen class="w-4 h-4 text-gray-500" /> 已上传文件
            </h3>
            <span class="text-[10px] text-gray-400">共 {{ recentFiles.length }} 个文件</span>
          </div>
          <table class="w-full text-xs">
            <thead>
              <tr class="border-b border-gray-100">
                <th class="px-4 py-2.5 text-left font-bold text-gray-600">文件名</th>
                <th class="px-4 py-2.5 text-center font-bold text-gray-600">类型</th>
                <th class="px-4 py-2.5 text-center font-bold text-gray-600">大小</th>
                <th class="px-4 py-2.5 text-center font-bold text-gray-600">状态</th>
                <th class="px-4 py-2.5 text-center font-bold text-gray-600">向量数</th>
                <th class="px-4 py-2.5 text-center font-bold text-gray-600">上传时间</th>
                <th class="px-4 py-2.5 text-center font-bold text-gray-600">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="f in recentFiles" :key="f.name" class="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
                <td class="px-4 py-2.5">
                  <div class="flex items-center gap-2">
                    <component :is="fileIcon(f.type)" :class="['w-4 h-4', fileIconColor(f.type)]" />
                    <span class="font-medium text-gray-700 truncate max-w-[200px]">{{ f.name }}</span>
                  </div>
                </td>
                <td class="px-4 py-2.5 text-center"><span class="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-[10px] font-mono">{{ f.type }}</span></td>
                <td class="px-4 py-2.5 text-center font-mono text-gray-500">{{ f.size }}</td>
                <td class="px-4 py-2.5 text-center">
                  <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-700">已入库</span>
                </td>
                <td class="px-4 py-2.5 text-center font-mono text-blue-600">{{ f.vectors }}</td>
                <td class="px-4 py-2.5 text-center text-gray-500">{{ f.date }}</td>
                <td class="px-4 py-2.5 text-center">
                  <div class="flex items-center justify-center gap-1">
                    <button class="p-1 hover:bg-gray-100 rounded text-gray-400 hover:text-blue-500 transition-colors" title="查看"><Eye class="w-3.5 h-3.5" /></button>
                    <button class="p-1 hover:bg-gray-100 rounded text-gray-400 hover:text-rose-500 transition-colors" title="删除"><Trash2 class="w-3.5 h-3.5" /></button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Upload, FileUp, FolderOpen, X, Eye, Trash2, FileText, FileSpreadsheet, File } from 'lucide-vue-next'

const dragOver = ref(false)
const fileInput = ref(null)

const fileIcon = (type) => {
  if (type === 'pdf') return FileText
  if (['xlsx', 'xls', 'csv'].includes(type)) return FileSpreadsheet
  return File
}
const fileIconBg = (type) => type === 'pdf' ? 'bg-rose-50' : ['xlsx', 'xls', 'csv'].includes(type) ? 'bg-emerald-50' : 'bg-blue-50'
const fileIconColor = (type) => type === 'pdf' ? 'text-rose-500' : ['xlsx', 'xls', 'csv'].includes(type) ? 'text-emerald-500' : 'text-blue-500'
const statusLabel = (s) => ({ uploading: '上传中', parsing: '解析中', done: '已完成', error: '失败', pending: '等待中' })[s] || s

const uploadQueue = ref([])
const recentFiles = ref([])

const loadIndexed = async () => {
  try {
    const token = localStorage.getItem('access_token')
    const resp = await fetch('/api/rag/indexed', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await resp.json()
    recentFiles.value = (data.sources || []).map(s => ({
      name: s.source || s,
      type: (s.source || s).split('.').pop().toLowerCase() || 'pdf',
      size: '-',
      vectors: s.count || '-',
      date: '-'
    }))
  } catch (e) { console.error('加载已入库文件失败', e) }
}

const onDrop = (e) => {
  dragOver.value = false
  const files = e.dataTransfer?.files
  if (files?.length) addFile(files[0])
}
const onFileSelect = (e) => { if (e.target.files?.length) addFile(e.target.files[0]) }
const addFile = async (file) => {
  const ext = file.name.split('.').pop().toLowerCase()
  const item = {
    name: file.name, type: ext,
    size: (file.size / 1024 / 1024).toFixed(1) + 'MB',
    progress: 10, status: 'uploading'
  }
  uploadQueue.value.push(item)
  const idx = uploadQueue.value.length - 1

  try {
    item.progress = 30
    const token = localStorage.getItem('access_token')
    const formData = new FormData()
    formData.append('file', file)

    item.status = 'uploading'
    item.progress = 50
    const resp = await fetch('/api/rag/ingest/upload', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    })

    item.progress = 80
    item.status = 'parsing'

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}))
      throw new Error(err.detail || '上传失败')
    }

    const result = await resp.json()
    item.progress = 100
    item.status = 'done'
    console.log('入库结果:', result)
    await loadIndexed()
  } catch (e) {
    console.error('上传失败:', e)
    if (uploadQueue.value[idx]) {
      uploadQueue.value[idx].status = 'error'
      uploadQueue.value[idx].progress = 100
    }
  }
}

onMounted(() => { loadIndexed() })
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }
</style>
