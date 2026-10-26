(() => {
  const value = document.querySelector("[data-board-value]");
  const detail = document.querySelector("[data-board-detail]");
  if (!value || !detail) return;
  const unavailable = (message) => {
    value.textContent = "Unavailable";
    detail.textContent = message;
  };
  fetch("docs/data/leaderboard.json", { cache: "no-store" })
    .then((response) => {
      if (!response.ok) throw new Error("Snapshot unavailable");
      return response.json();
    })
    .then((snapshot) => {
      if (
        snapshot.schema !== "wbggems.public-leaderboard.v1" ||
        snapshot.source !==
          "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/" ||
        snapshot.status !== "ok" ||
        !/^(?:0(?:\.\d+)?|1(?:\.0+)?)$/.test(snapshot.top_public_dti || "")
      ) {
        unavailable("Refresh unavailable. Open the official leaderboard.");
        return;
      }
      const checked = Date.parse(snapshot.checked_utc);
      const ageHours = (Date.now() - checked) / 3600000;
      if (!Number.isFinite(checked) || ageHours > 48 || ageHours < -1) {
        unavailable(
          "Snapshot is stale or its time is invalid. Open the official leaderboard.",
        );
        return;
      }
      value.textContent = snapshot.top_public_dti;
      detail.textContent = `Public leaderboard observation · ${new Date(checked).toISOString().slice(0, 16).replace("T", " ")} UTC · not a candidate receipt`;
    })
    .catch(() =>
      unavailable("Snapshot unavailable. Open the official leaderboard."),
    );
})();
