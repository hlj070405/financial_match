"""测试特定年份的财报下载"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.simple_report_service import SimplifiedReportService

async def test_specific():
    service = SimplifiedReportService()
    
    try:
        # 直接测试下载特定年份的报告
        pdf_path = await service.download_report_from_cninfo(
            '002594', 
            '比亚迪', 
            2023
        )
        
        if pdf_path:
            print(f'✅ 成功下载2023年报: {pdf_path}')
        else:
            print('❌ 下载2023年报失败')
            
    finally:
        await service.close()

if __name__ == "__main__":
    asyncio.run(test_specific())
