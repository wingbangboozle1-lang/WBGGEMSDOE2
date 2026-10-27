// Optional browser smoke test; see research/review-20261027.md for setup.
const puppeteer = require('puppeteer-core');
const {pathToFileURL} = require('node:url');
const fs = require('node:fs');
const path = require('node:path');
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
  const root = path.resolve(__dirname, '..');
  const paths = ['/docs/', '/site/', ...['docs','site'].flatMap(dir =>
    fs.readdirSync(path.join(root,dir), {recursive:true}).filter(f => f.endsWith('.html')).map(f => `/${dir}/${f}`))];

  for (const viewport of [{name:'desktop',width:1440,height:960},{name:'mobile',width:390,height:844}]) {
    for (const path of paths) {
      const page = await browser.newPage();
      const bad = [];
      page.on('pageerror', e => bad.push(`JS: ${e.message}`));
      page.on('console', msg => {if(msg.type()==='error') bad.push(`Console: ${msg.text()}`);});
      page.on('response', response => { if (response.url().startsWith(`${baseURL}/`) && response.status() >= 400) bad.push(`HTTP ${response.status()} ${response.url()}`); });
      await page.setViewport(viewport);
      const res = await page.goto(`${baseURL}${path}`, {waitUntil:'networkidle0',timeout:15000});
      const view = await page.evaluate(() => ({title:document.title,h1:document.querySelector('h1')?.innerText,scrollWidth:document.documentElement.scrollWidth,clientWidth:document.documentElement.clientWidth,leader:document.querySelector('#leader-value')?.textContent,refStatus:document.querySelector('#ref-status')?.textContent,stale:document.querySelector('.freshness')?.getAttribute('data-stale'),rows:document.querySelectorAll('table tbody tr').length,main:!!document.querySelector('main')}));
      if (res.status() >= 400) bad.push(`status ${res.status()}`);
      const staleApproval = await page.evaluate(() => [...document.querySelectorAll('h1,h2,h3')].some(h => ['download and submit','submit this file','cleared for submission'].includes(h.textContent.trim().toLowerCase())));
      if (staleApproval) bad.push('stale positive download/submit heading');
      if (!view.main || !view.h1) bad.push('missing main/h1');
      if (view.scrollWidth > view.clientWidth+1) bad.push(`horizontal page overflow ${view.scrollWidth} > ${view.clientWidth}`);
      if (path === '/docs/' && (view.rows !== 9 || (view.stale === 'true') !== shouldStale)) bad.push(`dashboard rows=${view.rows}, stale=${view.stale}`);
      if (path === '/site/' && view.leader !== expectedLeader) bad.push(`fieldnotes leader=${view.leader}, canonical=${expectedLeader}`);
      if (path === '/site/' && !view.refStatus?.includes('Newer rasters have not been audited')) bad.push(`fieldnotes freshness=${view.refStatus}`);
      if (/^\/docs\/(?:release\.html|submit\/index\.html|submission\/(?:index|executive-summary)\.html)$/.test(path)) {
        const release = await page.evaluate(() => ({
          blocked:!!document.querySelector('[data-release-status="blocked"]'),
          button:document.querySelector('button')?.disabled,
          rows:document.querySelectorAll('table tbody tr').length,
          downloads:[...document.querySelectorAll('a[download]')].filter(a=>a.href.includes('.tif')).map(a=>a.textContent),
          skip:document.querySelector('a.skip')?.href,
          current:location.href
        }));
        if (!release.blocked || release.button !== true || release.rows !== 14) bad.push(`release gate ${JSON.stringify(release)}`);
        if (release.downloads.length !== 5 || release.downloads.some(t=>!t.includes('DO NOT SUBMIT'))) bad.push(`download labels ${JSON.stringify(release.downloads)}`);
        if (release.skip !== release.current+'#main') bad.push(`skip link leaves the page: ${release.skip}`);
      }
      if (path === '/docs/' || path === '/docs/release.html') {
        await page.screenshot({path:require('node:path').join(root,`.cache/browser/${viewport.name}-${path.includes('release')?'release':'dashboard'}.png`),fullPage:true});
      }
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
  else console.log(`Browser review: ${paths.length} routes passed at both sizes (${paths.length*2} checks).`);
})().catch(e => {console.error(e);process.exit(1);});
