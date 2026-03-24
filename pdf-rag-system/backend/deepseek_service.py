import httpx
import json
from typing import Optional

class DeepSeekService:
    """DeepSeek API服务 - 通过硅基流动调用"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.siliconflow.cn/v1"
        
    async def generate_chat_title(self, first_message: str, first_response: str = "") -> str:
        """
        根据对话的首条消息生成简洁的标题
        
        :param first_message: 用户的第一条消息
        :param first_response: AI的第一条回复(可选)
        :return: 生成的标题
        """
        try:
            prompt = f"""请为以下对话生成一个简洁的标题(不超过20个字)，直接输出标题，不要有任何额外说明或标点符号。

用户问题: {first_message}"""
            
            if first_response:
                prompt += f"\nAI回复: {first_response[:200]}..."
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "deepseek-ai/DeepSeek-V3",
                        "messages": [
                            {
                                "role": "system",
                                "content": "你是一个专业的标题生成助手。请根据对话内容生成简洁、准确的标题，不超过20个字。只输出标题本身，不要有任何其他内容。"
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.7,
                        "max_tokens": 50
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    title = result["choices"][0]["message"]["content"].strip()
                    # 清理可能的引号和标点
                    title = title.strip('"\'。，！？、')
                    # 限制长度
                    if len(title) > 20:
                        title = title[:20]
                    return title
                else:
                    print(f"DeepSeek API错误: {response.status_code} - {response.text}")
                    # 返回默认标题
                    return first_message[:20] if len(first_message) > 20 else first_message
                    
        except Exception as e:
            print(f"生成标题异常: {str(e)}")
            # 返回默认标题
            return first_message[:20] if len(first_message) > 20 else first_message
    
    async def chat(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """
        通用的聊天接口
        
        :param prompt: 用户提示词
        :param temperature: 温度参数
        :param max_tokens: 最大token数
        :return: AI回复内容
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "deepseek-ai/DeepSeek-V3",
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"].strip()
                else:
                    print(f"DeepSeek API错误: {response.status_code} - {response.text}")
                    raise Exception(f"API调用失败: {response.status_code}")
                    
        except Exception as e:
            print(f"聊天异常: {str(e)}")
            raise
