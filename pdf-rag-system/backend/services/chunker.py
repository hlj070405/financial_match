"""
通用逻辑切分工具 (Logical Chunker)

支持三种切分策略，可按需组合：
  1. section   — 章节标题感知切分（按标题边界分段，段内超长再二次切分）
  2. table     — 表格整体保留（不跨块拆分）
  3. fixed     — 固定字符数兜底（RecursiveCharacterTextSplitter）

入口：
  logical_chunk(pages, strategy="auto", chunk_size=512, chunk_overlap=64, context_meta=None)

pages 格式（与 rag_service 保持一致）：
  [{"page_number": int, "text": str, "source": str, "is_table": bool(可选)}, ...]

context_meta 格式（可选，用于向每个 chunk 注入上下文头）：
  {"company": str, "year": int, "quarter": str, "stock_code": str}

返回格式：
  [{"id": str, "text": str, "metadata": {...}}, ...]
"""

import re
import hashlib
from typing import List, Dict, Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter


# ---------------------------------------------------------------------------
# 章节标题识别正则
# 覆盖常见中文财报/报告格式：
#   第一章 / 第1节 / 一、 / 1. / 1.1 / (一) / （1）/ 一级标题纯文字行
# ---------------------------------------------------------------------------
_SECTION_RE = re.compile(
    r'^\s*'
    r'(?:'
    r'第[一二三四五六七八九十百\d]+[章节条款项]'    # 第X章/节/条
    r'|[一二三四五六七八九十]+[、．.]'              # 一、 二．
    r'|\d+[、．.]\d*'                               # 1. 1.1
    r'|[（(]\d+[)）]'                              # (1) （一）
    r'|[（(][一二三四五六七八九十]+[)）]'
    r')'
    r'\s*.{1,40}$',
    re.MULTILINE
)

# 最大标题行长度（超过此长度不视为标题）
_MAX_TITLE_LEN = 40


# ---------------------------------------------------------------------------
# 内部工具
# ---------------------------------------------------------------------------

def _is_section_title(line: str) -> bool:
    stripped = line.strip()
    if not stripped or len(stripped) > _MAX_TITLE_LEN:
        return False
    return bool(_SECTION_RE.match(stripped))


def _make_chunk_id(source: str, page_num: int, idx: int, text_prefix: str) -> str:
    raw = f"{source}:{page_num}:{idx}:{text_prefix[:50]}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _build_context_prefix(source: str, context_meta: Dict, section_title: str = "") -> str:
    """
    构建注入到 chunk 头部的上下文标签，例如：
      [公司: 比亚迪, 股票代码: 002594, 报告期: 2024年Q4, 章节: 主要财务数据, 来源: xxx.pdf]
    """
    parts = []
    if context_meta.get("company"):
        parts.append(f"公司: {context_meta['company']}")
    if context_meta.get("stock_code"):
        parts.append(f"股票代码: {context_meta['stock_code']}")
    year = context_meta.get("year")
    if year:
        period = f"{year}年"
        if context_meta.get("quarter"):
            period += context_meta["quarter"]
        parts.append(f"报告期: {period}")
    if section_title:
        parts.append(f"章节: {section_title}")
    parts.append(f"来源: {source}")
    return "[" + ", ".join(parts) + "]\n"


def _split_into_sections(text: str) -> List[Dict]:
    """
    按章节标题将文本切分为逻辑段落。
    返回：[{"title": str, "body": str}, ...]
    """
    lines = text.split("\n")
    sections: List[Dict] = []
    current_title = ""
    current_lines: List[str] = []

    for line in lines:
        if _is_section_title(line):
            # 保存已累积的段落
            body = "\n".join(current_lines).strip()
            if body:
                sections.append({"title": current_title, "body": body})
            current_title = line.strip()
            current_lines = []
        else:
            current_lines.append(line)

    # 尾部剩余
    body = "\n".join(current_lines).strip()
    if body:
        sections.append({"title": current_title, "body": body})

    return sections


# ---------------------------------------------------------------------------
# 核心切分函数
# ---------------------------------------------------------------------------

