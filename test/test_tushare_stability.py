"""
Tushare 接口稳定性测试
测试多个接口的响应时间和成功率
"""
import sys
import time
import statistics
sys.path.insert(0, r"c:\Users\Administrator\Desktop\大数据 主题赛\pdf-rag-system\backend")

from services.tushare_service import TushareService


def test_api(name: str, func, *args, **kwargs):
    """测试单个 API 的响应时间和成功率"""
    results = []
    errors = []
    
    for i in range(3):  # 每个接口测试3次
        start = time.time()
        try:
            data = func(*args, **kwargs)
            elapsed = time.time() - start
            
            # 检查是否有错误
            if data and isinstance(data, list) and len(data) > 0:
                if isinstance(data[0], dict) and "error" in data[0]:
                    errors.append(data[0]["error"])
                else:
                    results.append({
                        "time": elapsed,
                        "count": len(data)
                    })
            elif isinstance(data, dict):
                if "error" in data:
                    errors.append(data["error"])
                else:
                    results.append({
                        "time": elapsed,
                        "count": 1
                    })
            else:
                results.append({
                    "time": elapsed,
                    "count": len(data) if data else 0
                })
        except Exception as e:
            errors.append(str(e))
        
        time.sleep(0.3)  # 避免频率限制
    
    return {
        "name": name,
        "success": len(results),
        "failed": len(errors),
        "errors": errors[:2] if errors else [],
        "avg_time": statistics.mean([r["time"] for r in results]) if results else None,
        "min_time": min([r["time"] for r in results]) if results else None,
        "max_time": max([r["time"] for r in results]) if results else None,
        "data_count": results[0]["count"] if results else 0
    }


def main():
    print("=" * 60)
    print("Tushare 接口稳定性测试")
    print("=" * 60)
    
    # 1. 测试连接
    print("\n[1] 测试连接...")
    conn = TushareService.test_connection()
    print(f"    状态: {conn.get('status')}")
    print(f"    消息: {conn.get('message')}")
    print(f"    Token: {conn.get('token_prefix')}")
    
    if conn.get("status") != "ok":
        print("\n❌ 连接失败，无法继续测试")
        return
    
    print("\n" + "-" * 60)
    
    # 2. 测试各个接口
    tests = [
        ("股票基本信息 stock_basic", TushareService.get_stock_basic),
        ("交易日历 trade_cal", TushareService.get_trade_calendar),
        ("日线行情 daily (000001.SZ)", lambda: TushareService.get_daily("000001.SZ")),
        ("每日指标 daily_basic (000001.SZ)", lambda: TushareService.get_daily_basic(ts_code="000001.SZ")),
        ("周线行情 weekly (000001.SZ)", lambda: TushareService.get_weekly("000001.SZ")),
        ("指数基本信息 index_basic", TushareService.get_index_basic),
        ("指数日线 index_daily (000001.SH)", lambda: TushareService.get_index_daily("000001.SH")),
        ("资金流向 moneyflow (000001.SZ)", lambda: TushareService.get_moneyflow("000001.SZ")),
        ("资产负债表 balancesheet (000001.SZ)", lambda: TushareService.get_balancesheet("000001.SZ")),
        ("现金流量表 cashflow (000001.SZ)", lambda: TushareService.get_cashflow("000001.SZ")),
    ]
    
    all_results = []
    
    for i, (name, func) in enumerate(tests, 1):
        print(f"\n[{i+1}] 测试 {name}...")
        if callable(func) and func.__name__ == "<lambda>":
            result = test_api(name, func)
        else:
            result = test_api(name, func)
        
        all_results.append(result)
        
        status = "✅" if result["success"] == 3 else ("⚠️" if result["success"] > 0 else "❌")
        print(f"    {status} 成功: {result['success']}/3, 数据量: {result['data_count']}")
        if result["avg_time"]:
            print(f"    ⏱️  响应时间: 平均 {result['avg_time']:.2f}s, 最小 {result['min_time']:.2f}s, 最大 {result['max_time']:.2f}s")
        if result["errors"]:
            print(f"    ❌ 错误: {result['errors'][0][:80]}")
    
    # 3. 汇总
    print("\n" + "=" * 60)
    print("测试汇总")
    print("=" * 60)
    
    total_success = sum(r["success"] for r in all_results)
    total_tests = len(all_results) * 3
    success_rate = total_success / total_tests * 100
    
    avg_times = [r["avg_time"] for r in all_results if r["avg_time"]]
    overall_avg = statistics.mean(avg_times) if avg_times else 0
    
    print(f"\n总成功率: {success_rate:.1f}% ({total_success}/{total_tests})")
    print(f"平均响应时间: {overall_avg:.2f}s")
    
    failed = [r for r in all_results if r["success"] < 3]
    if failed:
        print(f"\n⚠️ 不稳定接口:")
        for r in failed:
            print(f"   - {r['name']}: {r['success']}/3 成功")
    else:
        print(f"\n✅ 所有接口稳定!")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
