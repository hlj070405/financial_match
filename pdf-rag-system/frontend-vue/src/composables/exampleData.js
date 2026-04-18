/**
 * 示例数据 - 用于页面初始展示
 * 用户进入页面即可看到完整示例，也可以输入自己的查询调用真实 API
 */

// ==================== 财务诊断示例 (贵州茅台) ====================
export const EXAMPLE_DIAGNOSIS = {
  company: '贵州茅台',
  period: '2023年度',
  summary: '贵州茅台2023年实现营业总收入1,505.6亿元，同比增长18.04%，归母净利润747.3亿元，同比增长19.16%。公司毛利率维持在91.5%的超高水平，净利率达49.6%，ROE为33.6%。茅台凭借品牌壁垒和稀缺性，在高端白酒市场保持绝对龙头地位，现金流充沛、负债率极低，财务健康度极高。但需关注消费降级趋势和库存周期对高端白酒需求的潜在影响。',
  components: [
    {
      type: 'metric_cards',
      title: '核心财务指标',
      items: [
        { label: '营业总收入', value: '1,505.6亿', change: '+18.04%', trend: 'up' },
        { label: '归母净利润', value: '747.3亿', change: '+19.16%', trend: 'up' },
        { label: '毛利率', value: '91.5%', change: '+0.3pp', trend: 'up' },
        { label: 'ROE', value: '33.6%', change: '+1.2pp', trend: 'up' },
        { label: '资产负债率', value: '20.6%', change: '-0.8pp', trend: 'down' },
        { label: '每股收益', value: '59.49元', change: '+19.2%', trend: 'up' }
      ]
    },
    {
      type: 'text_insight',
      title: 'AI 核心发现',
      content: '**盈利能力卓越**：茅台毛利率91.5%在A股排名前列，品牌溢价能力极强。\n\n**成长性稳健**：营收连续5年双位数增长，直销渠道占比提升至40%，i茅台平台贡献显著增量。\n\n**⚠️ 风险提示**：批价波动风险、宏观消费降级压力、经销商库存周期需持续观察。'
    },
    {
      type: 'line_chart',
      title: '营收与利润趋势 (近5年)',
      x_axis: ['2019', '2020', '2021', '2022', '2023'],
      series: [
        { name: '营业收入(亿)', data: [888.5, 979.9, 1094.6, 1275.5, 1505.6] },
        { name: '净利润(亿)', data: [412.1, 467.0, 524.6, 627.2, 747.3] }
      ]
    },
    {
      type: 'pie_chart',
      title: '收入结构分析',
      data: [
        { name: '茅台酒', value: 85.2 },
        { name: '系列酒', value: 11.5 },
        { name: '其他业务', value: 3.3 }
      ]
    },
    {
      type: 'table',
      title: '关键财务指标明细',
      columns: ['指标', '2023年', '2022年', '变动'],
      rows: [
        ['营业收入', '1,505.6亿', '1,275.5亿', '+18.04%'],
        ['净利润', '747.3亿', '627.2亿', '+19.16%'],
        ['毛利率', '91.5%', '91.2%', '+0.3pp'],
        ['净利率', '49.6%', '49.2%', '+0.4pp'],
        ['经营现金流', '812.4亿', '698.5亿', '+16.3%']
      ]
    },
    {
      type: 'bar_chart',
      title: '行业对标分析',
      x_axis: ['毛利率(%)', '净利率(%)', 'ROE(%)', '营收增速(%)'],
      series: [
        { name: '贵州茅台', data: [91.5, 49.6, 33.6, 18.0] },
        { name: '五粮液', data: [75.8, 36.2, 25.1, 12.6] },
        { name: '泸州老窖', data: [87.3, 40.1, 30.2, 20.3] }
      ]
    },
    {
      type: 'radar_chart',
      title: '五维综合评分',
      indicators: ['盈利能力', '成长能力', '估值合理', '运营效率', '财务安全'],
      series: [
        { name: '贵州茅台', data: [98, 78, 55, 90, 95] }
      ]
    },
    {
      type: 'text_insight',
      title: 'AI 投资建议',
      content: '**综合评级：强烈推荐（长期持有）**\n\n茅台是A股最具确定性的核心资产之一，品牌护城河极深。当前估值处于历史中位偏下区间，建议长期投资者在回调时布局。短期需关注批价稳定性和宏观消费信心恢复节奏。'
    }
  ]
}

