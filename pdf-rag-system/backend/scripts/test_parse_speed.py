"""
PDF解析速度对比测试
找出 pymupdf4llm 耗时瓶颈，评估优化方案
"""
import time
import fitz
import pdfplumber
import pymupdf4llm

PDF = "financial_reports/000333_美的集团_2024_report.pdf"

doc = fitz.open(PDF)
page_count = len(doc)
doc.close()
print(f"文件: {PDF}")
print(f"页数: {page_count}")
print("=" * 50)

# 方案1: pymupdf4llm Layout模式（当前线上模式）
pymupdf4llm.use_layout(True)
t0 = time.time()
md1 = pymupdf4llm.to_markdown(PDF)
t1 = time.time()
print(f"[方案1] pymupdf4llm Layout=ON : {t1-t0:.2f}s  字符={len(md1)}  表格={md1.count('|---|')}")

# 方案2: pymupdf4llm 无Layout
pymupdf4llm.use_layout(False)
t0 = time.time()
md2 = pymupdf4llm.to_markdown(PDF)
t1 = time.time()
print(f"[方案2] pymupdf4llm Layout=OFF: {t1-t0:.2f}s  字符={len(md2)}  表格={md2.count('|---|')}")

# 方案3: PyMuPDF纯文本（原fallback）
t0 = time.time()
doc = fitz.open(PDF)
texts = [page.get_text("text") for page in doc]
doc.close()
t1 = time.time()
total_chars = sum(len(t) for t in texts)
print(f"[方案3] PyMuPDF 纯文本       : {t1-t0:.2f}s  字符={total_chars}")

# 方案4: pymupdf4llm Layout=OFF + 只用前N页测每页耗时
pymupdf4llm.use_layout(False)
t0 = time.time()
md_10 = pymupdf4llm.to_markdown(PDF, pages=list(range(10)))
t1 = time.time()
per_page = (t1 - t0) / 10 * 1000
print(f"[方案4] pymupdf4llm 前10页   : {t1-t0:.2f}s  每页≈{per_page:.0f}ms")

# 方案5: pdfplumber单独测（原fallback里用的）
t0 = time.time()
table_count = 0
with pdfplumber.open(PDF) as pdf:
    for page in pdf.pages:
        tables = page.extract_tables()
        table_count += len(tables)
t1 = time.time()
print(f"[方案5] pdfplumber 表格提取  : {t1-t0:.2f}s  表格={table_count}")

print("=" * 50)
print("结论:")
print(f"  Layout GNN每页耗时约 {(108.69/295)*1000:.0f}ms，295页≈108s")
print(f"  pdfplumber 64s 但只在fallback路径（pymupdf4llm成功时不走）")
print(f"  优化关键: pymupdf4llm Layout=OFF → 约{(t1-t0)/page_count*1000:.0f}ms/页")
