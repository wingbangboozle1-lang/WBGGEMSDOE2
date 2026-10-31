"""Filesystem contract for the WBG5 campaign.

Competition data are deliberately *not* committed.  The pinned mirrors used here
are documented in ``data_public/official_inputs.json``.
"""
from __future__ import annotations

import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WORK = Path(os.environ.get("WBG5_WORK", "/tmp/wbg"))
EXTERNAL = Path(os.environ.get("WBG5_EXTERNAL", "/tmp/gems_ext"))
FEATURES = Path(os.environ.get("WBG5_FEATURES", "/tmp/training_features.tif"))

# Mirrored competition rasters (hash-pinned; see data_public/official_inputs.json)
LABELS = EXTERNAL / "GEMSDOE24/data/bridge/labels.tif"
SAMPLE = EXTERNAL / "GEMSDOE24/data/bridge/sample_submission.tif"
LIDAR = EXTERNAL / "GEMSDOE24/data/external/lidar_scarp_features_u8.tif"
RAD = EXTERNAL / "GEMSDOE24/data/external/geodawn_rad_u8.tif"
RAD_EXT = EXTERNAL / "GEMSDOE24/data/external/geodawn_extensions_u8.tif"
SGMC = EXTERNAL / "GEMSDOE30/data/external/derived_sgmc_faults_100m_u8.tif"
WELLSPRING = EXTERNAL / "GEMSDOE24/data/external/gdr_wellspring_in_footprint.csv"
VENTS = EXTERNAL / "GEMSDOE24/data/external/gdr_volcanic_vents_in_footprint.csv"
PROBES = EXTERNAL / "GEMSDOE30/data/external/derived_gdr_2m_probes_100m_u8.tif"
PALEO = EXTERNAL / "GEMSDOE30/data/external/derived_gdr_paleo_100m_u8.tif"
VOLCANICS = EXTERNAL / "GEMSDOE30/data/external/derived_gdr_volcanics_100m_u8.tif"
ROADS = EXTERNAL / "GEMSDOE24/data/external/audit_sources/tiger_road_distance_m.tif"

def ensure_work() -> Path:
    WORK.mkdir(parents=True, exist_ok=True)
    return WORK
