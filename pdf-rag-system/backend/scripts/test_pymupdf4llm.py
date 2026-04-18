"""
测试 pymupdf4llm 替换 Docling 的转换效果
用小文件（季报）快速验证：速度、Markdown 结构质量、表格识别
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymupdf4llm

TEST_PDF = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "financial_reports",
    "000001_平安银行_2025Q3_report.pdf",
)


def test_convert_speed_and_quality():
    print(f"\n{'='*60}")
    print(f"测试文件: {os.path.basename(TEST_PDF)}")
    print(f"文件大小: {os.path.getsize(TEST_PDF) / 1024:.1f} KB")
    print(f"{'='*60}\n")

    # 1. 速度测试
    print("[1] 开始转换...")
    t0 = time.time()
    md_content = pymupdf4llm.to_markdown(TEST_PDF)
    elapsed = time.time() - t0
    print(f"    耗时: {elapsed:.2f}s")
    print(f"    输出字符数: {len(md_content)}")

    # 2. Markdown 结构质量
    lines = md_content.split("\n")
    h1 = [l for l in lines if l.startswith("# ")]
    h2 = [l for l in lines if l.startswith("## ")]
    h3 = [l for l in lines if l.startswith("### ")]
    tables = md_content.count("|---|")
    print(f"\n[2] Markdown 结构:")
    print(f"    H1 标题数: {len(h1)}")
    print(f"    H2 标题数: {len(h2)}")
    print(f"    H3 标题数: {len(h3)}")
    print(f"    表格数(含分隔线): {tables}")

    # 3. 输出前 800 字符预览
    print(f"\n[3] 内容预览（前800字符）:")
    print("-" * 40)
    print(md_content[:800])
    print("-" * 40)

    # 4. 找一段含表格的内容预览
    table_pos = md_content.find("|---|")
    if table_pos > 0:
        start = max(0, table_pos - 200)
        end = min(len(md_content), table_pos + 400)
        print(f"\n[4] 表格内容预览:")
        print("-" * 40)
        print(md_content[start:end])
        print("-" * 40)
    else:
        print("\n[4] 未检测到 Markdown 表格")

    # 5. 保存结果到临时文件供人工检查
    out_path = TEST_PDF.replace(".pdf", "_pymupdf4llm_test.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"\n[5] 完整结果已保存: {os.path.basename(out_path)}")

    # 6. 断言基本质量门槛
    assert len(md_content) > 1000, f"输出内容过少: {len(md_content)} 字符"
    assert elapsed < 60, f"转换超时: {elapsed:.1f}s（预期 <60s）"
    print(f"\n✅ 所有断言通过，pymupdf4llm 转换正常")


if __name__ == "__main__":
    test_convert_speed_and_quality()
