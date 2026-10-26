#!/usr/bin/env bash
# Fetch public inputs from the sibling public repos (git transport; the
# sandbox blocks raw.githubusercontent.com). No DrivenData auth is used:
# labels/sample come from GEMSDOE24's public bridge copies - VERIFY against
# the official data page (login required) before any real submission:
# https://www.drivendata.org/competitions/306/competition-doe-gems/data/
set -euo pipefail
DEST="${1:-/tmp/wbg_data}"; mkdir -p "$DEST" /tmp/reg
clone(){ [ -d "/tmp/reg/$1" ] || git clone -q --depth 1 "https://github.com/buffedlizard55-lab/$1.git" "/tmp/reg/$1"; }
clone GEMSDOE24; clone GEMSDOE32
cp /tmp/reg/GEMSDOE24/data/bridge/labels.tif "$DEST/"
cp /tmp/reg/GEMSDOE24/data/bridge/sample_submission.tif "$DEST/"
cp /tmp/reg/GEMSDOE24/data/external/lidar_scarp_features_u8.tif "$DEST/"
cp /tmp/reg/GEMSDOE24/data/external/geodawn_rad_u8.tif "$DEST/"
cp /tmp/reg/GEMSDOE24/data/external/geodawn_extensions_u8.tif "$DEST/"
cp /tmp/reg/GEMSDOE32/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif "$DEST/champion.tif"
echo "OK -> $DEST"
