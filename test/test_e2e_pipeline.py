"""
端到端 RAG Pipeline 测试

测试流程：
  1. PDF 解析（比亚迪 + 工商银行，两份不同公司）
  2. 逻辑切分（chunker）
  3. 向量化入库（ChromaDB）
  4. 三阶段检索：意图解析 → BM25 混合 → Reranker 精排
  5. LLM 评分：Kimi 对回答质量打分

核心验证：
  - 实体隔离：问"工行营收"不应召回比亚迪内容
  - 切分质量：表格是否完整保留、章节是否正确分段
  - 断路器：查询不存在的公司，Reranker 是否触发断路
"""

import os
import sys
import json
import asyncio
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pdf-rag-system", "backend"))

from services.rag_service import (
    parse_pdf, chunk_documents, ingest_pdf, retrieve,
    _get_collection, _get_embeddings,
)
from services.chunker import logical_chunk, parse_source_meta
from services.query_router import parse_intent, build_where_filter, hybrid_rerank, bge_rerank

from config import DEEPSEEK_API_KEY, KIMI_API_KEY, KIMI_BASE_URL, KIMI_MODEL, SILICONFLOW_BASE_URL, SILICONFLOW_MODEL

# ---------- 配置 ----------
TEST_USER_ID = 99999  # 专用测试 user_id，不影响正式数据
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "pdf-rag-system", "backend")
REPORTS_DIR = os.path.join(BACKEND_DIR, "financial_reports")

# 测试用 PDF（选两份不同公司，制造"实体混淆"场景）
TEST_PDFS = [
    os.path.join(REPORTS_DIR, "002594_比亚迪_2024_report.pdf"),
    os.path.join(REPORTS_DIR, "601398_工商银行_2024_report.pdf"),
]

# 测试问题集（query, expected_company, description）
TEST_QUERIES = [
    ("比亚迪2024年的营业收入是多少？", "比亚迪", "精确实体+年份"),
    ("工行2024年净利润", "工商银行", "简称→全称+精确指标"),
    ("比亚迪新能源汽车销量", "比亚迪", "语义查询，无年份"),
    ("工商银行资本充足率", "工商银行", "银行特有指标"),
    ("中国平安2024年报", None, "不存在的公司，测试断路器"),
]

# ---------- 工具函数 ----------

