// Optional browser smoke test; see research/review-20261027.md for setup.
const puppeteer = require('puppeteer-core');
const {pathToFileURL} = require('node:url');
const baseURL = process.env.BROWSER_BASE_URL || 'http://127.0.0.1:8000';

(async () => {
  const chromium = (await import(pathToFileURL(require.resolve('@sparticuz/chromium')))).default;
  const browser = await puppeteer.launch({args: chromium.args, executablePath: await chromium.executablePath(), headless: true});
  const snapshotResponse = await fetch(`${baseURL}/docs/data/leaderboard.json`);
  if (!snapshotResponse.ok) throw new Error('Canonical leaderboard snapshot unavailable');
  const snapshot = await snapshotResponse.json();
  const age = Date.now() - Date.parse(snapshot.captured_utc || '');
  const shouldStale = !['fresh', 'snapshot'].includes(snapshot.status) || !Number.isFinite(age) || age > 86400000 || age < -300000;
  const expectedLeader = typeof snapshot.top_public_dti === 'number' && snapshot.top_public_dti >= 0 && snapshot.top_public_dti <= 1 ? snapshot.top_public_dti.toFixed(4) : 'Unavailable';
  const failures = [];
  const paths = ['/docs/', '/docs/executive-summary.html', '/docs/research.html', '/docs/sources.html', '/docs/research/why-b2-scored-2778.html', '/docs/executive-summary/', '/site/', '/site/executive.html', '/site/research.html', ...['24','25','27','28','30','31','32','33','36'].map(n => `/site/sites/GEMSDOE${n}.html`)];
  for (const viewport of [{name:'desktop',width:1440,height:960},{name:'mobile',width:390,height:844}]) {
    for (const path of paths) {
      const page = await browser.newPage();
      const bad = [];
      page.on('pageerror', e => bad.push(`JS: ${e.message}`));
      page.on('response', response => { if (response.url().startsWith(`${baseURL}/`) && response.status() >= 400) bad.push(`HTTP ${response.status()} ${response.url()}`); });
      await page.setViewport(viewport);
      const res = await page.goto(`${baseURL}${path}`, {waitUntil:'networkidle0',timeout:15000});
      const view = await page.evaluate(() => ({title:document.title,h1:document.querySelector('h1')?.innerText,scrollWidth:document.documentElement.scrollWidth,clientWidth:document.documentElement.clientWidth,leader:document.querySelector('#leader-value')?.textContent,stale:document.querySelector('.freshness')?.getAttribute('data-stale'),rows:document.querySelectorAll('table tbody tr').length,main:!!document.querySelector('main')}));
      if (res.status() >= 400) bad.push(`status ${res.status()}`);
      if (!view.main || !view.h1) bad.push('missing main/h1');
      if (view.scrollWidth > view.clientWidth+1) bad.push(`horizontal page overflow ${view.scrollWidth} > ${view.clientWidth}`);
      if (path === '/docs/' && (view.rows !== 9 || (view.stale === 'true') !== shouldStale)) bad.push(`dashboard rows=${view.rows}, stale=${view.stale}`);
      if (path === '/site/' && view.leader !== expectedLeader) bad.push(`fieldnotes leader=${view.leader}, canonical=${expectedLeader}`);
      if (path === '/docs/research/why-b2-scored-2778.html') {
        const check = await page.evaluate(() => ({strong:document.querySelectorAll('.research-prose strong').length,sections:document.querySelectorAll('.research-prose h2').length,pre:document.querySelectorAll('.research-prose pre').length,canonical:document.querySelector('nav a[href="research.html"]')?.href}));
        if (check.strong < 10 || check.sections < 8 || check.pre !== 0 || !check.canonical.endsWith('/docs/research.html')) bad.push(`B2 render/navigation ${JSON.stringify(check)}`);
      }
      if (bad.length) failures.push({viewport:viewport.name,path,bad,view});
      console.log(JSON.stringify({viewport:viewport.name,path,...view,bad}));
      await page.close();
    }
  }
  await browser.close();
  if (failures.length) { console.error('FAILURES',JSON.stringify(failures,null,2)); process.exitCode=1; }
  else console.log('Browser review: all routes passed at both sizes.');
})().catch(e => {console.error(e);process.exit(1);});
