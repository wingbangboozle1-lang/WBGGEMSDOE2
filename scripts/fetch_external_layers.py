#!/usr/bin/env python3
"""Fetch and SHA-256 verify free public-domain / CC-BY-4.0 external geophysical layers.

All files are downloaded via `codeload.github.com` tar streams into git-ignored,
snapshot-excluded `.cache/external/` and verified bit-for-bit against full 64-hex
SHA-256 digests before use. A provenance receipt is written to
`evidence/external_layers_provenance.json`.
"""
from __future__ import annotations

from collections import defaultdict
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / ".cache" / "external"

EXTERNAL_PINS = [
    {
        "repo": "GEMSDOE24",
        "ref": "07345ea0604953d7efb858d9cfbc21e20c7aca0b",
        "src_path": "data/external/lidar_scarp_features_u8.tif",
        "dest_name": "lidar_scarp_features_u8.tif",
        "sha256": "d580bb8bdcdb941e32fefb8b38044bc5bf04e199bf2e83498c3576e6fc465568",
        "official_source": "USGS 3D Elevation Program (3DEP) 1 m DEMs (1m_DEM_links.csv)",
        "official_url": "https://www.usgs.gov/3d-elevation-program/about-3dep-products-services",
        "license": "US Public Domain (17 U.S.C. 105 / CC0)",
        "role": "model_feature",
    },
    {
        "repo": "GEMSDOE24",
        "ref": "07345ea0604953d7efb858d9cfbc21e20c7aca0b",
        "src_path": "data/external/lidar_scarp_features.json",
        "dest_name": "lidar_scarp_features.json",
        "sha256": "9ef0df6e87598a8b0cd52fe821661e5fdb3a00568c5d9b1c5d61fd6b242dcd41",
        "official_source": "USGS 3DEP 1 m scarp quantisation metadata",
        "official_url": "https://www.usgs.gov/3d-elevation-program/about-3dep-products-services",
        "license": "US Public Domain (CC0)",
        "role": "metadata",
    },
    {
        "repo": "GEMSDOE24",
        "ref": "07345ea0604953d7efb858d9cfbc21e20c7aca0b",
        "src_path": "data/external/geodawn_rad_u8.tif",
        "dest_name": "geodawn_rad_u8.tif",
        "sha256": "c22420f75999030d7cc65c9e31e50d232ea6158423bca051613a18a8b20ba682",
        "official_source": "USGS GeoDAWN Airborne Gamma-Ray Spectrometer Survey (K, Th, U, TC)",
        "official_url": "https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and",
        "license": "US Public Domain (USGS Data Release doi:10.5066/P9X8K366, CC0)",
        "role": "model_feature",
    },
    {
        "repo": "GEMSDOE24",
        "ref": "07345ea0604953d7efb858d9cfbc21e20c7aca0b",
        "src_path": "data/external/geodawn_extensions_u8.tif",
        "dest_name": "geodawn_extensions_u8.tif",
        "sha256": "a35a9c6d2a14786f4dab85481ee59769213072f5dab5b2535ea82ae4d9bb7d9b",
        "official_source": "USGS GeoDAWN Spectral Ratios (Th/K, U/K, U/Th) & 150 m Upward-Continued TMI",
        "official_url": "https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and",
        "license": "US Public Domain (USGS Data Release doi:10.5066/P9X8K366, CC0)",
        "role": "model_feature",
    },
    {
        "repo": "GEMSDOE24",
        "ref": "07345ea0604953d7efb858d9cfbc21e20c7aca0b",
        "src_path": "data/external/gdr_wellspring_in_footprint.csv",
        "dest_name": "gdr_wellspring_in_footprint.csv",
        "sha256": "122718e65bdf55aab0ee12ad20d80062f0deb1de957225a61ad880dd5dc196ea",
        "official_source": "DOE Geothermal Data Repository (GDR) #1391 INGENIOUS Thermal Wells & Springs",
        "official_url": "https://gdr.openei.org/submissions/1391",
        "license": "CC-BY-4.0 (Great Basin Center for Geothermal Energy / UNR)",
        "role": "model_feature_coords_and_temp_only",
    },
    {
        "repo": "GEMSDOE24",
        "ref": "07345ea0604953d7efb858d9cfbc21e20c7aca0b",
        "src_path": "data/external/gdr_volcanic_vents_in_footprint.csv",
        "dest_name": "gdr_volcanic_vents_in_footprint.csv",
        "sha256": "f91bafbaccaaf2754e71d60434fc0f9eb2c7b880c6e714883f4974542ff6a0bf",
        "official_source": "DOE GDR #1391 INGENIOUS Quaternary/Neogene Volcanic Vents",
        "official_url": "https://gdr.openei.org/submissions/1391",
        "license": "CC-BY-4.0 (GBCGE / UNR)",
        "role": "model_feature_coords_only",
    },
    {
        "repo": "GEMSDOE30",
        "ref": "35ce8911e2c3287eed973eacd12c252e8cb3f34c",
        "src_path": "data/external/derived_gdr_2m_probes_100m_u8.tif",
        "dest_name": "derived_gdr_2m_probes_100m_u8.tif",
        "sha256": "7ac3cfdf2412f7f8a8b82d928115888c510f106f0254fb0b3988448db2f3b6ec",
        "official_source": "DOE GDR #1391 INGENIOUS Shallow 2-Meter Temperature Probe Surveys",
        "official_url": "https://gdr.openei.org/submissions/1391",
        "license": "CC-BY-4.0 (GBCGE / UNR)",
        "role": "model_feature",
    },
    {
        "repo": "GEMSDOE30",
        "ref": "35ce8911e2c3287eed973eacd12c252e8cb3f34c",
        "src_path": "data/external/derived_gdr_paleo_100m_u8.tif",
        "dest_name": "derived_gdr_paleo_100m_u8.tif",
        "sha256": "d6a3609bd7943fa5f1126a3cc688441aeceee261a76cd6a90a206830400066a4",
        "official_source": "DOE GDR #1391 INGENIOUS Paleo-Geothermal Sinter, Travertine & Tufa Deposits",
        "official_url": "https://gdr.openei.org/submissions/1391",
        "license": "CC-BY-4.0 (GBCGE / UNR)",
        "role": "model_feature",
    },
    {
        "repo": "GEMSDOE24",
        "ref": "07345ea0604953d7efb858d9cfbc21e20c7aca0b",
        "src_path": "data/external/audit_sources/tiger_road_distance_m.tif",
        "dest_name": "tiger_road_distance_m.tif",
        "sha256": "e5350423508968fa2d32b0a6ae0d3fb4ae3ea645e3b8736f0c8e7ad9ff2f2988",
        "official_source": "US Census Bureau TIGER/Line Roads (scarp embankment de-confounder)",
        "official_url": "https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html",
        "license": "US Public Domain (17 U.S.C. 105)",
        "role": "deconfounder_feature",
    },
    {
        "repo": "GEMSDOE24",
        "ref": "07345ea0604953d7efb858d9cfbc21e20c7aca0b",
        "src_path": "data/external/derived_sgmc_faults_100m_u8.tif",
        "dest_name": "derived_sgmc_faults_100m_u8.tif",
        "sha256": "643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0",
        "official_source": "USGS State Geologic Map Compilation (SGMC, Data Series 1052)",
        "official_url": "https://pubs.usgs.gov/ds/1052/",
        "license": "US Public Domain (CC0)",
        "role": "diagnostic_evaluation_only_never_in_model",
    },
    {
        "repo": "GEMSDOE30",
        "ref": "35ce8911e2c3287eed973eacd12c252e8cb3f34c",
        "src_path": "data/external/derived_gdr_volcanics_100m_u8.tif",
        "dest_name": "derived_gdr_volcanics_100m_u8.tif",
        "sha256": "c219bd644e6f7a4071dc429e29b909a2296967b0657bf456bb6675413ee76cb2",
        "official_source": "DOE GDR #1391 INGENIOUS Quaternary & Neogene Volcanic Units & Vents",
        "official_url": "https://gdr.openei.org/submissions/1391",
        "license": "CC-BY-4.0 (GBCGE / UNR)",
        "role": "model_feature",
    },
    {
        "repo": "GEMSDOE85",
        "ref": "f016dd5194ec45fcb3e25afb29ffa6ea04207356",
        "src_path": "data/external/usgs_comcat_geodawn.csv",
        "dest_name": "usgs_comcat_geodawn.csv",
        "sha256": "c580226b3b0516653873b87077edb8e164c3545e9bc1e7c764789c52bdd30624",
        "official_source": "USGS Earthquake Hazards Program ComCat FDSN Event Web Service v1 (1900-2026, incl. 541 post-2021 post-INGENIOUS events)",
        "official_url": "https://earthquake.usgs.gov/fdsnws/event/1/",
        "license": "US Public Domain (17 U.S.C. 105 / CC0)",
        "role": "model_feature_coords_mag_year_only",
    },
    {
        "repo": "GEMSDOE85",
        "ref": "f016dd5194ec45fcb3e25afb29ffa6ea04207356",
        "src_path": "data/external/usgs_heat_flow_wells_epsg32611.csv",
        "dest_name": "usgs_heat_flow_wells_epsg32611.csv",
        "sha256": "9773bf59340e06901b2855d30b1972dc91374a5d344a8324452f9bb69304e370",
        "official_source": "USGS / SMU / DOE GDR #1391 INGENIOUS Borehole Conductive & Residual Heat Flow Compilation",
        "official_url": "https://gdr.openei.org/submissions/1391",
        "license": "CC-BY-4.0 / US Public Domain",
        "role": "model_feature_coords_and_heatflow_only",
    },
    {
        "repo": "GEMSDOE85",
        "ref": "f016dd5194ec45fcb3e25afb29ffa6ea04207356",
        "src_path": "data/external/gb_regional_stress_grid_10km.csv",
        "dest_name": "gb_regional_stress_grid_10km.csv",
        "sha256": "9e01d5de2b6070816513e163a8f34cf19559630d497ef8ddc60b4d18565140ef",
        "official_source": "USGS Western US Stress Map (Lund & Snee 2016, SIM 3353) / World Stress Map Regional SHmin & Simpson A_phi Grid",
        "official_url": "https://pubs.usgs.gov/sim/3353/",
        "license": "US Public Domain (17 U.S.C. 105) / CC-BY-4.0",
        "role": "model_feature_stress_tensor",
    },
]

