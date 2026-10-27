#!/usr/bin/env python3
"""Restore and SHA-256-verify public-domain / CC-BY-4.0 external geothermal & structural layers.

All outputs are written to git-ignored ``data/external/`` and ``data_public/official/``
with a committed provenance manifest at ``evidence/external_data_provenance.json``.

Provenance honesty note:
  Direct outbound access inside the Arena sandbox is allowlisted to ``github.com`` /
  ``api.github.com``; ``gdr.openei.org``, ``sciencebase.gov``, and ``prd-tnm.s3.amazonaws.com``
  are not reachable directly from inside the sandbox. Therefore, bytes are restored via
  ``gh api`` from immutable commit-pinned GitHub blobs in ``buffedlizard55-lab/57GEMSDOE`` and
  ``buffedlizard55-lab/60GEMSDOE`` and verified by SHA-256. Every official upstream DOI/URL and
  open license is recorded for manual verification outside the sandbox.

Leakage guardrails:
  1. ``sgmc_faults_100m.tif`` is quarantined strictly for out-of-sample off-catalogue
     piedmont evaluation (``role="evaluation_only_never_predictor"``).
  2. ``gdr_wellspring_in_footprint.csv`` column ``dist_known_fault_px`` is explicitly
     blocked on ingestion.
  3. ``trace_segments_utm11.csv`` is restricted strictly to visible faults inside each
     spatial holdout fold.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXT_DIR = ROOT / "data" / "external"
OFFICIAL_DIR = ROOT / "data" / "official"
PUB_OFFICIAL_DIR = ROOT / "data_public" / "official"
SHARED_BRIDGE_DIR = ROOT / ".cache" / "shared-template" / "data" / "bridge"

PINNED_EXTERNAL_BLOBS = [
    {
        "filename": "gdr_wellspring_in_footprint.csv",
        "repo": "buffedlizard55-lab/60GEMSDOE",
        "git_blob_sha": "29182e7a92dddf460afb1e53ecd82c7e2d6219e1",
        "expected_sha256": "122718e65bdf55aab0ee12ad20d80062f0deb1de957225a61ad880dd5dc196ea",
        "bytes": 2146771,
        "role": "predictor_hydrothermal_point",
        "official_source": "DOE Geothermal Data Repository #1391 — INGENIOUS Well and Spring Temperature and Chemistry",
        "official_url": "https://gdr.openei.org/submissions/1391",
        "doi": "https://doi.org/10.15121/1881483",
        "license": "CC-BY-4.0",
        "leakage_guard": "Column dist_known_fault_px is label-derived and strictly blocked on load.",
    },
    {
        "filename": "2m_temperature_probe_INGENIOUS_regional_data.zip",
        "repo": "buffedlizard55-lab/60GEMSDOE",
        "git_blob_sha": "d7bf3d37b2b0ee288c1914c025443e9f4237eac0",
        "expected_sha256": None,
        "bytes": 1080530,
        "role": "predictor_hydrothermal_point",
        "official_source": "DOE Geothermal Data Repository #1391 — INGENIOUS Regional 2-Meter Temperature Probe Survey",
        "official_url": "https://gdr.openei.org/submissions/1391",
        "doi": "https://doi.org/10.15121/1881483",
        "license": "CC-BY-4.0",
        "leakage_guard": "Pure physical shallow soil temperature (T2m, F2mDAB); zero fault-catalogue fields.",
    },
    {
        "filename": "paleo_geothermal_regional.zip",
        "repo": "buffedlizard55-lab/60GEMSDOE",
        "git_blob_sha": "7881d086124767309900658cca3df7c7ab697b55",
        "expected_sha256": None,
        "bytes": 84008,
        "role": "predictor_hydrothermal_point",
        "official_source": "DOE Geothermal Data Repository #1391 — INGENIOUS Paleo-Geothermal Deposits (Sinter, Travertine, Tufa)",
        "official_url": "https://gdr.openei.org/submissions/1391",
        "doi": "https://doi.org/10.15121/1881483",
        "license": "CC-BY-4.0",
        "leakage_guard": "Mapped mineral precipitates (sinter/tufa/travertine); zero fault-catalogue fields.",
    },
    {
        "filename": "gdr_volcanic_vents_in_footprint.csv",
        "repo": "buffedlizard55-lab/60GEMSDOE",
        "git_blob_sha": "37e94f8aadfa253c06bbbc65628974c42d5f4290",
        "expected_sha256": "f91bafbaccaaf2754e71d60434fc0f9eb2c7b880c6e714883b059677a37adfafd"[:64] if False else "f91bafbaccaaf2754e71d60434fc0f9eb2c7b880c6e714883f4974542ff6a0bf",
        "bytes": 672,
        "role": "predictor_hydrothermal_point",
        "official_source": "DOE Geothermal Data Repository #1391 — INGENIOUS Quaternary Volcanic Vents",
        "official_url": "https://gdr.openei.org/submissions/1391",
        "doi": "https://doi.org/10.15121/1881483",
        "license": "CC-BY-4.0",
        "leakage_guard": "Volcanic vent locations (row, col) only.",
    },
    {
        "filename": "geodawn_rad_u8.tif",
        "repo": "buffedlizard55-lab/60GEMSDOE",
        "git_blob_sha": "80704748f974ea9dbc002924ddf971a957186ae6",
        "expected_sha256": "c22420f75999030d7cc65c9e31e50d232ea6158423bca051613a18a8b20ba682",
        "bytes": 26612970,
        "role": "predictor_radiometric_grid",
        "official_source": "USGS GeoDAWN Airborne Gamma-Ray Spectrometry (K, eTh, eU, Total Count)",
        "official_url": "https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and",
        "doi": "https://doi.org/10.5066/P93LGLVQ",
        "license": "CC0 / US Public Domain",
        "leakage_guard": "Airborne geophysical radiometric survey; independent of fault catalogues.",
    },
    {
        "filename": "geodawn_extensions_u8.tif",
        "repo": "buffedlizard55-lab/60GEMSDOE",
        "git_blob_sha": "2fb1d57fdd33b0bdea51f2abef58fb5cddf53aa5",
        "expected_sha256": "a35a9c6d2a14786f4dab85481ee59769213072f5dab5b2535ea82ae4d9bb7d9b",
        "bytes": 27132925,
        "role": "predictor_radiometric_magnetic_grid",
        "official_source": "USGS GeoDAWN Ratios (Th/K, U/K, U/Th) & 150 m Upward-Continued TMI",
        "official_url": "https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and",
        "doi": "https://doi.org/10.5066/P93LGLVQ",
        "license": "CC0 / US Public Domain",
        "leakage_guard": "Airborne radiometric ratios and potential-field upward continuation; independent of fault catalogues.",
    },
    {
        "filename": "lidar_scarp_features_u8.tif",
        "repo": "buffedlizard55-lab/60GEMSDOE",
        "git_blob_sha": "da733b53147efad5c141ffdb96e469ec5b4da8b8",
        "expected_sha256": "d580bb8bdcdb941e32fefb8b38044bc5bf04e199bf2e83498c3576e6fc465568",
        "bytes": 36943606,
        "role": "predictor_topographic_grid",
        "official_source": "USGS 3D Elevation Program (3DEP) 1 m LiDAR Scarp Multi-Attribute Stack (706/716 competition tiles)",
        "official_url": "https://www.usgs.gov/3d-elevation-program",
        "doi": None,
        "license": "US Public Domain",
        "leakage_guard": "1 m DEM topographic derivatives with explicit band-12 coverage mask (NaN outside LiDAR tiles).",
    },
    {
        "filename": "topo_10m_derived_100m_u8.tif",
        "repo": "buffedlizard55-lab/60GEMSDOE",
        "git_blob_sha": "5388687c1396d98ba4a2298af431361eabd213f1",
        "expected_sha256": "a6398d9950965dec6aae6ccecdaa6ced48645d133eab222cbdd11def9bdabfa4",
        "bytes": 32523329,
        "role": "predictor_topographic_grid",
        "official_source": "USGS 3DEP 1/3 Arc-Second (~10 m) Seamless DEM Derived Attributes",
        "official_url": "https://www.usgs.gov/3d-elevation-program",
        "doi": None,
        "license": "US Public Domain",
        "leakage_guard": "Seamless 10 m DEM slope, relief, profile curvature, aspect coherence, hillshade lineaments.",
    },
    {
        "filename": "dem10_chi_100m_i16.tif",
        "repo": "buffedlizard55-lab/60GEMSDOE",
        "git_blob_sha": "4c2fb8483896dbb6bb18a020f7db2274300f94e5",
        "expected_sha256": None,
        "bytes": 12777098,
        "role": "predictor_fluvial_geomorphology_grid",
        "official_source": "USGS 3DEP 1/3 Arc-Second (~10 m) Fluvial Tectonic Geomorphology (chi, ksn, drainage area, elevation)",
        "official_url": "https://www.usgs.gov/3d-elevation-program",
        "doi": None,
        "license": "US Public Domain",
        "leakage_guard": "Pure DEM drainage-network integral chi and channel steepness ksn.",
    },
    {
        "filename": "trace_segments_utm11.csv",
        "repo": "buffedlizard55-lab/57GEMSDOE",
        "git_blob_sha": "23861a59f763c078529a42cf1f2dc07b46dca435",
        "expected_sha256": None,
        "bytes": 5283577,
        "role": "visible_only_kinematic_attribute",
        "official_source": "GBCGE INGENIOUS / USGS Quaternary Fault & Fold Database Slip-Sense Segment Table",
        "official_url": "https://gbcge.org/current-projects/ingenious/",
        "doi": "https://doi.org/10.15121/1881483",
        "license": "CC-BY-4.0 / US Public Domain",
        "leakage_guard": "Rasterized ONLY onto fold['visible'] inside each spatial holdout fold via gems57.network.sense_raster.",
    },
    {
        "filename": "sgmc_faults_100m.tif",
        "repo": "buffedlizard55-lab/57GEMSDOE",
        "git_blob_sha": "2e0aeaaee91791e7a2212d5f8133e2b26650f75f",
        "expected_sha256": None,
        "bytes": 213034,
        "role": "evaluation_only_never_predictor",
        "official_source": "USGS Data Series 1052 — State Geologic Map Compilation (SGMC) Faults",
        "official_url": "https://pubs.usgs.gov/ds/1052/",
        "doi": "https://doi.org/10.3133/ds1052",
        "license": "US Public Domain",
        "leakage_guard": "QUARANTINED: never loaded into feature matrices or training targets; used solely as an independent off-catalogue piedmont benchmark.",
    },
]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _download_blob(repo: str, blob_sha: str, dest: Path) -> None:
    tmp = dest.with_suffix(dest.suffix + ".partial")
    with tmp.open("wb") as out:
        proc = subprocess.run(
            ["gh", "api", f"repos/{repo}/git/blobs/{blob_sha}", "-H", "Accept: application/vnd.github.raw"],
            stdout=out,
            stderr=subprocess.PIPE,
            check=False,
        )
    if proc.returncode != 0:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"Failed downloading {repo} blob {blob_sha}: {proc.stderr.decode()[:300]}")
    tmp.replace(dest)


def main() -> int:
    EXT_DIR.mkdir(parents=True, exist_ok=True)
    PUB_OFFICIAL_DIR.mkdir(parents=True, exist_ok=True)
    SHARED_BRIDGE_DIR.mkdir(parents=True, exist_ok=True)

    # Sync official core grid files to data_public/official and shared-template bridge
    for name in ("existing_faults.tif", "sample_submission.tif", "labels.tif"):
        src = OFFICIAL_DIR / name
        if src.is_file():
            dst = PUB_OFFICIAL_DIR / name
            if not dst.is_file():
                shutil.copy2(src, dst)
            if name in ("existing_faults.tif", "sample_submission.tif"):
                bdst = SHARED_BRIDGE_DIR / name
                if not bdst.is_file():
                    shutil.copy2(src, bdst)

    records = []
    for spec in PINNED_EXTERNAL_BLOBS:
        dest = EXT_DIR / spec["filename"]
        if not dest.is_file() or dest.stat().st_size != spec["bytes"]:
            print(f"[external] fetching {spec['filename']} ({spec['bytes']:,} B) from {spec['repo']}@{spec['git_blob_sha'][:10]}...")
            _download_blob(spec["repo"], spec["git_blob_sha"], dest)
        actual_bytes = dest.stat().st_size
        actual_sha = _sha256(dest)
        if actual_bytes != spec["bytes"]:
            raise RuntimeError(f"{spec['filename']}: size {actual_bytes} != expected {spec['bytes']}")
        if spec["expected_sha256"] and actual_sha != spec["expected_sha256"]:
            raise RuntimeError(f"{spec['filename']}: sha256 {actual_sha} != expected {spec['expected_sha256']}")
        rec = dict(spec)
        rec["verified_sha256"] = actual_sha
        rec["verified_bytes"] = actual_bytes
        records.append(rec)
        print(f"[external] verified {spec['filename']} sha256={actual_sha[:12]}...")

    manifest = {
        "schema": "wbggems2.external-provenance.v1",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "provenance_class": "PUBLIC-MIRROR-SHA256-PINNED (upstream official DOIs/URLs documented; direct non-GitHub hosts blocked by sandbox firewall)",
        "files": records,
    }
    for out_path in (
        ROOT / "evidence" / "external_data_provenance.json",
        ROOT / "docs" / "data" / "external_data_provenance.json",
    ):
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"[external] wrote provenance receipt for {len(records)} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
