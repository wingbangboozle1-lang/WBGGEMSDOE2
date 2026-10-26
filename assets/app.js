/* A public leaderboard snapshot is not a file-linked submission receipt. */
(() => {
  const score = document.getElementById('leaderboard-score');
  const caption = document.getElementById('leaderboard-caption');
  const status = document.getElementById('feed-status');
  fetch('site-data/leaderboard.json', {cache: 'no-store'})
    .then(response => { if (!response.ok) throw new Error('feed unavailable'); return response.json(); })
    .then(data => {
      if (!Number.isFinite(data.score) || data.score < 0 || data.score > 1) throw new Error('invalid score');
      const time = new Date(data.observed_at_utc);
      if (!Number.isFinite(time.getTime())) throw new Error('invalid observation time');
      const formatted = new Intl.DateTimeFormat('en-GB', {day:'numeric',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit',timeZone:'UTC'}).format(time) + ' UTC';
      const ageHours = (Date.now() - time.getTime()) / 3600000;
      const stale = ageHours > 30 || ageHours < -1 || data.last_attempt_result !== 'success';
      if (score) score.textContent = data.score.toFixed(4);
      if (caption) caption.textContent = `${stale ? 'Snapshot / check source' : 'Public observation'} · ${formatted}`;
      if (status) status.textContent = `Leaderboard ${stale ? 'snapshot — verify source' : 'refreshed'}: ${formatted}`;
    })
    .catch(() => {
      if (caption) caption.textContent = 'Snapshot unavailable — check the official leaderboard';
      if (status) status.textContent = 'Leaderboard feed unavailable — check the official source';
    });
})();
