from urllib.request import Request,urlopen
from refresh_leaderboard import URL,TableRows
import json,re
partial=URL.replace('leaderboard/','leaderboard_partial/?page=1')
with urlopen(Request(partial,headers={'User-Agent':'GEMS-research-audit/1.0','HX-Request':'true'}),timeout=20) as r:page=r.read(2_000_000).decode('utf-8','replace')
i=page.lower().find('<table');j=page.lower().find('<tbody',i)
summary={'header_html':page[i:j][:6000], 'starts':page[:400]}
print('::notice title=Leaderboard table header::'+json.dumps(summary,ensure_ascii=True).replace('%','%25')[:8000])
