"""
测试带认证的 API 请求，模拟前端行为
"""
import sys
import requests
sys.path.insert(0, r"c:\Users\Administrator\Desktop\大数据 主题赛\pdf-rag-system\backend")

BASE_URL = "http://localhost:8000"

def get_token():
    """登录获取 token"""
    res = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": "test",
        "password": "test123"
    })
    if res.status_code == 200:
        return res.json().get("access_token")
    # 尝试注册
    res = requests.post(f"{BASE_URL}/api/auth/register", json={
        "username": "test",
        "password": "test123"
    })
    if res.status_code == 200:
        return res.json().get("access_token")
    print(f"登录失败: {res.status_code} {res.text}")
    return None


def test_apis(token):
    """测试各个 API"""
    headers = {"Authorization": f"Bearer {token}"}
    ts_code = "688047.SH"
    
    print(f"\n测试股票: {ts_code} (龙芯中科)")
    print("=" * 60)
    
    # 1. daily_basic
    print("\n[1] /api/tushare/daily_basic")
    res = requests.get(f"{BASE_URL}/api/tushare/daily_basic", 
                       params={"ts_code": ts_code}, headers=headers)
    print(f"    状态码: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        print(f"    count: {data.get('count')}")
        if data.get('data') and len(data['data']) > 0:
            d = data['data'][0]
            print(f"    pe: {d.get('pe')}")
            print(f"    pe_ttm: {d.get('pe_ttm')}")
            print(f"    pb: {d.get('pb')}")
            print(f"    dv_ratio: {d.get('dv_ratio')}")
            print(f"    total_mv: {d.get('total_mv')}")
        else:
            print("    ❌ data 为空!")
    else:
        print(f"    错误: {res.text[:200]}")
    
    # 2. balancesheet
    print("\n[2] /api/tushare/balancesheet/{ts_code}")
    res = requests.get(f"{BASE_URL}/api/tushare/balancesheet/{ts_code}", headers=headers)
    print(f"    状态码: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        print(f"    count: {data.get('count')}")
        if data.get('data') and len(data['data']) > 0:
            d = data['data'][0]
            print(f"    end_date: {d.get('end_date')}")
            print(f"    total_assets: {d.get('total_assets')}")
        else:
            print("    ❌ data 为空!")
    else:
        print(f"    错误: {res.text[:200]}")
    
    # 3. cashflow
    print("\n[3] /api/tushare/cashflow/{ts_code}")
    res = requests.get(f"{BASE_URL}/api/tushare/cashflow/{ts_code}", headers=headers)
    print(f"    状态码: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        print(f"    count: {data.get('count')}")
        if data.get('data') and len(data['data']) > 0:
            d = data['data'][0]
            print(f"    end_date: {d.get('end_date')}")
            print(f"    n_cashflow_act: {d.get('n_cashflow_act')}")
        else:
            print("    ❌ data 为空!")
    else:
        print(f"    错误: {res.text[:200]}")
    
    # 4. moneyflow
    print("\n[4] /api/tushare/moneyflow/{ts_code}")
    res = requests.get(f"{BASE_URL}/api/tushare/moneyflow/{ts_code}", headers=headers)
    print(f"    状态码: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        print(f"    count: {data.get('count')}")
    else:
        print(f"    错误: {res.text[:200]}")
    
    print("\n" + "=" * 60)


def main():
    token = get_token()
    if not token:
        print("无法获取 token，请检查后端是否运行")
        return
    print(f"获取 token 成功: {token[:20]}...")
    test_apis(token)


if __name__ == "__main__":
    main()
