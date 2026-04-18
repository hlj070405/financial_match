"""
展示完整的 chunks 切分结果到文件
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pdf-rag-system", "backend"))

from services.chunker import logical_chunk, parse_source_meta
from services.rag_service import chunk_documents

def show_complete_chunks():
    pdf_path = r"c:\Users\Administrator\Desktop\大数据 主题赛\pdf-rag-system\backend\financial_reports\000001_平安银行_2025Q3_report.pdf"
    md_path = os.path.splitext(pdf_path)[0] + ".md"
    
    if not os.path.exists(md_path):
        print(f"MD 文件不存在: {md_path}")
        return
    
    # 读取 MD 文件
    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()
    
    source_meta = parse_source_meta(os.path.basename(pdf_path))
    pages = [{"text": md_content, "source": os.path.basename(pdf_path)}]
    chunks = chunk_documents(pages, source_meta=source_meta, is_markdown=True)
    
    # 输出到文件
    output_path = r"c:\Users\Administrator\Desktop\大数据 主题赛\test\complete_chunks_output.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("完整 Chunks 切分结果\n")
        f.write(f"文档: {os.path.basename(pdf_path)}\n")
        f.write(f"总 chunks 数: {len(chunks)}\n")
        f.write("=" * 80 + "\n\n")
        
        for i, chunk in enumerate(chunks, 1):
            meta = chunk.get("metadata", {})
            f.write(f"{'=' * 80}\n")
            f.write(f"Chunk {i}/{len(chunks)}\n")
            f.write(f"{'=' * 80}\n")
            f.write(f"章节标题 (section_title): {meta.get('section_title', 'N/A')}\n")
            f.write(f"是否表格 (is_table): {meta.get('is_table', False)}\n")
            f.write(f"来源 (source): {meta.get('source', 'N/A')}\n")
            f.write(f"页码 (page_number): {meta.get('page_number', 'N/A')}\n")
            f.write(f"块索引 (chunk_index): {meta.get('chunk_index', 'N/A')}\n")
            f.write(f"股票代码: {meta.get('stock_code', 'N/A')}\n")
            f.write(f"公司: {meta.get('company', 'N/A')}\n")
            f.write(f"年份: {meta.get('year', 'N/A')}\n")
            f.write(f"季度: {meta.get('quarter', 'N/A')}\n")
            f.write(f"{'-' * 80}\n")
            f.write("【完整文本内容】:\n")
            f.write(f"{'-' * 80}\n")
            f.write(chunk.get("text", ""))
            f.write(f"\n\n")
    
    print(f"✅ 完整 chunks 已保存到: {output_path}")
    print(f"共 {len(chunks)} 个 chunks，每个 chunk 的完整内容都包含在内")

if __name__ == "__main__":
    show_complete_chunks()
