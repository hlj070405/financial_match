"""测试宁德时代财报下载"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.simple_report_service import SimplifiedReportService

async def test_ningde():
    service = SimplifiedReportService()
    
    try:
        # 测试宁德时代2024年报
        result = await service.process_user_query("帮我分析宁德时代2024年的年报")
        
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
    asyncio.run(test_ningde())
