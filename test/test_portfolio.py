"""
虚拟持仓模块测试
直接调用 service 层，使用 SQLite 内存数据库
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pdf-rag-system", "backend"))

# 使用内存数据库避免影响生产环境
os.environ["DATABASE_URL"] = "sqlite:///./test_portfolio.db"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.database import Base


# 创建测试数据库
test_engine = create_engine("sqlite:///./test_portfolio.db")
TestSession = sessionmaker(bind=test_engine)
Base.metadata.create_all(bind=test_engine)


def test_create_portfolio():
    """测试自动创建默认组合"""
    from portfolio.service import get_or_create_portfolio

    db = TestSession()
    try:
        p = get_or_create_portfolio(db, user_id=999)
        print(f"[1] 创建组合: id={p.id}, name={p.name}, 初始资金={p.initial_cash/100:.0f}元")
        assert p.name == "默认组合"
        assert p.user_id == 999

        # 再次获取应该是同一个
        p2 = get_or_create_portfolio(db, user_id=999)
        assert p.id == p2.id
        print("  ✅ 组合创建/获取 通过\n")
    finally:
        db.close()


def test_buy_stock():
    """测试买入"""
    from portfolio.service import add_transaction, calc_positions

    db = TestSession()
    try:
        print("[2] 测试买入: 10000股平安银行 @ 11.50元")
        result = add_transaction(
            db=db, user_id=999,
            ts_code="000001.SZ", stock_name="平安银行",
            direction="buy", price=11.50, quantity=10000,
        )
        assert result["status"] == "ok"
        txn = result["transaction"]
        print(f"  成交金额: ¥{txn['turnover']:,.2f}")
        print(f"  佣金: ¥{txn['commission']:.2f}")
        print(f"  总成本: ¥{txn['total_cost']:,.2f}")

        # 检查持仓
        positions = calc_positions(db, user_id=999)
        pos = positions["000001.SZ"]
        print(f"  持仓: {pos['quantity']}股, 平均成本: ¥{pos['avg_cost']:.4f}")
        assert pos["quantity"] == 10000
        print("  ✅ 买入 通过\n")
    finally:
        db.close()


def test_buy_more():
    """测试加仓（验证加权平均成本）"""
    from portfolio.service import add_transaction, calc_positions

    db = TestSession()
    try:
        print("[3] 测试加仓: 5000股平安银行 @ 12.00元")
        result = add_transaction(
            db=db, user_id=999,
            ts_code="000001.SZ", stock_name="平安银行",
            direction="buy", price=12.00, quantity=5000,
        )
        assert result["status"] == "ok"

        positions = calc_positions(db, user_id=999)
        pos = positions["000001.SZ"]
        print(f"  持仓: {pos['quantity']}股, 加权平均成本: ¥{pos['avg_cost']:.4f}")
        assert pos["quantity"] == 15000
        # 平均成本应该在 11.50 和 12.00 之间
        assert 11.50 < pos["avg_cost"] < 12.10
        print("  ✅ 加仓+加权平均成本 通过\n")
    finally:
        db.close()


def test_sell_stock():
    """测试卖出 + 盈亏计算"""
    from portfolio.service import add_transaction, calc_positions

    db = TestSession()
    try:
        print("[4] 测试卖出: 5000股平安银行 @ 13.00元")
        result = add_transaction(
            db=db, user_id=999,
            ts_code="000001.SZ", stock_name="平安银行",
            direction="sell", price=13.00, quantity=5000,
        )
        assert result["status"] == "ok"
        txn = result["transaction"]
        print(f"  成交金额: ¥{txn['turnover']:,.2f}")
        print(f"  佣金: ¥{txn['commission']:.2f}, 印花税: ¥{txn['stamp_tax']:.2f}")

        positions = calc_positions(db, user_id=999)
        pos = positions["000001.SZ"]
        print(f"  剩余: {pos['quantity']}股, 已实现盈亏: ¥{pos['realized_pnl']:.2f}")
        assert pos["quantity"] == 10000
        assert pos["realized_pnl"] > 0  # 13 > 平均成本，应该盈利
        print("  ✅ 卖出+盈亏 通过\n")
    finally:
        db.close()


def test_sell_too_much():
    """测试超额卖出（应失败）"""
    from portfolio.service import add_transaction

    db = TestSession()
    try:
        print("[5] 测试超额卖出: 50000股（应失败）")
        result = add_transaction(
            db=db, user_id=999,
            ts_code="000001.SZ", stock_name="平安银行",
            direction="sell", price=13.00, quantity=50000,
        )
        assert result["status"] == "error"
        print(f"  正确拒绝: {result['message']}")
        print("  ✅ 超额卖出拦截 通过\n")
    finally:
        db.close()


def test_portfolio_summary():
    """测试组合汇总"""
    from portfolio.service import get_portfolio_summary

    db = TestSession()
    try:
        print("[6] 测试组合汇总")
        # 不传实时价格
        summary = get_portfolio_summary(db, user_id=999)
        print(f"  组合名: {summary['portfolio_name']}")
        print(f"  持仓数: {summary['summary']['holding_count']}")
        print(f"  总成本: ¥{summary['summary']['total_cost']:,.2f}")
        print(f"  已实现盈亏: ¥{summary['summary']['total_realized_pnl']:.2f}")
        for h in summary["holdings"]:
            if h["quantity"] > 0:
                print(f"    {h['stock_name']}: {h['quantity']}股 @ ¥{h['avg_cost']:.2f}")

        # 传入模拟实时价格
        summary2 = get_portfolio_summary(db, user_id=999, current_prices={"000001.SZ": 14.00})
        h = summary2["holdings"][0]
        print(f"  带实时价格: 市值 ¥{h.get('market_value', 0):,.2f}, 浮动盈亏 ¥{h.get('unrealized_pnl', 0):,.2f}")
        print("  ✅ 组合汇总 通过\n")
    finally:
        db.close()


def test_transactions_list():
    """测试交易记录查询"""
    from portfolio.service import get_transactions

    db = TestSession()
    try:
        print("[7] 测试交易记录查询")
        txns = get_transactions(db, user_id=999)
        print(f"  共 {len(txns)} 条记录")
        for t in txns:
            print(f"    {t['trade_date']} {t['direction'].upper()} {t['stock_name']} {t['quantity']}股 @ ¥{t['price']:.2f}")
        assert len(txns) == 3  # 2 buy + 1 sell
        print("  ✅ 交易记录 通过\n")
    finally:
        db.close()


if __name__ == "__main__":
    passed = 0
    failed = 0

    tests = [
        test_create_portfolio,
        test_buy_stock,
        test_buy_more,
        test_sell_stock,
        test_sell_too_much,
        test_portfolio_summary,
        test_transactions_list,
    ]

    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"  ❌ {test_fn.__name__} 失败: {e}")
            import traceback
            traceback.print_exc()
            print()

    # 清理测试数据库
    try:
        os.remove("test_portfolio.db")
    except Exception:
        pass

    print("=" * 60)
    print(f"总计: {passed} 通过, {failed} 失败")
    print("=" * 60)
