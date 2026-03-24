"""
测试PDF路径格式
验证后端返回的PDF路径是否正确
"""

import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from simple_report_service import SimplifiedReportService

load_dotenv()


async def test_pdf_path():
    """测试PDF路径格式"""
    
    print("="*60)
    print("PDF路径格式测试")
    print("="*60)
    
    report_service = SimplifiedReportService()
    
    try:
        # 测试查询
        test_query = "对比宁德时代和比亚迪"
        
        print(f"\n测试查询: {test_query}")
        print("-" * 60)
        
        result = await report_service.process_user_query(test_query)
        
        print(f"\n需要财报: {result.get('need_financial_report', False)}")
        
        if result.get('need_financial_report', False):
            downloads = result.get('financial_reports', [])
            
            print(f"\n下载结果: {len(downloads)} 个")
            print("-" * 60)
            
            for i, download in enumerate(downloads, 1):
                print(f"\n[{i}] {download['company']} ({download['stock_code']}) {download['year']}年")
                print(f"    状态: {download['status']}")
                
                if download['status'] == 'success':
                    pdf_path = download['pdf_path']
                    print(f"    PDF路径: {pdf_path}")
                    
                    # 验证路径格式
                    if pdf_path.startswith('financial_reports/'):
                        print(f"    ✅ 路径格式正确（相对路径）")
                        
                        # 构建完整URL
                        full_url = f"http://localhost:8000/{pdf_path}"
                        print(f"    完整URL: {full_url}")
                        
                        # 检查文件是否存在
                        file_path = Path(__file__).parent.parent / pdf_path
                        if file_path.exists():
                            file_size = file_path.stat().st_size / 1024 / 1024
                            print(f"    ✅ 文件存在 ({file_size:.2f} MB)")
                        else:
                            print(f"    ❌ 文件不存在: {file_path}")
                    else:
                        print(f"    ❌ 路径格式错误（应该是相对路径）")
                        print(f"    期望格式: financial_reports/文件名.pdf")
                else:
                    print(f"    错误: {download.get('error', '未知错误')}")
        else:
            print("\nAI判断不需要财报")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        await report_service.close()
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_pdf_path())
