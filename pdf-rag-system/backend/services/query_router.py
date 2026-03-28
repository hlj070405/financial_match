"""
查询路由模块 (Query Router)

解决"实体混淆"三件套：
  1. 意图解析 (QueryIntent)   — 从自然语言 query 提取公司名、年份、季度
  2. 元数据过滤 (build_where) — 根据 intent 在 ChromaDB where 条件中锁定文档
  3. BM25 混合检索 (hybrid_rank) — 向量分 + BM25 分用 RRF 融合，提升硬实体召回

用法（在 retrieve() 中调用）：
    from services.query_router import parse_intent, build_where_filter, hybrid_rerank
"""

import re
import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple


# ---------------------------------------------------------------------------
# 1. 意图解析
# ---------------------------------------------------------------------------

# 常见中文公司简称/股票代码词典（可按需扩充）
_COMPANY_ALIASES: Dict[str, str] = {
    "工行": "工商银行",
    "建行": "建设银行",
    "农行": "农业银行",
    "中行": "中国银行",
    "交行": "交通银行",
    "招行": "招商银行",
    "浦发": "浦发银行",
    "光大": "光大银行",
    "民生": "民生银行",
    "兴业": "兴业银行",
    "平安银行": "平安银行",
    "比亚迪": "比亚迪",
    "宁德": "宁德时代",
    "宁德时代": "宁德时代",
    "茅台": "贵州茅台",
    "贵州茅台": "贵州茅台",
    "洋河": "洋河股份",
    "寒武纪": "寒武纪",
}

# 季度关键词映射
_QUARTER_MAP: Dict[str, str] = {
    "一季报": "Q1", "一季度": "Q1", "Q1": "Q1", "q1": "Q1",
    "半年报": "H1", "中报": "H1", "H1": "H1", "h1": "H1",
    "三季报": "Q3", "三季度": "Q3", "Q3": "Q3", "q3": "Q3",
    "年报": "Q4",  "全年": "Q4",   "Q4": "Q4", "q4": "Q4",
}


@dataclass
class QueryIntent:
    companies: List[str] = field(default_factory=list)   # 识别出的公司名（已规范化）
    year: Optional[int] = None
    quarter: Optional[str] = None                         # Q1/Q2/Q3/Q4/H1
    raw_query: str = ""

    def is_empty(self) -> bool:
        return not self.companies and self.year is None


def parse_intent(query: str) -> QueryIntent:
    """
    从自然语言 query 中提取公司名、年份、季度。

    示例：
      "工行2024年营收多少" → companies=["工商银行"], year=2024
      "比亚迪和宁德时代三季报对比" → companies=["比亚迪","宁德时代"], quarter="Q3"
    """
    intent = QueryIntent(raw_query=query)

    # 1. 提取公司名
    found_companies = []
    for alias, canonical in _COMPANY_ALIASES.items():
        if alias in query and canonical not in found_companies:
            found_companies.append(canonical)
    # 6位股票代码
    codes = re.findall(r'\b\d{6}\b', query)
    for code in codes:
        if code not in found_companies:
            found_companies.append(code)
    intent.companies = found_companies

    # 2. 提取年份（4位数字，合理范围）
    years = [int(y) for y in re.findall(r'\b(20\d{2})\b', query)]
    if years:
        intent.year = max(years)  # 取最大年份（通常是用户想要最新的）

    # 3. 提取季度
    for kw, qval in _QUARTER_MAP.items():
        if kw in query:
            intent.quarter = qval
            break

    return intent


# ---------------------------------------------------------------------------
# 2. 元数据过滤条件构建
# ---------------------------------------------------------------------------

def build_where_filter(
    intent: QueryIntent,
    indexed_sources: List[str],
    explicit_document_ids: Optional[List[int]] = None,
) -> Optional[Dict]:
    """
    根据意图解析结果构建 ChromaDB where 过滤条件。

    优先级：
      1. 显式传入 document_ids → 最高优先，直接用
      2. 意图中有公司名/年份 → 从 indexed_sources 中匹配 source 文件名，转为 source $in 过滤
      3. 无任何意图 → 返回 None（全库检索）

    Args:
        intent:              解析出的查询意图
        indexed_sources:     用户向量库中所有文档的 source 文件名列表
        explicit_document_ids: 调用方显式传入的 document_id 列表
    """
    # 优先级1：显式 document_ids
    if explicit_document_ids:
        if len(explicit_document_ids) == 1:
            return {"document_id": explicit_document_ids[0]}
        return {"document_id": {"$in": explicit_document_ids}}

    # 优先级2：意图匹配
    if intent.is_empty():
        return None

    matched_sources = _match_sources(intent, indexed_sources)
    if not matched_sources:
        return None

    if len(matched_sources) == 1:
        return {"source": matched_sources[0]}
    return {"source": {"$in": matched_sources}}


