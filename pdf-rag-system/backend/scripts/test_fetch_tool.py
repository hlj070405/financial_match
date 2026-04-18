"""
直接模拟 agent 调用 fetch_financial_report 工具的完整链路
排查 agent 无法获取财报的根因
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))


async def main():
    print("="*60)
    print("测试 fetch_financial_report 工具调用链路")
    print("美的集团 000333")
    print("="*60)

    # 1. 检查 SimplifiedReportService 能否实例化
    print("\n[步骤1] 初始化 SimplifiedReportService...")
    try:
        from report.simple_service import SimplifiedReportService
        svc = SimplifiedReportService()
        print("  ✅ 初始化成功")
    except Exception as e:
        print(f"  ❌ 初始化失败: {e}")
        import traceback; traceback.print_exc()
        return

    # 2. 直接调用下载
    print("\n[步骤2] 调用 download_report_from_cninfo...")
    try:
        pdf_path = await svc.download_report_from_cninfo(
            stock_code="000333",
            company_name="美的集团",
            year=2024,
            quarter=None
        )
        print(f"  返回值: {pdf_path}")
        if pdf_path:
            print(f"  ✅ 下载成功")
            full = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), pdf_path)
            exists = os.path.exists(full)
            print(f"  文件是否存在: {exists} ({full})")
        else:
            print(f"  ❌ 返回 None，下载失败")
    except Exception as e:
        print(f"  ❌ 异常: {e}")
        import traceback; traceback.print_exc()
    finally:
        await svc.close()

    # 3. 模拟 _execute_tool 调用（不走 DB/向量化，只验证参数路径）
    print("\n[步骤3] 模拟 _execute_tool('fetch_financial_report', ...) 参数解析...")
    tool_args = {
        "company_name": "美的集团",
        "stock_code": "000333",
        "year": 2024,
    }
    print(f"  输入参数: {tool_args}")

    company_name = tool_args.get("company_name", "")
    stock_code = tool_args.get("stock_code", "")
    quarter = tool_args.get("quarter")

    if "year" in tool_args and tool_args["year"]:
        year = tool_args["year"]
    else:
        from datetime import datetime
        now = datetime.now()
        year = now.year - 1 if now.month <= 4 else now.year

    print(f"  解析结果: company={company_name}, stock_code={stock_code}, year={year}, quarter={quarter}")

    if not stock_code:
        print("  ❌ 缺少 stock_code，工具会返回 error")
    else:
        print("  ✅ 参数合法，stock_code 存在")

    # 4. 检查 list_indexed_documents（向量库查重逻辑）
    print("\n[步骤4] 检查 list_indexed_documents 是否报错...")
    try:
        from rag.service import list_indexed_documents
        # user_id=1 模拟
        docs = list_indexed_documents(1)
        print(f"  ✅ 调用成功，已入库文档数: {len(docs)}")
        # 检查是否已有美的
        hits = [d for d in docs if "000333" in d.get("source", "") or "美的" in d.get("source", "")]
        if hits:
            print(f"  ⚠️  向量库已有美的相关文档（会跳过下载）: {[d['source'] for d in hits]}")
        else:
            print(f"  向量库中无美的文档，应该会触发下载")
    except Exception as e:
        print(f"  ❌ list_indexed_documents 失败: {e}")
        import traceback; traceback.print_exc()

    print("\n" + "="*60)
    print("诊断完成")


if __name__ == "__main__":
    asyncio.run(main())
