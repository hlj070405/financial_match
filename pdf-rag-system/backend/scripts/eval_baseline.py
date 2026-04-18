"""
eval_baseline.py — 基线评估脚本

流程：
  1. 读 eval_questions.json（30 题）
  2. 确保对应 PDF 已入库 ChromaDB（eval 专用 user_id=9999）
  3. 对每个问题：RAG 检索 context chunks → 分别喂 GLM-5.1 和 Qwen3.5-9B → K2.5 裁判打分
  4. 输出 eval_results.json

用法：
  cd backend
  python -m scripts.eval_baseline [--skip-ingest] [--questions 1,2,3] [--top-k 5]
"""

import os
import sys
import json
import time
import asyncio
import argparse
import traceback
from typing import Dict, List, Optional
from pathlib import Path

# 确保 backend 在 sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from core.config import (
    DEEPSEEK_API_KEY, KIMI_API_KEY, KIMI_BASE_URL,
    FINANCIAL_REPORTS_DIR,
)

import httpx

# ======================== 模型配置 ========================

EVAL_USER_ID = 9999  # 评估专用用户，不污染真实用户

# 蒸馏数据源（回答者 A）
GLM_MODEL = "Pro/zai-org/GLM-5.1"
GLM_BASE_URL = "https://api.siliconflow.cn/v1"
GLM_API_KEY = DEEPSEEK_API_KEY

# 基线被评者（回答者 B）
QWEN_MODEL = "Qwen/Qwen3.5-9B"
QWEN_BASE_URL = "https://api.siliconflow.cn/v1"
QWEN_API_KEY = DEEPSEEK_API_KEY

# 裁判
JUDGE_MODEL = "kimi-k2.5"
JUDGE_BASE_URL = KIMI_BASE_URL
JUDGE_API_KEY = KIMI_API_KEY

# RAG 检索参数
DEFAULT_TOP_K = 5

# ======================== LLM 调用 ========================