def _match_sources(intent: QueryIntent, indexed_sources: List[str]) -> List[str]:
    """
    在 indexed_sources 中找出匹配 intent 的文件名。
    匹配规则：
      - 公司名或股票代码出现在文件名中
      - 年份出现在文件名中（如有）
      - 季度出现在文件名中（如有，且宽松匹配：年报匹配 annual/Q4/FY）
    """
    matches = []
    for src in indexed_sources:
        src_lower = src.lower()

        # 公司名匹配（有 intent.companies 时必须至少命中一个）
        if intent.companies:
            company_hit = any(
                c.lower() in src_lower or c in src
                for c in intent.companies
            )
            if not company_hit:
                continue

        # 年份匹配
        if intent.year and str(intent.year) not in src:
            continue

        # 季度宽松匹配
        if intent.quarter:
            qmap = {
                "Q1": ["q1", "一季"],
                "Q2": ["q2", "二季", "h1", "半年"],
                "H1": ["h1", "半年", "q2"],
                "Q3": ["q3", "三季"],
                "Q4": ["q4", "annual", "fy", "年报", "全年"],
            }
            aliases = qmap.get(intent.quarter, [intent.quarter.lower()])
            if not any(a in src_lower for a in aliases):
                continue

        matches.append(src)

    return matches


# ---------------------------------------------------------------------------
# 3. BM25 混合检索（RRF 融合）
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> List[str]:
    """简单分词：按非汉字/非字母边界切分，保留汉字字符和英文单词。"""
    # 汉字逐字 + 英文单词
    tokens = re.findall(r'[\u4e00-\u9fff]|[a-zA-Z0-9]+', text.lower())
    return tokens


