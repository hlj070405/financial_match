import {
  MessageSquare,
  CandlestickChart,
  Database,
  Search,
  TrendingUp
} from 'lucide-vue-next'

export const ALL_MODULES = [
  {
    id: 'chat',
    title: '智能咨询',
    icon: MessageSquare,
    category: 'smart',
    features: [
      { id: 'chat_main', name: '幻思对话', desc: 'RAG 智能对话，基于知识库的深度问答与分析' }
    ]
  },
  {
    id: 'market',
    title: '行情终端',
    icon: CandlestickChart,
    category: 'market',
    features: [
      { id: 'mkt_kline', name: 'K线与基础行情', desc: '实时行情、分时图、日K线' },
      { id: 'mkt_indicator', name: '技术指标叠加', desc: 'MACD、RSI、布林带等技术指标' },
      { id: 'mkt_flow', name: '资金流向', desc: '主力资金、北向资金等资金面分析' }
    ]
  },
  {
    id: 'rag',
    title: '智能检索',
    icon: Search,
    category: 'enterprise',
    features: [
      { id: 'rag_search', name: '语义搜索', desc: '自然语言意图理解与语义级文档检索' }
    ]
  },
  {
    id: 'backtest',
    title: '量化回测',
    icon: TrendingUp,
    category: 'market',
    features: [
      { id: 'bt_main', name: '策略回测', desc: '选择股票和策略，执行历史回测分析' }
    ]
  },
  {
    id: 'datasource',
    title: '数据源管理',
    icon: Database,
    category: 'enterprise',
    features: [
      { id: 'ds_upload', name: '单文件上传', desc: '支持PDF、Excel等单文件上传与解析' },
      { id: 'ds_batch', name: '批量导入', desc: '大批量文档一键导入与自动处理' }
    ]
  }
]

export const ROLES = {
  'personal_general': {
    id: 'personal_general',
    name: '大众用户',
    group: 'personal',
    groupName: '个人用户',
    description: '多轮问询澄清需求，渐进式分析，享受专业分析师级服务',
    defaultModules: ['chat', 'market', 'rag', 'datasource'],
    color: 'blue'
  },
  'personal_wealthy': {
    id: 'personal_wealthy',
    name: '高净值用户',
    group: 'personal',
    groupName: '个人用户',
    description: '深度资产配置建议，个性化投资组合分析',
    defaultModules: ['chat', 'market', 'rag', 'datasource'],
    color: 'purple'
  },
  'personal_professional': {
    id: 'personal_professional',
    name: '专业投资者',
    group: 'personal',
    groupName: '个人用户',
    description: '热点整合、产业链深度分析、一键汇总领域报告',
    defaultModules: ['chat', 'market', 'rag', 'datasource'],
    color: 'indigo'
  },
}

export function getEnabledModules() {
  const saved = localStorage.getItem('user_modules')
  if (saved) {
    try { return JSON.parse(saved) } catch { return null }
  }
  return null
}

export function saveEnabledModules(moduleIds) {
  localStorage.setItem('user_modules', JSON.stringify(moduleIds))
}

export function getEnabledFeatures() {
  const saved = localStorage.getItem('user_features')
  if (saved) {
    try { return JSON.parse(saved) } catch { return null }
  }
  return null
}

export function saveEnabledFeatures(featureIds) {
  localStorage.setItem('user_features', JSON.stringify(featureIds))
}

export function getDefaultFeaturesForRole(roleId) {
  const featureIds = []
  for (const mod of ALL_MODULES) {
    for (const f of mod.features) {
      featureIds.push(f.id)
    }
  }
  return featureIds
}

export function getUserRole() {
  return localStorage.getItem('user_role') || null
}

export function saveUserRole(roleId) {
  localStorage.setItem('user_role', roleId)
}

export function getActiveModuleDefinitions() {
  const enabledIds = getEnabledModules()
  if (!enabledIds) return ALL_MODULES.slice(0, 5)
  return enabledIds
    .map(id => ALL_MODULES.find(m => m.id === id))
    .filter(Boolean)
}
