<template>
  <div class="glass-panel p-6">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-2xl font-semibold text-gray-800">📈 分析结果</h2>
      
      <!-- 流式状态指示器 -->
      <div v-if="isLoading && result" class="flex items-center text-blue-600 text-sm">
        <div class="animate-pulse mr-2">●</div>
        <span>实时生成中... ({{ result.length }} 字符)</span>
      </div>
    </div>
    
    <!-- 初始加载状态（还没有内容时） -->
    <div v-if="isLoading && (!result || result.length === 0)" class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      <p class="mt-4 text-gray-600">AI 正在分析中，马上开始生成...</p>
    </div>

    <!-- 空状态 -->
    <div v-else-if="!result || result.length === 0" class="text-center text-gray-500 py-12">
      <svg class="mx-auto h-16 w-16 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      <p class="mt-4">上传文档后查看分析结果</p>
    </div>

    <!-- 分析结果 - 实时 Markdown 渲染 -->
    <div v-else class="space-y-4">
      <div 
        class="prose prose-slate max-w-none prose-headings:text-gray-800 prose-p:text-gray-700 prose-strong:text-gray-900 prose-ul:text-gray-700 prose-ol:text-gray-700"
        v-html="renderedMarkdown"
      ></div>
      
      <!-- 生成完成提示 -->
      <div v-if="!isLoading" class="flex items-center text-green-600 text-sm pt-4 border-t border-gray-200/50">
        <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
        </svg>
        <span>分析完成 (共 {{ result.length }} 字符)</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { marked } from 'marked'

const props = defineProps({
  result: String,
  isLoading: Boolean
})

// 配置 marked
marked.setOptions({
  breaks: true,
  gfm: true,
  headerIds: false,
  mangle: false
})

// 渲染 Markdown
const renderedMarkdown = computed(() => {
  if (!props.result) return ''
  return marked.parse(props.result)
})
</script>

<style scoped>
/* Markdown 样式优化 */
:deep(.prose) {
  font-size: 15px;
  line-height: 1.7;
}

:deep(.prose h1) {
  font-size: 1.8em;
  margin-top: 1.5em;
  margin-bottom: 0.8em;
  font-weight: 700;
  border-bottom: 2px solid #e5e7eb;
  padding-bottom: 0.3em;
}

:deep(.prose h2) {
  font-size: 1.5em;
  margin-top: 1.3em;
  margin-bottom: 0.7em;
  font-weight: 600;
}

:deep(.prose h3) {
  font-size: 1.25em;
  margin-top: 1.2em;
  margin-bottom: 0.6em;
  font-weight: 600;
}

:deep(.prose p) {
  margin-top: 0.8em;
  margin-bottom: 0.8em;
}

:deep(.prose ul), :deep(.prose ol) {
  margin-top: 0.8em;
  margin-bottom: 0.8em;
  padding-left: 1.5em;
}

:deep(.prose li) {
  margin-top: 0.3em;
  margin-bottom: 0.3em;
}

:deep(.prose strong) {
  font-weight: 600;
  color: #1f2937;
}

:deep(.prose code) {
  background-color: #f3f4f6;
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-size: 0.9em;
  color: #e11d48;
}

:deep(.prose pre) {
  background-color: #1f2937;
  color: #f9fafb;
  padding: 1em;
  border-radius: 6px;
  overflow-x: auto;
  margin-top: 1em;
  margin-bottom: 1em;
}

:deep(.prose pre code) {
  background-color: transparent;
  color: inherit;
  padding: 0;
}

:deep(.prose blockquote) {
  border-left: 4px solid #3b82f6;
  padding-left: 1em;
  color: #6b7280;
  font-style: italic;
  margin: 1em 0;
}

:deep(.prose table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1em 0;
}

:deep(.prose th), :deep(.prose td) {
  border: 1px solid #e5e7eb;
  padding: 0.6em;
  text-align: left;
}

:deep(.prose th) {
  background-color: #f9fafb;
  font-weight: 600;
}

:deep(.prose a) {
  color: #3b82f6;
  text-decoration: underline;
}

:deep(.prose a:hover) {
  color: #2563eb;
}
</style>