async def call_llm(
    base_url: str,
    api_key: str,
    model: str,
    messages: List[Dict],
    temperature: float = 0.3,
    max_tokens: int = 4096,
    extra_body: Optional[Dict] = None,
) -> str:
    """通用 LLM 调用（OpenAI 兼容接口）"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if extra_body:
        body.update(extra_body)

    url = f"{base_url}/chat/completions"

    max_retries = 5
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=180) as client:
                resp = await client.post(url, headers=headers, json=body)
                if resp.status_code in (429, 503, 502, 500):
                    wait = 15 * (attempt + 1)
                    print(f"  [HTTP {resp.status_code}] {model}，等待 {wait}s 后重试({attempt+1}/{max_retries})...")
                    await asyncio.sleep(wait)
                    continue
                if resp.status_code != 200:
                    print(f"  [HTTP {resp.status_code}] {model}: {resp.text[:300]}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(5)
                        continue
                    return f"[ERROR] {model} HTTP {resp.status_code}"
                data = resp.json()
                msg = data["choices"][0]["message"]
                content = msg.get("content") or ""
                # 如果 content 为空，尝试 reasoning_content（K2.5 推理模型）
                if not content.strip():
                    reasoning = msg.get("reasoning_content") or ""
                    if reasoning:
                        content = reasoning
                    else:
                        # 打印完整响应结构帮助调试
                        print(f"  [WARN] {model} 返回空内容, msg keys={list(msg.keys())}")
                # 如果有 thinking 标签，只取最终回答
                if "<think>" in content and "</think>" in content:
                    content = content.split("</think>")[-1].strip()
                if not content.strip():
                    # 空内容当作失败，触发重试
                    if attempt < max_retries - 1:
                        print(f"  [EMPTY] {model} 空响应，重试({attempt+1}/{max_retries})...")
                        await asyncio.sleep(10)
                        continue
                return content
        except Exception as e:
            print(f"  [LLM 错误] {model} attempt={attempt+1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(10 * (attempt + 1))
            else:
                return f"[ERROR] {model} 调用失败: {e}"

    return f"[ERROR] {model} 调用失败: 超过{max_retries}次重试"


async def call_glm(context: str, question: str) -> str:
    """GLM-5.1 回答"""
    messages = [
        {"role": "system", "content": RAG_SYSTEM_PROMPT},
        {"role": "user", "content": _build_qa_prompt(context, question)},
    ]
    return await call_llm(GLM_BASE_URL, GLM_API_KEY, GLM_MODEL, messages)


async def call_qwen(context: str, question: str) -> str:
    """Qwen3.5-9B 回答（关闭 thinking mode，对比原始回答质量）"""
    messages = [
        {"role": "system", "content": RAG_SYSTEM_PROMPT},
        {"role": "user", "content": _build_qa_prompt(context, question)},
    ]
    return await call_llm(
        QWEN_BASE_URL, QWEN_API_KEY, QWEN_MODEL, messages,
        extra_body={"enable_thinking": False},
    )


async def call_judge(question: str, context: str, answer_a: str, answer_b: str) -> Dict:
    """K2.5 裁判打分，返回 {score_a, score_b, reasoning}"""
    messages = [
        {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
        {"role": "user", "content": _build_judge_prompt(question, context, answer_a, answer_b)},
    ]
    # kimi-k2.5 只允许 temperature=1，max_tokens 要够大避免 JSON 被截断
    raw = await call_llm(JUDGE_BASE_URL, JUDGE_API_KEY, JUDGE_MODEL, messages,
                         temperature=1.0, max_tokens=8192)

    # 解析 JSON
    try:
        # 尝试提取 JSON 块
        if "```json" in raw:
            json_str = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            json_str = raw.split("```")[1].split("```")[0].strip()
        elif "{" in raw:
            start = raw.index("{")
            end = raw.rindex("}") + 1
            json_str = raw[start:end]
        else:
            json_str = raw

        # 修复常见 JSON 格式问题（尾部逗号等）
        import re
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        result = json.loads(json_str)
        # 如果没有 score_a，从三维度平均计算
        if "score_a" not in result and "accuracy_a" in result:
            result["score_a"] = round(
                (result.get("accuracy_a", 0) + result.get("completeness_a", 0)
                 + result.get("professionalism_a", 0)) / 3, 1)
            result["score_b"] = round(
                (result.get("accuracy_b", 0) + result.get("completeness_b", 0)
                 + result.get("professionalism_b", 0)) / 3, 1)
        return {
            "score_a": result.get("score_a", 0),
            "score_b": result.get("score_b", 0),
            "accuracy_a": result.get("accuracy_a", 0),
            "accuracy_b": result.get("accuracy_b", 0),
            "completeness_a": result.get("completeness_a", 0),
            "completeness_b": result.get("completeness_b", 0),
            "professionalism_a": result.get("professionalism_a", 0),
            "professionalism_b": result.get("professionalism_b", 0),
            "reasoning": result.get("reasoning", ""),
        }
    except Exception as e:
        print(f"  [裁判解析失败] {e}")
        print(f"  裁判原始输出: {raw[:500]}")
        return {
            "score_a": 0, "score_b": 0,
            "accuracy_a": 0, "accuracy_b": 0,
            "completeness_a": 0, "completeness_b": 0,
            "professionalism_a": 0, "professionalism_b": 0,
            "reasoning": f"[PARSE_ERROR] {raw[:300]}",
        }


# ======================== Prompt 模板 ========================

RAG_SYSTEM_PROMPT = """你是一个专业的金融分析助手。严格基于提供的财报文档内容回答用户问题。

核心要求：
1. 严禁编造：如果上下文中没有某个数据，必须明确写"该数据未在提供的文档片段中出现"，绝对不能推测或编造任何数字
2. 引用准确：引用数字时必须与上下文完全一致，注意区分合并报表与母公司报表、不同年份的数据列
3. 宁缺勿滥：宁可回答不完整，也不要编造数据。部分回答优于错误回答
4. 回答要有条理，重点突出"""

JUDGE_SYSTEM_PROMPT = """你是金融问答评分器。直接输出JSON，禁止输出任何分析过程。

评分维度（1-5分）：accuracy=事实准确性，completeness=完整性，professionalism=专业性。
5=卓越 4=优秀 3=合格 2=较差 1=很差

