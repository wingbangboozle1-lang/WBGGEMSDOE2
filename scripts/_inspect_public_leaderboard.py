from urllib.request import Request,urlopen
from refresh_leaderboard import URL,TableRows
import json,re
with urlopen(Request(URL, headers={'User-Agent':'GEMS-research-audit/1.0'}),timeout=20) as r:
    page=r.read(2_000_000).decode('utf-8','replace')
positions=[m.start() for m in re.finditer('leaderboard',page,re.I)]
summary={'contexts':[page[max(0,i-120):i+230].replace('\n',' ') for i in positions[-12:]],'scripts':re.findall(r'<script[^>]*src=["\']([^"\']+)',page,re.I)}
print('::notice title=Leaderboard structure::'+json.dumps(summary,ensure_ascii=True).replace('%','%25')[:11000])
