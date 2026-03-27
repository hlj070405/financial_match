"""
Tushare 接口返回内容详细测试
验证每个接口的返回字段和数据格式是否符合预期
"""
import sys
import json
sys.path.insert(0, r"c:\Users\Administrator\Desktop\大数据 主题赛\pdf-rag-system\backend")

from services.tushare_service import TushareService


def check_fields(data, expected_fields, name):
    """检查返回数据是否包含预期字段"""
    if not data:
        return False, "返回数据为空"
    
    if isinstance(data, list) and len(data) > 0:
        if isinstance(data[0], dict) and "error" in data[0]:
            return False, f"接口错误: {data[0]['error']}"
        sample = data[0]
    elif isinstance(data, dict):
        if "error" in data:
            return False, f"接口错误: {data['error']}"
        sample = data
    else:
        return False, f"未知数据格式: {type(data)}"
    
    missing = [f for f in expected_fields if f not in sample]
    extra = [f for f in sample.keys() if f not in expected_fields]
    
    return len(missing) == 0, {
        "missing": missing,
        "extra": extra,
        "actual_fields": list(sample.keys())
    }


def print_sample(data, max_rows=2):
    """打印样本数据"""
    if isinstance(data, list) and len(data) > 0:
        for i, row in enumerate(data[:max_rows]):
            print(f"      [{i}] {json.dumps(row, ensure_ascii=False, default=str)[:200]}")
    elif isinstance(data, dict):
        print(f"      {json.dumps(data, ensure_ascii=False, default=str)[:200]}")


def test_stock_basic():
    """测试股票基本信息"""
    print("\n" + "=" * 60)
    print("[1] stock_basic - 股票基本信息")
    print("=" * 60)
    
    expected = ["ts_code", "symbol", "name", "area", "industry", "market", "list_date"]
    data = TushareService.get_stock_basic()
    
    ok, info = check_fields(data, expected, "stock_basic")
    print(f"    数据量: {len(data)}")
    print(f"    预期字段: {expected}")
    print(f"    字段检查: {'✅ 通过' if ok else '❌ 失败'}")
    if not ok and isinstance(info, dict):
        if info["missing"]:
            print(f"    缺失字段: {info['missing']}")
        if info["extra"]:
            print(f"    额外字段: {info['extra']}")
    
    print("    样本数据:")
    print_sample(data)
    
    # 数据合理性检查
    if data and len(data) > 0:
        sample = data[0]
        checks = []
        if sample.get("ts_code") and "." in sample["ts_code"]:
            checks.append("✅ ts_code 格式正确 (含交易所后缀)")
        else:
            checks.append("❌ ts_code 格式异常")
        
        if sample.get("name") and len(sample["name"]) >= 2:
            checks.append("✅ name 非空")
        else:
            checks.append("❌ name 为空或过短")
        
        if sample.get("list_date") and len(sample["list_date"]) == 8:
            checks.append("✅ list_date 格式正确 (YYYYMMDD)")
        else:
            checks.append("⚠️ list_date 格式可能异常")
        
        print("    数据合理性:")
        for c in checks:
            print(f"      {c}")
    
    return ok


def test_trade_calendar():
    """测试交易日历"""
    print("\n" + "=" * 60)
    print("[2] trade_cal - 交易日历")
    print("=" * 60)
    
    expected = ["exchange", "cal_date", "is_open", "pretrade_date"]
    data = TushareService.get_trade_calendar()
    
    ok, info = check_fields(data, expected, "trade_cal")
    print(f"    数据量: {len(data)}")
    print(f"    预期字段: {expected}")
    print(f"    字段检查: {'✅ 通过' if ok else '❌ 失败'}")
    
    print("    样本数据:")
    print_sample(data)
    
    # 数据合理性检查
    if data and len(data) > 0:
        sample = data[0]
        checks = []
        if sample.get("is_open") in [0, 1]:
            checks.append("✅ is_open 为 0 或 1")
        else:
            checks.append(f"❌ is_open 值异常: {sample.get('is_open')}")
        
        if sample.get("exchange") in ["SSE", "SZSE"]:
            checks.append("✅ exchange 为有效交易所")
        else:
            checks.append(f"⚠️ exchange 值: {sample.get('exchange')}")
        
        print("    数据合理性:")
        for c in checks:
            print(f"      {c}")
    
    return ok


