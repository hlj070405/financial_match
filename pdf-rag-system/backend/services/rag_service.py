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

from config import DEEPSEEK_API_KEY

# ---------- 配置 ----------

EMBEDDING_MODEL = "BAAI/bge-large-zh-v1.5"
EMBEDDING_DIM = 1024
EMBEDDING_BASE_URL = "https://api.siliconflow.cn/v1"
EMBEDDING_BATCH_SIZE = 16

CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")

CHUNK_SIZE = 512
CHUNK_OVERLAP = 64

# LLM 用于 RAG 回答（复用硅基流动 Qwen）
LLM_MODEL = "Qwen/Qwen2.5-72B-Instruct"
LLM_BASE_URL = "https://api.siliconflow.cn/v1"

# ---------- Embedding 客户端 ----------

_embedding_cache = {}


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
        os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR,
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
    full_path = pdf_path
    if not os.path.isabs(full_path):
        full_path = os.path.join(os.getcwd(), full_path)

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
                   score_threshold: float = 0.55) -> List[Dict]:
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

        results = collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )
    except Exception as e:
        print(f"[RAG] 检索失败: {e}")
        traceback.print_exc()
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
        retrieved.append({
            "text": doc,
            "source": meta.get("source", "unknown"),
            "page_number": meta.get("page_number", 0),
            "chunk_index": meta.get("chunk_index", 0),
            "is_table": meta.get("is_table", False),
            "document_id": meta.get("document_id"),
            "score": round(similarity, 4)
        })

    if filtered_count > 0:
        print(f"[RAG] 检索过滤: 丢弃 {filtered_count} 个低分结果 (阈值 {score_threshold})")

    return retrieved


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

    # ---- 构建 system prompt ----
    system_prompt = f"""# 身份
你是「{profile['identity']}」。

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
- items 数组最多 4 个选项"""

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


async def rag_chat_stream(
    query: str,
    user_id: int,
    top_k: int = 6,
    document_ids: List[int] = None,
    style: str = "专业分析",
    user_role: str = None,
    conversation_history: List[Dict] = None
):
    """
    RAG 对话（异步生成器，yield SSE 格式字符串）。
    支持动态身份(user_role)和结构化 JSON 交互输出。

    完整流程：检索 → 构建 prompt → 流式调用 LLM → yield 文本块 → 提取交互 JSON
    """
    # 1. 检索
    yield f"data: {json.dumps({'type': 'phase', 'content': '正在检索相关文档...'}, ensure_ascii=False)}\n\n"

    chunks = await retrieve(query, user_id, top_k=top_k, document_ids=document_ids)
    if not chunks:
        yield f"data: {json.dumps({'type': 'text', 'text': '未找到相关文档内容。请确认已上传相关PDF文件并完成向量化。'}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type': 'finish', 'data': {}})}\n\n"
        yield "data: [DONE]\n\n"
        return

    # 发送检索到的来源信息
    sources = [{"source": c["source"], "page_number": c["page_number"], "score": c["score"]} for c in chunks]
    yield f"data: {json.dumps({'type': 'sources', 'sources': sources}, ensure_ascii=False)}\n\n"

    # 2. 构建 prompt（动态身份）
    yield f"data: {json.dumps({'type': 'phase', 'content': 'AI 正在分析文档内容...'}, ensure_ascii=False)}\n\n"

    messages = _build_rag_prompt(query, chunks, style, user_role=user_role)

    # 插入历史对话（如果有）
    if conversation_history:
        history_messages = []
        for h in conversation_history[-6:]:  # 最近3轮
            if h.get("role") in ("user", "assistant"):
                history_messages.append({"role": h["role"], "content": h["content"]})
        if history_messages:
            messages = [messages[0]] + history_messages + [messages[-1]]

    # 3. 流式调用 LLM
    api_key = DEEPSEEK_API_KEY
    full_content = ""

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{LLM_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": LLM_MODEL,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 4096,
                    "stream": True
                }
            ) as resp:
                if resp.status_code != 200:
                    error_body = await resp.aread()
                    yield f"data: {json.dumps({'type': 'error', 'error': f'LLM API 错误: {resp.status_code} - {error_body.decode()}'})}\n\n"
                    return

                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            full_content += content
                            yield f"data: {json.dumps({'type': 'text', 'text': content}, ensure_ascii=False)}\n\n"
                    except json.JSONDecodeError:
                        continue

    except Exception as e:
        traceback.print_exc()
        yield f"data: {json.dumps({'type': 'error', 'error': f'RAG 生成失败: {str(e)}'})}\n\n"
        return

    # 4. 后处理：提取结构化交互 JSON
    _, interaction = _extract_interaction_json(full_content)
    if interaction:
        yield f"data: {json.dumps({'type': 'interaction', 'interaction': interaction}, ensure_ascii=False)}\n\n"

    # 5. 完成
    yield f"data: {json.dumps({'type': 'finish', 'data': {'total_length': len(full_content)}})}\n\n"
    yield "data: [DONE]\n\n"
    print(f"[RAG] 对话完成, 输出 {len(full_content)} 字符, 引用 {len(chunks)} 个文档块, 角色: {user_role or 'default'}")


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
