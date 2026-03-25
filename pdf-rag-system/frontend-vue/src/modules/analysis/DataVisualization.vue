<template>
  <div class="h-full flex flex-col gap-6 p-2 font-sans overflow-y-auto custom-scrollbar">
    <!-- Header Section -->
    <div class="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm shrink-0 flex items-center justify-between">
      <div>
        <h2 class="text-xl font-bold text-gray-900 flex items-center gap-3">
          <div class="p-2.5 rounded-xl bg-blue-50 text-blue-600">
            <BarChart3 class="w-6 h-6" />
          </div>
          幻诊·全景运营评估
        </h2>
        <p class="text-sm text-gray-500 mt-1.5 ml-1">
          透视真相的"心" — AI驱动的企业财务健康度全景分析
        </p>
      </div>

      <div class="flex items-center gap-3">
        <!-- 公司输入 -->
        <div class="flex items-center gap-2">
          <input
            v-model="companyInput"
            @keydown.enter="fetchDiagnosis"
            type="text"
            placeholder="输入公司名称..."
            class="px-4 py-2 text-sm border border-gray-200 rounded-xl bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 w-48 transition-all"
          />
          <button
            @click="fetchDiagnosis"
            :disabled="loading"
            class="px-4 py-2 bg-gray-900 text-white text-sm font-medium rounded-xl hover:bg-gray-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <Loader2 v-if="loading" class="w-4 h-4 animate-spin" />
            <Search v-else class="w-4 h-4" />
            {{ loading ? '分析中...' : '诊断' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading && !diagnosisData" class="flex-1 flex items-center justify-center">
      <div class="text-center">
        <Loader2 class="w-10 h-10 animate-spin text-blue-500 mx-auto" />
        <p class="text-sm text-gray-500 mt-4">AI 正在分析企业财务数据...</p>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="!diagnosisData" class="flex-1 flex items-center justify-center">
      <div class="text-center max-w-md">
        <div class="p-4 rounded-2xl bg-gray-50 inline-block mb-4">
          <BarChart3 class="w-12 h-12 text-gray-300" />
        </div>
        <h3 class="text-lg font-semibold text-gray-700 mb-2">输入公司名称开始诊断</h3>
        <p class="text-sm text-gray-400 leading-relaxed">
          AI 将自动分析企业财报，提取核心指标，生成行业对标与风险评估。每家公司的分析结果由 AI 自主编排，展示最有价值的信息。
        </p>
      </div>
    </div>

    <!-- Diagnosis Content -->
    <template v-else>
      <!-- Summary Banner -->
      <div v-if="diagnosisData.summary" class="bg-gradient-to-r from-gray-900 to-gray-800 rounded-2xl p-6 text-white shrink-0">
        <div class="flex items-center gap-2 mb-2">
          <Sparkles class="w-4 h-4 text-orange-400" />
          <span class="text-xs font-semibold text-orange-300 uppercase tracking-wider">AI 诊断摘要</span>
        </div>
        <h3 class="text-lg font-bold mb-1">{{ diagnosisData.company }} · {{ diagnosisData.period }}</h3>
        <p class="text-sm text-gray-300 leading-relaxed">{{ diagnosisData.summary }}</p>
      </div>

      <!-- Dynamic Components from AI -->
      <DiagnosisRenderer :components="diagnosisData.components || []" />
    </template>

    <!-- Error State -->
    <div v-if="error" class="bg-red-50 border border-red-100 rounded-2xl p-4 text-sm text-red-600">
      {{ error }}
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { BarChart3, Search, Loader2, Sparkles } from 'lucide-vue-next'
import DiagnosisRenderer from '../diagnosis/DiagnosisRenderer.vue'

const companyInput = ref('')
const diagnosisData = ref(null)
const loading = ref(false)
const error = ref('')

const fetchDiagnosis = async () => {
  if (!companyInput.value.trim() && !diagnosisData.value) {
    // 如果没有输入，加载mock数据用于演示
    loading.value = true
    error.value = ''
    try {
      const res = await fetch('/api/diagnosis/mock')
      if (!res.ok) throw new Error('请求失败')
      diagnosisData.value = await res.json()
    } catch (e) {
      error.value = '加载失败: ' + e.message
    } finally {
      loading.value = false
    }
    return
  }

  loading.value = true
  error.value = ''
  try {
    const res = await fetch('/api/diagnosis/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ company: companyInput.value.trim() })
    })
    if (!res.ok) throw new Error('请求失败')
    diagnosisData.value = await res.json()
  } catch (e) {
    error.value = '分析失败: ' + e.message
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #e5e7eb;
  border-radius: 3px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #d1d5db;
}
</style>
