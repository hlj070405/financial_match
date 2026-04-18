"""
LangChain RAG 服务 - 替代 Dify 的 RAG Pipeline

核心功能：
  1. PDF 解析（pymupdf4llm 转 Markdown + PyMuPDF fallback）
  2. 文本分块（Markdown 结构化切分 / 滑动窗口兜底）
  3. Embedding（硅基流动 BAAI/bge-large-zh-v1.5）
  4. 向量存储（ChromaDB 本地持久化）
  5. 检索对话（混合检索 + LLM 生成，支持流式输出）
"""

import os
import json
import hashlib
import asyncio
import traceback
from pathlib import Path
from typing import List, Dict, Optional, Generator
from datetime import datetime

# ========== DEBUG LOGGING ==========
_DEBUG_LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "debug-4459df.log")

def _debug_log(hypothesis_id: str, location: str, message: str, data: dict):
    import datetime as _dt
    import threading
    entry = {
        "sessionId": "4459df",
        "id": f"log_{int(_dt.datetime.now().timestamp()*1000)}",
        "timestamp": int(_dt.datetime.now().timestamp() * 1000),
        "location": location,
        "message": message,
        "data": data,
        "runId": "debug-run",
        "hypothesisId": hypothesis_id
    }
    try:
        with open(_DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass
# ========== END DEBUG LOGGING ==========


import fitz  # PyMuPDF
import httpx
import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rag.chunker import logical_chunk, parse_source_meta
from rag.query_router import parse_intent, build_where_filter, hybrid_rerank, bge_rerank

from core.config import (
    DEEPSEEK_API_KEY, KIMI_API_KEY, KIMI_BASE_URL, KIMI_MODEL,
    KIMI_TEMPERATURE, KIMI_MAX_TOKENS, KIMI_MAX_ROUNDS,
    EMBEDDING_MODEL, EMBEDDING_DIM, EMBEDDING_BASE_URL, EMBEDDING_BATCH_SIZE,
    CHUNK_SIZE, CHUNK_OVERLAP, FINANCIAL_REPORTS_DIR,
    CHROMA_HOST, CHROMA_PORT
)

# ---------- 配置 ----------

BACKEND_BASE_DIR = os.path.dirname(os.path.dirname(__file__))

LLM_MODEL = KIMI_MODEL
LLM_BASE_URL = KIMI_BASE_URL

# Kimi OpenAI-compatible client（用于 function calling）
from openai import AsyncOpenAI as _AsyncOpenAI
_kimi_async_client = _AsyncOpenAI(
    base_url=KIMI_BASE_URL,
    api_key=KIMI_API_KEY,
)

# ---------- Embedding 客户端 ----------

_embedding_cache = {}


def _resolve_existing_pdf_path(pdf_path: str) -> str:
    if not pdf_path:
        return pdf_path

    normalized = pdf_path.replace("\\", "/")
    candidates = []
    if os.path.isabs(pdf_path):
        candidates.append(pdf_path)
    else:
        candidates.append(os.path.join(os.getcwd(), pdf_path))
        candidates.append(os.path.join(BACKEND_BASE_DIR, pdf_path))

    tail = normalized.split("financial_reports/", 1)[1] if "financial_reports/" in normalized else normalized
    candidates.append(os.path.join(FINANCIAL_REPORTS_DIR, tail))
    candidates.append(os.path.join(BACKEND_BASE_DIR, "financial_reports", tail))

    seen = set()
    fallback = None
    for candidate in candidates:
        full_path = os.path.abspath(candidate)
        if fallback is None:
            fallback = full_path
        if full_path in seen:
            continue
        seen.add(full_path)
        if os.path.exists(full_path):
            return full_path
    return fallback or os.path.abspath(pdf_path)


def _infer_file_type(source_name: Optional[str]) -> str:
    ext = os.path.splitext((source_name or "").lower())[1]
    if ext == ".pdf":
        return "pdf"
    if ext in {".xls", ".xlsx", ".csv"}:
        return "excel"
    if ext in {".doc", ".docx"}:
        return "word"
    if ext in {".html", ".htm", ".mhtml", ".url"}:
        return "web"
    return ext.lstrip(".") or "unknown"


def _normalize_int_list(value) -> Optional[List[int]]:
    if value is None:
        return None
    if isinstance(value, int):
        return [value]
    if isinstance(value, str):
        raw_items = [item.strip() for item in value.split(",")]
    elif isinstance(value, (list, tuple, set)):
        raw_items = list(value)
    else:
        return None

    normalized = []
    for item in raw_items:
        if item in {None, ""}:
            continue
        try:
            normalized.append(int(item))
        except (TypeError, ValueError):
            continue
    return normalized or None


def _build_source_refs(items: List[Dict]) -> List[str]:
    refs = []
    seen = set()
    for item in items or []:
        source = item.get("source") or "unknown"
        page_number = item.get("page_number")
        is_table = item.get("is_table", False)
        ref = source
        if page_number:
            ref = f"{ref} 第{page_number}页"
        if is_table:
            ref = f"{ref} [表格]"
        if ref in seen:
            continue
        seen.add(ref)
        refs.append(ref)
    return refs


def _find_document_record(db, user_id: int, source_name: Optional[str] = None,
                          stock_code: Optional[str] = None,
                          company_name: Optional[str] = None,
                          year: Optional[int] = None):
    if db is None:
        return None

    from core.database import Document

    base_name = os.path.basename(source_name or "")
    query = db.query(Document).filter(Document.user_id == user_id)

    if base_name:
        matched = query.filter(Document.pdf_path.like(f"%{base_name}")).order_by(Document.id.desc()).first()
        if matched:
            return matched

    if stock_code and year is not None:
        matched = query.filter(
            Document.stock_code == stock_code,
            Document.year == year,
        ).order_by(Document.id.desc()).first()
        if matched:
            return matched

    if company_name and year is not None:
        matched = query.filter(
            Document.company == company_name,
            Document.year == year,
        ).order_by(Document.id.desc()).first()
        if matched:
            return matched

    if company_name:
        matched = query.filter(Document.company == company_name).order_by(Document.id.desc()).first()
        if matched:
            return matched

    return None


def _sort_retrieved_chunks(items: List[Dict], sort_by: str) -> List[Dict]:
    if sort_by == "score_asc":
        return sorted(items, key=lambda item: (item["score"], item["page_number"], item["chunk_index"]))
    if sort_by == "page_asc":
        return sorted(items, key=lambda item: (item["page_number"], item["chunk_index"], -item["score"]))
    if sort_by == "page_desc":
        return sorted(items, key=lambda item: (-item["page_number"], -item["chunk_index"], -item["score"]))
    if sort_by == "source_asc":
        return sorted(items, key=lambda item: (item["source"], item["page_number"], item["chunk_index"], -item["score"]))
    if sort_by == "source_desc":
        return sorted(items, key=lambda item: (item["source"], item["page_number"], item["chunk_index"], -item["score"]), reverse=True)
    return sorted(items, key=lambda item: (item["score"], -item["page_number"], -item["chunk_index"]), reverse=True)


_EMBEDDING_CONCURRENCY = 5  # 并发请求数


async def _get_embeddings(texts: List[str], api_key: str = None) -> List[List[float]]:
    """调用硅基流动 Embedding API（批量，5 路并发）"""
    key = api_key or DEEPSEEK_API_KEY
    if not key:
        raise ValueError("DEEPSEEK_API_KEY 未设置，无法调用 Embedding API")

    # 硅基流动 bge-large-zh 限制 512 tokens；表格/数字 token 密度高，保守截断到 600 字符
    _MAX_EMBED_CHARS = 600
    texts = [t[:_MAX_EMBED_CHARS] if len(t) > _MAX_EMBED_CHARS else t for t in texts]

    # 拆分为多个批次：[(batch_texts_0), (batch_texts_1), ...]
    batches: List[List[str]] = []
    for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
        batches.append(texts[i:i + EMBEDDING_BATCH_SIZE])

    if not batches:
        return []

    _debug_log("H2", "rag_service.py:241_batch_start", "Embedding batch starting", {
        "total_batches": len(batches),
        "batch_sizes": [len(b) for b in batches],
        "empty_texts_count": sum(1 for b in batches for t in b if not t.strip()),
    })

    sem = asyncio.Semaphore(_EMBEDDING_CONCURRENCY)
    results_map: Dict[int, List[List[float]]] = {}

    async def _embed_one_request(batch_texts: List[str]) -> List[List[float]]:
        """发送单次 embedding 请求"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{EMBEDDING_BASE_URL}/embeddings",
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": EMBEDDING_MODEL,
                    "input": batch_texts,
                    "encoding_format": "float"
                }
            )
            if resp.status_code != 200:
                raise Exception(f"Embedding API 错误: {resp.status_code} - {resp.text}")
            data = resp.json()
            return [item["embedding"] for item in sorted(data["data"], key=lambda x: x["index"])]

    async def _embed_batch(batch_idx: int, batch_texts: List[str]):
        async with sem:
            try:
                results_map[batch_idx] = await _embed_one_request(batch_texts)
            except Exception as e:
                if "413" in str(e) or "20042" in str(e):
                    # token 超限：逐条截断到 400 字符重试
                    print(f"[Embedding] 批次{batch_idx} 超限，逐条截断重试")
                    truncated = [t[:400] for t in batch_texts]
                    try:
                        results_map[batch_idx] = await _embed_one_request(truncated)
                    except Exception as e2:
                        print(f"[Embedding] 批次{batch_idx} 重试仍失败: {e2}")
                        results_map[batch_idx] = None
                else:
                    print(f"[Embedding] 批次{batch_idx} 失败: {e}")
                    results_map[batch_idx] = None

    await asyncio.gather(*[_embed_batch(idx, batch) for idx, batch in enumerate(batches)])

    # 按原始顺序拼接，跳过失败批次
    all_embeddings = []
    failed_count = 0
    zero_vector_count = 0
    for idx in range(len(batches)):
        batch_result = results_map.get(idx)
        if batch_result is None:
            # 失败批次用零向量填充（保持索引对齐）
            from config import EMBEDDING_DIM
            for _ in batches[idx]:
                all_embeddings.append([0.0] * EMBEDDING_DIM)
            failed_count += len(batches[idx])
        else:
            all_embeddings.extend(batch_result)
            for emb in batch_result:
                if all(v == 0.0 for v in emb):
                    zero_vector_count += 1

    _debug_log("H2", "rag_service.py:300_embedding_result", "Embedding batch completed", {
        "total_returned": len(all_embeddings),
        "failed_count": failed_count,
        "zero_vector_count": zero_vector_count,
        "first_embedding_sample": all_embeddings[0][:5] if all_embeddings else [],
    })
    if failed_count > 0:
        print(f"[Embedding] 警告: {failed_count} 条使用零向量填充")
    return all_embeddings


def _get_embedding_sync(text: str, api_key: str = None) -> List[float]:
    """同步版 Embedding（供 ChromaDB 的 EmbeddingFunction 使用）"""
    import httpx as _httpx
    key = api_key or DEEPSEEK_API_KEY
    with _httpx.Client(timeout=60.0) as client:
        resp = client.post(
            f"{EMBEDDING_BASE_URL}/embeddings",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            },
            json={
                "model": EMBEDDING_MODEL,
                "input": [text],
                "encoding_format": "float"
            }
        )
        if resp.status_code != 200:
            raise Exception(f"Embedding API 错误: {resp.status_code} - {resp.text}")
        return resp.json()["data"][0]["embedding"]


class SiliconFlowEmbedding:
    """ChromaDB 兼容的 EmbeddingFunction"""

    def name(self) -> str:
        return "siliconflow_bge_zh"

    @staticmethod
    def build_from_config(config):
        return SiliconFlowEmbedding()

    def get_config(self):
        return {}

    def __call__(self, input: List[str]) -> List[List[float]]:
        loop = None
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            pass

        if loop and loop.is_running():
            # 在异步环境中，用线程池跑同步调用
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(self._sync_embed, input)
                return future.result(timeout=120)
        else:
            return asyncio.run(self._async_embed(input))

    def _sync_embed(self, texts: List[str]) -> List[List[float]]:
        return asyncio.run(self._async_embed(texts))

    async def _async_embed(self, texts: List[str]) -> List[List[float]]:
        return await _get_embeddings(texts)


# ---------- ChromaDB 客户端（单例） ----------

_chroma_client = None
_embedding_fn = SiliconFlowEmbedding()


def _get_chroma():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.HttpClient(
            host=CHROMA_HOST,
            port=CHROMA_PORT,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
    return _chroma_client


def _collection_name(user_id: int) -> str:
    """每个用户一个 collection"""
    return f"user_{user_id}_docs"


def _get_collection(user_id: int):
    client = _get_chroma()
    return client.get_or_create_collection(
        name=_collection_name(user_id),
        embedding_function=_embedding_fn,
        metadata={"hnsw:space": "cosine"}
    )


# ---------- PDF 解析 ----------

def convert_pdf_to_markdown(pdf_path: str, output_md_path: str = None) -> str:
    """
    自适应 PDF → Markdown 转换策略：
    - 小文件（≤80页）：pymupdf4llm Layout ON，结构/表格质量最佳
    - 大文件（>80页）：PyMuPDF 纯文本 + pdfplumber 表格，速度优先（~10s vs ~100s）
    返回生成的 Markdown 文件路径。
    """
    try:
        import fitz as _fitz

        # 获取页数，决定解析策略
        _doc = _fitz.open(pdf_path)
        page_count = len(_doc)
        _doc.close()

        LARGE_PAGE_THRESHOLD = 80  # 超过此页数切换到快速模式

        if page_count <= LARGE_PAGE_THRESHOLD:
            # ---- 小文件：pymupdf4llm Layout 模式 ----
            import pymupdf4llm
            pymupdf4llm.use_layout(True)
            print(f"[pymupdf4llm] 小文件模式({page_count}页)，Layout ON，开始转换: {os.path.basename(pdf_path)}")
            md_content = pymupdf4llm.to_markdown(pdf_path)
        else:
            # ---- 大文件：PyMuPDF 文本 + pdfplumber 表格（仅前 TABLE_PAGE_LIMIT 页）----
            TABLE_PAGE_LIMIT = 30  # 只对前N页做 pdfplumber 表格提取，避免超长耗时
            print(f"[pymupdf4llm] 大文件模式({page_count}页)，快速文本+表格提取: {os.path.basename(pdf_path)}")

            doc = _fitz.open(pdf_path)
            page_texts = []
            for i, page in enumerate(doc):
                text = page.get_text("text").strip()
                if text:
                    page_texts.append(f"## 第{i+1}页\n\n{text}")
            doc.close()

            # pdfplumber 补充表格（只取前 TABLE_PAGE_LIMIT 页）
            table_sections = []
            try:
                import pdfplumber
                with pdfplumber.open(pdf_path) as pdf:
                    for i, page in enumerate(pdf.pages):
                        if i >= TABLE_PAGE_LIMIT:
                            break
                        tables = page.extract_tables()
                        for t_idx, table in enumerate(tables):
                            rows = []
                            for row in table:
                                cells = [str(c).strip() if c else "" for c in row]
                                rows.append(" | ".join(cells))
                            table_text = "\n".join(rows)
                            if table_text.strip():
                                table_sections.append(f"\n**[第{i+1}页 表格{t_idx+1}]**\n\n{table_text}\n")
            except Exception as e:
                print(f"[pymupdf4llm] pdfplumber 表格提取失败（不影响主流程）: {e}")

            md_content = "\n\n".join(page_texts)
            if table_sections:
                md_content += "\n\n---\n\n## 附：关键表格\n\n" + "\n".join(table_sections)

        if output_md_path is None:
            output_md_path = os.path.splitext(pdf_path)[0] + ".md"

        with open(output_md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        print(f"[pymupdf4llm] 转换完成: {output_md_path} ({page_count}页, {len(md_content)} 字符)")
        return output_md_path
    except Exception as e:
        print(f"[pymupdf4llm] 转换失败: {e}")
        traceback.print_exc()
        return None


def _ocr_page(page) -> str:
    """对单页 PDF 进行 OCR（扫描件兜底）"""
    try:
        from PIL import Image
        import pytesseract
        import io
        # 渲染为 300 DPI 图片
        pix = page.get_pixmap(dpi=300)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        text = pytesseract.image_to_string(img, lang="chi_sim+eng")
        return text.strip()
    except ImportError:
        # pytesseract / Pillow 未安装，跳过 OCR
        return ""
    except Exception as e:
        print(f"[OCR] 页面 OCR 失败: {e}")
        return ""


def parse_pdf(pdf_path: str, enable_ocr: bool = True) -> List[Dict]:
    """
    解析 PDF，返回页面列表。
    每页包含: page_number, text, tables(如有)
    enable_ocr: 当页面无文字时自动尝试 OCR
    """
    results = []
    ocr_pages = 0
    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        text = text.strip()

        # OCR 兜底：如果文本层为空或极少（扫描件），尝试 OCR
        if enable_ocr and len(text) < 20:
            ocr_text = _ocr_page(page)
            if len(ocr_text) > len(text):
                text = ocr_text
                ocr_pages += 1

        if text:
            results.append({
                "page_number": page_num + 1,
                "text": text,
                "source": os.path.basename(pdf_path)
            })
    doc.close()

    if ocr_pages > 0:
        print(f"[RAG] OCR 识别了 {ocr_pages} 页扫描内容")

    # 尝试用 pdfplumber 提取表格
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                if tables:
                    for table_idx, table in enumerate(tables):
                        rows = []
                        for row in table:
                            cells = [str(c).strip() if c else "" for c in row]
                            rows.append(" | ".join(cells))
                        table_text = "\n".join(rows)
                        if table_text.strip():
                            results.append({
                                "page_number": i + 1,
                                "text": f"[表格 {table_idx + 1}]\n{table_text}",
                                "source": os.path.basename(pdf_path),
                                "is_table": True
                            })
    except Exception as e:
        print(f"[RAG] pdfplumber 表格提取失败（不影响主流程）: {e}")

    return results


def extract_text_from_pdf(pdf_path: str, max_chars: int = 30000) -> str:
    """
    快速提取 PDF 全文（用于直接分析模式，不入向量库）。
    自动启用 OCR 兜底。截断到 max_chars 以免超出 LLM context。
    """
    pages = parse_pdf(pdf_path, enable_ocr=True)
    parts = []
    total = 0
    for p in pages:
        text = p["text"]
        tag = f"[第{p['page_number']}页]"
        if p.get("is_table"):
            tag += "[表格]"
        entry = f"{tag}\n{text}\n"
        if total + len(entry) > max_chars:
            remaining = max_chars - total
            if remaining > 100:
                parts.append(entry[:remaining] + "\n...(截断)")
            break
        parts.append(entry)
        total += len(entry)
    return "\n".join(parts)


# ---------- 文本分块 ----------

def chunk_documents(pages: List[Dict], source_meta: Dict = None, is_markdown: bool = False) -> List[Dict]:
    """
    逻辑切分：章节感知 + 表格整体保留 + 头部上下文注入。
    如果是预处理的 Markdown，将启用基于 Markdown 结构的高级分块。
    委托给 services.chunker.logical_chunk。
    """
    empty_pages = [p for p in pages if not (p.get("text") or "").strip()]
    _debug_log("H3", "rag_service.py:549_chunk_start", "chunk_documents called", {
        "total_pages": len(pages),
        "empty_pages": len(empty_pages),
        "first_page_len": len(pages[0].get("text", "")) if pages else 0,
        "is_markdown": is_markdown,
    })
    chunks = logical_chunk(
        pages,
        strategy="auto",
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        context_meta=source_meta or {},
        is_markdown=is_markdown,
    )
    _debug_log("H3", "rag_service.py:564_chunk_end", "chunk_documents result", {
        "chunks_count": len(chunks),
        "empty_chunks": sum(1 for c in chunks if not (c.get("text") or "").strip()),
    })
    return chunks


# ---------- 向量化入库 ----------

async def ingest_pdf(pdf_path: str, user_id: int, document_id: int = None,
                     progress_callback=None) -> Dict:
    """
    完整的 PDF 入库流程：解析 → 分块 → 向量化 → 存入 ChromaDB

    Args:
        progress_callback: 可选的异步回调函数 async fn(message: str)，用于向前端推送进度

    Returns:
        {"status": "ok", "chunks": N, "document_id": ..., "source": ...}
    """
    async def _progress(msg: str):
        if progress_callback:
            await progress_callback(msg)

    full_path = _resolve_existing_pdf_path(pdf_path)

    if not os.path.exists(full_path):
        return {"status": "error", "message": f"文件不存在: {full_path}"}

    source_name = os.path.basename(full_path)
    print(f"[RAG] 开始处理: {source_name}")

    # 从文件名解析公司/年份等元信息
    source_meta = parse_source_meta(source_name)
    print(f"[RAG] 解析元信息: {source_meta}")

    # 1. 解析/读取文件
    md_path = os.path.splitext(full_path)[0] + ".md"
    is_markdown = False
    pages = []
    
    if os.path.exists(md_path):
        # 尝试使用预处理好的 Markdown
        await _progress(f"发现预处理 Markdown 文件，正在加载...")
        print(f"[RAG] 发现预处理的 MD 文件: {md_path}")
        with open(md_path, "r", encoding="utf-8") as f:
            md_content = f.read()
            pages = [{"text": md_content, "source": source_name}]
            is_markdown = True
        print(f"[RAG] MD 读取完成")
        await _progress(f"预处理Markdown加载完成")
    else:
        # 尝试实时转换为 Markdown
        await _progress(f"正在进行文档结构化解析（pymupdf4llm），请稍候...")
        print(f"[RAG] 未找到预处理 MD，尝试 pymupdf4llm 转换: {full_path}")
        
        # 使用 run_in_executor 将同步的 pymupdf4llm 转换放入线程池
        loop = asyncio.get_event_loop()
        converted_md_path = await loop.run_in_executor(
            None, convert_pdf_to_markdown, full_path, md_path
        )
        
        if converted_md_path and os.path.exists(converted_md_path):
            print(f"[RAG] pymupdf4llm 转换成功，使用 Markdown 模式")
            with open(converted_md_path, "r", encoding="utf-8") as f:
                md_content = f.read()
                pages = [{"text": md_content, "source": source_name}]
                is_markdown = True
            await _progress(f"文档结构化解析完成")
        else:
            # Fallback 到原生 PDF 解析
            await _progress(f"结构化解析失败，使用原生 PDF 解析...")
            print(f"[RAG] pymupdf4llm 转换失败，回退到原生 PDF 解析: {full_path}")
            pages = parse_pdf(full_path)
            if not pages:
                return {"status": "error", "message": "PDF 解析结果为空"}
            await _progress(f"PDF解析完成，共 {len(pages)} 页")
        print(f"[RAG] 解析完成: {len(pages)} 页/段")
        await _progress(f"PDF解析完成，共 {len(pages)} 页")

    # 2. 分块（逻辑切分）
    chunks = chunk_documents(pages, source_meta=source_meta, is_markdown=is_markdown)
    if not chunks:
        return {"status": "error", "message": "分块结果为空"}
    print(f"[RAG] 分块完成: {len(chunks)} 个块")
    await _progress(f"文本分块完成，共 {len(chunks)} 个块")

    # 3. 获取 collection
    collection = _get_collection(user_id)

    # 4. 检查是否已存在同名文档的块，先删除旧的
    try:
        existing = collection.get(where={"source": source_name})
        if existing and existing["ids"]:
            collection.delete(ids=existing["ids"])
            print(f"[RAG] 已删除旧文档块: {len(existing['ids'])} 个")
    except Exception:
        pass

    # 5. 准备 metadata
    all_texts = [c["text"] for c in chunks]
    all_ids = [c["id"] for c in chunks]
    all_metadatas = []
    for c in chunks:
        meta = dict(c["metadata"])
        if document_id is not None:
            meta["document_id"] = document_id
        meta["page_number"] = int(meta.get("page_number", 0))
        meta["chunk_index"] = int(meta.get("chunk_index", 0))
        meta["is_table"] = bool(meta.get("is_table", False))
        meta["section_title"] = str(meta.get("section_title", ""))
        if meta.get("year"):
            meta["year"] = int(meta["year"])
        meta = {k: v for k, v in meta.items() if v != "" and v is not None}
        all_metadatas.append(meta)

    # 6. 一次性并发获取所有 Embedding（内部 5 路并发 + batch_size=64）
    import time as _time
    t_embed = _time.time()
    await _progress(f"正在向量化 {len(chunks)} 个文本块（这可能需要1-2分钟）...")
    try:
        all_embeddings = await _get_embeddings(all_texts)
    except Exception as e:
        print(f"[RAG] Embedding 批量获取失败: {e}")
        traceback.print_exc()
        return {"status": "error", "message": f"Embedding 失败: {e}"}
    embed_time = _time.time() - t_embed
    print(f"[RAG] Embedding 完成: {len(all_embeddings)} 个, 耗时 {embed_time:.1f}s")
    await _progress(f"向量化完成（{embed_time:.0f}秒），正在写入向量库...")

    # 7. 分批写入 ChromaDB（ChromaDB 单次写入有大小限制，按 batch 写）
    write_batch = 500
    total_written = 0
    total_batches = (len(chunks) + write_batch - 1) // write_batch
    for batch_no, i in enumerate(range(0, len(chunks), write_batch), 1):
        end = min(i + write_batch, len(chunks))
        try:
            collection.add(
                ids=all_ids[i:end],
                embeddings=all_embeddings[i:end],
                documents=all_texts[i:end],
                metadatas=all_metadatas[i:end]
            )
            total_written += (end - i)
            print(f"[RAG] 写入进度: {total_written}/{len(chunks)}")
            if total_batches > 1:
                await _progress(f"写入向量库: {total_written}/{len(chunks)} ({batch_no}/{total_batches})")
        except Exception as e:
            print(f"[RAG] 批次写入失败: {e}")
            traceback.print_exc()

    print(f"[RAG] 入库完成: {source_name}, {total_written} 个块")
    return {
        "status": "ok",
        "chunks": total_written,
        "source": source_name,
        "document_id": document_id
    }


# ---------- 检索 ----------

async def retrieve(query: str, user_id: int, top_k: int = 5,
                   document_ids: List[int] = None,
                   score_threshold: float = 0.55,
                   file_types: List[str] = None,
                   sort_by: str = "score_desc",
                   raise_on_error: bool = False,
                   enable_hybrid: bool = True,
                   enable_rerank: bool = True) -> List[Dict]:
    """
    从用户的向量库中检索相关文档块。

    三阶段漏斗：
      1. 意图解析 + 元数据过滤：自动从 query 提取公司名/年份，锁定向量库过滤条件
      2. BM25 混合重排：向量分 + BM25 分 RRF 融合，提升硬实体召回
      3. BGE-Reranker 精排：Cross-Encoder 精准判相关性，并触发断路器

    Args:
        query:          用户问题
        user_id:        用户ID
        top_k:          返回Top-K结果
        document_ids:   可选，显式限定文档范围（最高优先级）
        enable_hybrid:  是否启用 BM25 混合重排（默认开启）
        enable_rerank:  是否启用 BGE-Reranker 精排（默认开启）

    Returns:
        [{"text": ..., "source": ..., "score": ..., "rerank_score": ..., "is_relevant": bool}, ...]
    """
    collection = _get_collection(user_id)

    # ---- 意图解析 + 元数据过滤 ----
    intent = parse_intent(query)
    if intent.companies or intent.year:
        print(f"[RAG] 意图解析: companies={intent.companies}, year={intent.year}, quarter={intent.quarter}")

    # 从向量库拿所有 source 文件名（用于意图匹配）
    indexed_sources: List[str] = []
    if not document_ids and not intent.is_empty():
        try:
            all_meta = collection.get(include=["metadatas"])
            seen = set()
            for m in (all_meta.get("metadatas") or []):
                s = m.get("source", "")
                if s and s not in seen:
                    seen.add(s)
                    indexed_sources.append(s)
        except Exception:
            pass

    where_filter = build_where_filter(
        intent,
        indexed_sources,
        explicit_document_ids=_normalize_int_list(document_ids),
    )
    if where_filter:
        print(f"[RAG] 元数据过滤: {where_filter}")

    try:
        query_embedding = await _get_embeddings([query])
        _debug_log("H1", "rag_service.py:755_embed_call", "Embedding called for query", {"query_len": len(query), "embed_count": len(query_embedding) if query_embedding else 0, "first_embed_is_zero": bool(query_embedding and all(v == 0.0 for v in query_embedding[0]))})

        # 混合检索时多取候选，给 BM25 足够的重排空间
        query_limit = top_k
        if enable_hybrid:
            query_limit = min(max(top_k * 4, 20), 100)
        elif file_types or sort_by != "score_desc":
            query_limit = min(max(top_k * 5, top_k), 100)

        results = collection.query(
            query_embeddings=query_embedding,
            n_results=query_limit,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )
        _debug_log("H1", "rag_service.py:769_chroma_query", "ChromaDB query results", {
            "results_is_none": results is None,
            "results_keys": list(results.keys()) if results else [],
            "doc_count": len(results.get("documents", [[]])[0]) if results and results.get("documents") else 0,
            "distances_sample": results.get("distances", [[]])[0][:3] if results and results.get("distances") and results["distances"][0] else [],
        })
    except Exception as e:
        print(f"[RAG] 检索失败: {e}")
        traceback.print_exc()
        _debug_log("H1", "rag_service.py:770_chroma_exception", "ChromaDB query exception", {"error": str(e)})
        if raise_on_error:
            raise
        return []

    if not results or not results["documents"] or not results["documents"][0]:
        _debug_log("H1", "rag_service.py:777_empty_results", "ChromaDB returned empty results", {"results": str(results)[:200]})
        return []

    retrieved = []
    filtered_count = 0
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        similarity = 1 - (dist / 2)
        if similarity < score_threshold:
            filtered_count += 1
            continue
        source = meta.get("source", "unknown")
        file_type = _infer_file_type(source)
        if file_types and file_type not in file_types:
            filtered_count += 1
            continue
        retrieved.append({
            "text": doc,
            "source": source,
            "page_number": meta.get("page_number", 0),
            "chunk_index": meta.get("chunk_index", 0),
            "is_table": meta.get("is_table", False),
            "document_id": meta.get("document_id"),
            "file_type": file_type,
            "score": round(similarity, 4)
        })

    if filtered_count > 0:
        print(f"[RAG] 检索过滤: 丢弃 {filtered_count} 个低分结果 (阈值 {score_threshold})")

    # ---- 第二阶段：BM25 混合重排 ----
    if enable_hybrid and retrieved:
        retrieved = hybrid_rerank(query, retrieved)
        print(f"[RAG] BM25混合重排完成, 候选={len(retrieved)}")
    else:
        retrieved = _sort_retrieved_chunks(retrieved, sort_by)

    # ---- 第三阶段：BGE-Reranker 精排 + 断路器 ----
    is_relevant = True
    if enable_rerank and retrieved:
        retrieved, is_relevant = await bge_rerank(
            query,
            retrieved,
            api_key=DEEPSEEK_API_KEY,
            top_n=top_k,
        )
        if not is_relevant:
            print(f"[RAG] 断路器：知识库中无相关内容，返回空列表")
            # 断路后仍返回结果，但标记 is_relevant=False 供调用方判断
            for r in retrieved:
                r["is_relevant"] = False
            return retrieved

    return retrieved[:top_k]


# ---------- RAG 对话（流式） ----------

ROLE_PROFILES = {
    "personal_general": {
        "identity": "幻流智能咨询助手",
        "tone": "亲切易懂，避免过多专业术语，用比喻和生活化语言解释复杂概念",
        "focus": "帮助普通用户理解财报数据的核心含义，提供通俗的投资科普",
        "clarify": True,
        "suggest": True,
    },
    "personal_wealthy": {
        "identity": "幻流·高净值客户专属顾问",
        "tone": "专业而温和，兼顾深度与可读性，适当提供资产配置建议",
        "focus": "深度分析投资价值、风险收益比，对标同类资产表现",
        "clarify": True,
        "suggest": True,
    },
    "personal_professional": {
        "identity": "幻流·专业投研助手",
        "tone": "简洁精准，直接给出数据和结论，不做过多铺垫",
        "focus": "产业链深度分析、估值模型、技术面与基本面结合，量化指标优先",
        "clarify": False,
        "suggest": True,
    },
    "enterprise_small": {
        "identity": "幻流·企业金融数据分析师",
        "tone": "严谨规范，数据驱动，适合报告引用",
        "focus": "企业财务健康度、行业对标、风险预警",
        "clarify": True,
        "suggest": True,
    },
    "enterprise_large": {
        "identity": "幻流·企业级智能研究平台",
        "tone": "高度专业，结构化输出，适合机构级决策参考",
        "focus": "多维度量化分析、多源数据交叉验证、系统性风险评估",
        "clarify": False,
        "suggest": True,
    },
}

DEFAULT_PROFILE = {
    "identity": "幻流智能金融分析助手",
    "tone": "专业清晰，兼顾深度与可读性",
    "focus": "基于财报文档进行准确的数据分析与洞察",
    "clarify": True,
    "suggest": True,
}


def _build_rag_prompt(query: str, context_chunks: List[Dict],
                      style: str = "专业分析",
                      user_role: str = None,
                      has_context: bool = True) -> list:
    """
    构建 RAG 对话的 messages。
    支持动态身份、结构化 JSON 交互输出。
    """
    profile = ROLE_PROFILES.get(user_role, DEFAULT_PROFILE)

    # 组装上下文
    context_text = ""
    if has_context and context_chunks:
        context_parts = []
        for i, chunk in enumerate(context_chunks):
            source_info = f"[来源: {chunk['source']}, 第{chunk['page_number']}页"
            if chunk.get("is_table"):
                source_info += ", 表格数据"
            source_info += f", 相关度: {chunk['score']:.1%}]"
            context_parts.append(f"--- 参考片段 {i + 1} {source_info} ---\n{chunk['text']}")
        context_text = "\n\n".join(context_parts)

    from datetime import datetime as _dt
    _today = _dt.now().strftime("%Y年%m月%d日")
    _cur_year = _dt.now().year

    # ---- 构建 system prompt ----
    system_prompt = f"""# 身份
你是「{profile['identity']}」。

## 当前日期
今天的真实日期是 {_today}（当前年份是{_cur_year}年）。你的训练数据可能截止于2025年，但现在确实已经是{_cur_year}年。这意味你的所有信息都必须是2025年及以后的。

## 财报发布时间规律（调用 fetch_financial_report 时必须参考）
A股财报披露时间表：
- 年报（Q4）：次年 1月24日 ~ 4月30日陆续披露
- 一季报（Q1）：当年 4月30日前
- 半年报（H1）：当年 8月31日前
- 三季报（Q3）：当年 10月31日前

当前日期 {_today}，你应该智能判断最新可用的财报：
- 不要直接用当前年份，而是根据以上时间表判断哪个报告已经发布
- 优先获取最新的已发布报告，不指定 quarter 让系统自动选择最新可用报告。
- 如果用户说“最新财报”，就不要指定 quarter，留空由系统自动查找最新可用报告。

## 沟通风格
{profile['tone']}

## 分析重点
{profile['focus']}

## 当前分析风格
{style}

## 核心规则
1. 严格基于提供的参考文档内容回答，不要编造数据
2. 回答时引用来源，格式: [来源: 文件名, 第X页]
3. 如果参考文档中没有相关信息，明确告知用户
4. 必须使用标准 Markdown 标题层级组织回答：用 `#` 做报告主标题，`##` 做大章节，`###` 做子章节，`####` 做小节。禁止使用"一、""（一）""1."等中文序号作为标题，必须用 # 号标题语法
5. 对于财务数据，保持精确，表格必须使用 Markdown 表格语法（| 分隔列）

## 结构化交互指令
当你判断需要与用户进行交互时（例如需求不明确、有多个分析方向可选、需要用户确认），
请在正常文本回复之外，在回复的**最末尾**额外输出一个 JSON 块，格式如下：

```json
{{"interaction": {{
  "type": "clarify | options | confirm | suggest",
  "title": "交互标题",
  "items": [
    {{"label": "选项文本", "value": "传回后端的值", "desc": "可选描述"}}
  ]
}}}}
```

交互类型说明：
- **clarify**: 需求澄清，当用户问题模糊时，列出可能的意图让用户选择
- **options**: 分析方向选项，提供不同角度的分析路径
- **confirm**: 确认操作，需要用户确认后再执行
- **suggest**: 后续建议，分析完成后推荐用户可能感兴趣的下一步

规则：
- 如果用户意图已经非常明确，直接回答，不需要输出交互 JSON
- 交互 JSON 必须放在回复最末尾，且用 ```json 代码块包裹
- items 数组最多 4 个选项

## 工具使用原则（重要）
1. 尽量合并查询：对比多家公司时，不要对每个指标分别调用 search_vector_store，而是用一次宽泛查询获取尽可能多的信息
2. 每家公司最多调用 search_vector_store 1-2 次，避免反复搜索
3. **fetch_financial_report 调用判断**：上方"参考文档内容"是系统预检索的全库结果，**不能作为该目标公司是否已入库的依据**。只要用户明确提到某公司且参考文档中没有该公司来源的内容，就必须调用 fetch_financial_report 获取该公司财报；不要因为"参考文档不为空"就跳过调用
4. 收集到足够信息后，尽快生成最终分析报告，不要继续调用工具
5. 初始检索结果只作为候选上下文；如果用户明确提到具体公司、股票代码或指定财报，必须核实参考文档来源中是否包含该公司，若无则立即调用 fetch_financial_report
6. 当 fetch_financial_report 返回 document_id 时，后续 search_vector_store 必须优先传入 document_ids，在对应财报内定向检索

## 量化回测能力（run_backtest）
你能将用户的**任意交易想法**翻译为量化策略并回测。以下场景应主动调用 run_backtest：
- 用户描述具体买卖逻辑（"5日线上穿20日线就买"、"RSI低于30抄底"）
- 用户问某只股票适不适合某种策略（"茅台用MACD策略效果怎样"）
- 用户问个股技术面分析时，**主动附带一个经典策略的回测结果**作为技术面参考
- 用户说"帮我回测"、"测一下"等

**翻译原则：**
1. 把用户的自然语言拆解为 buy_conditions + sell_conditions
2. 不确定参数时用行业惯例默认值（如均线 5/20、RSI 14/30/70）
3. 用户说"均线策略"但没说哪根线，默认用 sma(5) cross_above/cross_below sma(20)
4. 用户说的策略不完整（只说了买没说卖），合理补全卖出条件

**结果解读原则（重要）：**
- 客观陈述回测数据：总收益、年化、夏普、最大回撤、交易频率
- 结果不理想时**如实说明**，不要美化或归因于用户。例如："该策略在此标的上年化收益为负，夏普比率低于0.5，表现不佳"就是合适的表述
- 分析策略本身的局限性（如趋势策略在震荡市失效、均值回归策略在单边行情中亏损），而非暗示用户选错了
- 可以客观建议尝试其他参数或策略方向，但不要过度承诺

**展示策略源码：**
回测结果中包含 strategy_code 字段，你**必须**在回复中展示策略逻辑，让用户看到 AI 是如何翻译他们的交易想法的。

**行业/板块多股回测：**
当用户问的是行业或板块级别的问题（如"布林带策略对新能源汽车表现怎样"），你应该：
1. 根据你的金融知识，选出该行业当前 3-5 只代表性个股（含股票代码），简要说明选择理由
2. 对每只股票分别调用 run_backtest（使用相同策略条件）
3. 汇总对比各股表现，用表格展示
4. 给出行业级别的客观结论"""

    if context_text:
        system_prompt += f"""

## 参考文档内容
{context_text}"""
    else:
        system_prompt += """

## 注意
当前未检索到相关文档内容。你可以基于你的金融专业知识回答，但需明确标注"以下为AI通用知识回答，未基于用户文档"。"""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query}
    ]


def _extract_interaction_json(text: str):
    """从 LLM 输出末尾提取结构化交互 JSON（如果有）。
    支持两种格式：
    1. ```json { "interaction": {...} } ```
    2. 裸 JSON: { "interaction": {...} }
    """
    import re
    stripped = text.strip()

    # 尝试1: ```json 代码块包裹
    pattern1 = r'```json\s*(\{[\s\S]*?"interaction"[\s\S]*?\})\s*```\s*$'
    match = re.search(pattern1, stripped)
    if match:
        try:
            parsed = json.loads(match.group(1))
            if "interaction" in parsed:
                clean_text = text[:text.rfind(match.group(0))].rstrip()
                return clean_text, parsed["interaction"]
        except json.JSONDecodeError:
            pass

    # 尝试2: 裸 JSON（无代码块）
    pattern2 = r'(\{"interaction"\s*:\s*\{[\s\S]*\}\s*\})\s*$'
    match = re.search(pattern2, stripped)
    if match:
        try:
            parsed = json.loads(match.group(1))
            if "interaction" in parsed:
                clean_text = text[:text.rfind(match.group(1))].rstrip()
                return clean_text, parsed["interaction"]
        except json.JSONDecodeError:
            pass

    return text, None


# ---------- Agent Tools 定义 ----------

AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_vector_store",
            "description": "在用户的向量知识库中搜索相关文档内容。当需要查找已入库的财报、年报等文档信息时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询词，例如：'比亚迪2024年营收'"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "返回结果数量，默认6",
                        "default": 6
                    },
                    "document_ids": {
                        "type": "array",
                        "description": "可选。限定只在指定 document_id 对应的文档内检索。对比特定公司财报时必须优先传入。",
                        "items": {
                            "type": "integer"
                        }
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_financial_report",
            "description": f"从巨潮资讯网抓取A股/港股上市公司的财报PDF，自动解析并向量化入库。调用前会先检查向量库是否已有该公司财报，已有则跳过下载。当用户提到具体公司名或股票代码、需要财报数据分析时调用。当前日期{datetime.now().strftime('%Y-%m-%d')}，请根据财报披露时间规律智能判断 year 和 quarter。不确定时不要指定 quarter，留空由系统自动查找最新可用报告。",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "公司名称，如'比亚迪'、'贵州茅台'"
                    },
                    "stock_code": {
                        "type": "string",
                        "description": "股票代码，如'002594'、'600519'、'00700'"
                    },
                    "year": {
                        "type": "integer",
                        "description": f"财报年份。请根据当前日期({datetime.now().strftime('%Y-%m-%d')})和财报披露时间规律判断，传入最可能已发布的财报年份"
                    },
                    "quarter": {
                        "type": "string",
                        "description": "季度(Q1/Q2/Q3/Q4/H1)，不指定则自动选择最新可用报告",
                        "enum": ["Q1", "Q2", "Q3", "Q4", "H1"]
                    }
                },
                "required": ["company_name", "stock_code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_backtest",
            "description": """执行量化回测。将用户描述的任意交易策略翻译为买入/卖出条件并运行历史回测。

## 条件格式
每个条件是 {"left": "指标表达式", "op": "运算符", "right": "指标表达式或数字"}

## 可用指标表达式
- price: 当前收盘价
- sma(N): N日简单均线，如 sma(5), sma(20), sma(60)
- ema(N): N日指数均线
- rsi(N): N日RSI指标，如 rsi(14)
- macd(): MACD线(DIF)
- macd_signal(): MACD信号线(DEA)
- boll_upper(N): N日布林带上轨
- boll_lower(N): N日布林带下轨
- boll_mid(N): N日布林带中轨
- volume: 成交量
- volume_ma(N): N日均量

## 可用运算符
- ">", "<", ">=", "<=": 比较
- "cross_above": 左侧从下方穿越右侧（金叉）
- "cross_below": 左侧从上方穿越右侧（死叉）

## 翻译示例
用户说"5日线上穿20日线买入，下穿卖出":
  buy_conditions: [{"left":"sma(5)","op":"cross_above","right":"sma(20)"}]
  sell_conditions: [{"left":"sma(5)","op":"cross_below","right":"sma(20)"}]

用户说"RSI低于30买入，高于70卖出":
  buy_conditions: [{"left":"rsi(14)","op":"<","right":"30"}]
  sell_conditions: [{"left":"rsi(14)","op":">","right":"70"}]

用户说"价格跌破布林带下轨且成交量放大时买入":
  buy_conditions: [{"left":"price","op":"<","right":"boll_lower(20)"},{"left":"volume","op":">","right":"volume_ma(20)"}]
  buy_logic: "all"

用户说"MACD金叉买入，死叉卖出":
  buy_conditions: [{"left":"macd()","op":"cross_above","right":"macd_signal()"}]
  sell_conditions: [{"left":"macd()","op":"cross_below","right":"macd_signal()"}]""",
            "parameters": {
                "type": "object",
                "properties": {
                    "ts_code": {
                        "type": "string",
                        "description": "股票代码(Tushare格式)，如 600519.SH(沪市) 或 000001.SZ(深市)"
                    },
                    "stock_name": {
                        "type": "string",
                        "description": "股票名称，如'贵州茅台'"
                    },
                    "strategy_name": {
                        "type": "string",
                        "description": "用户策略的简短描述，如'双均线金叉死叉'、'RSI超卖反弹+放量确认'"
                    },
                    "buy_conditions": {
                        "type": "array",
                        "description": "买入条件列表",
                        "items": {
                            "type": "object",
                            "properties": {
                                "left": {"type": "string"},
                                "op": {"type": "string", "enum": [">", "<", ">=", "<=", "cross_above", "cross_below"]},
                                "right": {"type": "string"}
                            },
                            "required": ["left", "op", "right"]
                        }
                    },
                    "sell_conditions": {
                        "type": "array",
                        "description": "卖出条件列表",
                        "items": {
                            "type": "object",
                            "properties": {
                                "left": {"type": "string"},
                                "op": {"type": "string", "enum": [">", "<", ">=", "<=", "cross_above", "cross_below"]},
                                "right": {"type": "string"}
                            },
                            "required": ["left", "op", "right"]
                        }
                    },
                    "buy_logic": {
                        "type": "string",
                        "description": "多个买入条件间的逻辑关系: all=全部满足(AND), any=任一满足(OR)，默认all",
                        "enum": ["all", "any"]
                    },
                    "sell_logic": {
                        "type": "string",
                        "description": "多个卖出条件间的逻辑关系: all=全部满足(AND), any=任一满足(OR)，默认all",
                        "enum": ["all", "any"]
                    },
                    "start_date": {
                        "type": "string",
                        "description": "回测起始日期 YYYY-MM-DD，默认近3年"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "回测结束日期 YYYY-MM-DD，默认今天"
                    },
                    "initial_cash": {
                        "type": "number",
                        "description": "初始资金(元)，默认100000"
                    }
                },
                "required": ["ts_code", "stock_name", "buy_conditions", "sell_conditions"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "portfolio_trade",
            "description": "记录用户的虚拟买入/卖出操作。当用户说'买入XX股某某股票'或'卖出'时调用。系统会自动计算A股佣金和印花税。价格如果用户没说，请使用最新收盘价（可先联网搜索）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "ts_code": {
                        "type": "string",
                        "description": "股票代码(Tushare格式)，如 000001.SZ、600519.SH"
                    },
                    "stock_name": {
                        "type": "string",
                        "description": "股票名称"
                    },
                    "direction": {
                        "type": "string",
                        "description": "buy(买入) 或 sell(卖出)",
                        "enum": ["buy", "sell"]
                    },
                    "price": {
                        "type": "number",
                        "description": "成交价格(元)。用户未指定则使用最新收盘价"
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "交易数量(股)。A股最小交易单位100股"
                    },
                    "trade_date": {
                        "type": "string",
                        "description": "成交日期 YYYY-MM-DD，默认今天"
                    }
                },
                "required": ["ts_code", "stock_name", "direction", "price", "quantity"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "portfolio_query",
            "description": "查询用户的虚拟持仓情况。当用户问'我的持仓怎么样'、'我买了什么股票'、'我的收益如何'时调用。返回所有持仓的成本、数量、盈亏等信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "include_prices": {
                        "type": "boolean",
                        "description": "是否获取最新价格计算浮动盈亏，默认true",
                        "default": True
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "builtin_function",
        "function": {"name": "$web_search"},
    }
]


