<template>
  <div class="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
    <div class="flex items-center gap-2 mb-3">
      <div class="p-2 rounded-lg bg-amber-50">
        <Lightbulb class="w-4 h-4 text-amber-500" />
      </div>
      <h3 class="text-sm font-bold text-gray-900">{{ data.title }}</h3>
    </div>
    <div class="text-sm text-gray-700 leading-relaxed whitespace-pre-line" v-html="renderedContent"></div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Lightbulb } from 'lucide-vue-next'
import { marked } from 'marked'

const props = defineProps({ data: Object })

marked.setOptions({ breaks: true, gfm: true })

const renderedContent = computed(() => {
  if (!props.data.content) return ''
  return marked.parse(props.data.content)
})
</script>
