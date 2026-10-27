"""Write, zip and validate the H3-PACK submission GeoTIFF.

Mirrors the official sample exactly: EPSG:32611, 100 m, 3730x3292, one float32
band, NaN outside the data footprint, {0, 1} inside it.  The file is written by
copying the sample's profile, so the grid, CRS and transform cannot drift.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import time
import zipfile
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT / "src"))
from wbg3.validate import validate_submission  # noqa: E402

SAMPLE = ROOT / "data/official/sample_submission.tif"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dots", default="scratch/h3_dots_final.npy")
    ap.add_argument("--name", default=None)
    ap.add_argument("--note", default=None)
    args = ap.parse_args()

    dots = np.load(ROOT / args.dots)
    if dots.dtype != bool:
        dots = dots > 0
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    name = args.name or f"wbg3-h3pack-34k-{stamp}-zeros"
    note = args.note or ("H3-PACK: collar-free, max-packing dot field; "
                         "34000 dots; no hidden label used")

    with rasterio.open(SAMPLE) as ref:
        profile = ref.profile.copy()
        footprint = np.isfinite(ref.read(1))
    if dots.shape != footprint.shape:
        raise SystemExit("dot grid does not match the sample grid")
    bad = int((dots & ~footprint).sum())
    if bad:
        raise SystemExit(f"{bad} dots fall outside the data footprint")

    data = np.where(footprint & dots, 1.0, 0.0).astype(np.float32)
    data[~footprint] = np.nan
    profile.update(dtype="float32", count=1, nodata=float("nan"), compress="deflate")

    outs = [ROOT / "docs/downloads" / f"{name}.tif", ROOT / "downloads" / f"{name}.tif"]
    for out in outs:
        out.parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(out, "w", **profile) as dst:
            dst.write(data, 1)
            dst.update_tags(COMMENT=note, RUN="H3-PACK")

    tif = outs[0]
    zpath = tif.with_suffix(".zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(tif, arcname=tif.name)

    report = validate_submission(tif, SAMPLE)
    report.update(
        evidence_class="LOCAL-FORMAT-MEASUREMENT",
        submission_name=name,
        note=note,
        tif_sha256=sha256(tif),
        zip_sha256=sha256(zpath),
        zip_member=tif.name,
        dots=int(dots.sum()),
        organizer_acceptance="unknown (no portal upload in this environment)",
        mirrors=[str(p.relative_to(ROOT)) for p in outs],
        zip_path=str(zpath.relative_to(ROOT)),
    )
    out = ROOT / "evidence/h3_submission.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "failures"}, indent=2))
    if report["failures"]:
        print("FAILURES:", report["failures"])
        return 1
    print("[ok] format validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
