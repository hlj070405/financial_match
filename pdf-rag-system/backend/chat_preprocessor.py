"""
聊天预处理层
在发给Dify之前统一处理：
1. 生成对话标题
2. 判断是否需要调用财报微服务
3. 如果需要，调用微服务获取PDF
"""

import json
from typing import Dict, List, Optional
from deepseek_service import DeepSeekService
from simple_report_service import SimplifiedReportService


class ChatPreprocessor:
    """聊天预处理器"""
    
    def __init__(self, deepseek_service: DeepSeekService):
        self.deepseek_service = deepseek_service
        self.report_service = None  # 延迟初始化
    
    async def preprocess(self, user_message: str, is_first_message: bool = False) -> Dict:
        """
        预处理用户消息
        
        Args:
            user_message: 用户消息
            is_first_message: 是否是首条消息
        
        Returns:
            {
                "title": "对话标题" (仅首条消息),
                "need_financial_report": True/False,
                "financial_reports": [...] (如果需要),
                "processed_message": "处理后的消息"
            }
        """
        result = {
            "title": None,
            "need_financial_report": False,
            "financial_reports": [],
            "processed_message": user_message
        }
        
        # 构建统一的判断提示词
        prompt = self._build_preprocessing_prompt(user_message, is_first_message)
        
        try:
            # 调用LLM进行统一判断
            response = await self.deepseek_service.chat(prompt, temperature=0.3, max_tokens=500)
            
            # 清理可能的markdown代码块标记
            response = response.strip()
            if response.startswith('```'):
                # 移除 ```json 或 ``` 开头
                lines = response.split('\n')
                if lines[0].startswith('```'):
                    lines = lines[1:]
                if lines[-1].strip() == '```':
                    lines = lines[:-1]
                response = '\n'.join(lines)
            
            # 解析LLM返回的JSON
            analysis = json.loads(response)
            
            # 提取标题（仅首条消息）
            if is_first_message and "title" in analysis:
                result["title"] = analysis["title"]
            
            # 判断是否需要财报
            if analysis.get("need_financial_report", False):
                result["need_financial_report"] = True
                
                # 调用财报微服务
                if self.report_service is None:
                    self.report_service = SimplifiedReportService()
                
                # 提取公司和年份信息
                companies = analysis.get("companies", [])
                if companies:
                    report_result = await self.report_service.process_user_query(user_message)
                    result["financial_reports"] = report_result.get("downloads", [])
        
        except json.JSONDecodeError as e:
            print(f"[预处理] JSON解析失败: {e}")
            print(f"[预处理] LLM响应: {response}")
        except Exception as e:
            print(f"[预处理] 处理失败: {e}")
        
        return result
    
    def _build_preprocessing_prompt(self, user_message: str, is_first_message: bool) -> str:
        """构建预处理提示词 - 一次性提取所有信息"""
        
        base_prompt = f"""分析用户消息，提取财报相关信息，返回JSON格式（不要有任何其他文字）：

用户消息: {user_message}

请返回：
{{
    {('"title": "简洁的对话标题（不超过15字）",' if is_first_message else '')}
    "need_financial_report": true/false,
    "companies": [
        {{"name": "公司名称", "stock_code": "股票代码", "year": 年份}}
    ]
}}

判断规则：
1. **积极获取财报**：只要提到具体公司名称（无论是否明确提到财报），都设置need_financial_report为true
   - 例如："分析比亚迪" → true（即使没说财报）
   - 例如："比亚迪怎么样" → true
   - 例如："对比宁德时代和比亚迪" → true
   - 只有纯闲聊、打招呼、通用问题才设为false
2. 股票代码必须准确：
   - 比亚迪→002594, 宁德时代→300750, 贵州茅台→600519
   - 腾讯→00700, 阿里巴巴→09988, 小米→01810
   - 特斯拉→TSLA, 苹果→AAPL, 微软→MSFT
   - 不确定返回空字符串
3. 年份默认2025，用户明确说明则使用指定年份
{('4. 标题要体现核心意图，简洁准确' if is_first_message else '')}

只返回JSON，不要有任何解释。"""
        
        return base_prompt
    
    async def close(self):
        """关闭资源"""
        if self.report_service:
            await self.report_service.close()
