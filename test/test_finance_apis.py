"""测试 LLM 驱动的金融分析 API"""

import requests
import json
import time
import sys

BASE = "http://127.0.0.1:8000"

def login():
    r = requests.post(f"{BASE}/api/auth/login", json={"username": "admin", "password": "admin123"})
    if r.status_code != 200:
        print(f"[FAIL] 登录失败: {r.status_code} {r.text}")
        sys.exit(1)
    token = r.json()["access_token"]
    print(f"[OK] 登录成功")
    return {"Authorization": f"Bearer {token}"}


def test_diagnosis(headers):
    print("\n" + "="*60)
    print("测试 /api/diagnosis/analyze (财务诊断)")
    print("="*60)
    t0 = time.time()
    r = requests.post(f"{BASE}/api/diagnosis/analyze", json={"company": "贵州茅台"}, headers=headers, timeout=120)
    elapsed = time.time() - t0
    print(f"  状态码: {r.status_code} ({elapsed:.1f}s)")
    if r.status_code == 200:
        data = r.json()
        print(f"  公司: {data.get('company')}")
        print(f"  周期: {data.get('period')}")
        print(f"  摘要: {data.get('summary', '')[:80]}...")
        comps = data.get("components", [])
        print(f"  组件数: {len(comps)}")
        for c in comps:
            print(f"    - {c.get('type')}: {c.get('title')}")
        return True
    else:
        print(f"  [FAIL] {r.text[:200]}")
        return False


def test_benchmark(headers):
    print("\n" + "="*60)
    print("测试 /api/diagnosis/benchmark (对标分析)")
    print("="*60)
    t0 = time.time()
    r = requests.post(f"{BASE}/api/diagnosis/benchmark",
                      json={"companyA": "贵州茅台", "companyB": "五粮液"},
                      headers=headers, timeout=120)
    elapsed = time.time() - t0
    print(f"  状态码: {r.status_code} ({elapsed:.1f}s)")
    if r.status_code == 200:
        data = r.json()
        print(f"  公司A: {data.get('companyA')}")
        print(f"  公司B: {data.get('companyB')}")
        print(f"  摘要: {data.get('summary', '')[:80]}...")
        metrics = data.get("metrics", [])
        print(f"  指标数: {len(metrics)}")
        for m in metrics[:3]:
            print(f"    - {m.get('name')}: A={m.get('valueA')} B={m.get('valueB')} winner={m.get('winner')}")
        print(f"  雷达A: {data.get('radarA')}")
        print(f"  雷达B: {data.get('radarB')}")
        return True
    else:
        print(f"  [FAIL] {r.text[:200]}")
        return False


def test_risk(headers):
    print("\n" + "="*60)
    print("测试 /api/diagnosis/risk (风险评估)")
    print("="*60)
    t0 = time.time()
    r = requests.post(f"{BASE}/api/diagnosis/risk",
                      json={"company": "比亚迪"},
                      headers=headers, timeout=120)
    elapsed = time.time() - t0
    print(f"  状态码: {r.status_code} ({elapsed:.1f}s)")
    if r.status_code == 200:
        data = r.json()
        print(f"  公司: {data.get('company')}")
        print(f"  综合评分: {data.get('overallScore')}")
        print(f"  风险等级: {data.get('riskLevel')}")
        cats = data.get("categories", [])
        print(f"  风险类别数: {len(cats)}")
        for c in cats[:3]:
            print(f"    - {c.get('name')}: {c.get('score')}分")
        factors = data.get("factors", [])
        print(f"  风险因子数: {len(factors)}")
        print(f"  AI研判: {data.get('aiSummary', '')[:80]}...")
        return True
    else:
        print(f"  [FAIL] {r.text[:200]}")
        return False


def test_chain_map(headers):
    print("\n" + "="*60)
    print("测试 /api/chain/map (产业链图谱)")
    print("="*60)
    t0 = time.time()
    r = requests.post(f"{BASE}/api/chain/map",
                      json={"industry": "新能源汽车"},
                      headers=headers, timeout=120)
    elapsed = time.time() - t0
    print(f"  状态码: {r.status_code} ({elapsed:.1f}s)")
    if r.status_code == 200:
        data = r.json()
        print(f"  行业: {data.get('industry')}")
        levels = data.get("levels", [])
        print(f"  层级数: {len(levels)}")
        nodes = data.get("sankeyNodes", [])
        links = data.get("sankeyLinks", [])
        print(f"  Sankey节点: {len(nodes)}, 链接: {len(links)}")
        cores = data.get("coreCompanies", [])
        print(f"  核心企业: {len(cores)}")
        for c in cores[:3]:
            print(f"    - {c.get('name')} ({c.get('code')}) {c.get('position')}")
        return True
    else:
        print(f"  [FAIL] {r.text[:200]}")
        return False


def test_compete(headers):
    print("\n" + "="*60)
    print("测试 /api/chain/compete (竞争格局)")
    print("="*60)
    t0 = time.time()
    r = requests.post(f"{BASE}/api/chain/compete",
                      json={"industry": "动力电池"},
                      headers=headers, timeout=120)
    elapsed = time.time() - t0
    print(f"  状态码: {r.status_code} ({elapsed:.1f}s)")
    if r.status_code == 200:
        data = r.json()
        print(f"  行业: {data.get('industry')}")
        companies = data.get("companies", [])
        print(f"  企业数: {len(companies)}")
        for c in companies[:3]:
            print(f"    - {c.get('name')}: 市占{c.get('share')}% 营收{c.get('revenue')}亿")
        forces = data.get("porterForces", [])
        print(f"  波特五力: {len(forces)}")
        points = data.get("keyPoints", [])
        print(f"  要点数: {len(points)}")
        return True
    else:
        print(f"  [FAIL] {r.text[:200]}")
        return False


def test_supply_risk(headers):
    print("\n" + "="*60)
    print("测试 /api/chain/supply-risk (供应链风险)")
    print("="*60)
    t0 = time.time()
    r = requests.post(f"{BASE}/api/chain/supply-risk",
                      json={"name": "半导体"},
                      headers=headers, timeout=120)
    elapsed = time.time() - t0
    print(f"  状态码: {r.status_code} ({elapsed:.1f}s)")
    if r.status_code == 200:
        data = r.json()
        print(f"  对象: {data.get('name')}")
        cards = data.get("overallCards", [])
        print(f"  总览卡片: {len(cards)}")
        risks = data.get("risks", [])
        print(f"  风险环节: {len(risks)}")
        for r_ in risks[:3]:
            print(f"    - {r_.get('segment')}: {r_.get('level')} - {r_.get('risk')}")
        print(f"  AI研判: {data.get('aiSummary', '')[:80]}...")
        return True
    else:
        print(f"  [FAIL] {r.text[:200]}")
        return False


if __name__ == "__main__":
    headers = login()
    
    results = {}
    
    # 可以通过命令行参数选择测试哪个
    tests = sys.argv[1:] if len(sys.argv) > 1 else ["diagnosis", "benchmark", "risk", "chain", "compete", "supply"]
    
    if "diagnosis" in tests:
        results["diagnosis"] = test_diagnosis(headers)
    if "benchmark" in tests:
        results["benchmark"] = test_benchmark(headers)
    if "risk" in tests:
        results["risk"] = test_risk(headers)
    if "chain" in tests:
        results["chain"] = test_chain_map(headers)
    if "compete" in tests:
        results["compete"] = test_compete(headers)
    if "supply" in tests:
        results["supply"] = test_supply_risk(headers)
    
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    for name, ok in results.items():
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {name}: {status}")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    print(f"\n  通过: {passed}/{total}")
