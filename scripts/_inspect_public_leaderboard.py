from urllib.request import Request,urlopen
from refresh_leaderboard import URL,TableRows
import json,re
with urlopen(Request(URL, headers={'User-Agent':'GEMS-research-audit/1.0'}),timeout=20) as r:
    final=r.geturl();status=r.status;page=r.read(2_000_000).decode('utf-8','replace')
p=TableRows();p.feed(page)
summary={'status':status,'url':final,'bytes':len(page),'title':(re.search(r'<title[^>]*>(.*?)</title>',page,re.S|re.I).group(1).strip() if re.search(r'<title[^>]*>(.*?)</title>',page,re.S|re.I) else None),'terms':{term:page.lower().count(term.lower()) for term in ['leaderboard','tversky','xiaofanhu','captcha','cloudflare','cloudfront','table','rank','log in','sign in','turnstile']},'head':page[:1200],'tables':[{'n':len(t),'first_rows':[row[:5] for row in t[:3]]} for t in p.tables[:2]]}
print('::notice title=Leaderboard structure::'+json.dumps(summary,ensure_ascii=True).replace('%','%25')[:6000])
