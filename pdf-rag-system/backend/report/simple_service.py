"""
简化版财报服务 V2
LLM意图识别 + AI识别股票代码 + 巨潮资讯网爬虫下载
优化：移除股票代码加载，使用AI直接识别，大幅提升启动速度
"""

import asyncio
import httpx
import json
import os
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv
from report.intent_service import ReportIntentService
from agent.deepseek import DeepSeekService
from report.timing import ReportTimingService, ReportType

# 加载环境变量
load_dotenv()


class SimplifiedReportService:
    """简化版财报服务"""
    
    def __init__(self):
        # 从环境变量读取API key（与main.py保持一致）
        api_key = os.getenv('DEEPSEEK_API_KEY', '')
        if not api_key:
            print("警告: 未找到DEEPSEEK_API_KEY环境变量，LLM功能将使用降级方案")
        self.deepseek_service = DeepSeekService(api_key)
        self.intent_service = ReportIntentService(self.deepseek_service)
        self.download_dir = Path("./financial_reports")
        self.download_dir.mkdir(exist_ok=True)
        self.client = None
        
        print("[INIT] 财报服务初始化完成（股票代码由预处理层提供）")
    
    async def _ensure_client(self):
        """确保HTTP客户端已初始化"""
        if self.client is None:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-Requested-With': 'XMLHttpRequest'
            }
            self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=headers)
    
    async def download_report_from_cninfo(
        self, 
        stock_code: str, 
        company_name: str,
        year: int,
        quarter: Optional[str] = None
    ) -> Optional[str]:
        """
        从巨潮资讯网下载财报PDF（支持年报、季报、中报）
        
        Args:
            stock_code: 股票代码
            company_name: 公司名称
            year: 年份
            quarter: 季度（Q1/Q2/Q3/Q4/H1），None表示自动选择最佳报告
        
        Returns:
            PDF文件路径，失败返回None
        """
        await self._ensure_client()
        
        try:
            # 巨潮资讯网查询API
            query_url = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
            
            # 智能选择报告类型
            report_info = ReportTimingService.get_best_report_type(
                user_year=year,
                user_quarter=quarter
            )
            
            # 获取搜索日期范围和category
            start_date, end_date = ReportTimingService.get_search_date_range(report_info)
            category = ReportTimingService.CATEGORY_MAP[report_info['type']]
            
            data = {
                "pageNum": "1",
                "pageSize": "30",
                "column": "szse",
                "tabName": "fulltext",
                "plate": "",
                "stock": "",  # 不使用stock参数，改用searchkey
                "searchkey": f"{stock_code} {company_name}",  # 同时搜索股票代码和公司名
                "secid": "",
                "category": category,
                "trade": "",
                "seDate": f"{start_date}~{end_date}",
                "sortName": "",
                "sortType": "",
                "isHLtitle": "true"
            }
            
            print(f"[下载] 查询巨潮: searchkey={data['searchkey']}, category={category}, seDate={data['seDate']}")
            resp = await self.client.post(query_url, data=data)
            
            if resp.status_code != 200:
                print(f"[下载] 巨潮查询失败, HTTP {resp.status_code}")
                return None
            
            result = resp.json()
            announcements = result.get('announcements', [])
            print(f"[下载] 返回公告数: {len(announcements)}")
            
            if not announcements:
                print(f"[下载] 未找到任何公告")
                return None
            
            # 通过标题关键词精确匹配目标报告
            title_keywords = ReportTimingService.get_report_title_keywords(report_info)
            target_report = None
            
            for ann in announcements:
                sec_code = ann.get('secCode', '')
                title = ann.get('announcementTitle', '')
                if sec_code != stock_code:
                    continue
                # 跳过摘要版，优先完整报告
                if '摘要' in title:
                    continue
                for kw in title_keywords:
                    if kw in title:
                        target_report = ann
                        print(f"[下载] 精确匹配: {title}")
                        break
                if target_report:
                    break
            
            # 兜底：按股票代码匹配第一条
            if not target_report:
                for announcement in announcements:
                    sec_code = announcement.get('secCode', '')
                    if sec_code == stock_code:
                        target_report = announcement
                        print(f"[下载] 使用第一个代码匹配的公告: {announcement.get('announcementTitle', '')}")
                        break
            
            if not target_report:
                print(f"[下载] 未找到股票代码 {stock_code} 的{report_info['description']}")
                return None
            
            # 获取PDF下载链接
            adjunct_url = target_report.get('adjunctUrl', '')
            
            if not adjunct_url:
                print(f"[下载] 未找到PDF下载链接")
                return None
            
            pdf_url = f"http://static.cninfo.com.cn/{adjunct_url}"
            
            print(f"[下载] 开始下载PDF: {pdf_url}")
            
            # 下载PDF
            pdf_response = await self.client.get(pdf_url)
            
            if pdf_response.status_code != 200:
                print(f"[下载] PDF下载失败")
                return None
            
            # 保存文件（文件名包含报告类型）
            report_type_suffix = report_info['period'].replace('/', '_')
            filename = f"{stock_code}_{company_name}_{report_type_suffix}_report.pdf"
            filepath = self.download_dir / filename
            
            with open(filepath, 'wb') as f:
                f.write(pdf_response.content)
            
            file_size = len(pdf_response.content) / 1024 / 1024
            print(f"[下载] 成功! 文件: {filepath} ({file_size:.2f} MB)")
            
            # 返回相对路径（仅文件名），用于前端构建URL
            return f"financial_reports/{filename}"
            
        except Exception as e:
            print(f"[下载] 失败: {str(e)}")
            return None
    
    async def process_user_query(self, user_query: str) -> Dict:
        """
        处理用户查询的完整流程
        
        Args:
            user_query: 用户输入
        
        Returns:
            {
                "intent": {...},
                "downloads": [
                    {
                        "company": "比亚迪",
                        "stock_code": "002594",
                        "year": 2025,
                        "pdf_path": "...",
                        "status": "success" | "failed"
                    }
                ]
            }
        """
        
        print(f"\n{'='*60}")
        print(f"处理用户查询: {user_query}")
        print(f"{'='*60}")
        
        # 1. LLM意图识别
        print(f"\n[步骤1] LLM意图识别...")
        intent = await self.intent_service.parse_user_query(user_query)
        print(f"识别结果: {json.dumps(intent, ensure_ascii=False, indent=2)}")
        
        # 2. 下载财报
        print(f"\n[步骤2] 下载财报...")
        downloads = []
        
        for company_info in intent['companies']:
            company_name = company_info['name']
            year = company_info.get('year', 2025)
            quarter = company_info.get('quarter')  # 获取季度信息
            stock_code = company_info.get('stock_code', '')
            
            if not stock_code:
                downloads.append({
                    'company': company_name,
                    'stock_code': None,
                    'year': year,
                    'pdf_path': None,
                    'status': 'failed',
                    'error': '未提供股票代码'
                })
                continue
            
            # 下载PDF（支持季报、中报）
            pdf_path = await self.download_report_from_cninfo(
                stock_code, 
                company_name, 
                year,
                quarter
            )
            
            downloads.append({
                'company': company_name,
                'stock_code': stock_code,
                'year': year,
                'pdf_path': pdf_path,
                'status': 'success' if pdf_path else 'failed',
                'error': None if pdf_path else '下载失败'
            })
        
        result = {
            'intent': intent,
            'downloads': downloads,
            'success_count': sum(1 for d in downloads if d['status'] == 'success'),
            'total_count': len(downloads)
        }
        
        print(f"\n{'='*60}")
        print(f"完成! 成功下载 {result['success_count']}/{result['total_count']} 份财报")
        print(f"{'='*60}\n")
        
        return result
    
    async def close(self):
        """关闭服务"""
        if self.client:
            await self.client.aclose()


async def main():
    """测试"""
    service = SimplifiedReportService()
    
    # 测试查询
    result = await service.process_user_query("帮我分析比亚迪2022年的财报")
    
    print("\n最终结果:")
    for download in result['downloads']:
        if download['status'] == 'success':
            print(f"[OK] {download['company']} ({download['stock_code']}) {download['year']}年")
            print(f"   PDF: {download['pdf_path']}")
        else:
            print(f"[FAIL] {download['company']} - {download['error']}")
    
    await service.close()


if __name__ == "__main__":
    asyncio.run(main())