async def _execute_tool(tool_name: str, tool_args: dict, user_id: int, db=None,
                        progress_queue: asyncio.Queue = None) -> str:
    """执行 agent tool 调用，返回结果字符串。
    progress_queue: 可选，用于向调用方实时推送进度消息（str）。
    """

    if tool_name == "search_vector_store":
        query = tool_args.get("query", "")
        top_k = tool_args.get("top_k", 6)
        document_ids = _normalize_int_list(tool_args.get("document_ids"))
        try:
            results = await retrieve(
                query,
                user_id,
                top_k=top_k,
                document_ids=document_ids,
                raise_on_error=True,
            )
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"知识库检索失败: {str(e)}",
                "document_ids": document_ids or []
            }, ensure_ascii=False)
        if not results:
            return json.dumps({
                "status": "empty",
                "message": "未找到相关文档内容。用户可能尚未上传相关财报。",
                "document_ids": document_ids or []
            }, ensure_ascii=False)
        # 精简返回给模型
        simplified = []
        for r in results:
            simplified.append({
                "text": r["text"][:500],
                "source": r["source"],
                "page": r["page_number"],
                "score": r["score"],
                "is_table": r.get("is_table", False),
                "document_id": r.get("document_id")
            })
        return json.dumps({
            "status": "ok",
            "count": len(simplified),
            "results": simplified,
            "sources": _build_source_refs(results),
            "document_ids": document_ids or []
        }, ensure_ascii=False)

    elif tool_name == "fetch_financial_report":
        company_name = tool_args.get("company_name", "")
        stock_code = tool_args.get("stock_code", "")
        quarter = tool_args.get("quarter")
        
        # 添加调试信息
        print(f"[DEBUG] fetch_financial_report 调用参数: {tool_args}")
        
        # 智能推断年份：如果模型没传 year，根据当前月份判断最新可用财报年份
        if "year" in tool_args and tool_args["year"]:
            year = tool_args["year"]
        else:
            now = datetime.now()
            # 1-4月：上一年年报正在披露，优先拿上一年
            # 5月后：当年Q1已出，但年报仍是上一年最完整的
            year = now.year - 1 if now.month <= 4 else now.year

        print(f"[DEBUG] 最终使用参数: company_name={company_name}, stock_code={stock_code}, year={year}, quarter={quarter}")

        if not stock_code:
            return json.dumps({"status": "error", "message": "缺少股票代码"}, ensure_ascii=False)

        # 先查向量库是否已有
        existing = list_indexed_documents(user_id)
        for doc in existing:
            src = doc.get("source", "")
            if stock_code in src and str(year) in src:
                matched_doc = _find_document_record(
                    db,
                    user_id,
                    source_name=src,
                    stock_code=stock_code,
                    company_name=company_name,
                    year=year,
                )
                return json.dumps({
                    "status": "already_exists",
                    "message": f"向量库中已有 {src}（{doc.get('count', 0)} 个向量块），无需重新下载。请直接使用 search_vector_store 检索。",
                    "source": src,
                    "chunks": doc.get("count", 0),
                    "document_id": matched_doc.id if matched_doc else None
                }, ensure_ascii=False)

        # 没有则下载
        try:
            from report.simple_service import SimplifiedReportService
            report_service = SimplifiedReportService()
            print(f"[DEBUG] 开始调用 download_report_from_cninfo...")
            pdf_path = await report_service.download_report_from_cninfo(
                stock_code, company_name, year, quarter
            )
            print(f"[DEBUG] download_report_from_cninfo 返回: {pdf_path}")
            await report_service.close()

            if not pdf_path:
                print(f"[DEBUG] 下载失败，返回failed状态")
                return json.dumps({"status": "failed", "message": f"未能从巨潮资讯网找到 {company_name}({stock_code}) {year}年的财报"}, ensure_ascii=False)

            # 入库 Document 记录
            doc_record = None
            if db:
                from core.database import Document
                existing_doc = db.query(Document).filter(
                    Document.user_id == user_id,
                    Document.pdf_path == pdf_path
                ).first()
                if existing_doc:
                    doc_record = existing_doc
                    doc_record.company = company_name
                    doc_record.stock_code = stock_code
                    doc_record.year = year
                else:
                    doc_record = Document(
                        user_id=user_id,
                        source='cninfo',
                        title=f"{company_name} {year}年财报",
                        company=company_name,
                        stock_code=stock_code,
                        year=year,
                        pdf_path=pdf_path
                    )
                    db.add(doc_record)
                db.commit()
                db.refresh(doc_record)

            # 向量化入库
            doc_id = doc_record.id if doc_record else None

            async def _ingest_progress(msg: str):
                if progress_queue:
                    await progress_queue.put(msg)

            ingest_result = await ingest_pdf(pdf_path, user_id, document_id=doc_id,
                                             progress_callback=_ingest_progress)

            if ingest_result.get("status") == "error":
                return json.dumps({"status": "error", "message": f"PDF解析入库失败: {ingest_result.get('message')}"}, ensure_ascii=False)

            return json.dumps({
                "status": "success",
                "message": f"已成功下载并入库 {company_name}({stock_code}) {year}年财报，共 {ingest_result.get('chunks', 0)} 个向量块。现在可以使用 search_vector_store 检索其中的内容。",
                "pdf_path": pdf_path,
                "chunks": ingest_result.get("chunks", 0),
                "document_id": doc_id
            }, ensure_ascii=False)

        except Exception as e:
            traceback.print_exc()
            return json.dumps({"status": "error", "message": f"财报抓取失败: {str(e)}"}, ensure_ascii=False)

    elif tool_name == "run_backtest":
        def _conditions_to_code(buy_conds, sell_conds, buy_logic="all", sell_logic="all"):
            """将条件 JSON 翻译为可读的策略伪代码"""
            OP_MAP = {
                ">": ">", "<": "<", ">=": ">=", "<=": "<=",
                "cross_above": "上穿 ↑", "cross_below": "下穿 ↓",
            }
            EXPR_MAP = {
                "price": "收盘价", "volume": "成交量",
            }
            import re as _r
            def _fmt(expr):
                expr = expr.strip()
                if expr in EXPR_MAP:
                    return EXPR_MAP[expr]
                m = _r.match(r'^(\w+)\(([^)]*)\)$', expr)
                if m:
                    n, a = m.group(1).lower(), m.group(2)
                    names = {"sma": "SMA均线", "ema": "EMA均线", "rsi": "RSI",
                             "macd": "MACD(DIF)", "macd_signal": "MACD信号线(DEA)",
                             "boll_upper": "布林带上轨", "boll_lower": "布林带下轨",
                             "boll_mid": "布林带中轨", "volume_ma": "均量"}
                    label = names.get(n, n.upper())
                    return f"{label}({a})" if a else label
                try:
                    float(expr)
                    return expr
                except ValueError:
                    return expr

            def _fmt_cond(c):
                return f"{_fmt(c['left'])} {OP_MAP.get(c['op'], c['op'])} {_fmt(c['right'])}"

            logic_cn = {"all": "且(AND)", "any": "或(OR)"}
            lines = ["# 策略逻辑"]
            joiner_buy = " 且 " if buy_logic == "all" else " 或 "
            joiner_sell = " 且 " if sell_logic == "all" else " 或 "
            buy_str = joiner_buy.join([_fmt_cond(c) for c in buy_conds])
            sell_str = joiner_sell.join([_fmt_cond(c) for c in sell_conds])
            lines.append(f"买入条件: {buy_str}")
            lines.append(f"卖出条件: {sell_str}")
            return "\n".join(lines)

        try:
            from backtest.engine import run_backtest as _run_backtest
            from backtest.strategies import FlexibleStrategy
            ts_code = tool_args.get("ts_code", "")
            stock_name = tool_args.get("stock_name", "")
            strategy_name = tool_args.get("strategy_name", "自定义策略")
            buy_conditions = tool_args.get("buy_conditions", [])
            sell_conditions = tool_args.get("sell_conditions", [])
            buy_logic = tool_args.get("buy_logic", "all")
            sell_logic = tool_args.get("sell_logic", "all")
            start_date = tool_args.get("start_date", "")
            end_date = tool_args.get("end_date", "")
            initial_cash = tool_args.get("initial_cash", 100000)

            # 默认近3年
            if not start_date:
                from datetime import timedelta
                start_date = (datetime.now() - timedelta(days=365*3)).strftime("%Y-%m-%d")

            if not ts_code:
                return json.dumps({"status": "error", "message": "缺少股票代码 ts_code"}, ensure_ascii=False)
            if not buy_conditions or not sell_conditions:
                return json.dumps({"status": "error", "message": "缺少买入或卖出条件"}, ensure_ascii=False)

            # 构建条件描述用于日志
            cond_desc = f"买入: {json.dumps(buy_conditions, ensure_ascii=False)}, 卖出: {json.dumps(sell_conditions, ensure_ascii=False)}"
            print(f"[Backtest] {stock_name}({ts_code}) 策略: {strategy_name}, {cond_desc}")

            if progress_queue:
                await progress_queue.put(f"正在回测 {stock_name}({ts_code})「{strategy_name}」...")

            strategy_params = {
                "buy_conditions": buy_conditions,
                "sell_conditions": sell_conditions,
                "buy_logic": buy_logic,
                "sell_logic": sell_logic,
            }

            # 在线程池执行（CPU阻塞操作）
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: _run_backtest(
                    ts_code=ts_code,
                    strategy_cls=FlexibleStrategy,
                    params=strategy_params,
                    start_date=start_date,
                    end_date=end_date,
                    initial_cash=initial_cash,
                )
            )

            # 生成可读策略代码
            strategy_code = _conditions_to_code(buy_conditions, sell_conditions, buy_logic, sell_logic)

            # 精简返回给模型（equity_curve太长，只给统计摘要 + 前5笔交易）
            summary = result.get("summary", {})
            trades = result.get("trades", [])
            return json.dumps({
                "status": "ok",
                "stock": f"{stock_name}({ts_code})",
                "strategy_name": strategy_name,
                "strategy_code": strategy_code,
                "period": f"{start_date} ~ {end_date or '至今'}",
                "summary": summary,
                "sample_trades": trades[:5],
                "total_trades": len(trades),
            }, ensure_ascii=False)

        except Exception as e:
            traceback.print_exc()
            return json.dumps({"status": "error", "message": f"回测执行失败: {str(e)}"}, ensure_ascii=False)

    elif tool_name == "portfolio_trade":
        try:
            from portfolio.service import add_transaction
            from core.database import SessionLocal
            trade_db = db if db else SessionLocal()
            try:
                result = add_transaction(
                    db=trade_db,
                    user_id=user_id,
                    ts_code=tool_args.get("ts_code", ""),
                    stock_name=tool_args.get("stock_name", ""),
                    direction=tool_args.get("direction", "buy"),
                    price=float(tool_args.get("price", 0)),
                    quantity=int(tool_args.get("quantity", 0)),
                    trade_date=tool_args.get("trade_date", ""),
                    notes=tool_args.get("notes", ""),
                )
                return json.dumps(result, ensure_ascii=False)
            finally:
                if not db:
                    trade_db.close()
        except Exception as e:
            traceback.print_exc()
            return json.dumps({"status": "error", "message": f"交易记录失败: {str(e)}"}, ensure_ascii=False)

    elif tool_name == "portfolio_query":
        try:
            from portfolio.service import get_portfolio_summary
            from core.database import SessionLocal
            query_db = db if db else SessionLocal()
            try:
                # 获取实时价格
                current_prices = {}
                include_prices = tool_args.get("include_prices", True)
                if include_prices:
                    try:
                        from portfolio.service import calc_positions
                        from backtest.data_store import fetch_daily
                        positions = calc_positions(query_db, user_id)
                        codes = [c for c, p in positions.items() if p["quantity"] > 0]
                        for code in codes:
                            try:
                                df = await asyncio.get_event_loop().run_in_executor(
                                    None, lambda c=code: fetch_daily(c, start_date="2025-01-01")
                                )
                                if len(df) > 0:
                                    current_prices[code] = float(df["close"].iloc[-1])
                            except Exception:
                                pass
                    except Exception as price_err:
                        print(f"[Portfolio] 获取价格失败: {price_err}")

                summary = get_portfolio_summary(query_db, user_id, current_prices=current_prices or None)
                return json.dumps(summary, ensure_ascii=False)
            finally:
                if not db:
                    query_db.close()
        except Exception as e:
            traceback.print_exc()
            return json.dumps({"status": "error", "message": f"持仓查询失败: {str(e)}"}, ensure_ascii=False)

    else:
        return json.dumps({"error": f"未知工具: {tool_name}"}, ensure_ascii=False)


