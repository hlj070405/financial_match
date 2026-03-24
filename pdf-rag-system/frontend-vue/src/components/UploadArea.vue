<template>
  <div class="glass-panel p-6">
    <h2 class="text-2xl font-semibold mb-4 text-gray-800">📄 上传财报文档</h2>
    
    <!-- 上传区域 -->
    <div 
      @click="triggerFileInput"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="handleDrop"
      :class="[
        'border-2 border-dashed rounded-[var(--glass-radius)] p-8 text-center cursor-pointer transition',
        isDragging ? 'border-blue-500 bg-blue-50/50' : 'border-gray-300 hover:border-blue-500 bg-white/30'
      ]"
    >
      <svg class="mx-auto h-12 w-12 text-gray-500" stroke="currentColor" fill="none" viewBox="0 0 48 48">
        <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
      <p class="mt-2 text-sm text-gray-700">点击或拖拽 PDF 文件到此处</p>
      <input 
        ref="fileInputRef" 
        type="file" 
        accept=".pdf" 
        class="hidden"
        @change="handleFileSelect"
      >
    </div>

    <!-- 文件信息 -->
    <div v-if="uploadedFile" class="mt-4">
      <div class="bg-blue-50/50 border border-blue-200/50 rounded-[var(--glass-radius)] p-3">
        <p class="text-sm font-medium text-blue-800">{{ uploadedFile.name }}</p>
        <p class="text-xs text-blue-600 mt-1">{{ formatFileSize(uploadedFile.size) }}</p>
      </div>
    </div>

    <!-- 上传进度 -->
    <div v-if="isUploading" class="mt-4">
      <div class="flex items-center justify-between text-sm text-gray-600 mb-2">
        <span>上传中...</span>
        <span>{{ uploadProgress }}%</span>
      </div>
      <div class="w-full bg-gray-200/50 rounded-full h-2">
        <div 
          class="bg-blue-600 h-2 rounded-full transition-all"
          :style="{ width: uploadProgress + '%' }"
        ></div>
      </div>
    </div>

    <!-- 分析表单 -->
    <div class="mt-6">
      <label class="block text-sm font-medium text-gray-700 mb-2">分析问题</label>
      <textarea 
        v-model="question"
        rows="4" 
        class="glass-input"
        placeholder="例如：分析该公司的盈利能力和财务风险"
      ></textarea>
    </div>

    <div class="mt-4">
      <label class="block text-sm font-medium text-gray-700 mb-2">分析风格</label>
      <select 
        v-model="style"
        class="glass-input"
      >
        <option value="专业分析">专业分析</option>
        <option value="简单分析(不含专业术语)">简单分析(不含专业术语)</option>
      </select>
    </div>

    <div class="mt-6 w-full flex justify-center">
      <GlassButton 
        class="w-full"
        @click="handleAnalyze"
        :disabled="!fileId || isAnalyzing"
      >
        {{ isAnalyzing ? '分析中...' : '开始分析' }}
      </GlassButton>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { uploadPDF } from '../api/analysis'
import GlassButton from './GlassButton.vue'

const emit = defineEmits(['file-uploaded', 'analyze'])
const props = defineProps({
  isAnalyzing: Boolean
})

const fileInputRef = ref(null)
const isDragging = ref(false)
const isUploading = ref(false)
const uploadProgress = ref(0)
const uploadedFile = ref(null)
const fileId = ref(null)
const question = ref('分析该公司的财务状况，包括盈利能力、偿债能力和运营效率')
const style = ref('专业分析')

const triggerFileInput = () => {
  fileInputRef.value?.click()
}

const handleFileSelect = (event) => {
  const file = event.target.files?.[0]
  if (file) {
    handleFile(file)
  }
}

const handleDrop = (event) => {
  isDragging.value = false
  const file = event.dataTransfer.files?.[0]
  if (file) {
    handleFile(file)
  }
}

const handleFile = async (file) => {
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    alert('请上传 PDF 文件')
    return
  }

  uploadedFile.value = file
  isUploading.value = true
  uploadProgress.value = 0

  try {
    const progressInterval = setInterval(() => {
      if (uploadProgress.value < 90) {
        uploadProgress.value += 10
      }
    }, 200)

    const result = await uploadPDF(file)
    
    clearInterval(progressInterval)
    uploadProgress.value = 100
    
    fileId.value = result.file_id
    emit('file-uploaded', result.file_id)

    setTimeout(() => {
      isUploading.value = false
      uploadProgress.value = 0
    }, 1000)

  } catch (error) {
    alert('上传失败: ' + (error.response?.data?.detail || error.message))
    isUploading.value = false
    uploadProgress.value = 0
  }
}

const handleAnalyze = () => {
  if (!question.value.trim()) {
    alert('请输入分析问题')
    return
  }
  
  emit('analyze', {
    question: question.value,
    style: style.value
  })
}

const formatFileSize = (bytes) => {
  return (bytes / 1024 / 1024).toFixed(2) + ' MB'
}
</script>