// ==================== 对标分析示例 (比亚迪 vs 长城汽车) ====================
export const EXAMPLE_BENCHMARK = {
  companyA: '比亚迪',
  companyB: '长城汽车',
  summary: '比亚迪在新能源转型方面领先行业，2023年营收突破6,023亿元，新能源汽车销量302万辆，全球第一。长城汽车营收1,732亿元，利润率较高但增速放缓。比亚迪在规模、技术和产业链一体化方面优势明显，长城在越野SUV和海外市场具有差异化竞争力。成长型投资者适合比亚迪，价值型投资者可关注长城汽车的估值修复机会。',
  metrics: [
    { name: '营业收入', valueA: '6,023亿', valueB: '1,732亿', winner: 'A' },
    { name: '净利润', valueA: '300.4亿', valueB: '70.2亿', winner: 'A' },
    { name: '毛利率', valueA: '20.2%', valueB: '19.9%', winner: 'A' },
    { name: '净利率', valueA: '5.0%', valueB: '4.1%', winner: 'A' },
    { name: 'ROE', valueA: '20.1%', valueB: '8.6%', winner: 'A' },
    { name: '营收增速', valueA: '+42.0%', valueB: '+26.1%', winner: 'A' },
    { name: '资产负债率', valueA: '77.4%', valueB: '66.3%', winner: 'B' },
    { name: 'P/E估值', valueA: '25.6x', valueB: '15.2x', winner: 'B' },
    { name: '研发投入', valueA: '395.7亿(6.6%)', valueB: '87.3亿(5.0%)', winner: 'A' },
    { name: '海外收入占比', valueA: '8.2%', valueB: '31.5%', winner: 'B' }
  ],
  radarLabels: ['盈利能力', '成长能力', '估值水平', '运营效率', '财务健康', '市场地位'],
  radarA: [72, 92, 55, 78, 58, 95],
  radarB: [65, 68, 75, 70, 72, 60],
  trend: {
    years: ['2020', '2021', '2022', '2023', '2024E'],
    seriesA: [1566, 2161, 4241, 6023, 7800],
    seriesB: [1033, 1364, 1373, 1732, 2050]
  }
}

// ==================== 风险评估示例 (恒大地产) ====================
export const EXAMPLE_RISK = {
  company: '恒大地产',
  overallScore: 89,
  riskLevel: '高风险',
  categories: [
    { name: '财务造假风险', score: 92, detail: '审计报告存在保留意见，2021年境外债务违约，财务数据真实性存疑' },
    { name: '偿债能力风险', score: 95, detail: '总负债超2.4万亿，资不抵债，无法偿还到期债务，已申请破产保护' },
    { name: '经营持续风险', score: 88, detail: '项目大面积停工，销售额断崖式下跌，保交楼压力巨大' },
    { name: '治理结构风险', score: 85, detail: '实控人被采取强制措施，管理层频繁变动，公司治理失效' },
    { name: '市场情绪风险', score: 90, detail: '股票长期停牌后复牌暴跌，投资者信心崩溃，品牌价值归零' },
    { name: '法律合规风险', score: 82, detail: '面临多起诉讼和监管调查，涉嫌财务欺诈，处罚风险极高' }
  ],
  factors: [
    { name: '债务违约', desc: '境内外债券全面违约，涉及金额超千亿', level: 'high' },
    { name: '资不抵债', desc: '总资产无法覆盖总负债，净资产为负', level: 'high' },
    { name: '项目停工', desc: '全国数百个项目停工，交付严重滞后', level: 'high' },
    { name: '监管处罚', desc: '涉嫌财务造假，面临证监会重罚', level: 'high' },
    { name: '管理层动荡', desc: '高管频繁离职，决策机制失灵', level: 'medium' },
    { name: '行业下行', desc: '房地产行业整体低迷，政策收紧', level: 'medium' }
  ],
  aiSummary: '恒大地产是典型的系统性风险案例。公司因过度举债扩张导致资金链断裂，总负债超2.4万亿元，已无法正常经营。债务违约、项目停工、管理层失控等多重风险叠加，投资价值已完全丧失。该案例充分说明高杠杆房企在行业下行周期中的脆弱性。强烈建议投资者规避所有关联标的，关注保交楼进展和债务重组方案。'
}