# ---------- RAG Agent 对话（流式 + function calling） ----------

async def rag_chat_stream(
    query: str,
    user_id: int,
    top_k: int = 6,
    document_ids: List[int] = None,
    style: str = "专业分析",
    user_role: str = None,
    conversation_history: List[Dict] = None,
    db=None
):
    """
    RAG Agent 对话（异步生成器，yield SSE 格式字符串）。

    使用 Kimi k2.5 + function calling：
    - search_vector_store: 检索向量库
    - fetch_financial_report: 从巨潮下载财报并入库
    - $web_search: Kimi 内置联网搜索

    流程：构建 prompt → Kimi 流式对话 → 处理 tool_calls → 继续对话 → yield 文本
    """
    # 1. 先检索向量库，将结果作为初始上下文
    yield f"data: {json.dumps({'type': 'phase', 'content': '正在检索相关文档...'}, ensure_ascii=False)}\n\n"

    chunks = await retrieve(query, user_id, top_k=top_k, document_ids=document_ids)

    # 断路器感知：is_relevant=False 表示 Reranker 判定库中无相关内容
    _is_relevant = all(c.get("is_relevant", True) for c in chunks) if chunks else True
    if not _is_relevant:
        chunks = []  # 不把无关内容塞进上下文，避免幻觉
        yield f"data: {json.dumps({'type': 'phase', 'content': '⚠️ 知识库中未检索到相关内容，将结合联网搜索补充'}, ensure_ascii=False)}\n\n"

    if chunks:
        sources = [{"source": c["source"], "page_number": c["page_number"], "score": c["score"]} for c in chunks]
        yield f"data: {json.dumps({'type': 'sources', 'sources': sources}, ensure_ascii=False)}\n\n"
    else:
        # 知识库为空时，显式告知前端检索结果为空
        yield f"data: {json.dumps({'type': 'sources', 'sources': []}, ensure_ascii=False)}\n\n"

    # 2. 构建 prompt（带初始检索结果）
    yield f"data: {json.dumps({'type': 'phase', 'content': 'AI 正在分析...'}, ensure_ascii=False)}\n\n"

    messages = _build_rag_prompt(query, chunks, style, user_role=user_role, has_context=bool(chunks))
    preferred_document_ids = _normalize_int_list(document_ids) or []

    # 插入历史对话
    if conversation_history:
        history_messages = []
        for h in conversation_history[-6:]:
            if h.get("role") in ("user", "assistant"):
                history_messages.append({"role": h["role"], "content": h["content"]})
        if history_messages:
            messages = [messages[0]] + history_messages + [messages[-1]]

    # 3. Kimi 流式对话 + function calling 循环
    full_content = ""
    streamed_content = ""  # 实际流式发送给前端的文本
    json_tail_buffer = ""  # 缓冲可能的 interaction JSON 尾部
    json_intercepting = False  # 是否正在拦截 JSON 尾部
    max_rounds = KIMI_MAX_ROUNDS

    try:
        for _round in range(max_rounds):
            # 流式请求（带重试机制）
            retry_count = 0
            max_retries = 3
            retry_delay = 2  # 秒
            
            while retry_count <= max_retries:
                try:
                    stream = await _kimi_async_client.chat.completions.create(
                        model=LLM_MODEL,
                        messages=messages,
                        tools=AGENT_TOOLS,
                        temperature=KIMI_TEMPERATURE,
                        max_tokens=KIMI_MAX_TOKENS,
                        stream=True,
                        extra_body={"thinking": {"type": "disabled"}},
                    )
                    break  # 成功则跳出重试循环
                except Exception as e:
                    if "engine_overloaded" in str(e).lower() and retry_count < max_retries:
                        retry_count += 1
                        print(f"[RAG] 模型过载，{retry_delay}秒后重试 ({retry_count}/{max_retries})")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # 指数退避
                    else:
                        raise e  # 非过载错误或重试次数用完，直接抛出

            # 收集 tool_calls 碎片
            collected_tool_calls = {}
            is_tool_call = False
            round_content = ""
            round_streamed = 0  # 本轮已流式输出的字符数

            async for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                finish = chunk.choices[0].finish_reason

                # 收集 tool_calls
                if delta and delta.tool_calls:
                    is_tool_call = True
                    for tc_delta in delta.tool_calls:
                        idx = tc_delta.index
                        if idx not in collected_tool_calls:
                            collected_tool_calls[idx] = {
                                "id": tc_delta.id or "",
                                "name": tc_delta.function.name if tc_delta.function and tc_delta.function.name else "",
                                "arguments": "",
                            }
                        if tc_delta.id:
                            collected_tool_calls[idx]["id"] = tc_delta.id
                        if tc_delta.function:
                            if tc_delta.function.name:
                                collected_tool_calls[idx]["name"] = tc_delta.function.name
                            if tc_delta.function.arguments:
                                collected_tool_calls[idx]["arguments"] += tc_delta.function.arguments

                # content delta 处理
                if delta and delta.content:
                    round_content += delta.content

                    # 如果已检测到 tool_calls，不输出 content（中间思考）
                    if is_tool_call:
                        continue

                    # 未检测到 tool_calls → 逐步流式输出（拦截尾部 interaction JSON）
                    full_content += delta.content
                    if json_intercepting:
                        json_tail_buffer += delta.content
                    else:
                        pending = json_tail_buffer + delta.content
                        json_start = -1
                        for marker in ['```json', '{"interaction"']:
                            pos = pending.find(marker)
                            if pos != -1 and (json_start == -1 or pos < json_start):
                                json_start = pos
                        if json_start != -1:
                            before = pending[:json_start].rstrip()
                            if before:
                                streamed_content += before
                                round_streamed += len(before)
                                yield f"data: {json.dumps({'type': 'text', 'text': before}, ensure_ascii=False)}\n\n"
                            json_tail_buffer = pending[json_start:]
                            json_intercepting = True
                            yield f"data: {json.dumps({'type': 'phase', 'content': '正在生成进一步建议...'}, ensure_ascii=False)}\n\n"
                        elif '`' in pending or '{' in pending:
                            safe_len = max(0, len(pending) - 15)
                            if safe_len > 0:
                                safe_text = pending[:safe_len]
                                streamed_content += safe_text
                                round_streamed += len(safe_text)
                                yield f"data: {json.dumps({'type': 'text', 'text': safe_text}, ensure_ascii=False)}\n\n"
                                json_tail_buffer = pending[safe_len:]
                            else:
                                json_tail_buffer = pending
                        else:
                            streamed_content += pending
                            round_streamed += len(pending)
                            yield f"data: {json.dumps({'type': 'text', 'text': pending}, ensure_ascii=False)}\n\n"
                            json_tail_buffer = ""

            # 本轮结束后处理
            if is_tool_call and round_content:
                if round_streamed > 0:
                    # 极少见：先输出了 content 后才出现 tool_calls，已无法撤回
                    print(f"[RAG-Agent] 警告: tool_call 轮次已泄漏 {round_streamed} chars（无法撤回）")
                else:
                    print(f"[RAG-Agent] 跳过 tool_call 轮次中间文本 ({len(round_content)} chars)")

            # 处理 tool_calls
            if is_tool_call and collected_tool_calls:
                tc_list = []
                for idx in sorted(collected_tool_calls.keys()):
                    tc = collected_tool_calls[idx]
                    tc_list.append({
                        "id": tc["id"],
                        "type": "function",
                        "function": {"name": tc["name"], "arguments": tc["arguments"]},
                    })

                messages.append({"role": "assistant", "content": round_content or None, "tool_calls": tc_list})

                for tc in tc_list:
                    fn_name = tc["function"]["name"]
                    raw_args = tc["function"].get("arguments") or "{}"
                    try:
                        fn_args = json.loads(raw_args)
                    except json.JSONDecodeError:
                        fn_args = {}

                    print(f"[RAG-Agent] Tool call round {_round+1}: {fn_name}({json.dumps(fn_args, ensure_ascii=False)})")

                    # yield tool_call 事件（暴露完整的 function calling JSON）
                    yield f"data: {json.dumps({'type': 'tool_call', 'tool_call_id': tc['id'], 'function': fn_name, 'arguments': fn_args, 'round': _round + 1}, ensure_ascii=False)}\n\n"

                    # $web_search 由 Kimi 内部处理
                    if fn_name == "$web_search":
                        yield f"data: {json.dumps({'type': 'phase', 'content': '正在联网搜索...'}, ensure_ascii=False)}\n\n"
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "name": fn_name,
                            # Kimi 内置 $web_search：把 tool_call.function.arguments 原封不动回传即可触发搜索
                            "content": raw_args,
                        })
                    else:
                        if fn_name == "search_vector_store" and preferred_document_ids and not _normalize_int_list(fn_args.get("document_ids")):
                            fn_args["document_ids"] = preferred_document_ids.copy()

                        # 自定义 tool — 发送详细 phase 事件
                        _cn = fn_args.get('company_name', '')
                        _yr = fn_args.get('year', datetime.now().year)
                        _q = fn_args.get('query', '')[:30]

                        if fn_name == "search_vector_store":
                            _phase = json.dumps({'type': 'phase', 'content': '正在检索知识库: "' + _q + '"'}, ensure_ascii=False)
                            yield f"data: {_phase}\n\n"
                        elif fn_name == "fetch_financial_report":
                            _phase = json.dumps({'type': 'phase', 'content': '正在检查' + _cn + str(_yr) + '年财报是否已入库...'}, ensure_ascii=False)
                            yield f"data: {_phase}\n\n"
                        elif fn_name == "run_backtest":
                            _sn = fn_args.get('stock_name', '') or fn_args.get('ts_code', '')
                            _st = fn_args.get('strategy_name', '自定义策略')
                            _phase = json.dumps({'type': 'phase', 'content': f'正在回测 {_sn}「{_st}」...'}, ensure_ascii=False)
                            yield f"data: {_phase}\n\n"
                        else:
                            yield f"data: {json.dumps({'type': 'phase', 'content': '正在处理...'}, ensure_ascii=False)}\n\n"

                        # 使用 progress_queue 在工具执行期间实时推送进度
                        _pq = asyncio.Queue()
                        _tool_task = asyncio.create_task(
                            _execute_tool(fn_name, fn_args, user_id, db=db, progress_queue=_pq)
                        )
                        # 轮询：每 0.3s 检查队列中的进度消息，直到任务完成
                        while not _tool_task.done():
                            try:
                                _progress_msg = await asyncio.wait_for(_pq.get(), timeout=0.3)
                                yield f"data: {json.dumps({'type': 'phase', 'content': _progress_msg}, ensure_ascii=False)}\n\n"
                            except asyncio.TimeoutError:
                                pass
                        # 任务完成后排空队列
                        while not _pq.empty():
                            _leftover = _pq.get_nowait()
                            yield f"data: {json.dumps({'type': 'phase', 'content': _leftover}, ensure_ascii=False)}\n\n"
                        tool_result = _tool_task.result()
                        try:
                            print(f"[RAG-Agent] Tool result: {tool_result[:200]}...")
                        except Exception:
                            print(f"[RAG-Agent] Tool result: (非文本内容，无法打印)")

                        # 根据结果发送详细 phase
                        try:
                            tr = json.loads(tool_result)
                            _st = tr.get("status", "")
                            _chunks = tr.get("chunks", 0)
                            _count = tr.get("count", 0)
                            _doc_ids = _normalize_int_list(tr.get("document_ids")) or []
                            if tr.get("document_id") is not None:
                                _doc_ids = _normalize_int_list(_doc_ids + [tr.get("document_id")]) or []

                            if fn_name == "fetch_financial_report":
                                if _st == "already_exists":
                                    _msg = '✓ 知识库已有' + _cn + '财报（' + str(_chunks) + '个向量块）'
                                    yield f"data: {json.dumps({'type': 'phase', 'content': _msg}, ensure_ascii=False)}\n\n"
                                elif _st == "success":
                                    _msg = '✓ 已下载并入库' + _cn + '财报（' + str(_chunks) + '个向量块）'
                                    yield f"data: {json.dumps({'type': 'phase', 'content': _msg}, ensure_ascii=False)}\n\n"
                                    yield f"data: {json.dumps({'type': 'report_ready', 'company': _cn, 'year': _yr, 'stock_code': fn_args.get('stock_code'), 'pdf_path': tr.get('pdf_path'), 'document_id': tr.get('document_id'), 'message': tr.get('message')}, ensure_ascii=False)}\n\n"
                                elif _st == "failed":
                                    _msg = '✗ 未找到' + _cn + '的财报'
                                    yield f"data: {json.dumps({'type': 'phase', 'content': _msg}, ensure_ascii=False)}\n\n"
                                elif _st == "error":
                                    _msg = '✗ ' + (tr.get("message") or ('处理' + _cn + '财报失败'))
                                    yield f"data: {json.dumps({'type': 'phase', 'content': _msg}, ensure_ascii=False)}\n\n"

                                if _st in {"already_exists", "success"} and _doc_ids:
                                    for doc_id in _doc_ids:
                                        if doc_id not in preferred_document_ids:
                                            preferred_document_ids.append(doc_id)
                            elif fn_name == "search_vector_store":
                                if _st == "ok":
                                    _msg = '✓ 检索到 ' + str(_count) + ' 条相关内容'
                                    yield f"data: {json.dumps({'type': 'phase', 'content': _msg}, ensure_ascii=False)}\n\n"
                                    if tr.get("sources"):
                                        yield f"data: {json.dumps({'type': 'sources', 'sources': tr.get('sources')}, ensure_ascii=False)}\n\n"
                                else:
                                    _msg = '✗ ' + (tr.get("message") or '知识库中未找到相关内容')
                                    yield f"data: {json.dumps({'type': 'phase', 'content': _msg}, ensure_ascii=False)}\n\n"
                        except Exception:
                            pass

                        # yield tool_result 事件（暴露完整的工具返回 JSON）
                        try:
                            _tr_json = json.loads(tool_result)
                        except Exception:
                            _tr_json = tool_result
                        yield f"data: {json.dumps({'type': 'tool_result', 'tool_call_id': tc['id'], 'function': fn_name, 'result': _tr_json}, ensure_ascii=False)}\n\n"

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "name": fn_name,
                            "content": tool_result,
                        })

                yield f"data: {json.dumps({'type': 'phase', 'content': 'AI 正在整合分析结果...'}, ensure_ascii=False)}\n\n"
                continue  # 继续下一轮对话

            # 非 tool_calls → 最终回复完成
            # 刷新缓冲区中未输出的非 JSON 文本
            if json_tail_buffer and not json_intercepting:
                streamed_content += json_tail_buffer
                yield f"data: {json.dumps({'type': 'text', 'text': json_tail_buffer}, ensure_ascii=False)}\n\n"
                json_tail_buffer = ""
            break

        # fallback: 如果轮次耗尽仍无有效文本输出给用户，强制生成最终回答
        if not streamed_content:
            yield f"data: {json.dumps({'type': 'phase', 'content': 'AI 正在生成最终分析报告...'}, ensure_ascii=False)}\n\n"
            messages.append({"role": "user", "content": "请立即基于上面所有已收集到的工具调用结果，生成完整的分析报告。不要再调用任何工具。"})
            fallback_stream = await _kimi_async_client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                temperature=KIMI_TEMPERATURE,
                max_tokens=KIMI_MAX_TOKENS,
                stream=True,
                extra_body={"thinking": {"type": "disabled"}},
            )
            async for chunk in fallback_stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    full_content += delta.content
                    streamed_content += delta.content
                    yield f"data: {json.dumps({'type': 'text', 'text': delta.content}, ensure_ascii=False)}\n\n"

    except Exception as e:
        traceback.print_exc()
        yield f"data: {json.dumps({'type': 'error', 'error': f'RAG Agent 生成失败: {str(e)}'})}\n\n"
        yield "data: [DONE]\n\n"
        return

    # 4. 后处理：从 full_content 提取结构化交互 JSON（不流式输出）
    _, interaction = _extract_interaction_json(full_content)
    if interaction:
        yield f"data: {json.dumps({'type': 'interaction', 'interaction': interaction}, ensure_ascii=False)}\n\n"

    # 5. 完成
    yield f"data: {json.dumps({'type': 'finish', 'data': {'total_length': len(streamed_content)}})}\n\n"
    yield "data: [DONE]\n\n"
    print(f"[RAG-Agent] 对话完成, 输出 {len(streamed_content)} 字符(full={len(full_content)}), 初始引用 {len(chunks)} 个文档块, 角色: {user_role or 'default'}")


