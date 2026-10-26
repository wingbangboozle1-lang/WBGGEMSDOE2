# Auditable source register

| Source | What it directly supports | Caveat / access |
|---|---|---|
| [DrivenData problem and metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) | Fault-pixel task; 300 m triangular DTI kernel, α=0.2, β=0.8; 100 m EPSG:32611 float32 submission. | Public page retrieved 2026-10-26. Public/private/Phase 2 labels differ. |
| [DrivenData public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) | Public leaderboard results, not file identities. | Timestamped snapshot; may change. Not a submission-page receipt. |
| [DrivenData staff — exact mask](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4) | Known-fault pixels are pixel-exact excluded; nearby pixels can be penalized or contain new-fault truth. | Forum post by DrivenData staff, 2026-09-21. |
| [DrivenData staff — slot limit](https://community.drivendata.org/t/submission-amount-question/11553/2) | Website limit prevails over the parenthetical three/week. | Account-specific availability was not accessible. |
| [DOE/NLR official rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) | Eligibility, one chosen final submission, generative AI disclosure and reproducible code requirements. | Review complete current rules and dates before entering. |
| [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution) | Organizer-provided modeling starting point. | Does not provide private labels or an upload receipt. |
| [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) | Airborne magnetic/radiometric surveys, acquisition and flight-path/CSV/grid availability; CC0 noted. | Raw survey files not directly downloaded here; not an endorsement of a candidate. |
| [USGS Dixie Valley magnetic faults](https://pubs.usgs.gov/publication/70023997) | Aeromagnetic data can reveal some structures not recognized at the surface. | Results are from a specific study; transfer to this holdout must be tested. |
| [USGS 3DEP DEM explanation](https://www.usgs.gov/faqs/what-data-sources-are-used-produce-3d-elevation-program-3dep-dems) | Official DEM data program. | This session did not verify competition tile coverage or download all tiles. |
| [INGENIOUS GDR compilation](https://gdr.openei.org/submissions/1391) | Public record lists fault, temperature, seismicity, geodetic and other data; page specifies CC BY 4.0 attribution. | Individual underlying source rights and spatial suitability require review. |
| [Competition data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) | Registered entrant access to competition assets. | Web retrieval redirected to login; no authenticated source receipt. |
| [Pinned 57GEMSDOE template](https://github.com/buffedlizard55-lab/57GEMSDOE/tree/822a0ce5546c7b6749cdd82eb145b6b3e616603d) | Shared team code and hash-pinned bridge conventions, not organizer code. | Restored, verified and reused without modification. |
