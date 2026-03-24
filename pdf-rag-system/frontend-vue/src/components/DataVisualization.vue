<template>
  <div class="h-full flex flex-col gap-6 p-2 font-sans overflow-hidden">
    <!-- Header Section -->
    <div class="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm shrink-0 flex items-center justify-between">
      <div>
        <h2 class="text-xl font-bold text-gray-900 flex items-center gap-3">
          <div class="p-2.5 rounded-xl bg-blue-50 text-blue-600">
            <BarChart3 class="w-6 h-6" />
          </div>
          幻诊·全景运营评估
        </h2>
        <p class="text-sm text-gray-500 mt-1.5 ml-1">透视真相的"心" — 企业财务健康度全景分析</p>
      </div>
      
      <div class="flex items-center gap-3">
        <div class="flex items-center bg-gray-50 rounded-xl p-1 border border-gray-100">
           <button 
             v-for="period in ['近7天', '近30天', '本季度', '本年度']" 
             :key="period"
             class="px-3 py-1.5 text-xs font-medium rounded-lg transition-all hover:text-gray-900 text-gray-500 hover:bg-white hover:shadow-sm relative group overflow-hidden"
           >
             <div class="absolute bottom-0 left-0 w-full h-0.5 bg-orange-500 opacity-0 group-hover:opacity-100 transition-opacity"></div>
             {{ period }}
           </button>
        </div>
        <button class="p-2.5 hover:bg-gray-50 rounded-xl text-gray-400 hover:text-gray-600 transition-colors border border-transparent hover:border-gray-100 relative group overflow-hidden">
          <div class="absolute bottom-0 left-0 w-full h-0.5 bg-orange-500 opacity-0 group-hover:opacity-100 transition-opacity"></div>
          <Download class="w-5 h-5" />
        </button>
      </div>
    </div>

    <!-- Metrics Grid -->
    <div class="grid grid-cols-4 gap-6 shrink-0">
      <div v-for="metric in metrics" :key="metric.title" class="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm hover:shadow-md transition-all group">
        <div class="flex items-center justify-between mb-4">
          <span class="text-sm font-medium text-gray-500">{{ metric.title }}</span>
          <div :class="cn('w-8 h-8 rounded-lg flex items-center justify-center transition-colors', metric.bgClass, metric.textClass)">
            <component :is="metric.icon" class="w-4 h-4" />
          </div>
        </div>
        <div class="flex items-baseline justify-between">
          <div class="text-2xl font-bold text-gray-900">{{ metric.value }}</div>
          <div class="flex items-center text-xs font-medium bg-gray-50 px-2 py-1 rounded-full">
            <component 
              :is="metric.trend === 'up' ? TrendingUp : TrendingDown" 
              :class="cn('w-3 h-3 mr-1', metric.trend === 'up' ? 'text-emerald-500' : 'text-rose-500')" 
            />
            <span :class="metric.trend === 'up' ? 'text-emerald-600' : 'text-rose-600'">{{ metric.change }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Charts Grid -->
    <div class="grid grid-cols-2 gap-6 flex-1 min-h-0">
      <!-- Revenue Chart -->
      <div class="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm flex flex-col min-h-0">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-sm font-bold text-gray-900 flex items-center gap-2">
            <LineChart class="w-4 h-4 text-blue-500" />
            营收与利润趋势
          </h3>
          <button class="text-gray-400 hover:text-gray-600">
            <MoreHorizontal class="w-4 h-4" />
          </button>
        </div>
        <div ref="revenueChart" class="flex-1 w-full min-h-[200px]"></div>
      </div>

      <!-- Pie Chart -->
      <div class="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm flex flex-col min-h-0">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-sm font-bold text-gray-900 flex items-center gap-2">
            <PieChartIcon class="w-4 h-4 text-violet-500" />
            业务结构分析
          </h3>
          <button class="text-gray-400 hover:text-gray-600">
            <MoreHorizontal class="w-4 h-4" />
          </button>
        </div>
        <div ref="pieChart" class="flex-1 w-full min-h-[200px]"></div>
      </div>

      <!-- Bar Chart -->
      <div class="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm flex flex-col min-h-0">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-sm font-bold text-gray-900 flex items-center gap-2">
            <BarChart2 class="w-4 h-4 text-emerald-500" />
            核心指标对标
          </h3>
          <button class="text-gray-400 hover:text-gray-600">
            <MoreHorizontal class="w-4 h-4" />
          </button>
        </div>
        <div ref="barChart" class="flex-1 w-full min-h-[200px]"></div>
      </div>

      <!-- Radar Chart -->
      <div class="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm flex flex-col min-h-0">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-sm font-bold text-gray-900 flex items-center gap-2">
            <Radar class="w-4 h-4 text-orange-500" />
            综合风险评估
          </h3>
          <button class="text-gray-400 hover:text-gray-600">
            <MoreHorizontal class="w-4 h-4" />
          </button>
        </div>
        <div ref="radarChart" class="flex-1 w-full min-h-[200px]"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import * as echarts from 'echarts'
import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { 
  BarChart3, 
  Download, 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Wallet, 
  Percent, 
  Scale,
  LineChart,
  PieChart as PieChartIcon,
  BarChart2,
  Radar,
  MoreHorizontal
} from 'lucide-vue-next'

const cn = (...inputs) => twMerge(clsx(inputs))

const revenueChart = ref(null)
const pieChart = ref(null)
const barChart = ref(null)
const radarChart = ref(null)

const metrics = ref([
  {
    title: '总营收 (TTM)',
    value: '¥602.3亿',
    change: '+23.5%',
    trend: 'up',
    icon: DollarSign,
    bgClass: 'bg-blue-50',
    textClass: 'text-blue-600'
  },
  {
    title: '净利润 (TTM)',
    value: '¥166.2亿',
    change: '+81.4%',
    trend: 'up',
    icon: Wallet,
    bgClass: 'bg-emerald-50',
    textClass: 'text-emerald-600'
  },
  {
    title: '净资产收益率 (ROE)',
    value: '27.6%',
    change: '+5.2%',
    trend: 'up',
    icon: Percent,
    bgClass: 'bg-violet-50',
    textClass: 'text-violet-600'
  },
  {
    title: '资产负债率',
    value: '58.3%',
    change: '-2.1%',
    trend: 'down', // down is good for liabilities usually, but visual indicator shows direction
    icon: Scale,
    bgClass: 'bg-orange-50',
    textClass: 'text-orange-600'
  }
])

onMounted(() => {
  initRevenueChart()
  initPieChart()
  initBarChart()
  initRadarChart()
})

const initRevenueChart = () => {
  const chart = echarts.init(revenueChart.value)
  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#f3f4f6',
      borderWidth: 1,
      textStyle: { color: '#1f2937', fontSize: 12 },
      extraCssText: 'box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); border-radius: 8px;'
    },
    legend: {
      data: ['营收', '净利润'],
      bottom: 0,
      icon: 'circle',
      textStyle: { fontSize: 12, color: '#6b7280' }
    },
    grid: {
      left: '2%',
      right: '4%',
      bottom: '10%',
      top: '5%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: ['2019', '2020', '2021', '2022', '2023'],
      axisLine: { lineStyle: { color: '#f3f4f6' } },
      axisTick: { show: false },
      axisLabel: { color: '#9ca3af', fontSize: 11, margin: 12 }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } },
      axisLabel: { color: '#9ca3af', fontSize: 11 }
    },
    series: [
      {
        name: '营收',
        type: 'line',
        data: [277, 156, 216, 424, 602],
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 3, color: '#3b82f6' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(59, 130, 246, 0.15)' },
            { offset: 1, color: 'rgba(59, 130, 246, 0.0)' }
          ])
        }
      },
      {
        name: '净利润',
        type: 'line',
        data: [16, 42, 30, 92, 166],
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 3, color: '#10b981' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(16, 185, 129, 0.15)' },
            { offset: 1, color: 'rgba(16, 185, 129, 0.0)' }
          ])
        }
      }
    ]
  }
  chart.setOption(option)
  window.addEventListener('resize', () => chart.resize())
}

