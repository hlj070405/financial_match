"""测试巨潮资讯网API的不同参数配置"""
import asyncio
import httpx
import json

async def test_query(stock_code, year, use_stock_param=True):
    """测试不同的查询参数"""
    client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    if use_stock_param:
        print(f"\n{'='*60}")
        print(f"测试1: 使用 stock 参数精确匹配 {stock_code}")
        print(f"{'='*60}")
        data = {
            "pageNum": "1",
            "pageSize": "30",
            "column": "szse",
            "tabName": "fulltext",
            "plate": "",
            "stock": stock_code,
            "searchkey": "",
            "secid": "",
            "category": "category_ndbg_szsh",
            "trade": "",
            "seDate": f"{year-1}-11-30~{year+1}-05-30",
            "sortName": "",
            "sortType": "",
            "isHLtitle": "true"
        }
    else:
        print(f"\n{'='*60}")
        print(f"测试2: 使用 searchkey 参数全文搜索 {stock_code}")
        print(f"{'='*60}")
        data = {
            "pageNum": "1",
            "pageSize": "30",
            "column": "szse",
            "tabName": "fulltext",
            "plate": "",
            "stock": "",
            "searchkey": stock_code,
            "secid": "",
            "category": "category_ndbg_szsh",
            "trade": "",
            "seDate": f"{year-1}-11-30~{year+1}-05-30",
            "sortName": "",
            "sortType": "",
            "isHLtitle": "true"
        }
    
    try:
        response = await client.post(
            'http://www.cninfo.com.cn/new/hisAnnouncement/query',
            data=data,
            headers=headers
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            announcements = result.get('announcements', [])
            print(f"找到公告数量: {len(announcements)}")
            
            if announcements:
                print(f"\n前3条公告:")
                for i, ann in enumerate(announcements[:3], 1):
                    print(f"\n[{i}] {ann.get('announcementTitle', 'N/A')}")
                    print(f"    股票代码: {ann.get('secCode', 'N/A')}")
                    print(f"    公告时间: {ann.get('announcementTime', 'N/A')}")
                    print(f"    PDF链接: {'有' if ann.get('adjunctUrl') else '无'}")
            else:
                print("未找到任何公告")
        else:
            print(f"请求失败: {response.text[:200]}")
            
    except Exception as e:
        print(f"错误: {e}")
    finally:
        await client.aclose()

async def main():
    # 测试平安银行 000001
    stock_code = "000001"
    year = 2023
    
    # 测试使用 stock 参数
    await test_query(stock_code, year, use_stock_param=True)
    
    # 测试使用 searchkey 参数
    await test_query(stock_code, year, use_stock_param=False)

if __name__ == "__main__":
    asyncio.run(main())
