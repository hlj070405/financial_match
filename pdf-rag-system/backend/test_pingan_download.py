"""测试平安银行财报下载"""
import asyncio
from simple_report_service import SimplifiedReportService

async def test():
    service = SimplifiedReportService()
    
    # 测试平安银行
    print("\n测试：平安银行 2023年财报")
    result = await service.process_user_query("平安银行2023年财报")
    
    print("\n" + "="*60)
    print("下载结果:")
    print("="*60)
    
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
    
    await service.close()

if __name__ == "__main__":
    asyncio.run(test())