class BM25:
    """轻量 BM25 实现，无外部依赖。k1=1.5, b=0.75"""

    def __init__(self, corpus: List[str], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_tokens: List[List[str]] = [_tokenize(doc) for doc in corpus]
        self.n = len(corpus)
        self.avgdl = (
            sum(len(t) for t in self.corpus_tokens) / self.n
            if self.n > 0 else 1.0
        )
        # 文档频率
        self.df: Dict[str, int] = {}
        for tokens in self.corpus_tokens:
            for token in set(tokens):
                self.df[token] = self.df.get(token, 0) + 1

    def score(self, query: str, doc_idx: int) -> float:
        query_tokens = _tokenize(query)
        doc_tokens = self.corpus_tokens[doc_idx]
        dl = len(doc_tokens)
        # 词频统计
        tf_map: Dict[str, int] = {}
        for t in doc_tokens:
            tf_map[t] = tf_map.get(t, 0) + 1

        s = 0.0
        for token in query_tokens:
            if token not in tf_map:
                continue
            tf = tf_map[token]
            df = self.df.get(token, 0)
            idf = math.log((self.n - df + 0.5) / (df + 0.5) + 1)
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
            s += idf * numerator / denominator
        return s

    def get_scores(self, query: str) -> List[float]:
        return [self.score(query, i) for i in range(self.n)]


def hybrid_rerank(
    query: str,
    candidates: List[Dict],
    vector_weight: float = 0.6,
    bm25_weight: float = 0.4,
    rrf_k: int = 60,
) -> List[Dict]:
    """
    对向量检索候选结果做 BM25 混合重排（RRF 融合）。

    Args:
        query:          用户原始查询
        candidates:     向量检索结果列表，每项含 text / score 等字段
        vector_weight:  向量分权重
        bm25_weight:    BM25 分权重
        rrf_k:          RRF 平滑参数（越大越平滑）

    Returns:
        重排后的 candidates 列表（原字段保留，新增 bm25_score / hybrid_score）
    """
    if not candidates:
        return candidates

    corpus = [c["text"] for c in candidates]
    bm25 = BM25(corpus)
    bm25_scores = bm25.get_scores(query)

    # 归一化 BM25 分到 [0,1]
    max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1.0
    bm25_norm = [s / max_bm25 for s in bm25_scores]

    # 向量分已是 [0,1]（cosine similarity）
    vector_scores = [c["score"] for c in candidates]

    # RRF：先对两路分别排序，再融合
    vec_rank = _rank_indices(vector_scores, reverse=True)
    bm25_rank = _rank_indices(bm25_scores, reverse=True)

    hybrid_scores = []
    for i in range(len(candidates)):
        rrf = (
            vector_weight / (rrf_k + vec_rank[i])
            + bm25_weight / (rrf_k + bm25_rank[i])
        )
        hybrid_scores.append(rrf)

    # 附加分数并重排
    for i, c in enumerate(candidates):
        c["bm25_score"] = round(bm25_norm[i], 4)
        c["hybrid_score"] = round(hybrid_scores[i], 6)

    candidates.sort(key=lambda x: x["hybrid_score"], reverse=True)
    return candidates


def _rank_indices(scores: List[float], reverse: bool = True) -> List[int]:
    """返回每个元素在排序后的名次（1-based）。"""
    indexed = sorted(enumerate(scores), key=lambda x: x[1], reverse=reverse)
    ranks = [0] * len(scores)
    for rank, (idx, _) in enumerate(indexed, start=1):
        ranks[idx] = rank
    return ranks


# ---------------------------------------------------------------------------
# 4. BGE-Reranker 精排（第三阶段，Cross-Encoder）
# ---------------------------------------------------------------------------

# 硅基流动 Reranker 模型，与 Embedding 同平台同 API Key
_RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"
_RERANKER_SCORE_THRESHOLD = 0.6   # 低于此分视为无关，触发"断路"


async def bge_rerank(
    query: str,
    candidates: List[Dict],
    api_key: str = None,
    base_url: str = "https://api.siliconflow.cn/v1",
    top_n: Optional[int] = None,
    score_threshold: float = _RERANKER_SCORE_THRESHOLD,
) -> Tuple[List[Dict], bool]:
    """
    调用硅基流动 BGE-Reranker-v2-m3 对候选结果做精排。

    Cross-Encoder 原理：将 query + doc 拼接后整体过模型，
    注意力机制同时感知两者关系，比 BM25（词频）精准得多。

    Args:
        query:            用户原始查询
        candidates:       BM25混合重排后的候选列表
        api_key:          硅基流动 API Key（默认从环境变量读取）
        top_n:            精排后保留数量（默认全部返回）
        score_threshold:  断路阈值，最高分低于此值则视为"无相关内容"

    Returns:
        (reranked_candidates, is_relevant)
        is_relevant=False 表示触发断路器，库中无有效内容
    """
    if not candidates:
        return candidates, False

    import httpx
    import os

    key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
    if not key:
        # 无 API Key 时降级：直接返回候选，不报错
        print("[Reranker] 无 API Key，跳过精排")
        return candidates, True

    documents = [c["text"] for c in candidates]

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{base_url}/rerank",
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": _RERANKER_MODEL,
                    "query": query,
                    "documents": documents,
                    "top_n": top_n or len(documents),
                    "return_documents": False,
                },
            )
            if resp.status_code != 200:
                print(f"[Reranker] API 错误 {resp.status_code}: {resp.text[:200]}")
                return candidates, True   # 降级：保留原顺序

            data = resp.json()
            results = data.get("results", [])
    except Exception as e:
        print(f"[Reranker] 调用失败，降级: {e}")
        return candidates, True

    if not results:
        return candidates, True

    # 将 reranker score 写回 candidates
    for item in results:
        idx = item["index"]
        score = item.get("relevance_score", 0.0)
        candidates[idx]["rerank_score"] = round(score, 4)

    # 按 rerank_score 排序
    candidates_with_score = [c for c in candidates if "rerank_score" in c]
    candidates_no_score = [c for c in candidates if "rerank_score" not in c]
    candidates_with_score.sort(key=lambda x: x["rerank_score"], reverse=True)
    reranked = candidates_with_score + candidates_no_score

    # 断路器：最高分仍低于阈值 → 库中无有效内容
    top_score = reranked[0]["rerank_score"] if reranked else 0.0
    is_relevant = top_score >= score_threshold
    if not is_relevant:
        print(f"[Reranker] 断路器触发：最高分 {top_score:.4f} < 阈值 {score_threshold}")

    if top_n:
        reranked = reranked[:top_n]

    return reranked, is_relevant
