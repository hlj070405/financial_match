"""
LangChain RAG 服务 - 替代 Dify 的 RAG Pipeline

核心功能：
  1. PDF 解析（PyMuPDF + pdfplumber 表格提取）
  2. 文本分块（滑动窗口 512 tokens, overlap 64）
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

import fitz  # PyMuPDF
import httpx
import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import (
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

    from database import Document

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


async def _get_embeddings(texts: List[str], api_key: str = None) -> List[List[float]]:
    """调用硅基流动 Embedding API（批量）"""
    key = api_key or DEEPSEEK_API_KEY
    if not key:
        raise ValueError("DEEPSEEK_API_KEY 未设置，无法调用 Embedding API")

    results = []
    for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
        batch = texts[i:i + EMBEDDING_BATCH_SIZE]
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{EMBEDDING_BASE_URL}/embeddings",
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": EMBEDDING_MODEL,
                    "input": batch,
                    "encoding_format": "float"
                }
            )
            if resp.status_code != 200:
                raise Exception(f"Embedding API 错误: {resp.status_code} - {resp.text}")
            data = resp.json()
            for item in sorted(data["data"], key=lambda x: x["index"]):
                results.append(item["embedding"])
    return results


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

def chunk_documents(pages: List[Dict]) -> List[Dict]:
    """
    将页面文本分块。
    使用 RecursiveCharacterTextSplitter（滑动窗口）。
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "。", "；", ".", ";", " ", ""],
        length_function=len,
    )

    chunks = []
    for page in pages:
        texts = splitter.split_text(page["text"])
        for i, text in enumerate(texts):
            chunk_id = hashlib.md5(f"{page['source']}:{page['page_number']}:{i}:{text[:50]}".encode()).hexdigest()
            chunks.append({
                "id": chunk_id,
                "text": text,
                "metadata": {
                    "source": page["source"],
                    "page_number": page["page_number"],
                    "chunk_index": i,
                    "is_table": page.get("is_table", False)
                }
            })

    return chunks


# ---------- 向量化入库 ----------

