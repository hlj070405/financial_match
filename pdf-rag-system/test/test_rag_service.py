"""
测试 RAG 服务完整链路: PDF解析 → 分块 → Embedding → 向量化入库 → 检索 → 对话
"""

import os
import sys
import asyncio
import json

# 添加 backend 到 path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))


def test_pdf_parse():
    """测试 PDF 解析"""
    from services.rag_service import parse_pdf

    # 找一个已有的 PDF
    reports_dir = os.path.join(os.path.dirname(__file__), "..", "backend", "financial_reports")
    if not os.path.exists(reports_dir):
        print("[SKIP] 无 financial_reports 目录")
        return None

    pdfs = [f for f in os.listdir(reports_dir) if f.endswith(".pdf")]
    if not pdfs:
        print("[SKIP] 无 PDF 文件")
        return None

    pdf_path = os.path.join(reports_dir, pdfs[0])
    print(f"\n[测试 PDF 解析] 文件: {pdfs[0]}")
    pages = parse_pdf(pdf_path)
    print(f"  解析页数: {len(pages)}")
    if pages:
        print(f"  首页预览: {pages[0]['text'][:100]}...")
    return pdf_path


def test_chunk():
    """测试文本分块"""
    from services.rag_service import parse_pdf, chunk_documents

    reports_dir = os.path.join(os.path.dirname(__file__), "..", "backend", "financial_reports")
    pdfs = [f for f in os.listdir(reports_dir) if f.endswith(".pdf")] if os.path.exists(reports_dir) else []
    if not pdfs:
        print("[SKIP] 无 PDF 文件")
        return

    pdf_path = os.path.join(reports_dir, pdfs[0])
    pages = parse_pdf(pdf_path)
    chunks = chunk_documents(pages)
    print(f"\n[测试分块] 文件: {pdfs[0]}")
    print(f"  原始页数: {len(pages)}")
    print(f"  分块数量: {len(chunks)}")
    if chunks:
        print(f"  首块预览: {chunks[0]['text'][:100]}...")
        print(f"  首块 metadata: {chunks[0]['metadata']}")


async def test_embedding():
    """测试 Embedding API 调用"""
    from services.rag_service import _get_embeddings

    texts = ["比亚迪2024年营收突破7500亿元", "新能源汽车销量全球第一"]
    print(f"\n[测试 Embedding] 输入 {len(texts)} 段文本")
    try:
        embeddings = await _get_embeddings(texts)
        print(f"  返回 {len(embeddings)} 个向量")
        print(f"  向量维度: {len(embeddings[0])}")
        print(f"  首向量前5维: {embeddings[0][:5]}")
        return True
    except Exception as e:
        print(f"  ❌ Embedding 失败: {e}")
        return False


async def test_ingest(pdf_path: str = None):
    """测试 PDF 向量化入库"""
    from services.rag_service import ingest_pdf

    if not pdf_path:
        reports_dir = os.path.join(os.path.dirname(__file__), "..", "backend", "financial_reports")
        pdfs = [f for f in os.listdir(reports_dir) if f.endswith(".pdf")] if os.path.exists(reports_dir) else []
        if not pdfs:
            print("[SKIP] 无 PDF 文件")
            return
        pdf_path = os.path.join(reports_dir, pdfs[0])

    print(f"\n[测试向量化入库] 文件: {os.path.basename(pdf_path)}")
    result = await ingest_pdf(pdf_path, user_id=1, document_id=999)
    print(f"  结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
    return result


async def test_retrieve():
    """测试检索"""
    from services.rag_service import retrieve

    query = "营收情况如何"
    print(f"\n[测试检索] 查询: {query}")
    results = await retrieve(query, user_id=1, top_k=3)
    print(f"  返回 {len(results)} 个结果")
    for i, r in enumerate(results):
        print(f"  [{i+1}] score={r['score']:.4f} source={r['source']} page={r['page_number']}")
        print(f"      {r['text'][:80]}...")


async def test_rag_chat():
    """测试 RAG 对话（流式）"""
    from services.rag_service import rag_chat_stream

    query = "这家公司的营收和利润情况怎么样？"
    print(f"\n[测试 RAG 对话] 查询: {query}")
    print("  流式输出:")
    full_text = ""
    async for chunk in rag_chat_stream(query=query, user_id=1, top_k=5):
        if chunk.startswith("data: "):
            data_str = chunk[6:].strip()
            if data_str == "[DONE]":
                continue
            try:
                evt = json.loads(data_str)
                evt_type = evt.get("type", "")
                if evt_type == "text":
                    text = evt.get("text", "")
                    full_text += text
                    print(text, end="", flush=True)
                elif evt_type == "sources":
                    print(f"\n  [来源] {json.dumps(evt['sources'], ensure_ascii=False)}")
                elif evt_type == "phase":
                    print(f"\n  [阶段] {evt['content']}")
                elif evt_type == "finish":
                    print(f"\n  [完成] 总长度: {evt.get('data', {}).get('total_length', len(full_text))}")
                elif evt_type == "error":
                    print(f"\n  [错误] {evt.get('error', '')}")
            except json.JSONDecodeError:
                pass
    print(f"\n  总输出长度: {len(full_text)}")


async def main():
    print("=" * 60)
    print("RAG 服务完整链路测试")
    print("=" * 60)

    # 1. PDF 解析
    pdf_path = test_pdf_parse()

    # 2. 分块
    test_chunk()

    # 3. Embedding
    emb_ok = await test_embedding()
    if not emb_ok:
        print("\n❌ Embedding 失败，后续测试无法进行")
        return

    # 4. 向量化入库
    if pdf_path:
        await test_ingest(pdf_path)

        # 5. 检索
        await test_retrieve()

        # 6. RAG 对话
        await test_rag_chat()
    else:
        print("\n⚠️ 无 PDF 文件，跳过入库/检索/对话测试")
        print("  请先将 PDF 放入 backend/financial_reports/ 目录")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
