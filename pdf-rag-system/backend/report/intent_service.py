"""
基于LLM的财报意图识别服务
将用户的自然语言转换为标准格式：公司 + 年份
"""

import json
import re
from datetime import datetime
from typing import List, Dict, Optional
from agent.deepseek import DeepSeekService

class ReportIntentService:
    """财报意图识别服务"""
    
    def __init__(self, deepseek_service: DeepSeekService):
        self.deepseek_service = deepseek_service
    
    async def parse_user_query(self, user_query: str) -> Dict:
        """
        解析用户查询，提取公司和年份信息
        
        Args:
            user_query: 用户输入（如："帮我分析比亚迪2023年的财报"）
        
        Returns:
            {
                "companies": [
                    {"name": "比亚迪", "stock_code": "002594", "year": 2023}
                ],
                "intent_type": "single" | "multiple" | "industry",
                "analysis_requirements": "财务分析"
            }
        """
        
        prompt = f"""
你是一个财报查询意图识别专家。请分析用户的查询，提取关键信息。

用户查询：{user_query}

请识别：
1. 公司名称（可能是全称、简称、股票代码）
2. 股票代码（A股6位数字如600519，港股5位数字如00700）
3. 年份（如果没有明确说明，默认2025年）
4. 季度/报告类型（如果明确提到）：
   - Q1: 一季报
   - Q2/H1: 中报/半年报
   - Q3: 三季报
   - Q4/FY: 年报
   - 不提及则留空，系统会根据当前时间自动选择最新可用报告
5. 查询类型：
   - single: 单个公司
   - multiple: 多个公司对比
   - industry: 行业分析
6. 分析需求（如：财务分析、盈利能力、偿债能力等）

返回JSON格式（严格按照格式，不要有任何额外文字）：
{{
  "companies": [
    {{
      "name": "公司名称或简称",
      "stock_code": "股票代码",
      "year": 2025,
      "quarter": "Q1"
    }}
  ],
  "intent_type": "single",
  "analysis_requirements": "分析需求描述"
}}

注意：quarter字段可选，如果用户没有明确提到季度/报告类型，则不要包含此字段

示例1：
用户："分析比亚迪2023年财报"
返回：
{{
  "companies": [{{"name": "比亚迪", "stock_code": "002594", "year": 2023}}],
  "intent_type": "single",
  "analysis_requirements": "财务分析"
}}

示例2：
用户："对比比亚迪和宁德时代的盈利能力"
返回：
{{
  "companies": [
    {{"name": "比亚迪", "stock_code": "002594", "year": 2025}},
    {{"name": "宁德时代", "stock_code": "300750", "year": 2025}}
  ],
  "intent_type": "multiple",
  "analysis_requirements": "盈利能力对比"
}}

示例3：
用户："新能源汽车行业的财务状况"
返回：
{{
  "companies": [{{"name": "新能源汽车", "year": 2025}}],
  "intent_type": "industry",
  "analysis_requirements": "行业财务状况分析"
}}

现在请分析用户的查询并返回JSON：
"""
        
        try:
            # 调用DeepSeek
            response = await self.deepseek_service.chat(prompt)
            
            # 清理响应（去除可能的markdown代码块标记）
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.startswith('```'):
                response = response[3:]
            if response.endswith('```'):
                response = response[:-3]
            response = response.strip()
            
            # 解析JSON
            result = json.loads(response)
            
            # 验证结果格式
            if 'companies' not in result or not isinstance(result['companies'], list):
                raise ValueError("返回格式错误：缺少companies字段")
            
            if 'intent_type' not in result:
                result['intent_type'] = 'single'
            
            if 'analysis_requirements' not in result:
                result['analysis_requirements'] = '财务分析'
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            print(f"原始响应: {response}")
            
            # 降级方案：使用正则表达式提取
            return self._fallback_parse(user_query)
        
        except Exception as e:
            print(f"意图识别失败: {e}")
            return self._fallback_parse(user_query)
    
    def _fallback_parse(self, user_query: str) -> Dict:
        """降级方案：使用正则表达式提取"""
        
        # 提取年份
        year_match = re.search(r'(20\d{2})', user_query)
        year = int(year_match.group(1)) if year_match else 2025
        
        # 简单的公司名称提取（这里可以扩展）
        companies = []
        
        # 常见公司简称
        common_companies = {
            '比亚迪': '比亚迪',
            'byd': '比亚迪',
            '宁德时代': '宁德时代',
            'catl': '宁德时代',
            '特斯拉': '特斯拉',
            '小米': '小米',
        }
        
        for key, name in common_companies.items():
            if key in user_query.lower():
                companies.append({
                    'name': name,
                    'year': year
                })
        
        if not companies:
            # 如果没有识别到，使用用户原始查询
            companies.append({
                'name': user_query.split('的')[0].split('分析')[-1].strip(),
                'year': year
            })
        
        return {
            'companies': companies,
            'intent_type': 'multiple' if len(companies) > 1 else 'single',
            'analysis_requirements': '财务分析'
        }


# 使用示例
async def test_intent_service():
    from deepseek_service import DeepSeekService
    
    deepseek = DeepSeekService()
    service = ReportIntentService(deepseek)
    
    test_queries = [
        "帮我分析比亚迪2023年的财报",
        "对比比亚迪和宁德时代的盈利能力",
        "新能源汽车行业的财务状况",
        "byd去年的年报",
        "分析002594这只股票",
    ]
    
    for query in test_queries:
        print(f"\n查询: {query}")
        result = await service.parse_user_query(query)
        print(f"结果: {json.dumps(result, ensure_ascii=False, indent=2)}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_intent_service())
