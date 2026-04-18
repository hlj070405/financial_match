"""
验证自适应解析策略速度
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.service import convert_pdf_to_markdown

# 大文件：美的集团年报 295页
large_pdf = "financial_reports/000333_美的集团_2024_report.pdf"
# 小文件：平安银行季报 ~30页
small_pdf = "financial_reports/000001_平安银行_2025Q3_report.pdf"

for pdf in [large_pdf, small_pdf]:
    if not os.path.exists(pdf):
        print(f"跳过（不存在）: {pdf}")
        continue

    out_md = pdf.replace(".pdf", "_adaptive_test.md")
    # 清理旧文件
    if os.path.exists(out_md):
        os.remove(out_md)

    print(f"\n{'='*55}")
    print(f"文件: {os.path.basename(pdf)}")
    print(f"大小: {os.path.getsize(pdf)/1024:.1f} KB")

    t0 = time.time()
    result = convert_pdf_to_markdown(pdf, out_md)
    elapsed = time.time() - t0

    if result:
        with open(out_md, encoding="utf-8") as f:
            md = f.read()
        tables = md.count("|---|")
        h2 = md.count("\n## ")
        print(f"耗时: {elapsed:.2f}s")
        print(f"字符数: {len(md)}, H2标题: {h2}, 表格分隔线: {tables}")
        print(f"内容预览:\n{md[:300]}")
    else:
        print(f"❌ 转换失败")