// ==================== 产业链图谱示例 (新能源汽车) ====================
export const EXAMPLE_CHAIN_MAP = {
  industry: '新能源汽车',
  levels: [
    { name: '上游原材料', count: 12, desc: '锂矿、钴矿、镍矿、正负极材料、电解液、隔膜等', color: '#0ea5e9' },
    { name: '中游零部件', count: 18, desc: '电池、电机、电控、热管理、底盘、智能驾驶系统', color: '#14b8a6' },
    { name: '整车制造', count: 8, desc: '新能源整车设计、制造与品牌运营', color: '#10b981' },
    { name: '下游销售', count: 6, desc: '经销商网络、直营门店、线上平台', color: '#8b5cf6' },
    { name: '后市场服务', count: 5, desc: '充电桩、换电站、维修保养、电池回收', color: '#f59e0b' }
  ],
  coreCompanies: [
    { name: '宁德时代', code: '300750.SZ', position: '龙头' },
    { name: '比亚迪', code: '002594.SZ', position: '龙头' },
    { name: '天齐锂业', code: '002466.SZ', position: '上游' },
    { name: '汇川技术', code: '300124.SZ', position: '中游' },
    { name: '特锐德', code: '300001.SZ', position: '下游' },
    { name: '格林美', code: '002340.SZ', position: '后市场' },
    { name: '华友钴业', code: '603799.SH', position: '上游' }
  ],
  sankeyNodes: [
    { name: '锂矿/钴矿', color: '#0ea5e9' },
    { name: '正极材料', color: '#0ea5e9' },
    { name: '负极材料', color: '#0ea5e9' },
    { name: '电解液', color: '#0ea5e9' },
    { name: '隔膜', color: '#0ea5e9' },
    { name: '动力电池', color: '#14b8a6' },
    { name: '驱动电机', color: '#14b8a6' },
    { name: '电控系统', color: '#14b8a6' },
    { name: '智能驾驶', color: '#14b8a6' },
    { name: '整车制造', color: '#10b981' },
    { name: '经销网络', color: '#8b5cf6' },
    { name: '充电设施', color: '#f59e0b' },
    { name: '电池回收', color: '#f59e0b' }
  ],
  sankeyLinks: [
    { source: '锂矿/钴矿', target: '正极材料', value: 30 },
    { source: '正极材料', target: '动力电池', value: 35 },
    { source: '负极材料', target: '动力电池', value: 20 },
    { source: '电解液', target: '动力电池', value: 15 },
    { source: '隔膜', target: '动力电池', value: 10 },
    { source: '动力电池', target: '整车制造', value: 45 },
    { source: '驱动电机', target: '整车制造', value: 15 },
    { source: '电控系统', target: '整车制造', value: 12 },
    { source: '智能驾驶', target: '整车制造', value: 18 },
    { source: '整车制造', target: '经销网络', value: 50 },
    { source: '整车制造', target: '充电设施', value: 20 },
    { source: '动力电池', target: '电池回收', value: 10 }
  ],
  valueDistribution: [
    { name: '动力电池', value: 40 },
    { name: '整车制造', value: 25 },
    { name: '智能驾驶', value: 15 },
    { name: '原材料', value: 12 },
    { name: '后市场', value: 8 }
  ]
}

// ==================== 竞争格局示例 (动力电池) ====================
export const EXAMPLE_COMPETE = {
  industry: '动力电池',
  companies: [
    { name: '宁德时代', share: 43.1, revenue: 4009, growth: 22.0, margin: 22.9, rnd: 6.5, strength: 5, color: '#6366f1' },
    { name: '比亚迪(弗迪)', share: 16.8, revenue: 980, growth: 48.5, margin: 20.2, rnd: 6.6, strength: 4, color: '#8b5cf6' },
    { name: 'LG新能源', share: 13.6, revenue: 2210, growth: 8.2, margin: 13.5, rnd: 7.8, strength: 4, color: '#06b6d4' },
    { name: '松下', share: 7.3, revenue: 1380, growth: -2.5, margin: 10.8, rnd: 5.2, strength: 3, color: '#10b981' },
    { name: '三星SDI', share: 5.4, revenue: 1050, growth: 12.3, margin: 12.1, rnd: 8.1, strength: 3, color: '#f59e0b' },
    { name: 'SK On', share: 4.8, revenue: 780, growth: 35.6, margin: -5.2, rnd: 9.2, strength: 3, color: '#ef4444' }
  ],
  porterForces: [
    { name: '供应商议价能力', level: '强', score: 75 },
    { name: '买方议价能力', level: '中', score: 55 },
    { name: '新进入者威胁', level: '弱', score: 25 },
    { name: '替代品威胁', level: '中', score: 50 },
    { name: '行业内竞争', level: '强', score: 82 }
  ],
  keyPoints: [
    '宁德时代以43%全球份额稳居龙头，技术代际领先（麒麟电池、神行超充）',
    '比亚迪刀片电池凭借安全性和成本优势快速抢占份额，垂直一体化模式显著',
    '固态电池技术路线是下一代竞争焦点，丰田、QuantumScape等新玩家虎视眈眈',
    '产能过剩风险加剧，2024年全球动力电池产能利用率降至55%左右',
    '上游锂价回落利好电池厂盈利修复，但长期材料供应安全仍是战略议题'
  ],
  trend: {
    years: ['2020', '2021', '2022', '2023', '2024E'],
    series: [
      { name: '宁德时代', data: [25.0, 32.6, 37.0, 43.1, 44.5], color: '#6366f1' },
      { name: '比亚迪', data: [6.7, 8.8, 13.6, 16.8, 18.2], color: '#8b5cf6' },
      { name: 'LG新能源', data: [23.5, 20.3, 14.4, 13.6, 12.8], color: '#06b6d4' },
      { name: '松下', data: [18.2, 12.2, 7.3, 7.3, 6.5], color: '#10b981' }
    ]
  },
  radarIndicators: [
    { name: '技术实力', max: 100 },
    { name: '成本控制', max: 100 },
    { name: '产能规模', max: 100 },
    { name: '客户覆盖', max: 100 },
    { name: '创新能力', max: 100 }
  ],
  radarData: [
    { name: '宁德时代', values: [95, 82, 95, 90, 88], color: '#6366f1' },
    { name: '比亚迪', values: [85, 92, 78, 65, 82], color: '#8b5cf6' },
    { name: 'LG新能源', values: [88, 68, 75, 85, 80], color: '#06b6d4' },
    { name: '松下', values: [82, 72, 60, 55, 70], color: '#10b981' }
  ]
}

