"""
回测模块端到端测试
直接调用引擎层，不依赖 FastAPI 服务
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pdf-rag-system", "backend"))


def test_data_store():
    """测试 BaoStock 数据获取 + Parquet 缓存"""
    from backtest.data_store import fetch_daily, clear_cache

    print("=" * 60)
    print("[1] 测试数据获取: 平安银行 (000001.SZ)")
    print("=" * 60)

    # 清缓存确保真实下载
    clear_cache("000001.SZ")

    t0 = time.time()
    df = fetch_daily("000001.SZ", "2023-01-01", "2024-12-31")
    t1 = time.time()

    print(f"  首次下载: {len(df)} 条, 耗时 {t1 - t0:.2f}s")
    print(f"  列: {list(df.columns)}")
    print(f"  日期范围: {df['date'].iloc[0]} ~ {df['date'].iloc[-1]}")
    print(f"  收盘价范围: {df['close'].min():.2f} ~ {df['close'].max():.2f}")

    # 第二次读缓存
    t2 = time.time()
    df2 = fetch_daily("000001.SZ", "2023-01-01", "2024-12-31")
    t3 = time.time()

    print(f"  缓存读取: {len(df2)} 条, 耗时 {t3 - t2:.4f}s")
    assert len(df2) == len(df), "缓存数据条数不一致"
    print("  ✅ 数据获取+缓存 通过\n")
    return True


def test_strategies():
    """测试策略注册表"""
    from backtest.strategies import list_strategies, get_strategy

    print("=" * 60)
    print("[2] 测试策略注册表")
    print("=" * 60)

    strategies = list_strategies()
    print(f"  已注册策略: {len(strategies)} 个")
    for s in strategies:
        print(f"    - {s['id']}: {s['name']} ({len(s['params'])} 个参数)")

    # 获取特定策略
    sma = get_strategy("sma_cross")
    assert sma["cls"] is not None
    print("  ✅ 策略注册表 通过\n")
    return True


def test_backtest_sma():
    """测试双均线交叉回测"""
    from backtest.engine import run_backtest

    print("=" * 60)
    print("[3] 测试回测: 平安银行 双均线交叉 (2023-2024)")
    print("=" * 60)

    t0 = time.time()
    result = run_backtest(
        ts_code="000001.SZ",
        strategy_id="sma_cross",
        params={"short_period": 5, "long_period": 20},
        start_date="2023-01-01",
        end_date="2024-12-31",
        initial_cash=100000,
    )
    t1 = time.time()

    s = result["summary"]
    print(f"  耗时: {t1 - t0:.2f}s")
    print(f"  初始资金: ¥{s['initial_cash']:,.0f}")
    print(f"  最终价值: ¥{s['final_value']:,.2f}")
    print(f"  总收益率: {s['total_return_pct']:.2f}%")
    print(f"  年化收益: {s['annual_return_pct']:.2f}%")
    print(f"  夏普比率: {s['sharpe_ratio']:.4f}")
    print(f"  最大回撤: {s['max_drawdown_pct']:.2f}%")
    print(f"  总交易数: {s['total_trades']}")
    print(f"  胜率: {s['win_rate_pct']:.1f}%")
    print(f"  资金曲线点数: {len(result['equity_curve'])}")
    print(f"  交易明细数: {len(result['trades'])}")

    assert result["status"] == "ok"
    assert s["final_value"] > 0
    assert len(result["equity_curve"]) > 0
    print("  ✅ 双均线回测 通过\n")
    return True


def test_backtest_macd():
    """测试 MACD 回测"""
    from backtest.engine import run_backtest

    print("=" * 60)
    print("[4] 测试回测: 贵州茅台 MACD (2022-2024)")
    print("=" * 60)

    t0 = time.time()
    result = run_backtest(
        ts_code="600519.SH",
        strategy_id="macd_signal",
        start_date="2022-01-01",
        end_date="2024-12-31",
        initial_cash=200000,
    )
    t1 = time.time()

    s = result["summary"]
    print(f"  耗时: {t1 - t0:.2f}s")
    print(f"  最终价值: ¥{s['final_value']:,.2f} (收益 {s['total_return_pct']:.2f}%)")
    print(f"  夏普: {s['sharpe_ratio']:.4f}, 回撤: {s['max_drawdown_pct']:.2f}%")
    print(f"  交易: {s['total_trades']}笔, 胜率: {s['win_rate_pct']:.1f}%")

    assert result["status"] == "ok"
    print("  ✅ MACD回测 通过\n")
    return True


def test_backtest_rsi():
    """测试 RSI 回测"""
    from backtest.engine import run_backtest

    print("=" * 60)
    print("[5] 测试回测: 比亚迪 RSI超卖反弹 (2023-2024)")
    print("=" * 60)

    t0 = time.time()
    result = run_backtest(
        ts_code="002594.SZ",
        strategy_id="rsi_reversal",
        params={"period": 14, "oversold": 30, "overbought": 70},
        start_date="2023-01-01",
        end_date="2024-12-31",
    )
    t1 = time.time()

    s = result["summary"]
    print(f"  耗时: {t1 - t0:.2f}s")
    print(f"  最终价值: ¥{s['final_value']:,.2f} (收益 {s['total_return_pct']:.2f}%)")
    print(f"  交易: {s['total_trades']}笔, 胜率: {s['win_rate_pct']:.1f}%")

    assert result["status"] == "ok"
    print("  ✅ RSI回测 通过\n")
    return True


if __name__ == "__main__":
    passed = 0
    failed = 0

    for test_fn in [test_data_store, test_strategies, test_backtest_sma, test_backtest_macd, test_backtest_rsi]:
        try:
            if test_fn():
                passed += 1
        except Exception as e:
            failed += 1
            print(f"  ❌ {test_fn.__name__} 失败: {e}")
            import traceback
            traceback.print_exc()
            print()

    print("=" * 60)
    print(f"总计: {passed} 通过, {failed} 失败")
    print("=" * 60)
