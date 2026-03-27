<template>
  <div class="h-full flex flex-col">
    <!-- Hero -->
    <div class="relative overflow-hidden bg-gradient-to-br from-violet-50 via-white to-fuchsia-50 border-b border-gray-100">
      <div class="absolute inset-0 opacity-20">
        <div class="absolute top-3 left-16 w-48 h-48 bg-violet-200 rounded-full blur-3xl animate-pulse"></div>
        <div class="absolute bottom-0 right-10 w-40 h-40 bg-fuchsia-200 rounded-full blur-3xl animate-pulse" style="animation-delay:1s"></div>
      </div>
      <div class="relative px-6 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500 to-fuchsia-600 flex items-center justify-center shadow-md shadow-violet-500/20 shrink-0">
              <Plug class="w-4.5 h-4.5 text-white" />
            </div>
            <div>
              <h1 class="text-base font-bold text-gray-900">多源异构接入</h1>
              <p class="text-[11px] text-gray-500 mt-0.5">对接数据库、API、文件系统等多种数据源，统一数据管理</p>
            </div>
          </div>
          <button @click="showAddModal = true"
            class="px-4 py-2 bg-violet-600 text-white text-xs font-medium rounded-lg hover:bg-violet-700 transition-colors flex items-center gap-1.5">
            <Plus class="w-3.5 h-3.5" /> 添加数据源
          </button>
        </div>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto p-6 custom-scrollbar">
      <div class="max-w-5xl mx-auto space-y-5">
        <!-- Connected Sources Grid -->
        <div class="grid grid-cols-3 gap-4">
          <div v-for="src in dataSources" :key="src.id"
            class="bg-white border border-gray-100 rounded-xl shadow-sm overflow-hidden hover:shadow-md transition-all group">
            <!-- Header -->
            <div :class="['h-2', src.statusColor]"></div>
            <div class="p-4">
              <div class="flex items-center justify-between mb-3">
                <div class="flex items-center gap-2.5">
                  <div :class="['w-10 h-10 rounded-xl flex items-center justify-center', src.iconBg]">
                    <component :is="src.icon" :class="['w-5 h-5', src.iconColor]" />
                  </div>
                  <div>
                    <h3 class="text-sm font-bold text-gray-900">{{ src.name }}</h3>
                    <p class="text-[10px] text-gray-400">{{ src.type }}</p>
                  </div>
                </div>
                <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button class="p-1.5 hover:bg-gray-100 rounded-lg text-gray-400 hover:text-gray-700 transition-colors"><Settings class="w-3.5 h-3.5" /></button>
                  <button class="p-1.5 hover:bg-gray-100 rounded-lg text-gray-400 hover:text-rose-500 transition-colors"><Trash2 class="w-3.5 h-3.5" /></button>
                </div>
              </div>
              <div class="space-y-2">
                <div class="flex items-center justify-between text-[11px]">
                  <span class="text-gray-500">状态</span>
                  <span :class="['px-2 py-0.5 rounded-full text-[9px] font-bold', src.statusBadge]">{{ src.status }}</span>
                </div>
                <div class="flex items-center justify-between text-[11px]">
                  <span class="text-gray-500">数据量</span>
                  <span class="font-mono text-gray-800">{{ src.dataCount }}</span>
                </div>
                <div class="flex items-center justify-between text-[11px]">
                  <span class="text-gray-500">最后同步</span>
                  <span class="text-gray-600">{{ src.lastSync }}</span>
                </div>
                <div class="flex items-center justify-between text-[11px]">
                  <span class="text-gray-500">同步频率</span>
                  <span class="text-gray-600">{{ src.syncFreq }}</span>
                </div>
              </div>
              <div class="mt-3 flex gap-2">
                <button class="flex-1 py-1.5 text-[10px] font-medium bg-gray-50 text-gray-600 rounded-lg hover:bg-gray-100 transition-colors flex items-center justify-center gap-1">
                  <RefreshCw class="w-3 h-3" /> 同步
                </button>
                <button class="flex-1 py-1.5 text-[10px] font-medium bg-violet-50 text-violet-700 rounded-lg hover:bg-violet-100 transition-colors flex items-center justify-center gap-1">
                  <Eye class="w-3 h-3" /> 详情
                </button>
              </div>
            </div>
          </div>

          <!-- Add New Card -->
          <div @click="showAddModal = true"
            class="border-2 border-dashed border-gray-200 rounded-xl p-8 flex flex-col items-center justify-center cursor-pointer hover:border-violet-300 hover:bg-violet-50/30 transition-all group">
            <div class="w-12 h-12 rounded-xl bg-gray-100 group-hover:bg-violet-100 flex items-center justify-center mb-3 transition-colors">
              <Plus class="w-5 h-5 text-gray-400 group-hover:text-violet-500 transition-colors" />
            </div>
            <p class="text-xs font-medium text-gray-500 group-hover:text-violet-700 transition-colors">添加新数据源</p>
            <p class="text-[10px] text-gray-400 mt-1">数据库 / API / 文件系统</p>
          </div>
        </div>

        <!-- Sync Log -->
        <div class="bg-white border border-gray-100 rounded-xl shadow-sm overflow-hidden">
          <div class="px-5 py-3 bg-gray-50 border-b border-gray-100 flex items-center justify-between">
            <h3 class="text-xs font-bold text-gray-800 flex items-center gap-2">
              <Activity class="w-4 h-4 text-violet-500" /> 同步日志
            </h3>
            <span class="text-[10px] text-gray-400">最近24小时</span>
          </div>
          <div class="divide-y divide-gray-50">
            <div v-for="(log, i) in syncLogs" :key="i"
              class="px-5 py-2.5 flex items-center gap-3 hover:bg-gray-50/50 transition-colors">
              <div :class="['w-2 h-2 rounded-full shrink-0', log.success ? 'bg-emerald-500' : 'bg-rose-500']"></div>
              <span class="text-[10px] text-gray-400 font-mono w-16 shrink-0">{{ log.time }}</span>
              <span class="text-xs text-gray-700 flex-1">{{ log.text }}</span>
              <span class="text-[10px] font-mono text-gray-400 shrink-0">{{ log.duration }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Plug, Plus, Settings, Trash2, RefreshCw, Eye, Activity,
  Database, Globe, FolderOpen, FileSpreadsheet, Cloud } from 'lucide-vue-next'