def logical_chunk(
    pages: List[Dict],
    strategy: str = "auto",
    chunk_size: int = 512,
    chunk_overlap: int = 64,
    context_meta: Optional[Dict] = None,
) -> List[Dict]:
    """
    通用逻辑切分入口。

    Args:
        pages:        页面列表，每项含 page_number / text / source / is_table(可选)
        strategy:     切分策略
                        "auto"    — 自动：表格整体保留，普通文本先章节切分再兜底
                        "section" — 仅章节切分（表格同样走章节逻辑）
                        "fixed"   — 纯固定字符数（兼容旧行为）
        chunk_size:   单块最大字符数
        chunk_overlap:块间重叠字符数
        context_meta: 注入上下文的元信息字典，可含 company/year/quarter/stock_code

    Returns:
        chunks 列表，每项含 id / text / metadata
    """
    meta = context_meta or {}

    # 估算前缀最大长度，从 chunk_size 中扣除，确保 prefix+body 不超出 Embedding token 限制
    _sample_prefix = _build_context_prefix("x" * 40, meta, "x" * 30)
    prefix_budget = len(_sample_prefix) + 10  # 留余量
    effective_chunk_size = max(chunk_size - prefix_budget, 200)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=effective_chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "；", ".", ";", " ", ""],
        length_function=len,
    )

    chunks: List[Dict] = []
    global_idx = 0

    for page in pages:
        source = page.get("source", "unknown")
        page_num = page.get("page_number", 0)
        text = page.get("text", "")
        is_table = page.get("is_table", False)

        if not text.strip():
            continue

        if strategy == "fixed":
            _chunks_fixed(
                text, source, page_num, is_table, meta,
                splitter, chunks, global_idx
            )
            global_idx += len(chunks) - global_idx  # 不对，下面统一用 append 后的 len
            # 重新对齐 global_idx
            global_idx = len(chunks)

        elif is_table and strategy in ("auto",):
            # auto 策略下，表格整体保留
            prefix = _build_context_prefix(source, meta, "表格数据")
            full_text = prefix + text
            # 超长表格截断（避免超出 LLM 上下文）
            max_table = chunk_size * 4
            if len(full_text) > max_table:
                full_text = full_text[:max_table] + "\n...(表格截断)"
            chunk_id = _make_chunk_id(source, page_num, global_idx, text)
            chunks.append({
                "id": chunk_id,
                "text": full_text,
                "metadata": {
                    "source": source,
                    "page_number": page_num,
                    "chunk_index": global_idx,
                    "is_table": True,
                    "section_title": "表格数据",
                    **_filter_meta(meta),
                }
            })
            global_idx += 1

        else:
            # section / auto 普通文本：先章节分段，段内超长再切分
            sections = _split_into_sections(text)
            if not sections:
                sections = [{"title": "", "body": text}]

            for sec in sections:
                title = sec["title"]
                body = sec["body"]
                if not body.strip():
                    continue

                prefix = _build_context_prefix(source, meta, title)
                # 如果段落本身不超长，整段作为一个 chunk
                if len(prefix) + len(body) <= chunk_size:
                    chunk_id = _make_chunk_id(source, page_num, global_idx, body)
                    chunks.append({
                        "id": chunk_id,
                        "text": prefix + body,
                        "metadata": {
                            "source": source,
                            "page_number": page_num,
                            "chunk_index": global_idx,
                            "is_table": False,
                            "section_title": title,
                            **_filter_meta(meta),
                        }
                    })
                    global_idx += 1
                else:
                    # 段落超长：二次固定切分，每块复用同一 prefix
                    sub_texts = splitter.split_text(body)
                    for sub in sub_texts:
                        chunk_id = _make_chunk_id(source, page_num, global_idx, sub)
                        chunks.append({
                            "id": chunk_id,
                            "text": prefix + sub,
                            "metadata": {
                                "source": source,
                                "page_number": page_num,
                                "chunk_index": global_idx,
                                "is_table": False,
                                "section_title": title,
                                **_filter_meta(meta),
                            }
                        })
                        global_idx += 1

    return chunks


def _chunks_fixed(
    text, source, page_num, is_table, meta,
    splitter, chunks, start_idx
):
    """fixed 策略：纯固定字符数切分，保持向后兼容。"""
    texts = splitter.split_text(text)
    for i, t in enumerate(texts):
        idx = start_idx + i
        chunk_id = _make_chunk_id(source, page_num, idx, t)
        chunks.append({
            "id": chunk_id,
            "text": t,
            "metadata": {
                "source": source,
                "page_number": page_num,
                "chunk_index": idx,
                "is_table": is_table,
                "section_title": "",
                **_filter_meta(meta),
            }
        })


def _filter_meta(meta: Dict) -> Dict:
    """只保留可写入 ChromaDB 的标量字段（str/int/float/bool）。"""
    allowed = ("company", "stock_code", "year", "quarter")
    result = {}
    for k in allowed:
        v = meta.get(k)
        if v is not None and v != "" and v != 0:
            result[k] = v
    return result


# ---------------------------------------------------------------------------
# 便捷工具：从文件名解析 context_meta
# ---------------------------------------------------------------------------

def parse_source_meta(source_name: str) -> Dict:
    """
    从文件名解析公司名、股票代码、年份、季度。

    支持格式：
      {股票代码}_{公司名}_{年份}[季度]_*.pdf
      例：002594_比亚迪_2024_report.pdf
          300750_宁德时代_2025Q3_report.pdf
    """
    import os
    name = os.path.splitext(os.path.basename(source_name or ""))[0]
    result = {"stock_code": "", "company": "", "year": 0, "quarter": ""}

    # 格式1：6位股票代码开头
    m = re.match(
        r'^(\d{6})_([^_]+)_(\d{4})(Q[1-4]|H[12])?(?:_.*)?$',
        name
    )
    if m:
        result["stock_code"] = m.group(1)
        result["company"] = m.group(2)
        result["year"] = int(m.group(3))
        result["quarter"] = m.group(4) or ""
        return result

    # 格式2：无股票代码，仅年份
    m2 = re.search(r'(\d{4})(Q[1-4]|H[12])?', name)
    if m2:
        result["year"] = int(m2.group(1))
        result["quarter"] = m2.group(2) or ""
    return result
