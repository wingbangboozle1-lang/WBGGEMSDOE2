from urllib.request import Request,urlopen
from refresh_leaderboard import URL,TableRows,parse_top
import json
partial=URL.replace('leaderboard/','leaderboard_partial/?page=1')
with urlopen(Request(partial, headers={'User-Agent':'GEMS-research-audit/1.0','HX-Request':'true'}),timeout=20) as r:
    final=r.geturl();status=r.status;page=r.read(2_000_000).decode('utf-8','replace')
p=TableRows();p.feed(page)
try: value=parse_top(page);error=None
except Exception as exc:value=None;error=str(exc)
summary={'status':status,'url':final,'bytes':len(page),'tables':[{'n':len(t),'first_rows':[row[:5] for row in t[:3]]} for t in p.tables[:2]],'parsed':value,'error':error}
print('::notice title=Leaderboard partial structure::'+json.dumps(summary,ensure_ascii=True).replace('%','%25')[:8000])