async def ingest_pdf(pdf_path: str, user_id: int, document_id: int = None) -> Dict:
    """
    完整的 PDF 入库流程：解析 → 分块 → 向量化 → 存入 ChromaDB

    Returns:
        {"status": "ok", "chunks": N, "document_id": ..., "source": ...}
    """
    full_path = _resolve_existing_pdf_path(pdf_path)

    if not os.path.exists(full_path):
        return {"status": "error", "message": f"文件不存在: {full_path}"}

    source_name = os.path.basename(full_path)
    print(f"[RAG] 开始处理: {source_name}")

    # 1. 解析 PDF
    pages = parse_pdf(full_path)
    if not pages:
        return {"status": "error", "message": "PDF 解析结果为空"}
    print(f"[RAG] 解析完成: {len(pages)} 页/段")

    # 2. 分块
    chunks = chunk_documents(pages)
    if not chunks:
        return {"status": "error", "message": "分块结果为空"}
    print(f"[RAG] 分块完成: {len(chunks)} 个块")

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

    # 5. 批量 Embedding + 写入
    batch_size = EMBEDDING_BATCH_SIZE
    total_written = 0
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        texts = [c["text"] for c in batch]
        ids = [c["id"] for c in batch]
        metadatas = []
        for c in batch:
            meta = dict(c["metadata"])
            if document_id is not None:
                meta["document_id"] = document_id
            # ChromaDB metadata 只能存 str/int/float/bool
            meta["page_number"] = int(meta["page_number"])
            meta["chunk_index"] = int(meta["chunk_index"])
            meta["is_table"] = bool(meta.get("is_table", False))
            metadatas.append(meta)

        try:
            embeddings = await _get_embeddings(texts)
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )
            total_written += len(batch)
            print(f"[RAG] 写入进度: {total_written}/{len(chunks)}")
        except Exception as e:
            print(f"[RAG] 批次写入失败: {e}")
            traceback.print_exc()

    print(f"[RAG] ✅ 入库完成: {source_name}, {total_written} 个块")
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
                   raise_on_error: bool = False) -> List[Dict]:
    """
    从用户的向量库中检索相关文档块。

    Args:
        query: 用户问题
        user_id: 用户ID
        top_k: 返回Top-K结果
        document_ids: 可选，限定在特定文档内检索

    Returns:
        [{"text": ..., "source": ..., "page_number": ..., "score": ...}, ...]
    """
    collection = _get_collection(user_id)

    # 构建 where 过滤条件
    where_filter = None
    if document_ids and len(document_ids) > 0:
        if len(document_ids) == 1:
            where_filter = {"document_id": document_ids[0]}
        else:
            where_filter = {"document_id": {"$in": document_ids}}

    try:
        # 获取查询 embedding
        query_embedding = await _get_embeddings([query])

        query_limit = top_k
        if file_types or sort_by != "score_desc":
            query_limit = min(max(top_k * 5, top_k), 100)

        results = collection.query(
            query_embeddings=query_embedding,
            n_results=query_limit,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )
    except Exception as e:
        print(f"[RAG] 检索失败: {e}")
        traceback.print_exc()
        if raise_on_error:
            raise
        return []

    if not results or not results["documents"] or not results["documents"][0]:
        return []

    retrieved = []
    filtered_count = 0
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        # ChromaDB cosine distance: 0 = 完全相同, 2 = 完全不同
        # 转换为相似度分数 (0~1)
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

    retrieved = _sort_retrieved_chunks(retrieved, sort_by)
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
今天的真实日期是 {_today}（当前年份是{_cur_year}年，不是2025年）。你的训练数据可能截止于2025年，但现在确实已经是{_cur_year}年。

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
4. 使用 Markdown 格式组织回答，结构清晰
5. 对于财务数据，保持精确

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
3. fetch_financial_report 只在确认知识库中没有该公司数据时才调用
4. 收集到足够信息后，尽快生成最终分析报告，不要继续调用工具
5. 初始检索结果只作为候选上下文；如果用户明确提到具体公司、股票代码或指定财报，不能仅凭初始全库召回下结论
6. 当 fetch_financial_report 返回 document_id 时，后续 search_vector_store 必须优先传入 document_ids，在对应财报内定向检索"""

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
        "type": "builtin_function",
        "function": {"name": "$web_search"},
    }
]


async def _execute_tool(tool_name: str, tool_args: dict, user_id: int, db=None) -> str:
    """执行 agent tool 调用，返回结果字符串"""

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
        # 智能推断年份：如果模型没传 year，根据当前月份判断最新可用财报年份
        if "year" in tool_args and tool_args["year"]:
            year = tool_args["year"]
        else:
            now = datetime.now()
            # 1-4月：上一年年报正在披露，优先拿上一年
            # 5月后：当年Q1已出，但年报仍是上一年最完整的
            year = now.year - 1 if now.month <= 4 else now.year

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
            from services.simple_report_service import SimplifiedReportService
            report_service = SimplifiedReportService()
            pdf_path = await report_service.download_report_from_cninfo(
                stock_code, company_name, year, quarter
            )
            await report_service.close()

            if not pdf_path:
                return json.dumps({"status": "failed", "message": f"未能从巨潮资讯网找到 {company_name}({stock_code}) {year}年的财报"}, ensure_ascii=False)

            # 入库 Document 记录
            doc_record = None
            if db:
                from database import Document
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
            ingest_result = await ingest_pdf(pdf_path, user_id, document_id=doc_id)

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

    if chunks:
        sources = [{"source": c["source"], "page_number": c["page_number"], "score": c["score"]} for c in chunks]
        yield f"data: {json.dumps({'type': 'sources', 'sources': sources}, ensure_ascii=False)}\n\n"

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
            # 流式请求
            stream = await _kimi_async_client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                tools=AGENT_TOOLS,
                temperature=KIMI_TEMPERATURE,
                max_tokens=KIMI_MAX_TOKENS,
                stream=True,
                extra_body={"thinking": {"type": "disabled"}},
            )

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
                        else:
                            yield f"data: {json.dumps({'type': 'phase', 'content': '正在处理...'}, ensure_ascii=False)}\n\n"

                        tool_result = await _execute_tool(fn_name, fn_args, user_id, db=db)
                        print(f"[RAG-Agent] Tool result: {tool_result[:200]}...")

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
