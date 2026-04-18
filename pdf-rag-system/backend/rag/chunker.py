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

from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter

# ---------------------------------------------------------------------------
# 章节标题识别弱特征 (仅用于 fallback 的纯文本切分)
# ---------------------------------------------------------------------------
_MAX_TITLE_LEN = 40


# ---------------------------------------------------------------------------
# 内部工具
# ---------------------------------------------------------------------------

def _looks_like_table_row(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if "\t" in stripped or "|" in stripped:
        return True
    if stripped.count("  ") >= 2:
        return True
    numeric_tokens = 0
    for token in stripped.replace("|", " ").split():
        compact = token.replace(",", "").replace(".", "").replace("%", "")
        if compact and all(ch.isdigit() for ch in compact):
            numeric_tokens += 1
    return numeric_tokens >= 3


def _is_numbering_prefix(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False

    if stripped.startswith("第") and len(stripped) >= 3 and stripped[1] in "一二三四五六七八九十百0123456789":
        return True

    if len(stripped) >= 2 and stripped[0] in "一二三四五六七八九十" and stripped[1] in "、.．":
        return True

    if stripped[0].isdigit():
        idx = 0
        dot_count = 0
        while idx < len(stripped) and (stripped[idx].isdigit() or stripped[idx] in ".．、"):
            if stripped[idx] in ".．、":
                dot_count += 1
            idx += 1
        if dot_count >= 1 and idx < len(stripped):
            return True

    if stripped[0] in "(（" and len(stripped) >= 3 and stripped[1] in "一二三四五六七八九十0123456789" and stripped[2] in ")）":
        return True

    return False


def _score_section_title(line: str, next_line: str = "") -> int:
    stripped = line.strip()
    if not stripped or len(stripped) > _MAX_TITLE_LEN:
        return -10
        
    # 过滤过短的噪声（如单个字符 "-" 或 "计"）
    if len(stripped) < 2:
        return -10
        
    # 标题必须包含至少一个汉字或字母（过滤纯数字如 "130", "(1)"）
    has_text = any('\u4e00' <= ch <= '\u9fff' or ch.isalpha() for ch in stripped)
    if not has_text:
        return -10

    score = 0
    if _is_numbering_prefix(stripped):
        score += 3
    if len(stripped) <= 20:
        score += 2
    elif len(stripped) <= 32:
        score += 1

    punctuation_count = sum(ch in "，。；：、】【,.!！?？:;" for ch in stripped)
    if punctuation_count <= 1:
        score += 1
    else:
        score -= 1

    if stripped.endswith(("。", ".", "；", ";", "：", ":", "，", ",")):
        score -= 2

    digit_count = sum(ch.isdigit() for ch in stripped)
    if digit_count / max(len(stripped), 1) > 0.35:
        score -= 2

    if _looks_like_table_row(stripped):
        score -= 3

    if next_line:
        next_stripped = next_line.strip()
        if len(next_stripped) > max(len(stripped) + 10, 35):
            score += 1
        if _looks_like_table_row(next_stripped):
            score -= 1

    return score


def _is_section_title(line: str, next_line: str = "") -> bool:
    return _score_section_title(line, next_line) >= 3


def _make_chunk_id(source: str, page_num: int, idx: int, text_prefix: str) -> str:
    raw = f"{source}:{page_num}:{idx}:{text_prefix[:50]}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _build_context_prefix(source: str, context_meta: Dict, section_title: str = "") -> str:
    """
    构建注入到 chunk 头部的轻量上下文，仅保留当前章节。
    """
    if section_title:
        return f"当前章节：{section_title}\n"
    return ""


def _split_into_sections(text: str) -> List[Dict]:
    """
    按章节标题将文本切分为逻辑段落。
    返回：[{"title": str, "body": str}, ...]
    """
    lines = text.split("\n")
    sections: List[Dict] = []
    current_title = ""
    current_lines: List[str] = []

    for idx, line in enumerate(lines):
        next_line = lines[idx + 1] if idx + 1 < len(lines) else ""
        if _is_section_title(line, next_line):
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
# 跨页表格修复
# ---------------------------------------------------------------------------

def _extract_trailing_table_header(lines: List[str]) -> List[str]:
    """
    从一组文本行的末尾向前搜索，提取表格列标题行。
    表头特征：短行（<35字），包含"项目"/"年"/"季度"等标签，非数字主导。
    返回找到的表头行列表（正序），找不到返回空列表。
    """
    if not lines:
        return []

    candidates = []
    for line in reversed(lines):
        stripped = line.strip()
        if not stripped:
            if candidates:
                break
            continue
        if len(stripped) > 40:
            break
        digits = sum(c.isdigit() for c in stripped)
        if len(stripped) > 0 and digits / len(stripped) > 0.5:
            break
        candidates.append(stripped)
        if len(candidates) >= 10:
            break

    candidates.reverse()

    header_markers = ['项目', '年', '季度', '单位', '期末', '期初', '本期', '上期', '增减']
    header_text = ' '.join(candidates)
    has_marker = any(m in header_text for m in header_markers)

    if has_marker and len(candidates) >= 2:
        return candidates
    return []


def _starts_with_table_data(lines: List[str], skip_noise: int = 3) -> bool:
    """
    检查内容前几行是否包含表格数据（数字密集的行）。
    skip_noise: 跳过前N行噪声（如公司名、页码等）。
    """
    data_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        data_lines.append(stripped)
        if len(data_lines) >= skip_noise + 5:
            break

    numeric_lines = 0
    for line in data_lines[min(skip_noise, len(data_lines) - 1):]:
        digits = sum(c.isdigit() for c in line)
        if digits >= 3:
            numeric_lines += 1

    return numeric_lines >= 2


def _repair_table_headers_across_pages(md_content: str) -> str:
    """
    修复跨页表格：当 ## 第X页 把表头和数据分到不同 section 时，
    将上一 section 末尾的表头复制到下一 section 开头。
    """
    page_pattern = re.compile(r'(^## 第\d+页.*$)', re.MULTILINE)
    parts = page_pattern.split(md_content)
    # parts: [before_header0, header0, content0, header1, content1, ...]

    if len(parts) < 3:
        return md_content

    result = [parts[0]]
    repaired = 0

    for i in range(1, len(parts), 2):
        header = parts[i]
        content = parts[i + 1] if i + 1 < len(parts) else ""

        prev_text = result[-1] if result else ""
        prev_lines = prev_text.split('\n')

        table_header_lines = _extract_trailing_table_header(prev_lines)

        if table_header_lines:
            curr_lines = content.split('\n')
            if _starts_with_table_data(curr_lines):
                header_block = '\n'.join(table_header_lines)
                content = f"\n{header_block}\n{content}"
                repaired += 1

        result.append(header)
        result.append(content)

    if repaired > 0:
        print(f"[chunker] 修复了 {repaired} 处跨页表格表头")

    return ''.join(result)


# ---------------------------------------------------------------------------
# 核心切分函数 (Markdown & 纯文本双轨支持)
# ---------------------------------------------------------------------------

def logical_chunk(
    pages: List[Dict],
    strategy: str = "auto",
    chunk_size: int = 512,
    chunk_overlap: int = 64,
    context_meta: Optional[Dict] = None,
    is_markdown: bool = False,
) -> List[Dict]:
    """
    通用逻辑切分入口。

    Args:
        pages:        页面列表，对于 is_markdown=True，预期只有一条记录 `[{"text": "完整markdown内容", "source": "xxx"}]`
        strategy:     切分策略
                        "auto"    — 自动策略
                        "section" — 仅章节切分
                        "fixed"   — 纯固定字符数
        chunk_size:   单块最大字符数
        chunk_overlap:块间重叠字符数
        context_meta: 注入上下文的元信息字典，可含 company/year/quarter/stock_code
        is_markdown:  指示传入的 text 是否是结构化的 Markdown。如果是，将使用 MarkdownHeaderTextSplitter。

    Returns:
        chunks 列表，每项含 id / text / metadata
    """
    if is_markdown:
        return _logical_chunk_markdown(
            pages, chunk_size, chunk_overlap, context_meta
        )

    return _logical_chunk_plaintext(
        pages, strategy, chunk_size, chunk_overlap, context_meta
    )


def _logical_chunk_markdown(
    pages: List[Dict],
    chunk_size: int = 512,
    chunk_overlap: int = 64,
    context_meta: Optional[Dict] = None,
) -> List[Dict]:
    """
    使用 MarkdownHeaderTextSplitter 基于预处理的 Markdown 结构进行高精度切分。
    """
    meta = context_meta or {}
    
    # 估算前缀长度
    _sample_prefix = _build_context_prefix("x" * 40, meta, "x" * 30)
    prefix_budget = len(_sample_prefix) + 10
    effective_chunk_size = max(chunk_size - prefix_budget, 200)

    # 1. 按照 Markdown 层级切分
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)

    # 2. 如果单块过长，再次字符切分兜底
    char_splitter = RecursiveCharacterTextSplitter(
        chunk_size=effective_chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "；", ".", ";", " ", ""],
        length_function=len,
    )

    chunks: List[Dict] = []
    global_idx = 0

    for page in pages:
        source = page.get("source", "unknown")
        # 针对 Markdown 模式，我们不再依赖精确的 page_number（因为它是全文档融合的）
        page_num = page.get("page_number", 1) 
        text = page.get("text", "")

        if not text.strip():
            continue

        # 修复跨页表格：将被 ## 第X页 切断的表头复制到下一页
        text = _repair_table_headers_across_pages(text)

        md_splits = markdown_splitter.split_text(text)

        for split in md_splits:
            content = split.page_content.strip()
            if not content:
                continue

            # 拼装层级路径，例如： "第一节 业务回顾 -> 核心业务情况"
            path_parts = []
            for h in ["Header 1", "Header 2", "Header 3"]:
                if h in split.metadata:
                    path_parts.append(split.metadata[h])
            section_title = " -> ".join(path_parts) if path_parts else ""

            prefix = _build_context_prefix(source, meta, section_title)
            
            # 是否需要二次兜底切分
            if len(prefix) + len(content) <= chunk_size:
                chunk_id = _make_chunk_id(source, page_num, global_idx, content)
                chunks.append({
                    "id": chunk_id,
                    "text": prefix + content,
                    "metadata": {
                        "source": source,
                        "page_number": page_num,
                        "chunk_index": global_idx,
                        "is_table": "|" in content and "-|-" in content, # 粗略判定是否包含MD表格
                        "section_title": section_title,
                        **_filter_meta(meta),
                    }
                })
                global_idx += 1
            else:
                # 段落超长：二次固定切分，每块复用同一 prefix
                sub_texts = char_splitter.split_text(content)
                for sub in sub_texts:
                    chunk_id = _make_chunk_id(source, page_num, global_idx, sub)
                    chunks.append({
                        "id": chunk_id,
                        "text": prefix + sub,
                        "metadata": {
                            "source": source,
                            "page_number": page_num,
                            "chunk_index": global_idx,
                            "is_table": "|" in sub and "-|-" in sub,
                            "section_title": section_title,
                            **_filter_meta(meta),
                        }
                    })
                    global_idx += 1

    return chunks


def _logical_chunk_plaintext(
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
