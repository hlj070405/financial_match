<template>
  <div 
    ref="containerRef" 
    class="financial-overlay"
    @mousemove="handleMouseMove"
  >
    <div
      v-for="(term, index) in visibleTerms"
      :key="index"
      class="financial-term"
      :style="{
        left: term.x + 'px',
        top: term.y + 'px',
        color: term.color,
        opacity: term.opacity,
        fontSize: term.size + 'px',
        animationDelay: term.delay + 's'
      }"
    >
      {{ term.text }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

const containerRef = ref(null)
const visibleTerms = ref([])
let mouseX = 0
let mouseY = 0
let termIdCounter = 0

// 真实金融术语和热点词汇
const financialTerms = [
  // 财报分析核心指标
  'ROE', 'ROA', 'EPS', 'P/E', 'P/B', 'PEG',
  '资产负债率', '流动比率', '速动比率', '现金比率',
  '毛利率', '净利率', '营收增长', '利润增长',
  
  // 风险评估
  '信用评级', 'VaR', '违约概率', '偿债能力',
  '流动性风险', '市场风险', '操作风险', '信用风险',
  
  // 投资决策
  '估值分析', '价值投资', '成长投资', '量化策略',
  '资产配置', '风险对冲', '套利交易', '因子模型',
  
  // 2026热点
  'AI渗透', '新质生产力', '供应链重构', '碳中和',
  '数字货币', '半导体', '新能源', '生物医药',
  
  // 宏观经济
  'GDP', 'CPI', 'PPI', 'PMI', '利率中枢',
  '货币政策', '财政政策', '通胀预期', '汇率波动',
  
  // 市场指标
  '市盈率', '市净率', '换手率', '振幅',
  '成交量', '资金流向', '北向资金', '融资融券',
  
  // 行业分析
  '行业对标', '竞争格局', '市场份额', '护城河',
  '盈利模式', '商业模式', '核心竞争力', '增长曲线',
  
  // 技术分析
  'MACD', 'KDJ', 'RSI', '布林带',
  '均线系统', '支撑位', '阻力位', '趋势线',
  
  // 财务健康
  '现金流', '营运资本', '资本结构', '杠杆率',
  '存货周转', '应收账款', '资产周转率', '权益乘数'
]

const colors = [
  '#60a5fa', // 蓝色 - 稳健
  '#a78bfa', // 紫色 - 创新
  '#f472b6', // 粉色 - 增长
  '#22d3ee', // 青色 - 流动
  '#fbbf24', // 金色 - 价值
]

const handleMouseMove = (event) => {
  mouseX = event.clientX
  mouseY = event.clientY
  
  // 随机决定是否生成新词汇（降低频率以保持优雅）
  if (Math.random() > 0.85) {
    createTerm()
  }
}

const createTerm = () => {
  const randomTerm = financialTerms[Math.floor(Math.random() * financialTerms.length)]
  const randomColor = colors[Math.floor(Math.random() * colors.length)]
  
  // 在鼠标周围随机偏移位置
  const offsetX = (Math.random() - 0.5) * 200
  const offsetY = (Math.random() - 0.5) * 200
  
  const newTerm = {
    id: termIdCounter++,
    text: randomTerm,
    x: mouseX + offsetX,
    y: mouseY + offsetY,
    color: randomColor,
    opacity: 0,
    size: 12 + Math.random() * 8,
    delay: Math.random() * 0.3
  }
  
  visibleTerms.value.push(newTerm)
  
  // 淡入效果
  setTimeout(() => {
    const term = visibleTerms.value.find(t => t.id === newTerm.id)
    if (term) {
      term.opacity = 0.6 + Math.random() * 0.3
    }
  }, 50)
  
  // 自动淡出并移除
  setTimeout(() => {
    const index = visibleTerms.value.findIndex(t => t.id === newTerm.id)
    if (index !== -1) {
      visibleTerms.value[index].opacity = 0
      setTimeout(() => {
        visibleTerms.value.splice(index, 1)
      }, 800)
    }
  }, 3000 + Math.random() * 2000)
  
  // 限制同时显示的词汇数量
  if (visibleTerms.value.length > 50) {
    visibleTerms.value.shift()
  }
}

onMounted(() => {
  // 初始随机生成一些词汇
  for (let i = 0; i < 15; i++) {
    setTimeout(() => {
      const randomX = Math.random() * window.innerWidth
      const randomY = Math.random() * window.innerHeight
      mouseX = randomX
      mouseY = randomY
      createTerm()
    }, i * 200)
  }
})

onBeforeUnmount(() => {
  visibleTerms.value = []
})
</script>

<style scoped>
.financial-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
  pointer-events: none;
  overflow: hidden;
}

.financial-term {
  position: absolute;
  font-weight: 600;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  letter-spacing: 0.5px;
  text-shadow: 0 0 20px currentColor, 0 0 40px currentColor;
  transform: translate(-50%, -50%);
  transition: opacity 0.8s ease-out;
  pointer-events: none;
  white-space: nowrap;
  animation: float 4s ease-in-out infinite;
  backdrop-filter: blur(1px);
}

@keyframes float {
  0%, 100% {
    transform: translate(-50%, -50%) translateY(0px);
  }
  50% {
    transform: translate(-50%, -50%) translateY(-10px);
  }
}

.financial-term::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 120%;
  height: 120%;
  background: radial-gradient(circle, currentColor 0%, transparent 70%);
  opacity: 0.1;
  transform: translate(-50%, -50%);
  filter: blur(15px);
  z-index: -1;
}
</style>
