# Historical MSPTCD methods — not the current untested shortlist

This note describes **already implemented** MSPTCD feature families. It is retained for scientific provenance, not as a new lane nomination or a claim of geological truth. The source is [`src/wbggems/msptcd.py`](../src/wbggems/msptcd.py), and the historical result is [source-reported, not independently reproduced](msptcd_findings.md). The active genuinely distinct desk proposals and their cost/data limits are in [`research/hypotheses.md`](hypotheses.md).

| Implemented family | Input layers in the owner mirror | Code operation | Non-fault mimic |
|---|---|---|---|
| Potential-field tilt | RTP (band 2), TMI vertical gradient (9), isostatic gravity (13), gravity vertical gradient (11) | Smoothed, normalized derivative ratios and horizontal tilt gradients | Contacts, dikes, magnetic remanence, gridding/flight-line artifacts |
| Gravity–magnetic offset | RTP (2), isostatic gravity (13), conductive-base proxy (15) | Compare magnetic-gradient strength at bounded depth-proxy shifts along gravity-gradient normals | Intrusion margins, geologic boundaries and misaligned survey grids |
| Electrical flank asymmetry | Conductive-base proxy (15), conductivity (17), potential-field orientation | Cross-flank sampled conductivity differences gated by the proxy gradient | Saline playas, basin fill, clay alteration unrelated to faulting |
| Scarp and radiometric context | Detrended elevation (12), slope (19), `tc` (6) | Hessian ridge responses and a terrain-weighted radiometric gradient | Shorelines, roads, fans, lithology, vegetation and flight-line artifacts |
| Strain/seismicity context | Strain invariant/shear/dilation (4, 7, 8), earthquake distance and intensity (10, 16) | Strain ratios, shear-edge gate and a log seismicity index | Interpolation halos, injection/mining swarms and regional trends |

The official inventory identifies `depth_to_base_surf` as depth to a **conductive base**, whereas mirror metadata says basement; equivalence is not established. The official description lists `tc` as radiometric total count, while the owner-mirror band description says tilt/curvature. Its positive quantiles do not by themselves authenticate units or data origin.

The previous H5 proposed fine-resolution drainage displacement and survey-line repeatability. [USGS 3DEP](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services) offers free elevation products, and [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) publishes survey lines and grids (DOI `10.5066/P93LGLVQ`). Exact study-area tiles, usable overlapping flight/tie lines, coverage and binary accessibility were **not** checked here. The [competition problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) refers to a `1m_DEM_links.csv` on its login-protected data page; the [GDR 1391 inventory](https://gdr.openei.org/submissions/1391) does **not** list that CSV. An earlier assertion to the contrary was incorrect.

The historical TIFF is **DO NOT SUBMIT**: see the [byte audit](../evidence/local_artifact_audit_20261027.json). No new experiment, prediction or competition slot was used in this review.
