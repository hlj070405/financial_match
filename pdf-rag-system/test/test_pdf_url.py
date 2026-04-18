"""
测试PDF URL是否可访问
验证前端能否通过HTTP访问PDF文件
"""

import httpx
import asyncio
from pathlib import Path


async def test_pdf_url_access():
    """测试PDF URL访问"""
    
    print("="*60)
    print("PDF URL访问测试")
    print("="*60)
    
    # 检查是否有已下载的PDF文件
    reports_dir = Path(__file__).parent.parent / "financial_reports"
    
    if not reports_dir.exists():
        print(f"\n❌ 财报目录不存在: {reports_dir}")
        return
    
    pdf_files = list(reports_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"\n❌ 财报目录中没有PDF文件: {reports_dir}")
        print("请先运行: python tests/test_pdf_path.py 下载测试财报")
        return
    
    print(f"\n找到 {len(pdf_files)} 个PDF文件")
    print("-" * 60)
    
    async with httpx.AsyncClient() as client:
        for pdf_file in pdf_files[:2]:  # 只测试前2个
            filename = pdf_file.name
            relative_path = f"financial_reports/{filename}"
            url = f"http://localhost:8000/{relative_path}"
            
            print(f"\n测试文件: {filename}")
            print(f"相对路径: {relative_path}")
            print(f"完整URL: {url}")
            
            try:
                response = await client.get(url, timeout=10.0)
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    content_length = len(response.content)
                    
                    print(f"✅ 访问成功!")
                    print(f"   状态码: {response.status_code}")
                    print(f"   Content-Type: {content_type}")
                    print(f"   文件大小: {content_length / 1024 / 1024:.2f} MB")
                    
                    if 'pdf' in content_type.lower():
                        print(f"   ✅ Content-Type正确（PDF文件）")
                    else:
                        print(f"   ⚠️ Content-Type可能不正确")
                else:
                    print(f"❌ 访问失败")
                    print(f"   状态码: {response.status_code}")
                    print(f"   响应: {response.text[:200]}")
                    
            except httpx.ConnectError:
                print(f"❌ 无法连接到后端服务器")
                print(f"   请确保后端正在运行: uvicorn main:app --reload")
            except Exception as e:
                print(f"❌ 请求失败: {str(e)}")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)
    print("\n提示:")
    print("1. 如果访问失败，请确保后端正在运行")
    print("2. 如果Content-Type不正确，检查StaticFiles配置")
    print("3. 前端应该使用相同的URL格式访问PDF")


if __name__ == "__main__":
    asyncio.run(test_pdf_url_access())
