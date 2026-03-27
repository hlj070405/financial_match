"""
测试特定股票的数据返回情况
检查龙芯中科 688047.SH 的数据
"""
import sys
import json
sys.path.insert(0, r"c:\Users\Administrator\Desktop\大数据 主题赛\pdf-rag-system\backend")

from services.tushare_service import TushareService


def main():
    ts_code = "688047.SH"  # 龙芯中科
    print(f"测试股票: {ts_code}")
    print("=" * 60)
    
    # 1. 每日指标
    print("\n[1] daily_basic - 每日指标")
    data = TushareService.get_daily_basic(ts_code=ts_code)
    print(f"    返回数据量: {len(data)}")
    if data and len(data) > 0:
        d = data[0]
        print(f"    trade_date: {d.get('trade_date')}")
        print(f"    close: {d.get('close')}")
        print(f"    pe: {d.get('pe')}")
        print(f"    pe_ttm: {d.get('pe_ttm')}")
        print(f"    pb: {d.get('pb')}")
        print(f"    ps: {d.get('ps')}")
        print(f"    turnover_rate: {d.get('turnover_rate')}")
        print(f"    dv_ratio (股息率): {d.get('dv_ratio')}")
        print(f"    total_mv: {d.get('total_mv')}")
        print(f"    circ_mv: {d.get('circ_mv')}")
        print(f"    完整数据: {json.dumps(d, ensure_ascii=False, default=str)}")
    else:
        print("    ❌ 无数据返回!")
    
    # 2. 资产负债表
    print("\n[2] balancesheet - 资产负债表")
    data = TushareService.get_balancesheet(ts_code=ts_code)
    print(f"    返回数据量: {len(data)}")
    if data and len(data) > 0:
        d = data[0]
        print(f"    end_date: {d.get('end_date')}")
        print(f"    total_assets: {d.get('total_assets')}")
        print(f"    total_liab: {d.get('total_liab')}")
    else:
        print("    ❌ 无数据返回!")
        if data and isinstance(data[0], dict) and "error" in data[0]:
            print(f"    错误: {data[0]['error']}")
    
    # 3. 现金流量表
    print("\n[3] cashflow - 现金流量表")
    data = TushareService.get_cashflow(ts_code=ts_code)
    print(f"    返回数据量: {len(data)}")
    if data and len(data) > 0:
        d = data[0]
        print(f"    end_date: {d.get('end_date')}")
        print(f"    n_cashflow_act: {d.get('n_cashflow_act')}")
    else:
        print("    ❌ 无数据返回!")
    
    # 4. 日线行情
    print("\n[4] daily - 日线行情")
    data = TushareService.get_daily(ts_code=ts_code)
    print(f"    返回数据量: {len(data)}")
    if data and len(data) > 0:
        print(f"    最新: {data[-1].get('trade_date')} close={data[-1].get('close')}")
    
    # 5. 资金流向
    print("\n[5] moneyflow - 资金流向")
    data = TushareService.get_moneyflow(ts_code=ts_code)
    print(f"    返回数据量: {len(data)}")
    if data and len(data) > 0:
        print(f"    最新: {data[-1].get('trade_date')}")
    else:
        print("    ❌ 无数据返回!")
    
    print("\n" + "=" * 60)
    print("测试完成")


if __name__ == "__main__":
    main()
