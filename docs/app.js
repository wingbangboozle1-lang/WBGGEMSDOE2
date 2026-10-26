/* A scheduled snapshot is never called live; flag it if it ages or refresh fails. */
(() => {
  const now = Date.now();
  document.querySelectorAll('.freshness').forEach((element) => {
    const reference = element.dataset.captured || 'no timestamp';
    const captured = Date.parse(element.dataset.captured || '');
    const failed = element.dataset.status === 'stale';
    const aged = !Number.isFinite(captured) || now - captured > 24 * 60 * 60 * 1000;
    const future = Number.isFinite(captured) && captured > now + 5 * 60 * 1000;
    if (failed || aged || future) {
      element.dataset.stale = 'true';
      const warning = failed ? 'Refresh incomplete' : future ? 'Timestamp is in the future' : 'Snapshot is over 24h old';
      element.textContent = `${warning} · reference time ${reference}`;
    }
  });
})();
