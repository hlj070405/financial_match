"""测试季报、中报功能"""
import asyncio
from services.simple_report_service import SimplifiedReportService

async def test():
    service = SimplifiedReportService()
    
    test_cases = [
        ("平安银行2024年年报", "应该下载2024年年报"),
        ("平安银行", "应该自动选择最新可用报告（2024年报）"),
        ("平安银行2025年一季报", "应该下载2025年一季报"),
        ("比亚迪2024年中报", "应该下载2024年中报"),
    ]
    
    for query, expected in test_cases:
        print("\n" + "="*60)
        print(f"测试: {query}")
        print(f"预期: {expected}")
        print("="*60)
        
        try:
            result = await service.process_user_query(query)
            
            for download in result['downloads']:
                print(f"\n公司: {download['company']}")
                print(f"股票代码: {download['stock_code']}")
                print(f"年份: {download['year']}")
                print(f"状态: {download['status']}")
                
                if download['status'] == 'success':
                    print(f"PDF路径: {download['pdf_path']}")
                    print("✅ 下载成功")
                else:
                    print(f"错误: {download.get('error', '未知错误')}")
                    print("❌ 下载失败")
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
    
    await service.close()

if __name__ == "__main__":
    asyncio.run(test())
