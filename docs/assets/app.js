(() => {
  'use strict';
  const search = document.getElementById('site-search');
  const rows = Array.from(document.querySelectorAll('#site-rows tr'));
  if (search && rows.length) {
    search.addEventListener('input', () => {
      const query = search.value.trim().toLowerCase();
      rows.forEach((row) => {
        row.hidden = query !== '' && !row.dataset.site.includes(query);
      });
    });
  }

  const score = document.querySelector('[data-feed-score]');
  const date = document.querySelector('[data-feed-date]');
  const status = document.querySelector('[data-feed-status]');
  const sources = document.querySelector('[data-source-status]');
  if (!score && !date && !status && !sources) return;

  fetch('data/feed.json', {cache: 'no-store'})
    .then((response) => {
      if (!response.ok) throw new Error('feed unavailable');
      return response.json();
    })
    .then((feed) => {
      const parsed = Number(feed.top_score);
      const valid = typeof feed.top_score === 'string' && /^(0(?:\.\d+)?|1(?:\.0+)?)$/.test(feed.top_score) && parsed >= 0 && parsed <= 1;
      if (!valid) throw new Error('invalid score');
      if (score) score.textContent = feed.top_score;
      if (date) date.textContent = feed.observed_at_utc || feed.observed_date_utc || 'date unavailable';
      if (status) {
        const states = {fresh: 'refreshed public observation', stale: 'refresh failed; last observation retained', snapshot: 'dated snapshot'};
        const when = Date.parse(feed.observed_at_utc || feed.observed_date_utc || '');
        const old = Number.isFinite(when) && Date.now() - when > 24 * 60 * 60 * 1000;
        status.textContent = old ? 'last public observation is older than 24 hours' : (states[feed.status] || 'status unavailable');
      }
      if (sources && Array.isArray(feed.site_refs) && feed.site_refs.length) {
        const changed = feed.site_refs.filter((row) => row.status === 'different_from_archival_file_ref').length;
        const unavailable = feed.site_refs.filter((row) => row.status === 'unavailable').length;
        const checked = feed.site_refs_checked_at_utc || 'time unavailable';
        sources.textContent = `Focus main refs checked ${checked}: ${changed} differ from the historical file commits, ${unavailable} unavailable. Current main contents are not automatically raster-audited.`;
      }
    })
    .catch(() => {
      if (status) status.textContent = 'feed unavailable; displaying the last built snapshot';
    });
})();
