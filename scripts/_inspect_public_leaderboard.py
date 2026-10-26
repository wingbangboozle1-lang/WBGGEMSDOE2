from pathlib import Path
from tempfile import TemporaryDirectory
import json
from refresh_leaderboard import refresh
with TemporaryDirectory() as tmp:
    path=Path(tmp)/'out.json'
    ok=refresh(path);data=json.loads(path.read_text())
    print('::notice title=Official leaderboard refresh::'+json.dumps({k:data.get(k) for k in ('status','captured_utc','source_url','data_url','top_public_dti','last_error')}))
    if not ok: raise SystemExit('public endpoint refresh failed in diagnostic run')