// ==================== 供应链风险示例 (半导体) ====================
export const EXAMPLE_SUPPLY_RISK = {
  name: '半导体',
  overallCards: [
    { label: '综合风险指数', value: '72', sub: '高于行业均值18点', valueColor: 'text-rose-600', border: 'border-rose-200' },
    { label: '高风险环节', value: '4个', sub: '光刻/EDA/材料/设备', valueColor: 'text-amber-600', border: 'border-amber-200' },
    { label: '供应商集中度', value: '极高', sub: 'Top3占比超80%', valueColor: 'text-red-600', border: 'border-red-200' },
    { label: '替代可行性', value: '中等', sub: '国产化率约15-25%', valueColor: 'text-blue-600', border: 'border-blue-200' }
  ],
  geoRisks: [
    { region: '中国台湾', level: 85 },
    { region: '美国', level: 78 },
    { region: '日本', level: 62 },
    { region: '韩国', level: 55 },
    { region: '荷兰', level: 72 },
    { region: '中国大陆', level: 35 }
  ],
  risks: [
    { segment: '光刻机', level: '高', risk: 'ASML垄断EUV光刻机，出口管制严格限制先进制程获取', alternative: '上海微电子DUV突破中，EUV仍需5年+', impact: 5 },
    { segment: 'EDA工具', level: '高', risk: 'Cadence/Synopsys/Siemens三巨头垄断，制裁断供风险极高', alternative: '华大九天部分环节替代，全流程尚需时日', impact: 5 },
    { segment: '先进制程代工', level: '高', risk: '台积电占全球先进制程90%+，地缘政治风险突出', alternative: '中芯国际14nm量产，7nm需突破设备限制', impact: 5 },
    { segment: '半导体材料', level: '高', risk: '光刻胶、靶材等高端材料依赖日本进口', alternative: '南大光电等国产替代进行中，高端仍有差距', impact: 4 },
    { segment: '封装测试', level: '低', risk: '国内封测企业技术成熟，全球竞争力较强', alternative: '长电科技、通富微电等已具备先进封装能力', impact: 2 },
    { segment: 'IC设计', level: '中', risk: '架构授权(ARM)和IP核依赖海外，RISC-V是新方向', alternative: '海思/紫光展锐发力，RISC-V生态逐步完善', impact: 3 }
  ],
  heatmapSegments: ['光刻机', 'EDA工具', '先进代工', '半导体材料', '封装测试', 'IC设计'],
  heatmapDimensions: ['中断概率', '影响程度', '恢复时间'],
  heatmapData: [
    [0, 0, 90], [1, 0, 95], [2, 0, 85],
    [0, 1, 88], [1, 1, 92], [2, 1, 80],
    [0, 2, 82], [1, 2, 90], [2, 2, 75],
    [0, 3, 70], [1, 3, 78], [2, 3, 60],
    [0, 4, 20], [1, 4, 25], [2, 4, 15],
    [0, 5, 55], [1, 5, 65], [2, 5, 45]
  ],
  aiSummary: '半导体供应链是当前全球地缘政治博弈的核心战场。光刻机（ASML）、EDA工具（美国三巨头）和先进制程代工（台积电）构成三大"卡脖子"瓶颈，出口管制持续升级使中国大陆获取先进技术的渠道日益收窄。国产替代正在加速推进，封测环节已基本实现自主可控，但在光刻机和EDA领域仍存在5-10年的技术代差。建议企业制定双源供应策略，加大国产设备验证力度，同时关注RISC-V等开源架构带来的弯道超车机会。'
}