def test_daily():
    """测试日线行情"""
    print("\n" + "=" * 60)
    print("[3] daily - 日线行情 (000001.SZ 平安银行)")
    print("=" * 60)
    
    expected = ["ts_code", "trade_date", "open", "high", "low", "close", "vol", "amount"]
    data = TushareService.get_daily("000001.SZ")
    
    ok, info = check_fields(data, expected, "daily")
    print(f"    数据量: {len(data)}")
    print(f"    预期字段: {expected}")
    print(f"    字段检查: {'✅ 通过' if ok else '❌ 失败'}")
    if not ok and isinstance(info, dict):
        print(f"    实际字段: {info.get('actual_fields')}")
    
    print("    样本数据:")
    print_sample(data)
    
    # 数据合理性检查
    if data and len(data) > 0:
        sample = data[-1]  # 最新一条
        checks = []
        
        if sample.get("open") and sample.get("close"):
            if 0 < sample["open"] < 1000 and 0 < sample["close"] < 1000:
                checks.append(f"✅ 价格合理 (open={sample['open']}, close={sample['close']})")
            else:
                checks.append(f"⚠️ 价格可能异常")
        
        if sample.get("high") and sample.get("low"):
            if sample["high"] >= sample["low"]:
                checks.append("✅ high >= low")
            else:
                checks.append("❌ high < low 数据异常")
        
        if sample.get("vol") and sample["vol"] > 0:
            checks.append(f"✅ 成交量 > 0 (vol={sample['vol']})")
        
        print("    数据合理性:")
        for c in checks:
            print(f"      {c}")
    
    return ok


def test_daily_basic():
    """测试每日指标"""
    print("\n" + "=" * 60)
    print("[4] daily_basic - 每日指标 (000001.SZ)")
    print("=" * 60)
    
    expected = ["ts_code", "trade_date", "close", "turnover_rate", "pe", "pe_ttm", "pb", "total_mv", "circ_mv"]
    data = TushareService.get_daily_basic(ts_code="000001.SZ")
    
    ok, info = check_fields(data, expected, "daily_basic")
    print(f"    数据量: {len(data)}")
    print(f"    预期字段: {expected}")
    print(f"    字段检查: {'✅ 通过' if ok else '❌ 失败'}")
    if not ok and isinstance(info, dict):
        print(f"    实际字段: {info.get('actual_fields')}")
    
    print("    样本数据:")
    print_sample(data)
    
    # 数据合理性检查
    if data and len(data) > 0:
        sample = data[0]
        checks = []
        
        pe = sample.get("pe") or sample.get("pe_ttm")
        if pe and 0 < pe < 1000:
            checks.append(f"✅ PE 合理 ({pe:.2f})")
        elif pe:
            checks.append(f"⚠️ PE 可能异常 ({pe})")
        
        pb = sample.get("pb")
        if pb and 0 < pb < 100:
            checks.append(f"✅ PB 合理 ({pb:.2f})")
        
        total_mv = sample.get("total_mv")
        if total_mv and total_mv > 0:
            checks.append(f"✅ 总市值 > 0 ({total_mv/10000:.0f}亿)")
        
        print("    数据合理性:")
        for c in checks:
            print(f"      {c}")
    
    return ok


def test_index_daily():
    """测试指数日线"""
    print("\n" + "=" * 60)
    print("[5] index_daily - 指数日线 (000001.SH 上证综指)")
    print("=" * 60)
    
    expected = ["ts_code", "trade_date", "open", "high", "low", "close", "vol", "amount"]
    data = TushareService.get_index_daily("000001.SH")
    
    ok, info = check_fields(data, expected, "index_daily")
    print(f"    数据量: {len(data)}")
    print(f"    预期字段: {expected}")
    print(f"    字段检查: {'✅ 通过' if ok else '❌ 失败'}")
    if not ok and isinstance(info, dict):
        print(f"    实际字段: {info.get('actual_fields')}")
    
    print("    样本数据:")
    print_sample(data)
    
    # 数据合理性检查
    if data and len(data) > 0:
        sample = data[-1]  # 最新一条
        checks = []
        
        close = sample.get("close")
        if close and 2000 < close < 10000:
            checks.append(f"✅ 上证综指点位合理 ({close:.2f})")
        elif close:
            checks.append(f"⚠️ 点位可能异常 ({close})")
        
        print("    数据合理性:")
        for c in checks:
            print(f"      {c}")
    
    return ok


