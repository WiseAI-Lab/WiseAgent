from datetime import datetime

date_str = str(datetime.now())
print(date_str)
res = datetime.fromisoformat(date_str)
print(type(res))