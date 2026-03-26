<template>
  <div class="h-full flex flex-col">
    <!-- Hero -->
    <div class="relative overflow-hidden bg-gradient-to-br from-teal-50 via-white to-emerald-50 border-b border-gray-100">
      <div class="absolute inset-0 opacity-20">
        <div class="absolute top-3 left-16 w-48 h-48 bg-teal-200 rounded-full blur-3xl animate-pulse"></div>
        <div class="absolute bottom-0 right-10 w-40 h-40 bg-emerald-200 rounded-full blur-3xl animate-pulse" style="animation-delay:1s"></div>
      </div>
      <div class="relative px-6 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-teal-500 to-emerald-600 flex items-center justify-center shadow-md shadow-teal-500/20 shrink-0">
              <LayoutTemplate class="w-4.5 h-4.5 text-white" />
            </div>
            <div>
              <h1 class="text-base font-bold text-gray-900">自定义模板</h1>
              <p class="text-[11px] text-gray-500 mt-0.5">企业定制化报告模板与格式，标准化研报输出流程</p>
            </div>
          </div>
          <button @click="showCreateModal = true"
            class="px-4 py-2 bg-teal-600 text-white text-xs font-medium rounded-lg hover:bg-teal-700 transition-colors flex items-center gap-1.5">
            <Plus class="w-3.5 h-3.5" /> 新建模板
          </button>
        </div>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto p-6 custom-scrollbar">
      <div class="max-w-5xl mx-auto">
        <!-- Template Grid -->
        <div class="grid grid-cols-3 gap-4">
          <div v-for="tpl in templates" :key="tpl.id"
            class="bg-white border border-gray-100 rounded-xl shadow-sm overflow-hidden hover:shadow-md transition-all group cursor-pointer">
            <!-- Preview -->
            <div :class="['h-32 relative flex items-center justify-center', tpl.previewBg]">
              <div class="absolute inset-0 opacity-10">
                <div class="w-3/4 mx-auto mt-4 space-y-2">
                  <div class="h-3 bg-white/60 rounded w-2/3"></div>
                  <div class="h-2 bg-white/40 rounded w-full"></div>
                  <div class="h-2 bg-white/40 rounded w-5/6"></div>
                  <div class="h-2 bg-white/40 rounded w-3/4"></div>
                  <div class="h-8 bg-white/20 rounded mt-3"></div>
                </div>
              </div>
              <component :is="tpl.icon" class="w-8 h-8 text-white/80" />
              <div class="absolute top-2 right-2">
                <span v-if="tpl.isDefault" class="px-2 py-0.5 bg-white/90 text-[9px] font-bold text-teal-700 rounded-md">默认</span>
              </div>
            </div>
            <!-- Info -->
            <div class="p-4">
              <h3 class="text-sm font-bold text-gray-900 group-hover:text-teal-700 transition-colors">{{ tpl.name }}</h3>
              <p class="text-[10px] text-gray-500 mt-1 line-clamp-2">{{ tpl.desc }}</p>
              <div class="flex items-center justify-between mt-3">
                <div class="flex items-center gap-2">
                  <span class="px-2 py-0.5 bg-gray-100 text-gray-500 text-[9px] font-medium rounded">{{ tpl.sections }}章节</span>
                  <span class="px-2 py-0.5 bg-gray-100 text-gray-500 text-[9px] font-medium rounded">{{ tpl.usage }}次使用</span>
                </div>
                <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button class="p-1.5 hover:bg-gray-100 rounded-lg transition-colors text-gray-400 hover:text-gray-700" title="编辑">
                    <Pencil class="w-3.5 h-3.5" />
                  </button>
                  <button class="p-1.5 hover:bg-gray-100 rounded-lg transition-colors text-gray-400 hover:text-gray-700" title="复制">
                    <Copy class="w-3.5 h-3.5" />
                  </button>
                  <button class="p-1.5 hover:bg-rose-50 rounded-lg transition-colors text-gray-400 hover:text-rose-500" title="删除">
                    <Trash2 class="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Template Editor Preview (when selected) -->
        <div class="mt-6 bg-white border border-gray-100 rounded-xl shadow-sm p-6">
          <h3 class="text-sm font-bold text-gray-800 flex items-center gap-2 mb-4">
            <Settings class="w-4 h-4 text-gray-500" /> 模板章节配置预览
          </h3>
          <div class="grid grid-cols-2 gap-3">
            <div v-for="(section, i) in previewSections" :key="i"
              class="flex items-center gap-3 p-3 bg-gray-50 rounded-lg group/item">
              <div class="w-7 h-7 rounded-lg bg-teal-100 text-teal-700 flex items-center justify-center text-[11px] font-bold shrink-0">{{ i + 1 }}</div>
              <div class="flex-1 min-w-0">
                <p class="text-xs font-medium text-gray-700">{{ section.title }}</p>
                <p class="text-[10px] text-gray-400 truncate">{{ section.hint }}</p>
              </div>
              <div class="flex items-center gap-1 opacity-0 group-hover/item:opacity-100 transition-opacity">
                <GripVertical class="w-3.5 h-3.5 text-gray-300 cursor-move" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { LayoutTemplate, Plus, Pencil, Copy, Trash2, Settings, GripVertical,
  FileText, BarChart3, TrendingUp, Shield, BookOpen, Briefcase } from 'lucide-vue-next'

const showCreateModal = ref(false)

const templates = ref([
  { id: 1, name: '个股深度分析', desc: '覆盖公司基本面、财务、估值、风险的全面个股分析模板', icon: FileText, sections: 8, usage: 45, isDefault: true, previewBg: 'bg-gradient-to-br from-sky-400 to-blue-500' },
  { id: 2, name: '行业研究报告', desc: '行业规模、竞争格局、产业链、投资逻辑一体化行业报告', icon: BarChart3, sections: 7, usage: 32, isDefault: false, previewBg: 'bg-gradient-to-br from-violet-400 to-purple-500' },
  { id: 3, name: '宏观经济月报', desc: '每月宏观经济数据跟踪与政策解读标准化模板', icon: TrendingUp, sections: 6, usage: 18, isDefault: false, previewBg: 'bg-gradient-to-br from-emerald-400 to-teal-500' },
  { id: 4, name: '风险评估报告', desc: '企业信用风险、财务风险、市场风险综合评估', icon: Shield, sections: 5, usage: 12, isDefault: false, previewBg: 'bg-gradient-to-br from-rose-400 to-pink-500' },
  { id: 5, name: 'IPO研究报告', desc: '新股上市前景分析、估值定价与申购建议', icon: BookOpen, sections: 9, usage: 8, isDefault: false, previewBg: 'bg-gradient-to-br from-amber-400 to-orange-500' },
  { id: 6, name: '企业尽调报告', desc: '投前尽职调查标准化模板，覆盖法律、财务、业务', icon: Briefcase, sections: 10, usage: 5, isDefault: false, previewBg: 'bg-gradient-to-br from-gray-500 to-gray-700' }
])

const previewSections = ref([
  { title: '公司概况', hint: '公司基本信息、主营业务、发展历程' },
  { title: '财务分析', hint: '收入、利润、现金流、资产负债核心指标' },
  { title: '行业地位', hint: '市场份额、竞争优势、护城河分析' },
  { title: '估值分析', hint: 'PE/PB/DCF等多维度估值对比' },
  { title: '催化剂与风险', hint: '近期催化因素与主要风险提示' },
  { title: '投资建议', hint: '综合评级、目标价、建仓策略' }
])
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }
</style>
