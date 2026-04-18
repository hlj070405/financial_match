"""测试比亚迪的各项数据"""
import sys
sys.path.insert(0, r"c:\Users\Administrator\Desktop\大数据 主题赛\pdf-rag-system\backend")

from services.tushare_service import TushareService

ts_code = "002594.SZ"
print(f"测试: {ts_code} (比亚迪)")

print("\n[1] balancesheet")
data = TushareService.get_balancesheet(ts_code)
print(f"    返回: {len(data)} 条")
if data and len(data) > 0:
    print(f"    end_date: {data[0].get('end_date')}")

print("\n[2] cashflow")
data = TushareService.get_cashflow(ts_code)
print(f"    返回: {len(data)} 条")

print("\n[3] moneyflow")
data = TushareService.get_moneyflow(ts_code)
print(f"    返回: {len(data)} 条")
if data and len(data) > 0:
    print(f"    最新: {data[-1].get('trade_date')}")