def separator(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def cleanup_test_collection():
    """清理测试用的 ChromaDB collection"""
    try:
        import chromadb
        from chromadb.config import Settings
        from config import CHROMA_HOST, CHROMA_PORT
        client = chromadb.HttpClient(
            host=CHROMA_HOST, port=CHROMA_PORT,
            settings=Settings(anonymized_telemetry=False)
        )
        col_name = f"user_{TEST_USER_ID}_docs"
        try:
            client.delete_collection(col_name)
            print(f"[清理] 已删除旧 collection: {col_name}")
        except Exception:
            print(f"[清理] collection {col_name} 不存在，无需清理")
    except Exception as e:
        print(f"[清理] 清理失败: {e}")


async def llm_score(query: str, retrieved_chunks: list, description: str) -> dict:
    """
    让硅基流动 Qwen 对检索结果打分（支持低 temperature）。
    返回 {"score": int, "reason": str}
    """
    from openai import AsyncOpenAI
    client = AsyncOpenAI(base_url=SILICONFLOW_BASE_URL, api_key=DEEPSEEK_API_KEY)

    chunks_text = ""
    for i, c in enumerate(retrieved_chunks):
        chunks_text += f"\n--- 片段{i+1} [来源:{c['source']}, 第{c['page_number']}页, "
        chunks_text += f"vec_score={c.get('score',0):.3f}, "
        chunks_text += f"rerank={c.get('rerank_score','N/A')}] ---\n"
        chunks_text += c["text"][:300] + "\n"

    prompt = f"""你是 RAG 系统质量评估专家。请对以下检索结果打分（1-10分）。

## 评分标准
- 10分：检索到的内容完全覆盖问题，来源正确，无实体混淆
- 7-9分：检索到了主要相关内容，来源基本正确
- 4-6分：部分相关，但存在实体混淆或关键信息缺失
- 1-3分：检索结果与问题无关或严重混淆

## 测试场景
{description}

## 用户问题
{query}

## 检索结果（共 {len(retrieved_chunks)} 条）
{chunks_text if chunks_text.strip() else "（空，未检索到任何内容）"}

请严格按 JSON 格式回答，不要其他内容：
{{"score": <1-10整数>, "reason": "<简短评价，50字以内>"}}"""

    try:
        resp = await client.chat.completions.create(
            model=SILICONFLOW_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=200,
        )
        text = resp.choices[0].message.content.strip()
        # 提取 JSON
        import re
        m = re.search(r'\{[^}]+\}', text)
        if m:
            return json.loads(m.group())
        return {"score": 0, "reason": f"LLM 返回格式异常: {text[:100]}"}
    except Exception as e:
        return {"score": -1, "reason": f"LLM 调用失败: {str(e)}"}


# ---------- 主测试流程 ----------

async def main():
    skip_ingest = "--skip-ingest" in sys.argv
    total_start = time.time()

    if not skip_ingest:
        # ========== 阶段0：清理 ==========
        separator("阶段0：清理测试环境")
        cleanup_test_collection()

        # ========== 阶段1：PDF 解析 ==========
        separator("阶段1：PDF 解析")
        all_pages = {}
        for pdf_path in TEST_PDFS:
            if not os.path.exists(pdf_path):
                print(f"[跳过] 文件不存在: {pdf_path}")
                continue
            t0 = time.time()
            pages = parse_pdf(pdf_path, enable_ocr=False)
            elapsed = time.time() - t0
            source = os.path.basename(pdf_path)
            all_pages[source] = pages
            text_pages = [p for p in pages if not p.get("is_table")]
            table_pages = [p for p in pages if p.get("is_table")]
            print(f"  ✓ {source}")
            print(f"    文本页: {len(text_pages)}, 表格段: {len(table_pages)}, 耗时: {elapsed:.1f}s")

        if not all_pages:
            print("[错误] 无可用 PDF 文件，终止测试")
            return

        # ========== 阶段2：逻辑切分 ==========
        separator("阶段2：逻辑切分")
        all_chunks = {}
        for source, pages in all_pages.items():
            meta = parse_source_meta(source)
            print(f"  元信息: {meta}")
            chunks = logical_chunk(pages, strategy="auto", chunk_size=512, chunk_overlap=64, context_meta=meta)
            all_chunks[source] = chunks

            table_chunks = [c for c in chunks if c["metadata"].get("is_table")]
            section_titles = set(c["metadata"].get("section_title", "") for c in chunks if c["metadata"].get("section_title"))
            has_prefix = any("[公司:" in c["text"][:80] or "[公司:" in c["text"][:80] for c in chunks[:3])

            print(f"  ✓ {source}")
            print(f"    总块数: {len(chunks)}, 表格块: {len(table_chunks)}, 识别章节: {len(section_titles)}个")
            print(f"    上下文前缀: {'✓ 已注入' if has_prefix else '✗ 未注入'}")
            if section_titles:
                sample = list(section_titles)[:5]
                print(f"    章节样例: {sample}")
            if chunks:
                print(f"    Chunk[0] 前100字: {chunks[0]['text'][:100]}...")

        # ========== 阶段3：向量化入库 ==========
        separator("阶段3：向量化入库")
        for pdf_path in TEST_PDFS:
            if not os.path.exists(pdf_path):
                continue
            source = os.path.basename(pdf_path)
            t0 = time.time()
            result = await ingest_pdf(pdf_path, TEST_USER_ID)
            elapsed = time.time() - t0
            print(f"  ✓ {source}: {result.get('chunks', 0)} 块入库, 耗时: {elapsed:.1f}s")
    else:
        separator("跳过阶段0-3（复用已有入库数据）")
        from services.rag_service import list_indexed_documents
        docs = list_indexed_documents(TEST_USER_ID)
        for d in docs:
            print(f"  已入库: {d['source']} ({d['count']} 块)")
        if not docs:
            print("  ⚠️ 无已入库数据，请先不带 --skip-ingest 运行一次")
            return

    # ========== 阶段4：三阶段检索 ==========
    separator("阶段4：三阶段检索 + LLM 评分")

    scores = []
    for query, expected_company, desc in TEST_QUERIES:
        print(f"\n  --- 测试: {desc} ---")
        print(f"  Q: {query}")
        print(f"  期望公司: {expected_company or '无（断路器测试）'}")

        # 意图解析
        intent = parse_intent(query)
        print(f"  意图: companies={intent.companies}, year={intent.year}, quarter={intent.quarter}")

        # 检索
        t0 = time.time()
        results = await retrieve(
            query, TEST_USER_ID, top_k=5,
            enable_hybrid=True, enable_rerank=True,
        )
        elapsed = time.time() - t0

        # 判断实体隔离
        if results:
            sources_hit = set(r["source"] for r in results)
            print(f"  命中来源: {sources_hit}")
            for i, r in enumerate(results[:3]):
                print(f"    [{i+1}] score={r.get('score',0):.3f} "
                      f"bm25={r.get('bm25_score','N/A')} "
                      f"rerank={r.get('rerank_score','N/A')} "
                      f"| {r['source']}:p{r['page_number']} "
                      f"| {r['text'][:60]}...")

            # 实体隔离检查
            if expected_company:
                correct_sources = [s for s in sources_hit if expected_company in s]
                wrong_sources = [s for s in sources_hit if expected_company not in s]
                if wrong_sources:
                    print(f"  ⚠️ 实体混淆: 召回了 {wrong_sources}")
                else:
                    print(f"  ✓ 实体隔离正确")
        else:
            print(f"  结果: 空（{elapsed:.2f}s）")
            is_relevant = True
            if not results:
                print(f"  ✓ 断路器/空结果（符合预期）" if expected_company is None else "  ✗ 不应为空")

        # 检查 is_relevant 标记
        any_irrelevant = any(not r.get("is_relevant", True) for r in results)
        if any_irrelevant:
            print(f"  断路器触发: is_relevant=False")

        print(f"  检索耗时: {elapsed:.2f}s")

        # LLM 评分
        print(f"  请求 Kimi 评分...")
        score_result = await llm_score(query, results, desc)
        score = score_result.get("score", 0)
        reason = score_result.get("reason", "")
        scores.append({
            "query": query,
            "expected": expected_company,
            "desc": desc,
            "n_results": len(results),
            "score": score,
            "reason": reason,
            "elapsed": round(elapsed, 2),
        })
        print(f"  Kimi 评分: {score}/10 — {reason}")

    # ========== 汇总 ==========
    separator("测试汇总")
    total_elapsed = time.time() - total_start

    print(f"\n{'查询':<30} {'期望':>8} {'召回':>4} {'评分':>4} {'耗时':>6}  原因")
    print("-" * 100)
    for s in scores:
        q_short = s["query"][:28]
        print(f"{q_short:<30} {(s['expected'] or '断路'):<8} {s['n_results']:>4} "
              f"{s['score']:>4}/10 {s['elapsed']:>5.1f}s  {s['reason']}")

    avg_score = sum(s["score"] for s in scores if s["score"] > 0) / max(1, len([s for s in scores if s["score"] > 0]))
    print(f"\n平均分: {avg_score:.1f}/10")
    print(f"总耗时: {total_elapsed:.1f}s")

    print("\n测试完成。（数据已保留，可用 --skip-ingest 复测）")


if __name__ == "__main__":
    asyncio.run(main())