const initPieChart = () => {
  const chart = echarts.init(pieChart.value)
  const option = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#f3f4f6',
      borderWidth: 1,
      textStyle: { color: '#1f2937', fontSize: 12 },
      extraCssText: 'box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); border-radius: 8px;'
    },
    legend: {
      orient: 'vertical',
      right: '0%',
      top: 'center',
      icon: 'circle',
      textStyle: { fontSize: 12, color: '#6b7280' },
      itemGap: 16
    },
    series: [
      {
        type: 'pie',
        radius: ['50%', '80%'],
        center: ['30%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 6,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: { show: false },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold',
            color: '#1f2937'
          },
          scale: true,
          scaleSize: 10
        },
        data: [
          { value: 335, name: '新能源汽车', itemStyle: { color: '#3b82f6' } },
          { value: 234, name: '电池业务', itemStyle: { color: '#8b5cf6' } },
          { value: 154, name: '电子产品', itemStyle: { color: '#10b981' } },
          { value: 135, name: '其他业务', itemStyle: { color: '#f59e0b' } }
        ]
      }
    ]
  }
  chart.setOption(option)
  window.addEventListener('resize', () => chart.resize())
}

const initBarChart = () => {
  const chart = echarts.init(barChart.value)
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#f3f4f6',
      borderWidth: 1,
      textStyle: { color: '#1f2937', fontSize: 12 },
      extraCssText: 'box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); border-radius: 8px;'
    },
    legend: {
      data: ['比亚迪', '特斯拉', '宁德时代'],
      bottom: 0,
      icon: 'circle',
      textStyle: { fontSize: 12, color: '#6b7280' }
    },
    grid: {
      left: '2%',
      right: '4%',
      bottom: '10%',
      top: '5%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: ['ROE', '毛利率', '净利率', '资产周转率'],
      axisLine: { lineStyle: { color: '#f3f4f6' } },
      axisTick: { show: false },
      axisLabel: { color: '#9ca3af', fontSize: 11, margin: 12 }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } },
      axisLabel: { color: '#9ca3af', fontSize: 11 }
    },
    series: [
      {
        name: '比亚迪',
        type: 'bar',
        barGap: '20%',
        barWidth: 12,
        data: [27.6, 21.9, 27.6, 1.42],
        itemStyle: { color: '#3b82f6', borderRadius: [4, 4, 0, 0] }
      },
      {
        name: '特斯拉',
        type: 'bar',
        barWidth: 12,
        data: [23.1, 25.6, 15.5, 0.89],
        itemStyle: { color: '#8b5cf6', borderRadius: [4, 4, 0, 0] }
      },
      {
        name: '宁德时代',
        type: 'bar',
        barWidth: 12,
        data: [19.8, 22.4, 16.8, 1.12],
        itemStyle: { color: '#10b981', borderRadius: [4, 4, 0, 0] }
      }
    ]
  }
  chart.setOption(option)
  window.addEventListener('resize', () => chart.resize())
}