def test_moneyflow():
    """测试资金流向"""
    print("\n" + "=" * 60)
    print("[6] moneyflow - 资金流向 (000001.SZ)")
    print("=" * 60)
    
    expected = ["ts_code", "trade_date", "buy_sm_vol", "sell_sm_vol", "buy_md_vol", "sell_md_vol", 
                "buy_lg_vol", "sell_lg_vol", "buy_elg_vol", "sell_elg_vol", "net_mf_vol"]
    data = TushareService.get_moneyflow("000001.SZ")
    
    ok, info = check_fields(data, expected, "moneyflow")
    print(f"    数据量: {len(data)}")
    print(f"    预期字段: {expected}")
    print(f"    字段检查: {'✅ 通过' if ok else '❌ 失败'}")
    if not ok and isinstance(info, dict):
        print(f"    实际字段: {info.get('actual_fields')}")
    
    print("    样本数据:")
    print_sample(data)
    
    return ok


def test_balancesheet():
    """测试资产负债表"""
    print("\n" + "=" * 60)
    print("[7] balancesheet - 资产负债表 (000001.SZ)")
    print("=" * 60)
    
    # 资产负债表字段很多，只检查核心字段
    expected = ["ts_code", "ann_date", "end_date", "total_assets", "total_liab", "total_hldr_eqy_exc_min_int"]
    data = TushareService.get_balancesheet("000001.SZ")
    
    ok, info = check_fields(data, expected, "balancesheet")
    print(f"    数据量: {len(data)}")
    print(f"    预期核心字段: {expected}")
    print(f"    字段检查: {'✅ 通过' if ok else '❌ 失败'}")
    if not ok and isinstance(info, dict):
        print(f"    缺失字段: {info.get('missing')}")
        print(f"    实际字段数: {len(info.get('actual_fields', []))}")
    
    print("    样本数据 (部分字段):")
    if data and len(data) > 0:
        sample = data[0]
        key_fields = ["ts_code", "end_date", "total_assets", "total_liab"]
        filtered = {k: sample.get(k) for k in key_fields}
        print(f"      {json.dumps(filtered, ensure_ascii=False, default=str)}")
    
    # 数据合理性检查
    if data and len(data) > 0:
        sample = data[0]
        checks = []
        
        total_assets = sample.get("total_assets")
        total_liab = sample.get("total_liab")
        if total_assets and total_liab:
            if total_assets > total_liab:
                checks.append(f"✅ 总资产 > 总负债 (资产={total_assets/1e8:.0f}亿, 负债={total_liab/1e8:.0f}亿)")
            else:
                checks.append("⚠️ 总资产 <= 总负债")
        
        print("    数据合理性:")
        for c in checks:
            print(f"      {c}")
    
    return ok


def test_cashflow():
    """测试现金流量表"""
    print("\n" + "=" * 60)
    print("[8] cashflow - 现金流量表 (000001.SZ)")
    print("=" * 60)
    
    expected = ["ts_code", "ann_date", "end_date", "n_cashflow_act", "n_cashflow_inv_act", "n_cash_flows_fnc_act"]
    data = TushareService.get_cashflow("000001.SZ")
    
    ok, info = check_fields(data, expected, "cashflow")
    print(f"    数据量: {len(data)}")
    print(f"    预期核心字段: {expected}")
    print(f"    字段检查: {'✅ 通过' if ok else '❌ 失败'}")
    if not ok and isinstance(info, dict):
        print(f"    缺失字段: {info.get('missing')}")
        print(f"    实际字段数: {len(info.get('actual_fields', []))}")
    
    print("    样本数据 (部分字段):")
    if data and len(data) > 0:
        sample = data[0]
        key_fields = ["ts_code", "end_date", "n_cashflow_act", "n_cashflow_inv_act", "n_cash_flows_fnc_act"]
        filtered = {k: sample.get(k) for k in key_fields}
        print(f"      {json.dumps(filtered, ensure_ascii=False, default=str)}")
    
    return ok


def main():
    print("=" * 60)
    print("Tushare 接口返回内容详细测试")
    print("=" * 60)
    
    results = []
    
    results.append(("stock_basic", test_stock_basic()))
    results.append(("trade_cal", test_trade_calendar()))
    results.append(("daily", test_daily()))
    results.append(("daily_basic", test_daily_basic()))
    results.append(("index_daily", test_index_daily()))
    results.append(("moneyflow", test_moneyflow()))
    results.append(("balancesheet", test_balancesheet()))
    results.append(("cashflow", test_cashflow()))
    
    # 汇总
    print("\n" + "=" * 60)
    print("测试汇总")
    print("=" * 60)
    
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    
    print(f"\n字段检查通过: {passed}/{total}")
    
    for name, ok in results:
        status = "✅" if ok else "❌"
        print(f"  {status} {name}")
    
    if passed == total:
        print("\n✅ 所有接口返回内容符合预期!")
    else:
        failed = [name for name, ok in results if not ok]
        print(f"\n⚠️ 以下接口需要检查: {failed}")


if __name__ == "__main__":
    main()
