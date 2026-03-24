"""详细测试平安银行查询 - 尝试不同的column参数"""
import asyncio
import httpx

async def test_different_columns():
    client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    stock_code = "000001"
    year = 2023
    
    # 测试不同的column值
    columns = ["szse", "sse", "szse_main", "sse_main", ""]
    
    for column in columns:
        print(f"\n{'='*60}")
        print(f"测试 column='{column}'")
        print(f"{'='*60}")
        
        data = {
            "pageNum": "1",
            "pageSize": "30",
            "column": column,
            "tabName": "fulltext",
            "plate": "",
            "stock": stock_code,  # 先试试stock参数
            "searchkey": "",
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
            
            if response.status_code == 200:
                result = response.json()
                announcements = result.get('announcements', [])
                
                if announcements:
                    print(f"✅ 找到 {len(announcements)} 条公告")
                    for i, ann in enumerate(announcements[:3], 1):
                        print(f"\n[{i}] {ann.get('announcementTitle', 'N/A')}")
                        print(f"    股票代码: {ann.get('secCode', 'N/A')}")
                        print(f"    公司: {ann.get('secName', 'N/A')}")
                else:
                    print(f"❌ 未找到公告 (announcements={announcements})")
            else:
                print(f"❌ 请求失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 错误: {e}")
    
    # 特别测试：直接搜索"平安银行"
    print(f"\n{'='*60}")
    print(f"测试 searchkey='平安银行'")
    print(f"{'='*60}")
    
    data = {
        "pageNum": "1",
        "pageSize": "30",
        "column": "szse",
        "tabName": "fulltext",
        "plate": "",
        "stock": "",
        "searchkey": "平安银行",
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
        
        if response.status_code == 200:
            result = response.json()
            announcements = result.get('announcements', [])
            
            if announcements:
                print(f"✅ 找到 {len(announcements)} 条公告")
                for i, ann in enumerate(announcements[:5], 1):
                    print(f"\n[{i}] {ann.get('announcementTitle', 'N/A')}")
                    print(f"    股票代码: {ann.get('secCode', 'N/A')}")
                    print(f"    公司: {ann.get('secName', 'N/A')}")
            else:
                print(f"❌ 未找到公告")
        else:
            print(f"❌ 请求失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 错误: {e}")
    
    await client.aclose()

if __name__ == "__main__":
    asyncio.run(test_different_columns())
