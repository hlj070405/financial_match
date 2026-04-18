"""
测试财报下载链路 - 美的集团
分步骤诊断：cninfo查询 → PDF链接 → 下载
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx

STOCK_CODE = "000333"
COMPANY_NAME = "美的集团"


async def test_step1_cninfo_query():
    """步骤1: 测试巨潮资讯网查询接口"""
    print("\n" + "="*60)
    print(f"步骤1: 查询 {COMPANY_NAME}({STOCK_CODE}) 财报列表")
    print("="*60)

    query_url = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'http://www.cninfo.com.cn/new/commonUrl/pageOfSearch?url=disclosure/list/search',
    }

    # 测试年报查询（2024年报）
    data = {
        "pageNum": "1",
        "pageSize": "30",
        "column": "szse",
        "tabName": "fulltext",
        "plate": "",
        "stock": "",
        "searchkey": f"{STOCK_CODE} {COMPANY_NAME}",
        "secid": "",
        "category": "category_ndbg_szsh",  # 年度报告
        "trade": "",
        "seDate": "2024-12-01~2025-05-31",
        "sortName": "",
        "sortType": "",
        "isHLtitle": "true"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=headers) as client:
            print(f"POST {query_url}")
            print(f"searchkey: {data['searchkey']}, category: {data['category']}, seDate: {data['seDate']}")
            resp = await client.post(query_url, data=data)
            print(f"HTTP状态码: {resp.status_code}")

            if resp.status_code != 200:
                print(f"❌ 请求失败: {resp.text[:500]}")
                return None

            result = resp.json()
            announcements = result.get('announcements', [])
            total = result.get('totalAnnouncement', 0)
            print(f"返回公告总数: {total}, 本页: {len(announcements)}")

            if not announcements:
                print("❌ 未找到任何公告，列出完整响应结构:")
                print(list(result.keys()))
                return None

            print(f"\n前5条公告:")
            for i, ann in enumerate(announcements[:5]):
                sec_code = ann.get('secCode', '')
                title = ann.get('announcementTitle', '')
                adj_url = ann.get('adjunctUrl', '')
                match = "✅" if sec_code == STOCK_CODE else "❌"
                print(f"  [{i+1}] {match} {sec_code} | {title}")
                print(f"       adjunctUrl: {adj_url}")

            return announcements

    except Exception as e:
        print(f"❌ 异常: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_step2_find_target(announcements):
    """步骤2: 在结果中匹配目标报告"""
    print("\n" + "="*60)
    print("步骤2: 匹配目标报告")
    print("="*60)

    if not announcements:
        print("❌ 无公告数据，跳过")
        return None

    title_keywords = ["2024年年度报告", "2024年度报告", "2024年报"]
    target = None

    for ann in announcements:
        sec_code = ann.get('secCode', '')
        title = ann.get('announcementTitle', '')

        if sec_code != STOCK_CODE:
            continue

        for kw in title_keywords:
            if kw in title:
                target = ann
                print(f"✅ 精确匹配: {title} (secCode: {sec_code})")
                break
        if target:
            break

    if not target:
        print("未找到精确匹配，尝试代码匹配兜底:")
        for ann in announcements:
            if ann.get('secCode', '') == STOCK_CODE:
                target = ann
                print(f"  兜底匹配: {ann.get('announcementTitle', '')}")
                break

    if not target:
        print(f"❌ 未找到 secCode={STOCK_CODE} 的任何公告")
        print("所有公告的 secCode:", list(set(a.get('secCode','') for a in announcements)))

    return target


async def test_step3_download_pdf(target):
    """步骤3: 下载PDF"""
    print("\n" + "="*60)
    print("步骤3: 下载PDF")
    print("="*60)

    if not target:
        print("❌ 无目标报告，跳过")
        return

    adj_url = target.get('adjunctUrl', '')
    if not adj_url:
        print(f"❌ adjunctUrl 为空，公告字段: {list(target.keys())}")
        return

    pdf_url = f"http://static.cninfo.com.cn/{adj_url}"
    print(f"PDF URL: {pdf_url}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'http://www.cninfo.com.cn/',
    }

    try:
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True, headers=headers) as client:
            resp = await client.get(pdf_url)
            print(f"HTTP状态码: {resp.status_code}")
            print(f"Content-Type: {resp.headers.get('content-type', 'unknown')}")
            print(f"Content-Length: {len(resp.content) / 1024:.1f} KB")

            if resp.status_code == 200 and len(resp.content) > 10000:
                print(f"✅ PDF下载成功")
            else:
                print(f"❌ 下载异常，前200字节: {resp.content[:200]}")
    except Exception as e:
        print(f"❌ 下载异常: {e}")
        import traceback
        traceback.print_exc()


async def main():
    print(f"测试目标: {COMPANY_NAME}({STOCK_CODE}) 2024年年报")

    announcements = await test_step1_cninfo_query()
    target = await test_step2_find_target(announcements)
    await test_step3_download_pdf(target)

    print("\n" + "="*60)
    print("测试完成")


if __name__ == "__main__":
    asyncio.run(main())
