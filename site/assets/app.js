'use strict';

function utcLabel(value) {
  if (typeof value !== 'string' || !value) return 'time unavailable';
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? 'time unavailable' : date.toLocaleString('en-GB', {timeZone: 'UTC', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'}) + ' UTC';
}
function element(tag, text, className) {
  const node = document.createElement(tag);
  node.textContent = text;
  if (className) node.className = className;
  return node;
}
async function loadLeaderboard() {
  try {
    const response = await fetch('data/leaderboard.json', {cache: 'no-store'});
    if (!response.ok) throw new Error('unavailable');
    const data = await response.json();
    const lead = data.leaderboard || {};
    const value = document.getElementById('leader-value');
    const meta = document.getElementById('leader-meta');
    if (value && meta) {
      value.textContent = typeof lead.value === 'number' && lead.value >= 0 && lead.value <= 1 ? lead.value.toFixed(4) : 'Unavailable';
      const age = Date.now() - Date.parse(lead.observed_at);
      const stale = lead.status === 'stale' || !Number.isFinite(age) || age > 48 * 60 * 60 * 1000 || age < -300000;
      meta.textContent = (stale ? 'Stale / unverified refresh · ' : lead.status === 'fresh' ? 'Organizer-published · ' : 'Organizer-published snapshot · ') + utcLabel(lead.observed_at);
      if (stale) meta.classList.add('stale');
    }
    const refs = document.getElementById('ref-status');
    if (refs) {
      const rows = Array.isArray(data.sites) ? data.sites : [];
      const changed = rows.filter(x => x.status === 'changed').length;
      const unknown = rows.filter(x => x.status === 'unknown').length;
      refs.textContent = rows.length ? `${changed} site refs changed, ${unknown} unknown since the ${utcLabel(data.baseline_observed_at)} HEAD observation (not the older file pins). New files are not automatically audited.` : 'Site-ref freshness has not yet been checked by the scheduled feed.';
    }
  } catch (_) {
    const meta = document.getElementById('leader-meta');
    const value = document.getElementById('leader-value');
    if (value) value.textContent = 'Unavailable';
    if (meta) { meta.textContent = 'Feed unavailable · check official leaderboard'; meta.classList.add('stale'); }
  }
}
async function loadFocus() {
  const body = document.getElementById('focus-body');
  if (!body) return;
  try {
    const response = await fetch('data/focus.json');
    if (!response.ok) throw new Error('unavailable');
    const data = await response.json();
    if (!Array.isArray(data.entries) || data.entries.length !== 9) throw new Error('incomplete');
    body.replaceChildren();
    for (const entry of data.entries) {
      const row = document.createElement('tr');
      const title = document.createElement('td');
      const siteLink = element('a', entry.site, 'site-name');
      if (!/^sites\/GEMSDOE(?:24|25|27|28|30|31|32|33|36)\.html$/.test(entry.site_url)) throw new Error('unexpected site page');
      siteLink.href = entry.site_url; title.append(siteLink);
      const file = element('a', entry.file, 'file-link');
      const url = new URL(entry.url);
      if (url.protocol !== 'https:' || url.hostname !== 'github.com') throw new Error('unexpected source');
      file.href = url.href; file.title = 'Pinned historical file — research only';
      title.append(file); row.append(title);
      const claim = document.createElement('td'); claim.append(element('strong', entry.claimed_value), element('small', 'OWNER-REPORTED')); row.append(claim);
      const estimate = document.createElement('td'); estimate.append(element('strong', 'Unknown'), element('small', 'NOT CALIBRATED')); row.append(estimate);
      const unique = document.createElement('td'); unique.append(element('span', 'NO', 'pill pill-neutral'), element('small', `${(entry.max_peer_overlap.fraction * 100).toFixed(1)}% near ${entry.max_peer_overlap.peer}`)); row.append(unique);
      const decision = document.createElement('td'); decision.append(element('span', 'DO NOT SUBMIT', 'pill pill-danger'), element('small', 'Historical reference')); row.append(decision);
      body.append(row);
    }
  } catch (_) {
    body.replaceChildren();
    const row = document.createElement('tr'), cell = element('td', 'Audit data unavailable. No file is approved; see the repository evidence.');
    cell.colSpan = 5; row.append(cell); body.append(row);
  }
}
loadLeaderboard();
loadFocus();