const initRadarChart = () => {
  const chart = echarts.init(radarChart.value)
  const option = {
    tooltip: {
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#f3f4f6',
      borderWidth: 1,
      textStyle: { color: '#1f2937', fontSize: 12 },
      extraCssText: 'box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); border-radius: 8px;'
    },
    legend: {
      data: ['当前评分', '行业平均'],
      bottom: 0,
      icon: 'circle',
      textStyle: { fontSize: 12, color: '#6b7280' }
    },
    radar: {
      indicator: [
        { name: '盈利能力', max: 100 },
        { name: '偿债能力', max: 100 },
        { name: '运营能力', max: 100 },
        { name: '成长能力', max: 100 },
        { name: '市场地位', max: 100 }
      ],
      radius: '65%',
      center: ['50%', '50%'],
      splitArea: {
        show: true,
        areaStyle: {
          color: ['#f9fafb', '#ffffff']
        }
      },
      axisLine: { lineStyle: { color: '#e5e7eb' } },
      splitLine: { lineStyle: { color: '#e5e7eb' } },
      axisName: {
        color: '#6b7280',
        fontSize: 11
      }
    },
    series: [
      {
        type: 'radar',
        data: [
          {
            value: [85, 72, 88, 92, 78],
            name: '当前评分',
            areaStyle: { color: 'rgba(59, 130, 246, 0.2)' },
            lineStyle: { color: '#3b82f6', width: 2 },
            itemStyle: { color: '#3b82f6' },
            symbol: 'circle',
            symbolSize: 6
          },
          {
            value: [70, 65, 75, 68, 72],
            name: '行业平均',
            areaStyle: { color: 'rgba(139, 92, 246, 0.1)' },
            lineStyle: { color: '#8b5cf6', width: 2, type: 'dashed' },
            itemStyle: { color: '#8b5cf6' },
            symbol: 'none'
          }
        ]
      }
    ]
  }
  chart.setOption(option)
  window.addEventListener('resize', () => chart.resize())
}
</script>