DEM10_REPO = "GEMSDOE10"
DEM10_TAG = "ext/dem10-36343078537"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_many(repo: str, ref: str, wanted: dict[str, Path]) -> None:
    if not wanted:
        return
    url = f"https://codeload.github.com/buffedlizard55-lab/{repo}/tar.gz/{ref}"
    req = urllib.request.Request(url, headers={"User-Agent": "wbggemsdoe2-fetch-external"})
    with urllib.request.urlopen(req, timeout=240) as resp:
        with tarfile.open(fileobj=resp, mode="r|gz") as tf:
            for member in tf:
                if not member.isfile():
                    continue
                parts = member.name.split("/", 1)
                rel = parts[1] if len(parts) > 1 else parts[0]
                if rel in wanted:
                    dest = wanted[rel]
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    fh = tf.extractfile(member)
                    if fh is not None:
                        tmp = dest.with_suffix(dest.suffix + ".tmp")
                        with tmp.open("wb") as out:
                            for chunk in iter(lambda: fh.read(1 << 20), b""):
                                out.write(chunk)
                        tmp.replace(dest)


def fetch_and_verify(dest_dir: Path = DEST) -> dict:
    dest_dir.mkdir(parents=True, exist_ok=True)
    by_repo_ref: dict[tuple[str, str], dict[str, Path]] = defaultdict(dict)
    for item in EXTERNAL_PINS:
        target = dest_dir / item["dest_name"]
        if target.is_file() and sha256_file(target) == item["sha256"]:
            continue
        by_repo_ref[(item["repo"], item["ref"])][item["src_path"]] = target

    for (repo, ref), mapping in by_repo_ref.items():
        print(f"[external] Streaming {len(mapping)} file(s) from {repo}@{ref[:10]}...", flush=True)
        extract_many(repo, ref, mapping)

    verified_rows = []
    for item in EXTERNAL_PINS:
        target = dest_dir / item["dest_name"]
        if not target.is_file():
            raise FileNotFoundError(f"Missing external layer after fetch: {target}")
        got = sha256_file(target)
        if got != item["sha256"]:
            raise ValueError(f"SHA-256 mismatch for {item['dest_name']}: {got} != {item['sha256']}")
        verified_rows.append(
            {
                "name": item["dest_name"],
                "bytes": target.stat().st_size,
                "sha256": got,
                "mirror_repo": f"buffedlizard55-lab/{item['repo']}",
                "mirror_ref": item["ref"],
                "official_source": item["official_source"],
                "official_url": item["official_url"],
                "license": item["license"],
                "role": item["role"],
            }
        )

    dem10_dir = dest_dir / "dem10"
    dem10_dir.mkdir(parents=True, exist_ok=True)
    man_file = dem10_dir / "manifest.json"
    if not man_file.is_file():
        extract_many(DEM10_REPO, DEM10_TAG, {"manifest.json": man_file})
    manifest = json.loads(man_file.read_text(encoding="utf-8"))
    need_dem10 = {}
    for ch in manifest["channels"]:
        p = dem10_dir / f"{ch}.f32.npy"
        want = manifest["channel_stats"][ch]["sha256"]
        if not (p.is_file() and sha256_file(p) == want):
            need_dem10[f"{ch}.f32.npy"] = p
    if need_dem10:
        print(f"[external] Streaming {len(need_dem10)} 10m 3DEP DEM channels...", flush=True)
        extract_many(DEM10_REPO, DEM10_TAG, need_dem10)

    dem10_rows = []
    for ch in manifest["channels"]:
        p = dem10_dir / f"{ch}.f32.npy"
        want = manifest["channel_stats"][ch]["sha256"]
        got = sha256_file(p)
        if got != want:
            raise ValueError(f"SHA-256 mismatch on 10m DEM channel {ch}: {got} != {want}")
        dem10_rows.append({"channel": ch, "bytes": p.stat().st_size, "sha256": got})

    receipt = {
        "schema": "wbggems.external-provenance.v1",
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "storage_note": "Stored strictly in git-ignored, snapshot-excluded .cache/external/.",
        "files": verified_rows,
        "dem10_seamless_3dep": {
            "mirror_repo": f"buffedlizard55-lab/{DEM10_REPO}",
            "mirror_tag": DEM10_TAG,
            "official_source": "USGS 3D Elevation Program (3DEP) 1/3 arc-second (~10 m) Seamless DEM",
            "official_url": "https://www.usgs.gov/3d-elevation-program/about-3dep-products-services",
            "license": "US Public Domain (17 U.S.C. 105 / CC0)",
            "channels": dem10_rows,
        },
    }
    out = ROOT / "evidence" / "external_layers_provenance.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"[external] Verified {len(verified_rows)} external files + {len(dem10_rows)} 10m DEM channels.")
    return receipt


if __name__ == "__main__":
    raise SystemExit(0 if fetch_and_verify() else 1)
