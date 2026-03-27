<template>
  <div class="h-full flex flex-col bg-white">
    <!-- Header -->
    <div class="px-6 py-4 border-b border-gray-200">
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-lg bg-[#1a365d] flex items-center justify-center shrink-0">
          <Upload class="w-4 h-4 text-white" />
        </div>
        <div>
          <h1 class="text-[15px] font-bold text-gray-900">文档入库</h1>
          <p class="text-[11px] text-gray-400 mt-0.5">上传 PDF 文件，自动解析并向量化入库</p>
        </div>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto p-6">
      <div class="max-w-5xl mx-auto space-y-5">

        <!-- Upload Area -->
        <n-upload
          :action="uploadAction"
          :headers="uploadHeaders"
          :max="1"
          accept=".pdf"
          :show-file-list="false"
          :on-before-upload="onBeforeUpload"
          :on-finish="onUploadFinish"
          :on-error="onUploadError"
          :on-progress="onUploadProgress"
          directory-dnd
          ref="uploadRef"
        >
          <n-upload-dragger>
            <div class="flex flex-col items-center py-4">
              <n-icon :size="40" :depth="3" class="mb-3">
                <Upload />
              </n-icon>
              <p class="text-sm font-medium text-gray-600 mb-1">拖拽文件到此处，或点击上传</p>
              <p class="text-[11px] text-gray-400">仅支持 PDF 文件，单文件最大 50MB</p>
            </div>
          </n-upload-dragger>
        </n-upload>

        <!-- Upload Progress -->
        <n-card v-if="currentUpload" size="small" :bordered="true">
          <div class="flex items-center gap-3">
            <n-icon :size="20" color="#1a365d"><FileText /></n-icon>
            <div class="flex-1 min-w-0">
              <div class="flex items-center justify-between mb-1">
                <span class="text-xs font-medium text-gray-800 truncate">{{ currentUpload.name }}</span>
                <n-tag :type="uploadStatusType" size="small" :bordered="false">{{ uploadStatusText }}</n-tag>
              </div>
              <n-progress
                type="line"
                :percentage="currentUpload.progress"
                :status="currentUpload.status === 'error' ? 'error' : currentUpload.status === 'done' ? 'success' : 'default'"
                :show-indicator="false"
                :height="4"
              />
            </div>
            <span class="text-[11px] text-gray-400 font-mono shrink-0">{{ currentUpload.size }}</span>
          </div>
        </n-card>

        <!-- Indexed Files Table -->
        <n-card size="small" :bordered="true" :segmented="{ content: true }">
          <template #header>
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <n-icon :size="16" color="#4a5568"><FolderOpen /></n-icon>
                <span class="text-xs font-bold text-gray-700">已入库文档</span>
              </div>
              <span class="text-[11px] text-gray-400">共 {{ tableData.length }} 个文件</span>
            </div>
          </template>
          <n-data-table
            :columns="columns"
            :data="tableData"
            :bordered="false"
            :single-line="false"
            size="small"
            :row-key="row => row.name"
            :loading="tableLoading"
          />
        </n-card>

      </div>
    </div>

    <!-- Delete Confirm Dialog -->
    <n-modal v-model:show="showDeleteModal" preset="dialog" type="warning"
      title="确认删除"
      :content="`确定要删除「${deleteTarget?.name}」的向量数据吗？此操作不可撤销。`"
      positive-text="确认删除"
      negative-text="取消"
      :positive-button-props="{ type: 'error', size: 'small' }"
      :negative-button-props="{ size: 'small' }"
      :loading="isDeleting"
      @positive-click="doDelete"
      @negative-click="showDeleteModal = false"
    />

    <!-- View Document Modal -->
    <n-modal v-model:show="showViewModal" preset="card" :title="viewTarget?.name || '文档详情'"
      style="width: 640px; max-width: 90vw;" :bordered="true" size="small">
      <n-spin :show="viewLoading">
        <div v-if="viewChunks.length > 0" class="space-y-3 max-h-[60vh] overflow-y-auto">
          <div v-for="(chunk, i) in viewChunks" :key="i"
            class="border border-gray-100 rounded-md p-3 text-xs leading-relaxed text-gray-700 bg-gray-50/50">
            <div class="flex items-center gap-2 mb-1.5">
              <n-tag size="tiny" type="info" :bordered="false">第{{ chunk.page }}页</n-tag>
              <n-tag v-if="chunk.isTable" size="tiny" type="warning" :bordered="false">表格</n-tag>
              <span class="text-[10px] text-gray-400 ml-auto font-mono">片段 #{{ i + 1 }}</span>
            </div>
            <p class="whitespace-pre-wrap">{{ chunk.text }}</p>
          </div>
        </div>
        <n-empty v-else-if="!viewLoading" description="暂无向量数据" />
      </n-spin>
    </n-modal>

  </div>
</template>

<script setup>
import { ref, h, computed, onMounted } from 'vue'
import {
  NUpload, NUploadDragger, NIcon, NCard, NTag, NProgress,
  NDataTable, NModal, NSpin, NEmpty, NButton, useMessage
} from 'naive-ui'
import { Upload, FileText, FolderOpen, Eye, Trash2 } from 'lucide-vue-next'

const message = useMessage()

// ===================== Upload =====================

const uploadRef = ref(null)
const currentUpload = ref(null)

const uploadAction = '/api/rag/ingest/upload'
const uploadHeaders = computed(() => ({
  'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`
}))

const uploadStatusType = computed(() => {
  if (!currentUpload.value) return 'default'
  const s = currentUpload.value.status
  return s === 'done' ? 'success' : s === 'error' ? 'error' : s === 'parsing' ? 'info' : 'warning'
})

const uploadStatusText = computed(() => {
  if (!currentUpload.value) return ''
  const map = { uploading: '上传中', parsing: '解析入库中', done: '已完成', error: '失败' }
  return map[currentUpload.value.status] || '等待中'
})

const onBeforeUpload = ({ file }) => {
  if (file.file.size > 50 * 1024 * 1024) {
    message.error('文件大小不能超过 50MB')
    return false
  }
  currentUpload.value = {
    name: file.name,
    size: formatBytes(file.file.size),
    progress: 0,
    status: 'uploading'
  }
  return true
}

const onUploadProgress = ({ event }) => {
  if (currentUpload.value && event?.percent) {
    currentUpload.value.progress = Math.min(Math.round(event.percent), 90)
  }
}

const onUploadFinish = ({ file, event }) => {
  try {
    const resp = JSON.parse(event?.target?.response || '{}')
    if (resp.status === 'ok' || resp.chunks) {
      if (currentUpload.value) {
        currentUpload.value.progress = 100
        currentUpload.value.status = 'done'
      }
      message.success(`入库成功，共 ${resp.chunks || 0} 个向量块`)
      loadIndexed()
      setTimeout(() => { currentUpload.value = null }, 3000)
    } else {
      onUploadError({ event })
    }
  } catch {
    onUploadError({ event })
  }
  return file
}

const onUploadError = ({ event }) => {
  let detail = '上传失败'
  try {
    const resp = JSON.parse(event?.target?.response || '{}')
    detail = resp.detail || detail
  } catch {}
  if (currentUpload.value) {
    currentUpload.value.progress = 100
    currentUpload.value.status = 'error'
  }
  message.error(detail)
}

// ===================== Table =====================

const tableData = ref([])
const tableLoading = ref(false)

const columns = [
  {
    title: '文件名',
    key: 'name',
    ellipsis: { tooltip: true },
    render(row) {
      return h('div', { class: 'flex items-center gap-2' }, [
        h(NIcon, { size: 14, color: '#c53030' }, { default: () => h(FileText) }),
        h('span', { class: 'font-medium text-gray-800 text-xs' }, row.name)
      ])
    }
  },
  {
    title: '类型',
    key: 'type',
    width: 70,
    align: 'center',
    render(row) {
      return h(NTag, { size: 'tiny', bordered: false, type: 'default' }, { default: () => row.type })
    }
  },
  {
    title: '大小',
    key: 'size',
    width: 90,
    align: 'center',
    render(row) {
      return h('span', { class: 'font-mono text-[11px] text-gray-500' }, row.size || '-')
    }
  },
  {
    title: '状态',
    key: 'status',
    width: 80,
    align: 'center',
    render() {
      return h(NTag, { size: 'small', type: 'success', bordered: false }, { default: () => '已入库' })
    }
  },
  {
    title: '向量数',
    key: 'vectors',
    width: 80,
    align: 'center',
    render(row) {
      return h('span', { class: 'font-mono text-xs text-[#1a365d] font-semibold' }, String(row.vectors))
    }
  },
  {
    title: '入库时间',
    key: 'date',
    width: 150,
    align: 'center',
    render(row) {
      return h('span', { class: 'text-[11px] text-gray-500' }, row.date || '-')
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    align: 'center',
    render(row) {
      return h('div', { class: 'flex items-center justify-center gap-1' }, [
        h(NButton, {
          quaternary: true, circle: true, size: 'tiny',
          onClick: () => viewDocument(row)
        }, { icon: () => h(NIcon, { size: 14 }, { default: () => h(Eye) }) }),
        h(NButton, {
          quaternary: true, circle: true, size: 'tiny',
          onClick: () => confirmDelete(row)
        }, { icon: () => h(NIcon, { size: 14, color: '#c53030' }, { default: () => h(Trash2) }) })
      ])
    }
  }
]

const loadIndexed = async () => {
  tableLoading.value = true
  try {
    const token = localStorage.getItem('access_token')
    const resp = await fetch('/api/rag/indexed', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await resp.json()
    tableData.value = (data.sources || []).map(s => ({
      name: s.source || s,
      type: (s.source || '').split('.').pop()?.toLowerCase() || 'pdf',
      size: s.file_size ? formatBytes(s.file_size) : '-',
      vectors: s.count || 0,
      date: s.created_at ? formatDate(s.created_at) : '-',
      document_id: s.document_id
    }))
  } catch (e) {
    console.error('加载已入库文件失败', e)
  } finally {
    tableLoading.value = false
  }
}

// ===================== Delete =====================

const showDeleteModal = ref(false)
const deleteTarget = ref(null)
const isDeleting = ref(false)

const confirmDelete = (row) => {
  deleteTarget.value = row
  showDeleteModal.value = true
}

const doDelete = async () => {
  if (!deleteTarget.value) return
  isDeleting.value = true
  try {
    const token = localStorage.getItem('access_token')
    const resp = await fetch(`/api/rag/document/${encodeURIComponent(deleteTarget.value.name)}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const result = await resp.json()
    if (resp.ok && result.status === 'ok') {
      message.success(`已删除 ${result.deleted || 0} 个向量块`)
      await loadIndexed()
    } else {
      message.error(result.detail || result.message || '删除失败')
    }
  } catch (e) {
    message.error('删除请求失败: ' + e.message)
  } finally {
    isDeleting.value = false
    showDeleteModal.value = false
    deleteTarget.value = null
  }
}

// ===================== View =====================

const showViewModal = ref(false)
const viewTarget = ref(null)
const viewChunks = ref([])
const viewLoading = ref(false)

const viewDocument = async (row) => {
  viewTarget.value = row
  showViewModal.value = true
  viewLoading.value = true
  viewChunks.value = []
  try {
    const token = localStorage.getItem('access_token')
    const resp = await fetch(`/api/rag/document/${encodeURIComponent(row.name)}?limit=200`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    const data = await resp.json()
    viewChunks.value = (data.chunks || [])
      .map(r => ({
        text: r.text,
        page: r.page_number,
        isTable: r.is_table,
        score: r.score
      }))
  } catch (e) {
    message.error('查询文档内容失败')
  } finally {
    viewLoading.value = false
  }
}

// ===================== Utils =====================

const formatBytes = (bytes) => {
  if (!bytes || bytes === 0) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(1) + ' MB'
}

const formatDate = (isoStr) => {
  if (!isoStr) return '-'
  try {
    const d = new Date(isoStr)
    const pad = (n) => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
  } catch {
    return isoStr
  }
}

onMounted(() => { loadIndexed() })
</script>
