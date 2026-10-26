from urllib.request import Request,urlopen
from refresh_leaderboard import URL,TableRows
import json
with urlopen(Request(URL, headers={'User-Agent':'GEMS-research-audit/1.0'}),timeout=20) as r:
    page=r.read(2_000_000).decode('utf-8','replace')
p=TableRows();p.feed(page)
summary={'bytes':len(page),'tables':[{'n':len(t),'first_rows':[row[:5] for row in t[:3]]} for t in p.tables[:3]]}
print('::notice title=Leaderboard structure::'+json.dumps(summary,ensure_ascii=True)[:6000])