const showAddModal = ref(false)

const dataSources = ref([
  { id: 1, name: 'PostgreSQL 主库', type: '关系型数据库', icon: Database, iconBg: 'bg-blue-50', iconColor: 'text-blue-600',
    status: '已连接', statusBadge: 'bg-emerald-100 text-emerald-700', statusColor: 'bg-emerald-500',
    dataCount: '2.8M 条', lastSync: '5分钟前', syncFreq: '每15分钟' },
  { id: 2, name: 'Tushare API', type: 'REST API', icon: Globe, iconBg: 'bg-amber-50', iconColor: 'text-amber-600',
    status: '已连接', statusBadge: 'bg-emerald-100 text-emerald-700', statusColor: 'bg-emerald-500',
    dataCount: '5.2K 接口', lastSync: '实时', syncFreq: '实时推送' },
  { id: 3, name: '财报PDF仓库', type: '文件系统(NFS)', icon: FolderOpen, iconBg: 'bg-rose-50', iconColor: 'text-rose-600',
    status: '已连接', statusBadge: 'bg-emerald-100 text-emerald-700', statusColor: 'bg-emerald-500',
    dataCount: '1,247 个文件', lastSync: '1小时前', syncFreq: '每日凌晨' },
  { id: 4, name: 'Wind 金融终端', type: '专有API', icon: FileSpreadsheet, iconBg: 'bg-emerald-50', iconColor: 'text-emerald-600',
    status: '已连接', statusBadge: 'bg-emerald-100 text-emerald-700', statusColor: 'bg-emerald-500',
    dataCount: '15.6K 指标', lastSync: '30分钟前', syncFreq: '每30分钟' },
  { id: 5, name: 'S3 对象存储', type: '云存储', icon: Cloud, iconBg: 'bg-violet-50', iconColor: 'text-violet-600',
    status: '同步中', statusBadge: 'bg-blue-100 text-blue-700', statusColor: 'bg-blue-500',
    dataCount: '850GB', lastSync: '同步中...', syncFreq: '按需' },
  { id: 6, name: 'Redis 缓存', type: '键值存储', icon: Database, iconBg: 'bg-red-50', iconColor: 'text-red-600',
    status: '连接断开', statusBadge: 'bg-rose-100 text-rose-700', statusColor: 'bg-rose-500',
    dataCount: '-', lastSync: '2小时前', syncFreq: '实时' }
])

const syncLogs = ref([
  { time: '15:45:02', text: 'Tushare API: 日线数据同步完成，更新 4,823 条记录', success: true, duration: '2.3s' },
  { time: '15:30:00', text: 'Wind 金融终端: 财务指标同步完成，更新 1,256 条', success: true, duration: '8.7s' },
  { time: '15:15:01', text: 'PostgreSQL 主库: 增量同步完成，新增 342 条', success: true, duration: '1.1s' },
  { time: '15:00:00', text: 'S3 对象存储: 开始全量同步，850GB', success: true, duration: '进行中' },
  { time: '14:45:03', text: 'Redis 缓存: 连接超时，尝试重连失败', success: false, duration: '-' },
  { time: '14:30:00', text: 'Wind 金融终端: 实时行情数据同步完成', success: true, duration: '0.8s' },
  { time: '06:00:00', text: '财报PDF仓库: 夜间全量扫描完成，新增 23 个文件', success: true, duration: '45.2s' }
])
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 4px; }
</style>
