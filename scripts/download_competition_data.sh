#!/usr/bin/env bash
# download_competition_data.sh — stage GEMS Prize competition data into data/
#
# BLOCKER (verified): the official data page requires a DrivenData login:
#   https://www.drivendata.org/competitions/306/competition-doe-gems/data/
#   -> redirects to https://www.drivendata.org/accounts/login/
# No credentials are available in this environment, so this script can only
# document the sources.  Run it on an unrestricted machine with a logged-in
# DrivenData session, or obtain the files from the public mirrors below.
#
# Official source (login required):
#   https://www.drivendata.org/competitions/306/competition-doe-gems/data/
#     training_features.tif   (19-channel numeric feature stack, EPSG:32611, 100 m)
#     labels.tif              (USGS + INGENIOUS fault labels)
#     sample_submission.tif   (format template: total fault absence)
#     1m_DEM_links.csv        (DEM download URLs)
#
# Public mirrors referenced by the competition documentation (dropbox; no auth):
#   https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?dl=1
#       (competition rules / submission procedure PDF)
#   https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?dl=1
#   https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?dl=1
#   https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?dl=1
#   https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?dl=1
#
# Official context pages (no auth):
#   https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/   (problem)
#   https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/   (about)
#   https://www.drivendata.org/competitions/306/competition-doe-gems/rules/      (rules)
#   https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/
#   https://github.com/drivendataorg/gems-prize-reference-solution              (reference solution)
#   https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
#   https://gbcge.org/current-projects/ingenious/
#   https://epsg.io/32611
#   https://gdr.openei.org/submissions/1391                                     (GEMS data submission)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="${REPO_ROOT}/data"

echo "==> WBGGEMSDOE2 data staging"
echo "NOTE: DrivenData requires login; fetch the four files above into ${DATA_DIR}:"
echo "  training_features.tif  labels.tif  sample_submission.tif  1m_DEM_links.csv"
mkdir -p "${DATA_DIR}"

if [ -f "${DATA_DIR}/training_features.tif" ] && [ -f "${DATA_DIR}/labels.tif" ]; then
    echo "OK: competition features + labels present in ${DATA_DIR}"
else
    echo "WARN: training_features.tif / labels.tif missing — holdout scoring is blocked"
    echo "      until they are staged (DrivenData login required)."
fi
ls -la "${DATA_DIR}" 2>/dev/null || true