# ---------- 文档管理 ----------

def get_document_stats(user_id: int) -> Dict:
    """获取用户向量库统计信息"""
    try:
        collection = _get_collection(user_id)
        count = collection.count()
        return {"status": "ok", "total_chunks": count}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def delete_document_vectors(user_id: int, source_name: str) -> Dict:
    """删除某个文档的所有向量"""
    try:
        collection = _get_collection(user_id)
        existing = collection.get(where={"source": source_name})
        if existing and existing["ids"]:
            collection.delete(ids=existing["ids"])
            return {"status": "ok", "deleted": len(existing["ids"])}
        return {"status": "ok", "deleted": 0, "message": "未找到该文档的向量"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def list_indexed_documents(user_id: int) -> List[Dict]:
    """列出用户已向量化的文档名及其块数"""
    try:
        collection = _get_collection(user_id)
        all_meta = collection.get(include=["metadatas"])
        source_counts = {}
        if all_meta and all_meta["metadatas"]:
            for meta in all_meta["metadatas"]:
                src = meta.get("source")
                if src:
                    source_counts[src] = source_counts.get(src, 0) + 1
        return sorted(
            [{"source": s, "count": c} for s, c in source_counts.items()],
            key=lambda x: x["source"]
        )
    except Exception:
        return []


def get_document_chunks(user_id: int, source_name: str, limit: Optional[int] = None) -> List[Dict]:
    try:
        collection = _get_collection(user_id)
        result = collection.get(where={"source": source_name}, include=["documents", "metadatas"])
        documents = result.get("documents") or []
        metadatas = result.get("metadatas") or []

        chunks = []
        for doc, meta in zip(documents, metadatas):
            chunks.append({
                "text": doc,
                "source": meta.get("source", source_name),
                "page_number": meta.get("page_number", 0),
                "chunk_index": meta.get("chunk_index", 0),
                "is_table": meta.get("is_table", False),
                "document_id": meta.get("document_id")
            })

        chunks.sort(key=lambda item: (item["page_number"], item["chunk_index"]))
        if limit is not None and limit > 0:
            return chunks[:limit]
        return chunks
    except Exception:
        return []