严格只输出以下JSON，不要输出任何其他文字：
{"accuracy_a":X,"accuracy_b":X,"completeness_a":X,"completeness_b":X,"professionalism_a":X,"professionalism_b":X,"score_a":X.X,"score_b":X.X,"reasoning":"50字以内"}"""


def _build_qa_prompt(context: str, question: str) -> str:
    return f"""以下是从财报文档中检索到的相关内容：

---
{context}
---

请基于以上内容回答问题：{question}"""


def _build_judge_prompt(question: str, context: str, answer_a: str, answer_b: str) -> str:
    return f"""## 参考上下文（来自财报文档）
{context[:3000]}

## 用户问题
{question}

## 回答 A（GLM-5.1）
{answer_a}

## 回答 B（Qwen3.5-9B）
{answer_b}

请严格按照评分标准，对两个回答分别打分。输出 JSON 格式。"""


# ======================== RAG 检索 ========================

async def ensure_ingested(report_filename: str, reports_dir: str) -> bool:
    """确保 PDF 已入库到 eval 用户的 ChromaDB collection"""
    from rag.service import _get_collection, ingest_pdf

    collection = _get_collection(EVAL_USER_ID)

    # 检查是否已入库
    try:
        existing = collection.get(where={"source": report_filename}, limit=1)
        if existing and existing["ids"]:
            return True
    except Exception:
        pass

    # 入库
    pdf_path = os.path.join(reports_dir, report_filename)
    if not os.path.exists(pdf_path):
        print(f"  [SKIP] PDF 不存在: {pdf_path}")
        return False

    print(f"  [INGEST] 正在入库: {report_filename} ...")
    t0 = time.time()
    result = await ingest_pdf(pdf_path, EVAL_USER_ID)
    elapsed = time.time() - t0

    if result.get("status") == "ok":
        print(f"  [INGEST] 完成: {result.get('chunks', 0)} 个块, {elapsed:.1f}s")
        return True
    else:
        print(f"  [INGEST] 失败: {result.get('message', 'unknown')}")
        return False


async def retrieve_context(question: str, top_k: int = DEFAULT_TOP_K) -> str:
    """调用 RAG retrieve 获取 context 文本"""
    from rag.service import retrieve

    results = await retrieve(
        query=question,
        user_id=EVAL_USER_ID,
        top_k=top_k,
        score_threshold=0.45,  # 评估时稍微放宽阈值，确保能拿到内容
        enable_hybrid=True,
        enable_rerank=True,
    )

    if not results:
        return "[未检索到相关内容]"

    context_parts = []
    for i, r in enumerate(results, 1):
        source = r.get("source", "unknown")
        score = r.get("score", 0)
        text = r.get("text", "")
        context_parts.append(f"[片段{i}] (来源: {source}, 相关度: {score:.2f})\n{text}")

    return "\n\n".join(context_parts)


async def _rejudge_failed(results: List[Dict], output_path: str):
    """对 score_a==0 且有回答的题目重新跑裁判"""
    failed = [r for r in results
              if r.get("status") == "ok"
              and r.get("scores", {}).get("score_a", 0) == 0
              and r.get("answer_a") and r.get("answer_b")]

    if not failed:
        print("[rejudge] 没有需要重新评分的题目")
        return

    print(f"[rejudge] 发现 {len(failed)} 题裁判失败，开始重新评分...\n")

    for i, r in enumerate(failed):
        qid = r["id"]
        print(f"[rejudge {i+1}/{len(failed)}] Q{qid}: {r['question'][:50]}...")

        # 优先用已保存的 context，没有则重新检索
        context = r.get("context", "")
        if not context:
            print(f"  重新检索 context...")
            context = await retrieve_context(r["question"], top_k=5)
            r["context"] = context[:5000]

        t0 = time.time()
        scores = await call_judge(r["question"], context, r["answer_a"], r["answer_b"])
        elapsed = time.time() - t0
        print(f"  评分: A={scores['score_a']} B={scores['score_b']}, {elapsed:.1f}s")

        r["scores"] = scores
        r["judge_time"] = round(elapsed, 1)
        _save_results(results, output_path)

        await asyncio.sleep(10)  # K2.5 限流严重，拉大间隔

    success = sum(1 for r in failed if r.get("scores", {}).get("score_a", 0) > 0)
    print(f"\n[rejudge] 完成: {success}/{len(failed)} 题成功重新评分")


# ======================== 主流程 ========================

async def run_eval(
    questions_path: str,
    output_path: str,
    reports_dir: str,
    skip_ingest: bool = False,
    question_ids: Optional[List[int]] = None,
    top_k: int = DEFAULT_TOP_K,
    rejudge: bool = False,
):
    """运行评估"""
    # 加载题目
    with open(questions_path, "r", encoding="utf-8") as f:
        all_questions = json.load(f)

    if question_ids:
        questions = [q for q in all_questions if q["id"] in question_ids]
    else:
        questions = all_questions

    print(f"\n{'='*60}")
    print(f"基线评估: {len(questions)} 题")
    print(f"回答者 A: {GLM_MODEL} (蒸馏源)")
    print(f"回答者 B: {QWEN_MODEL} (微调目标)")
    print(f"裁判:     {JUDGE_MODEL}")
    print(f"RAG Top-K: {top_k}")
    print(f"{'='*60}\n")

    # 加载已有结果（断点续跑）
    results = []
    done_ids = set()
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            results = json.load(f)
        done_ids = {r["id"] for r in results}
        print(f"[续跑] 已有 {len(done_ids)} 条结果\n")

    # ---- rejudge 模式：只重新跑裁判 ----
    if rejudge:
        await _rejudge_failed(results, output_path)
        print(f"\n{'='*60}")
        print("=== 评估汇总 ===")
        _print_summary(results)
        print(f"\n结果已保存: {output_path}")
        return

    # Step 1: 入库
    if not skip_ingest:
        print("=== Step 1: 确保 PDF 入库 ===\n")
        needed_reports = list({q["report"] for q in questions})
        for report in sorted(needed_reports):
            await ensure_ingested(report, reports_dir)
        print()

    # Step 2: 逐题评估
    print("=== Step 2: 逐题评估 ===\n")
    for idx, q in enumerate(questions):
        qid = q["id"]
        if qid in done_ids:
            print(f"[{idx+1}/{len(questions)}] Q{qid} 已有结果，跳过")
            continue

        print(f"[{idx+1}/{len(questions)}] Q{qid}: {q['question'][:50]}...")

        # 2a. RAG 检索
        t0 = time.time()
        context = await retrieve_context(q["question"], top_k)
        t_retrieve = time.time() - t0
        ctx_len = len(context)
        print(f"  检索: {ctx_len} 字符, {t_retrieve:.1f}s")

        if context == "[未检索到相关内容]":
            print(f"  [WARN] 未检索到内容，跳过评估")
            results.append({
                "id": qid,
                "company": q["company"],
                "category": q["category"],
                "question": q["question"],
                "context_length": 0,
                "status": "no_context",
            })
            _save_results(results, output_path)
            continue

        # 2b. 两个模型分别回答（并发）
        t0 = time.time()
        answer_a_task = call_glm(context, q["question"])
        answer_b_task = call_qwen(context, q["question"])
        answer_a, answer_b = await asyncio.gather(answer_a_task, answer_b_task)
        t_answer = time.time() - t0
        print(f"  回答: A={len(answer_a)}字 B={len(answer_b)}字, {t_answer:.1f}s")

        # 2c. 裁判打分
        t0 = time.time()
        scores = await call_judge(q["question"], context, answer_a, answer_b)
        t_judge = time.time() - t0
        print(f"  评分: A={scores['score_a']} B={scores['score_b']}, {t_judge:.1f}s")

        result = {
            "id": qid,
            "company": q["company"],
            "category": q["category"],
            "question": q["question"],
            "report": q["report"],
            "context": context[:5000],
            "context_length": ctx_len,
            "retrieve_time": round(t_retrieve, 1),
            "answer_time": round(t_answer, 1),
            "judge_time": round(t_judge, 1),
            "answer_a": answer_a,
            "answer_b": answer_b,
            "scores": scores,
            "status": "ok",
        }
        results.append(result)

        # 每题保存一次（断点续跑）
        _save_results(results, output_path)

        # 避免限流（K2.5 RPM 限制严格）
        await asyncio.sleep(5)

    # Step 3: 汇总报告
    print(f"\n{'='*60}")
    print("=== 评估汇总 ===\n")
    _print_summary(results)
    print(f"\n结果已保存: {output_path}")


def _save_results(results: List[Dict], output_path: str):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def _print_summary(results: List[Dict]):
    ok_results = [r for r in results if r.get("status") == "ok"]
    if not ok_results:
        print("无有效评估结果")
        return

    # 总体平均
    avg_a = sum(r["scores"]["score_a"] for r in ok_results) / len(ok_results)
    avg_b = sum(r["scores"]["score_b"] for r in ok_results) / len(ok_results)
    print(f"有效评估: {len(ok_results)} / {len(results)} 题\n")
    print(f"{'模型':<20} {'平均分':<10} {'准确性':<10} {'完整性':<10} {'专业性':<10}")
    print("-" * 60)

    dims = ["accuracy", "completeness", "professionalism"]
    for label, suffix in [("GLM-5.1 (A)", "_a"), ("Qwen3.5-9B (B)", "_b")]:
        scores_by_dim = {}
        for d in dims:
            key = d + suffix
            scores_by_dim[d] = sum(r["scores"].get(key, 0) for r in ok_results) / len(ok_results)
        avg = sum(scores_by_dim.values()) / len(dims)
        print(f"{label:<20} {avg:<10.2f} {scores_by_dim['accuracy']:<10.2f} "
              f"{scores_by_dim['completeness']:<10.2f} {scores_by_dim['professionalism']:<10.2f}")

    print(f"\n差距: GLM-5.1 领先 {avg_a - avg_b:+.2f} 分")

    # 按 category 统计
    categories = sorted(set(r["category"] for r in ok_results))
    if len(categories) > 1:
        print(f"\n--- 按题目类型 ---")
        print(f"{'类型':<20} {'GLM-5.1':<10} {'Qwen3.5-9B':<10} {'差距':<10}")
        print("-" * 50)
        for cat in categories:
            cat_results = [r for r in ok_results if r["category"] == cat]
            ca = sum(r["scores"]["score_a"] for r in cat_results) / len(cat_results)
            cb = sum(r["scores"]["score_b"] for r in cat_results) / len(cat_results)
            print(f"{cat:<20} {ca:<10.2f} {cb:<10.2f} {ca-cb:+.2f}")

    # 无 context 的题目
    no_ctx = [r for r in results if r.get("status") == "no_context"]
    if no_ctx:
        print(f"\n[注意] {len(no_ctx)} 题未检索到上下文:")
        for r in no_ctx:
            print(f"  - Q{r['id']}: {r['question'][:40]}...")


# ======================== 入口 ========================

def main():
    parser = argparse.ArgumentParser(description="基线评估: GLM-5.1 vs Qwen3.5-9B")
    parser.add_argument("--skip-ingest", action="store_true", help="跳过 PDF 入库步骤")
    parser.add_argument("--questions", type=str, default=None,
                        help="指定题号，逗号分隔，如 1,2,3")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K, help="RAG 检索 Top-K")
    parser.add_argument("--output", type=str, default=None, help="输出文件路径")
    parser.add_argument("--rejudge", action="store_true",
                        help="只重新跑裁判（对 score_a==0 的题目重新评分，复用已有回答）")
    args = parser.parse_args()

    scripts_dir = Path(__file__).resolve().parent
    questions_path = scripts_dir / "eval_questions.json"
    output_path = args.output or str(scripts_dir / "eval_results.json")
    reports_dir = str(BACKEND_DIR / "financial_reports")

    question_ids = None
    if args.questions:
        question_ids = [int(x.strip()) for x in args.questions.split(",")]

    asyncio.run(run_eval(
        questions_path=str(questions_path),
        output_path=output_path,
        reports_dir=reports_dir,
        skip_ingest=args.skip_ingest,
        question_ids=question_ids,
        top_k=args.top_k,
        rejudge=args.rejudge,
    ))


if __name__ == "__main__":
    main()
