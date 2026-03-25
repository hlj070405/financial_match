"""幻诊·全景运营评估 - Mock接口 & 未来Dify集成入口"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/diagnosis", tags=["diagnosis"])


MOCK_DIAGNOSIS = {
    "company": "比亚迪",
    "period": "2024年年报",
    "summary": "比亚迪2024年营收突破7500亿元，同比增长33.3%，净利润突破400亿。新能源汽车销量全球第一，但毛利率受价格战影响略有承压。应收账款周转天数偏高值得关注。",
    "components": [
        {
            "type": "metric_cards",
            "title": "核心财务指标",
            "items": [
                {"label": "总营收 (TTM)", "value": "¥7,503亿", "change": "+33.3%", "trend": "up"},
                {"label": "净利润 (TTM)", "value": "¥402.5亿", "change": "+34.0%", "trend": "up"},
                {"label": "净资产收益率 (ROE)", "value": "22.5%", "change": "+1.8%", "trend": "up"},
                {"label": "资产负债率", "value": "77.4%", "change": "+0.3%", "trend": "up"}
            ]
        },
        {
            "type": "text_insight",
            "title": "AI 核心发现",
            "content": "**关键发现：**\n\n1. 营收与利润双双高增长，新能源汽车业务是核心驱动力\n2. 资产负债率77.4%处于行业偏高水平，但考虑到重资产行业特性属于合理范围\n3. **应收账款周转天数95天，显著高于行业均值62天，需关注回款风险**\n4. 经营性现金流/净利润比值为0.65，低于1.0的健康标准，利润质量有待验证\n5. 研发投入同比增长45%，技术壁垒持续加固"
        },
        {
            "type": "line_chart",
            "title": "营收与利润趋势 (近5年)",
            "x_axis": ["2020", "2021", "2022", "2023", "2024"],
            "series": [
                {"name": "营收(亿)", "data": [1566, 2161, 4241, 6023, 7503]},
                {"name": "净利润(亿)", "data": [42.3, 30.5, 166.2, 300.4, 402.5]}
            ]
        },
        {
            "type": "pie_chart",
            "title": "收入结构分析 (AI认为结构变化是重要信号)",
            "data": [
                {"name": "新能源汽车", "value": 5050},
                {"name": "电池及储能", "value": 1200},
                {"name": "手机部件及组装", "value": 980},
                {"name": "城市轨道交通", "value": 173},
                {"name": "其他", "value": 100}
            ]
        },
        {
            "type": "table",
            "title": "AI发现的异常指标",
            "columns": ["指标", "当前值", "行业均值", "偏离度", "风险等级"],
            "rows": [
                ["应收账款周转天数", "95天", "62天", "+53.2%", "⚠️ 警告"],
                ["经营现金流/净利润", "0.65", "1.20", "-45.8%", "🔴 危险"],
                ["资产负债率", "77.4%", "65.0%", "+19.1%", "⚠️ 警告"],
                ["研发费用率", "6.8%", "4.2%", "+61.9%", "🟢 良好"],
                ["存货周转天数", "58天", "72天", "-19.4%", "🟢 优秀"]
            ]
        },
        {
            "type": "bar_chart",
            "title": "核心指标行业对标",
            "x_axis": ["ROE(%)", "毛利率(%)", "净利率(%)", "营收增速(%)"],
            "series": [
                {"name": "比亚迪", "data": [22.5, 20.2, 5.4, 33.3]},
                {"name": "特斯拉", "data": [20.1, 17.9, 13.1, 2.1]},
                {"name": "宁德时代", "data": [16.8, 22.4, 12.6, 22.0]}
            ]
        },
        {
            "type": "radar_chart",
            "title": "五维综合评分",
            "indicators": ["盈利能力", "偿债能力", "运营效率", "成长能力", "市场地位"],
            "series": [
                {"name": "比亚迪", "data": [78, 55, 72, 92, 95]},
                {"name": "行业平均", "data": [65, 70, 68, 60, 50]}
            ]
        },
        {
            "type": "comparison",
            "title": "关键指标 vs 行业",
            "company": "比亚迪",
            "benchmark": "新能源行业均值",
            "items": [
                {"label": "毛利率", "company_value": "20.2%", "industry_value": "18.5%", "deviation": "+1.7%"},
                {"label": "净利率", "company_value": "5.4%", "industry_value": "8.2%", "deviation": "-2.8%"},
                {"label": "ROE", "company_value": "22.5%", "industry_value": "14.3%", "deviation": "+8.2%"},
                {"label": "营收增速", "company_value": "33.3%", "industry_value": "18.7%", "deviation": "+14.6%"},
                {"label": "研发费用率", "company_value": "6.8%", "industry_value": "4.2%", "deviation": "+2.6%"}
            ]
        },
        {
            "type": "text_insight",
            "title": "AI 投资建议",
            "content": "**综合评级：谨慎乐观**\n\n比亚迪在新能源汽车领域的市场地位和成长能力均处于行业领先水平，但需关注以下风险：\n\n- **短期风险**：应收账款周转恶化，经营现金流质量偏低\n- **中期风险**：价格战持续压缩毛利率空间\n- **长期看好**：研发高投入构建技术护城河，全球化布局打开增长天花板\n\n> 建议关注Q2应收账款回款情况及海外市场进展"
        }
    ]
}


@router.get("/mock")
async def get_mock_diagnosis():
    """返回Mock诊断数据，用于前端开发测试"""
    return MOCK_DIAGNOSIS


@router.post("/analyze")
async def analyze_company(payload: dict):
    """未来接入Dify Workflow的接口（当前返回mock数据）"""
    # TODO: 接入Dify workflow，传入公司名/财报PDF，获取AI分析结果
    return MOCK_DIAGNOSIS
