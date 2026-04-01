"""测试修复后的财报服务"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.simple_report_service import SimplifiedReportService

async def test():
    service = SimplifiedReportService()
    
    try:
        # 测试比亚迪2023年报
        result = await service.process_user_query("帮我分析比亚迪2023年的年报")
        
        print("\n=== 测试结果 ===")
        print(f"成功数量: {result['success_count']}/{result['total_count']}")
        
        for download in result['downloads']:
            if download['status'] == 'success':
                print(f"✅ {download['company']} ({download['stock_code']}) {download['year']}年")
                print(f"   PDF: {download['pdf_path']}")
            else:
                print(f"❌ {download['company']} - {download.get('error', '未知错误')}")
    
    finally:
        await service.close()

if __name__ == "__main__":
    asyncio.run(test())
