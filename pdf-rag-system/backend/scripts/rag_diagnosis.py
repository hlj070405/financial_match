"""RAG 检索质量诊断：检查低分题的检索结果是否包含答案所需数据"""
import asyncio, sys, json
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from rag.service import retrieve

CASES = [
    {
        "id": 16,
        "q": "赛力斯2025年的营业收入和净利润分别是多少？问界系列的销量是多少？",
        "keywords": ["1650", "61.5", "42.6", "问界"],
        "note": "Qwen=2.0, 编造了1256.79亿归母净利润",
    },
    {
        "id": 26,
        "q": "美的集团2025年的存货周转天数和应收账款周转天数分别是多少？运营效率如何？",
        "keywords": ["周转天数", "周转率", "存货周转", "应收账款周转"],
        "note": "Qwen=1.7, 编造了4585亿营收等不存在的数据",
    },
    {
        "id": 29,
        "q": "招商银行2025年的ROE是多少？在股份制银行中处于什么水平？",
        "keywords": ["13.44", "ROE", "净资产收益率", "加权平均"],
        "note": "Qwen=2.7, 混淆ROA和ROE",
    },
    {
        "id": 20,
        "q": "宁德时代2024年的经营性现金流量净额是多少？与净利润相比表现如何？",
        "keywords": ["经营活动产生的现金流量净额", "28,357,911", "283"],
        "note": "GLM=2.0, 把283亿读成969亿",
    },
    {
        "id": 8,
        "q": "宁德时代2024年的营业收入和净利润分别是多少？研发费用占营收的比例是多少？",
        "keywords": ["营业收入", "研发投入", "研发费用"],
        "note": "GLM=2.7, 声称合并营收未披露",
    },
    {
        "id": 7,
        "q": "贵州茅台2024年直销渠道和批发渠道的收入占比分别是多少？渠道结构有什么变化？",
        "keywords": ["直销", "批发", "渠道"],
        "note": "Qwen=2.7, 答案过长",
    },
]


async def main():
    for case in CASES:
        qid = case["id"]
        q = case["q"]
        print("=" * 60)
        print("Q%d: %s" % (qid, q))
        print("问题: %s" % case["note"])
        print("-" * 60)

        chunks = await retrieve(q, user_id=9999, top_k=5)
        if not chunks:
            print("  [!] 没有检索到任何chunk")
            print()
            continue

        full_text = ""
        for i, c in enumerate(chunks):
            text = c.get("text", "")
            full_text += text
            src = c.get("source", "?")
            page = c.get("page_number", 0)
            score = c.get("score", 0)
            rerank = c.get("rerank_score", "N/A")
            print("  [%d] %s p%s score=%.3f rerank=%s" % (i + 1, src, page, score, rerank))
            print("      %s" % text[:250].replace("\n", " "))
            print()

        print("  --- 关键词检查 ---")
        for kw in case["keywords"]:
            found = kw in full_text
            print("  [%s] %s" % ("Y" if found else "X", kw))

        print()


if __name__ == "__main__":
    asyncio.run(main())
