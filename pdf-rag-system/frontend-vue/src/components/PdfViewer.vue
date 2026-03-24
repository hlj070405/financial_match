<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in duration-200" @click.self="close">
    <div class="bg-white rounded-2xl shadow-2xl w-[90vw] h-[90vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-300">
      <!-- Header -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-gray-50">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-orange-100 flex items-center justify-center">
            <FileText class="w-5 h-5 text-orange-600" />
          </div>
          <div>
            <h3 class="font-semibold text-gray-900">{{ title }}</h3>
            <p class="text-xs text-gray-500">{{ subtitle }}</p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button 
            @click="downloadPdf"
            class="p-2 hover:bg-gray-200 rounded-lg transition-colors"
            title="下载PDF"
          >
            <Download class="w-5 h-5 text-gray-600" />
          </button>
          <button 
            @click="close"
            class="p-2 hover:bg-gray-200 rounded-lg transition-colors"
          >
            <X class="w-5 h-5 text-gray-600" />
          </button>
        </div>
      </div>

      <!-- PDF Content -->
      <div class="flex-1 overflow-hidden bg-gray-100">
        <iframe
          v-if="pdfUrl"
          :src="pdfUrl"
          class="w-full h-full border-0"
          title="PDF Viewer"
        />
        <div v-else class="flex items-center justify-center h-full">
          <div class="text-center space-y-3">
            <AlertCircle class="w-12 h-12 text-gray-400 mx-auto" />
            <p class="text-sm text-gray-600">无法加载PDF</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { X, Download, FileText, AlertCircle } from 'lucide-vue-next'

const props = defineProps({
  isOpen: Boolean,
  pdfUrl: String,
  title: String,
  subtitle: String
})

const emit = defineEmits(['close'])

const close = () => {
  emit('close')
}

const downloadPdf = () => {
  if (props.pdfUrl) {
    const link = document.createElement('a')
    link.href = props.pdfUrl
    link.download = `${props.title}.pdf`
    link.click()
  }
}
</script>
