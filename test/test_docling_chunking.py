"""
测试 Docling Markdown 预处理后的 PDF 分块效果

使用方法:
    python test/test_docling_chunking.py --pdf-path pdf-rag-system/backend/financial_reports/000001_平安银行_2025Q3_report.pdf

功能:
    1. 检查是否存在同名的 .md 预处理文件
    2. 调用 ingest_pdf 流程进行入库
    3. 分析生成的 chunks，验证:
       - 章节标题是否正确提取 (section_title)
       - Markdown 表格结构是否保留
       - 分块是否符合预期
"""

import os
import sys
import json
import argparse
from pathlib import Path

# 添加 backend 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pdf-rag-system", "backend"))

from services.chunker import logical_chunk, parse_source_meta
from services.rag_service import ingest_pdf, chunk_documents


def analyze_chunks(chunks: list, max_preview: int = 3) -> None:
    """分析生成的 chunks 并打印统计信息"""
    print("\n" + "=" * 60)
    print("📊 Chunks 分析报告")
    print("=" * 60)
    
    total_chunks = len(chunks)
    print(f"\n总共生成 {total_chunks} 个 chunks")
    
    # 统计有章节标题的 chunks
    chunks_with_title = [c for c in chunks if c.get("metadata", {}).get("section_title")]
    print(f"其中 {len(chunks_with_title)} 个 chunks 有章节标题 ({len(chunks_with_title)/total_chunks*100:.1f}%)")
    
    # 统计表格 chunks
    table_chunks = [c for c in chunks if c.get("metadata", {}).get("is_table")]
    print(f"其中 {len(table_chunks)} 个 chunks 是表格 ({len(table_chunks)/total_chunks*100:.1f}%)")
    
    # 分析章节标题分布
    title_counts = {}
    for c in chunks:
        title = c.get("metadata", {}).get("section_title", "")
        if title:
            title_counts[title] = title_counts.get(title, 0) + 1
    
    print(f"\n📚 提取到的章节标题 (共 {len(title_counts)} 个唯一标题):")
    for title, count in sorted(title_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"   - {title[:50]}{'...' if len(title) > 50 else ''} ({count} chunks)")
    
    # 展示前几个 chunks 的预览
    print(f"\n📝 前 {max_preview} 个 chunks 预览:")
    for i, chunk in enumerate(chunks[:max_preview]):
        print(f"\n--- Chunk {i+1} ---")
        meta = chunk.get("metadata", {})
        print(f"Section: {meta.get('section_title', 'N/A')}")
        print(f"Is Table: {meta.get('is_table', False)}")
        print(f"Text Preview (前200字符):")
        text = chunk.get("text", "")[:200]
        print(f"   {text}{'...' if len(chunk.get('text', '')) > 200 else ''}")


async def test_ingest_with_markdown(pdf_path: str, user_id: int = 1) -> None:
    """测试 PDF 入库，验证 Markdown 预处理效果"""
    
    pdf_path = os.path.abspath(pdf_path)
    if not os.path.exists(pdf_path):
        print(f"❌ PDF 文件不存在: {pdf_path}")
        return
    
    print(f"📄 测试文件: {os.path.basename(pdf_path)}")
    print(f"📁 完整路径: {pdf_path}")
    
    # 检查预处理文件
    md_path = os.path.splitext(pdf_path)[0] + ".md"
    has_md = os.path.exists(md_path)
    
    print(f"\n🔍 预处理状态:")
    if has_md:
        md_size = os.path.getsize(md_path)
        print(f"   ✅ 发现 Markdown 预处理文件: {os.path.basename(md_path)}")
        print(f"   📏 文件大小: {md_size:,} bytes")
    else:
        print(f"   ⚠️ 未找到 Markdown 预处理文件，将使用原生 PDF 解析")
    
    # 解析元信息
    source_meta = parse_source_meta(os.path.basename(pdf_path))
    print(f"\n📋 文件元信息: {json.dumps(source_meta, ensure_ascii=False)}")
    
    # 执行入库
    print(f"\n🚀 开始入库流程...")
    result = await ingest_pdf(pdf_path, user_id=user_id)
    
    if result.get("status") == "error":
        print(f"❌ 入库失败: {result.get('message')}")
        return
    
    print(f"✅ 入库成功!")
    print(f"   - Chunks 数量: {result.get('chunks', 0)}")
    
    # 如果需要更详细的分析，可以手动测试分块逻辑
    if has_md:
        print(f"\n🔬 详细分块分析 (使用 Markdown 模式)...")
        with open(md_path, "r", encoding="utf-8") as f:
            md_content = f.read()
        
        pages = [{"text": md_content, "source": os.path.basename(pdf_path)}]
        chunks = chunk_documents(pages, source_meta=source_meta, is_markdown=True)
        
        analyze_chunks(chunks, max_preview=len(chunks))  # 展示所有 chunks
    else:
        print(f"\n⚠️ 无 Markdown 文件，跳过详细分析")


def main():
    parser = argparse.ArgumentParser(description="测试 Docling Markdown 预处理后的 PDF 分块效果")
    parser.add_argument("--pdf-path", type=str, 
                        default="pdf-rag-system/backend/financial_reports/000001_平安银行_2025Q3_report.pdf",
                        help="要测试的 PDF 文件路径")
    parser.add_argument("--user-id", type=int, default=1, help="用户 ID")
    
    args = parser.parse_args()
    
    import asyncio
    asyncio.run(test_ingest_with_markdown(args.pdf_path, args.user_id))


if __name__ == "__main__":
    main()
