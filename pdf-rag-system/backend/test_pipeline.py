"""
财报 RAG 完整链路测试
每步独立，失败即停
"""
import asyncio
import sys
import os
from pathlib import Path

# ── Step 1: 财报获取（巨潮资讯） ────────────────────────────────────────
async def test_report_fetch():
    print("\n" + "="*60)
    print("STEP 1: 财报获取（巨潮资讯）")
    print("="*60)
    from services.simple_report_service import SimplifiedReportService

    service = SimplifiedReportService()

    print("\n[1b] 直接下载: 比亚迪(002594) 2025Q3 财报")
    pdf_path = await service.download_report_from_cninfo(
        stock_code="002594",
        company_name="比亚迪",
        year=2025,
        quarter="Q3"
    )
    if pdf_path:
        full_path = Path("C:/Users/Administrator/Desktop/financial_rag/pdf-rag-system/backend") / pdf_path
        size_mb = full_path.stat().st_size / 1024 / 1024
        print(f"    [OK] 下载成功: {pdf_path} ({size_mb:.2f} MB)")
        assert full_path.exists(), f"文件不存在: {full_path}"
        assert size_mb > 0.1, f"文件太小: {size_mb:.4f} MB"
    else:
        print("    [FAIL] 下载失败")
        return None

    await service.close()
    return str(full_path)


# ── Step 2: 文本提取（PDF -> text） ────────────────────────────────────────
def test_text_extraction(pdf_path: str):
    print("\n" + "="*60)
    print("STEP 2: 文本提取（PDF -> text）")
    print("="*60)
    from services.rag_service import parse_pdf

    pages = parse_pdf(pdf_path, enable_ocr=False)
    print(f"  解析页数: {len(pages)}")
    for p in pages[:3]:
        text = p["text"]
        print(f"  第{p['page_number']}页: {len(text)}字符, 前100: {text[:100]!r}")

    assert pages, "PDF解析为空"
    total_chars = sum(len(p["text"]) for p in pages)
    print(f"  总字符数: {total_chars}")
    return pages


# ── Step 3+4: 分块 + ChromaDB 入库 ─────────────────────────────────────────
async def test_ingest(pdf_path: str, user_id: int = 1):
    print("\n" + "="*60)
    print("STEP 3+4: 分块 + ChromaDB 入库")
    print("="*60)
    from services.rag_service import ingest_pdf

    print(f"  输入: {pdf_path}")
    result = await ingest_pdf(pdf_path, user_id=user_id)
    print(f"  结果: {result}")

    if result.get("status") == "ok":
        print(f"    [OK] 入库完成: {result.get('chunks')} 个块, source={result.get('source')}")
        return result
    else:
        print(f"    [FAIL] 入库失败: {result.get('message', result)}")
        return None


# ── Step 5: ChromaDB 检索 ──────────────────────────────────────────────────
async def test_retrieve(query: str, user_id: int = 1):
    print("\n" + "="*60)
    print("STEP 5: ChromaDB 检索")
    print("="*60)
    from services.rag_service import retrieve

    print(f"  查询: {query!r}")
    results = await retrieve(query, user_id)
    print(f"  检索到 {len(results)} 条结果")

    if not results:
        print("  [WARN] 无检索结果！")
        return results

    for i, r in enumerate(results):
        src = r.get("source", "")
        score = r.get("score", 0)
        text = (r.get("text", "") or "")
        page = r.get("page_number", "?")
        print(f"\n  --- 结果 {i+1}/{len(results)} ---")
        print(f"  来源: {src}")
        print(f"  页码: {page}  |  相关度分数: {score:.4f}")
        print(f"  内容({len(text)}字符):")
        # 打印内容，多行缩进
        for line in text.split("\n"):
            if line.strip():
                print(f"    {line[:120]}")
    return results


# ── Step 6: 端到端 RAG 流式 ────────────────────────────────────────────────
def test_e2e_stream(query: str):
    print("\n" + "="*60)
    print("STEP 6: 端到端 RAG 流式 (Dify Workflow)")
    print("="*60)
    import requests
    import json
    import re
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

    session = requests.Session()
    login_resp = session.post("http://127.0.0.1:8000/api/auth/login",
                              json={"username": "admin", "password": "admin123"})
    login_resp.raise_for_status()
    print(f"  登录响应: {login_resp.text[:200]}")

    # 提取 token
    m = re.search(r'"(?:access_token|token)"\s*:\s*"([^"]+)"', login_resp.text)
    if not m:
        # 尝试其他格式
        m = re.search(r'bearer["\s:]+([^",\s}]+)', login_resp.text, re.IGNORECASE)
    if not m:
        print(f"  [FAIL] 无法从登录响应提取 token: {login_resp.text[:300]}")
        return []

    token = m.group(1)
    session.headers["Authorization"] = f"Bearer {token}"
    print(f"  Token前20: {token[:20]}...")

    resp = session.post(
        "http://127.0.0.1:8000/api/chat",
        json={"message": query, "style": "专业分析", "document_ids": None},
        stream=True,
        headers={"Accept": "text/event-stream"},
        timeout=120
    )
    resp.raise_for_status()

    events = []
    error_count = 0
    phase_events = []
    text_chars = 0

    for line in resp.iter_lines(decode_unicode=False):
        if not line:
            continue
        text = line.decode("utf-8", errors="replace")
        if text.startswith("data:"):
            raw = text[5:].strip()
            if raw == "[DONE]":
                break
            try:
                obj = json.loads(raw)
                events.append(obj)
                t = obj.get("type", "?")
                content = (obj.get("content") or "")[:60]
                if t == "error":
                    error_count += 1
                    print(f"  [ERR] {content!r}")
                elif t == "phase":
                    phase_events.append(content)
                    print(f"  [PHS] {content!r}")
                elif t in ("text", "final"):
                    text_chars += len(content)
            except json.JSONDecodeError:
                print(f"  [RAW] {raw[:80]!r}")

    print(f"\n  统计: {len(events)}事件 | {error_count}错误 | {text_chars}字符文本")
    return events


# ── 主流程 ──────────────────────────────────────────────────────────────────
async def main():
    print("="*60)
    print("开始完整链路测试")
    print("="*60)

    # Step 1: 财报获取
    pdf_path = await test_report_fetch()
    if not pdf_path:
        print("\n[STEP1 FAIL] 财报获取失败，测试中止")
        return

    # Step 2: 文本提取
    pages = test_text_extraction(pdf_path)
    if not pages or sum(len(p["text"]) for p in pages) < 100:
        print("\n[STEP2 FAIL] 文本提取失败，测试中止")
        return

    # Step 3+4: 分块+入库
    ingest_result = await test_ingest(pdf_path, user_id=1)
    if not ingest_result:
        print("\n[STEP3/4 FAIL] 入库失败，测试中止")
        return

    # Step 5: 检索（async）
    results = await test_retrieve("比亚迪2025Q3营收情况", user_id=1)
    if not results:
        print("\n[STEP5 WARN] 检索为空，跳过Step6")
        return

    # Step 6: 端到端流式
    test_e2e_stream("比亚迪2025Q3的营收情况")

    print("\n" + "="*60)
    print("全部测试完成")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
