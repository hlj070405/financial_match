import {
  MessageSquare,
  GitMerge,
  BarChart3,
  Activity,
  CandlestickChart,
  FileText,
  TrendingUp,
  Database,
  Search
} from 'lucide-vue-next'

export const CATEGORIES = [
  { id: 'smart', label: '智能分析' },
  { id: 'finance', label: '金融分析' },
  { id: 'market', label: '行情数据' },
  { id: 'professional', label: '专业服务' },
  { id: 'enterprise', label: '企业数据' }
]

export const ALL_MODULES = [
  {
    id: 'chat',
    title: '智能咨询',
    icon: MessageSquare,
    category: 'smart',
    features: [
      { id: 'chat_clarify', name: '多轮需求澄清', desc: '通过多次问询逐步明确用户真实意图', roles: ['personal_general', 'personal_wealthy', 'enterprise_small', 'enterprise_large'], targetLabel: '大众用户 / 高净值用户 / 企业用户' },
      { id: 'chat_profile', name: '用户画像分析', desc: '智能分析用户投资偏好与风险承受能力', roles: ['personal_general', 'personal_wealthy', 'enterprise_large'], targetLabel: '大众用户 / 高净值用户 / 大型企业' },
      { id: 'chat_progressive', name: '渐进式引导分析', desc: '多源数据渐进式分析，让普通人也能获得专业级服务', roles: ['personal_general', 'personal_wealthy', 'enterprise_small', 'enterprise_large'], targetLabel: '大众用户 / 高净值用户 / 企业用户' },
      { id: 'chat_suggest', name: '研究建议推荐', desc: '基于分析结果推荐相关研究方向与报告', roles: ['personal_general', 'personal_wealthy', 'personal_professional', 'enterprise_small', 'enterprise_large'], targetLabel: '所有用户' },
      { id: 'chat_direct', name: '专业直达模式', desc: '跳过澄清流程，直接进入深度分析', roles: ['personal_professional'], targetLabel: '专业投资者' }
    ]
  },
  {
    id: 'logic',
    title: '推理可视化',
    icon: GitMerge,
    category: 'smart',
    features: [
      { id: 'logic_chain', name: '决策链路展示', desc: '可视化Agent推理过程与决策依据', roles: ['personal_general', 'personal_wealthy', 'personal_professional', 'enterprise_small', 'enterprise_large'], targetLabel: '所有用户' },
      { id: 'logic_detail', name: '推理步骤详细日志', desc: '完整记录每一步推理的输入输出与工具调用', roles: ['personal_professional', 'enterprise_large'], targetLabel: '专业投资者 / 大型企业' }
    ]
  },
  {
    id: 'data',
    title: '财务诊断',
    icon: BarChart3,
    category: 'finance',
    features: [
      { id: 'data_basic', name: '基础财报解读', desc: '核心财务指标提取与通俗解读', roles: ['personal_general', 'personal_wealthy', 'personal_professional', 'enterprise_small', 'enterprise_large'], targetLabel: '所有用户' },
      { id: 'data_benchmark', name: '多维对标分析', desc: '同行业横向对比，多维度量化评估', roles: ['personal_wealthy', 'personal_professional', 'enterprise_small', 'enterprise_large'], targetLabel: '高净值用户 / 专业投资者 / 企业用户' },
      { id: 'data_risk', name: '风险预警评分', desc: '基于财务数据的风险量化评分与预警', roles: ['personal_wealthy', 'personal_professional', 'enterprise_small', 'enterprise_large'], targetLabel: '高净值用户 / 专业投资者 / 企业用户' }
    ]
  },
  {
    id: 'sentiment',
    title: '舆情分析',
    icon: Activity,
    category: 'finance',
    features: [
      { id: 'sent_hotspot', name: '热点追踪', desc: '实时金融热点事件监测与推送', roles: ['personal_general', 'personal_wealthy', 'personal_professional', 'enterprise_small', 'enterprise_large'], targetLabel: '所有用户' },
      { id: 'sent_emotion', name: '情绪指数', desc: '市场情绪量化指标与趋势变化', roles: ['personal_wealthy', 'personal_professional', 'enterprise_large'], targetLabel: '高净值用户 / 专业投资者 / 大型企业' },
      { id: 'sent_graph', name: '事件关联图谱', desc: '事件间因果关系与传导路径可视化', roles: ['personal_professional', 'enterprise_large'], targetLabel: '专业投资者 / 大型企业' }
    ]
  },
  {
    id: 'market',
    title: '行情终端',
    icon: CandlestickChart,
    category: 'market',
    features: [
      { id: 'mkt_kline', name: 'K线与基础行情', desc: '实时行情、分时图、日K线', roles: ['personal_general', 'personal_wealthy', 'personal_professional', 'enterprise_small', 'enterprise_large'], targetLabel: '所有用户' },
      { id: 'mkt_indicator', name: '技术指标叠加', desc: 'MACD、RSI、布林带等技术指标', roles: ['personal_wealthy', 'personal_professional', 'enterprise_large'], targetLabel: '高净值用户 / 专业投资者 / 大型企业' },
      { id: 'mkt_flow', name: '资金流向', desc: '主力资金、北向资金等资金面分析', roles: ['personal_professional', 'enterprise_large'], targetLabel: '专业投资者 / 大型企业' }
    ]
  },
  {
    id: 'report',
    title: '一键研报',
    icon: FileText,
    category: 'professional',
    features: [
      { id: 'rpt_summary', name: '摘要报告', desc: '快速生成行业或个股分析摘要', roles: ['personal_wealthy', 'personal_professional', 'enterprise_small', 'enterprise_large'], targetLabel: '高净值用户 / 专业投资者 / 企业用户' },
      { id: 'rpt_deep', name: '深度行业报告', desc: '整合多源数据生成完整行业研究报告', roles: ['personal_professional', 'enterprise_large'], targetLabel: '专业投资者 / 大型企业' },
      { id: 'rpt_template', name: '自定义模板', desc: '企业定制化报告模板与格式', roles: ['enterprise_large'], targetLabel: '大型企业' }
    ]
  },
  {
    id: 'chain',
    title: '产业链分析',
    icon: TrendingUp,
    category: 'professional',
    features: [
      { id: 'chain_map', name: '上下游关系图', desc: '产业链上下游企业映射与关联展示', roles: ['personal_professional', 'enterprise_large'], targetLabel: '专业投资者 / 大型企业' },
      { id: 'chain_risk', name: '供应链风险评估', desc: '供应链中断风险识别与影响评估', roles: ['personal_professional', 'enterprise_large'], targetLabel: '专业投资者 / 大型企业' },
      { id: 'chain_compete', name: '竞争格局对比', desc: '行业竞争态势与市场份额分析', roles: ['personal_professional', 'enterprise_large'], targetLabel: '专业投资者 / 大型企业' }
    ]
  },
  {
    id: 'rag',
    title: '智能检索',
    icon: Search,
    category: 'enterprise',
    features: [
      { id: 'rag_search', name: '语义搜索', desc: '自然语言意图理解与语义级文档检索', roles: ['enterprise_small', 'enterprise_large'], targetLabel: '企业用户' },
      { id: 'rag_rank', name: '向量相似度排序', desc: '余弦相似度+ANN近似最近邻精准匹配', roles: ['enterprise_large'], targetLabel: '大型企业' },
      { id: 'rag_filter', name: '噪声过滤与剪枝', desc: '语义剪枝去除无关内容，提升检索精度', roles: ['enterprise_large'], targetLabel: '大型企业' }
    ]
  },
  {
    id: 'datasource',
    title: '数据源管理',
    icon: Database,
    category: 'enterprise',
    features: [
      { id: 'ds_upload', name: '单文件上传', desc: '支持PDF、Excel等单文件上传与解析', roles: ['enterprise_small', 'enterprise_large'], targetLabel: '企业用户' },
      { id: 'ds_batch', name: '批量导入', desc: '大批量文档一键导入与自动处理', roles: ['enterprise_large'], targetLabel: '大型企业' },
      { id: 'ds_multi', name: '多源异构接入', desc: '对接数据库、API、文件系统等多种数据源', roles: ['enterprise_large'], targetLabel: '大型企业' }
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
    defaultModules: ['chat', 'logic', 'data', 'sentiment', 'market'],
    color: 'blue'
  },
  'personal_wealthy': {
    id: 'personal_wealthy',
    name: '高净值用户',
    group: 'personal',
    groupName: '个人用户',
    description: '深度资产配置建议，个性化投资组合分析',
    defaultModules: ['chat', 'logic', 'data', 'sentiment', 'market', 'report'],
    color: 'purple'
  },
  'personal_professional': {
    id: 'personal_professional',
    name: '专业投资者',
    group: 'personal',
    groupName: '个人用户',
    description: '热点整合、产业链深度分析、一键汇总领域报告',
    defaultModules: ['chat', 'logic', 'data', 'sentiment', 'market', 'report', 'chain'],
    color: 'indigo'
  },
  'enterprise_small': {
    id: 'enterprise_small',
    name: '中小企业',
    group: 'enterprise',
    groupName: '企业用户',
    description: '轻量级金融数据分析，适合中小规模数据场景',
    defaultModules: ['chat', 'logic', 'data', 'sentiment', 'market', 'report', 'rag'],
    color: 'emerald'
  },
  'enterprise_large': {
    id: 'enterprise_large',
    name: '大型企业',
    group: 'enterprise',
    groupName: '企业用户',
    description: '多源异构大数据处理，语义检索全链路，企业级数据管理',
    defaultModules: ['chat', 'logic', 'data', 'sentiment', 'market', 'report', 'chain', 'rag', 'datasource'],
    color: 'orange'
  }
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
  if (!roleId || !ROLES[roleId]) return []
  const featureIds = []
  for (const mod of ALL_MODULES) {
    for (const f of mod.features) {
      if (f.roles.includes(roleId)) {
        featureIds.push(f.id)
      }
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
