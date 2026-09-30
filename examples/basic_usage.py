from ashare_data import AShareData

api = AShareData()

print(api.quote("600519"))
print(api.daily_kline("600519", limit=5)[-2:])
print(api.minute_kline("600519", period="m5", limit=5)[-2:])
print(api.financials("600519", statement="income", periods=2))
print(api.announcements("600519", page_size=3))

