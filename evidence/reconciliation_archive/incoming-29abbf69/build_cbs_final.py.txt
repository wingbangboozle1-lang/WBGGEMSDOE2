#!/usr/bin/env python3
"""Pass-2 final candidate construction for the CBS campaign.

The campaign's holdout budget sweep was monotone (catalogue recovery always
rewards more coverage), so the 64,284-dot artifact it emitted is holdout-optimal
but live-pessimal: every live measurement in this repo penalises dot count
(score law -0.000775 per 1,000 dots; the two ~60k lineage files are the worst
scorers of the nine). The holdout is therefore used to validate the SURFACE
(where), and the live-calibrated score law to set the BUDGET (how many).
This script re-emits the saved cross-fitted CTRL-arm OOF surface at 38,000
collar-free dots, re-scores that exact emission rule per fold with the shared
evaluator, re-runs the uniqueness audit, and writes via the shared writer.
No new experiment and no new surface is created.
"""
from __future__ import annotations
import datetime as dt, hashlib, json, sys
from pathlib import Path
import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, "/tmp/wbg/template/src")
from gems57 import evaluate_holdout, spatial, submission_writer  # noqa: E402
from wbggems.novelty import spearman_footprint  # noqa: E402
from wbggems.validate import inspect_tif  # noqa: E402
from run_wbg2_cbs import dotted  # noqa: E402

FINAL_BUDGET = 38_000
MIRROR = Path("/tmp/wbg/mirror"); FOCUS = Path("/tmp/wbg/focus")

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

def main():
    sample = MIRROR / "reference_grid_mirror.tif"
    with rasterio.open(sample) as ds:
        fp = np.isfinite(ds.read(1)) & (ds.read_masks(1) > 0)
    with rasterio.open(MIRROR / "existing_faults_mirror.tif") as ds:
        cat = (ds.read(1) == 1) & fp
    surf = np.load("/tmp/wbg/cache/oof_ctrl_19b_dotted.npy")
    dcat = ndi.distance_transform_edt(~cat)
    full_base = fp & (dcat > 3.0)
    x1 = int(round(0.0082 * float(full_base.sum())))
    factor = FINAL_BUDGET / x1
    folds = list(spatial.folds(cat, fp, buffer_px=80))
    tm_sum, per_fold = None, []
    for f in folds:
        dvis = ndi.distance_transform_edt(~(f["visible"] & fp))
        base = fp & f["region"] & (dvis > 3.0)
        b = int(round(0.0082 * factor * float(base.sum())))
        dots = dotted(surf, base, b)
        sc, tm = evaluate_holdout.evaluate(dots.astype(np.float32), f, fp, block_side=200)
        tm_sum = tm if tm_sum is None else tm_sum + tm
        per_fold.append({"fold": int(f["fold"]), "budget": b, "dti": sc["dti"], "n_truth": sc["n_truth"]})
        print(per_fold[-1], flush=True)
    zero_ref = np.zeros_like(tm_sum); zero_ref[:, 2] = tm_sum[:, 3]; zero_ref[:, 3] = tm_sum[:, 3]
    pooled_only = evaluate_holdout.pooled_summary({"cand": tm_sum, "zero_ref": zero_ref},
                                                  draws=1000, seed=520810, candidate="cand")
    hold = pooled_only["scores"]["cand"]
    print("POOLED candidate @38k rule:", hold, flush=True)

    cand_dots = dotted(surf, full_base, FINAL_BUDGET)
    cand = cand_dots.astype(np.float32)
    rows = []
    def compare(name, path, category):
        with rasterio.open(path) as ds:
            a = ds.read(1)
        ref_dots = np.isfinite(a) & (a > 0) & fp
        d = ndi.distance_transform_edt(~ref_dots)
        cov = float(((d <= 3) & fp).sum()) / float(fp.sum())
        ov = float((d[cand_dots] <= 3).mean())
        rho = spearman_footprint(np.where(fp, surf, 0.0),
                                 np.where(fp, np.nan_to_num(a, nan=0.0), 0.0).astype(np.float32), fp)
        rows.append({"id": name, "category": category, "sha256": sha256(path),
                     "ref_dots": int(ref_dots.sum()), "coverage3px_of_footprint": cov,
                     "candidate_overlap_3px": ov, "enrichment_over_coverage": ov / max(cov, 1e-9),
                     "surface_spearman": rho, "exact_shared_dots": int((cand_dots & ref_dots).sum()),
                     "literal_duplicate_flag": bool(ov > 0.70 or abs(rho) > 0.90)})
        print(f"vs {name:26s} ov={ov:.4f} rho={rho:+.4f} cov={cov:.4f}", flush=True)
    cfg = json.loads((ROOT / "config/registry_inputs.json").read_text())
    for r in cfg["inputs"][:9]:
        compare(r["id"], FOCUS / f"{r['id']}.tif", "focus_champion")
    for nm, pth in [("DZ16", "docs/downloads/wbg2-dz16-n34500-20261027T000000Z-8e4646cf-zeros.tif"),
                    ("H3PACK", "docs/downloads/h3-pack/wbg3-h3pack-34k-20261027T174337Z-zeros.tif"),
                    ("MSPTCD_E3", "docs/downloads/msptcd/wbg2-msptcd-e3-25594dots-20261027T173000Z-2642eedd-zeros.tif"),
                    ]:
        compare(nm, ROOT / pth, "sibling_lane")
    p64 = ROOT / "docs/downloads/cbs/wbg2-cbs-ctrl-19b-dotted-64284dots-20261027T191325Z-9cae06c2-zeros.tif"
    if p64.is_file():
        compare("CBS_64K_SUPERSEDED", p64, "superseded_self")
    for r in cfg["inputs"][9:]:
        compare(r["id"], FOCUS / f"{r['id']}.tif", "literal_witness")
    disc = [r for r in rows if r["category"] in ("focus_champion", "sibling_lane")]
    unique_disc = all(not r["literal_duplicate_flag"] for r in disc)

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    h8 = hashlib.sha256(cand.tobytes()).hexdigest()[:8]
    stem = f"wbg2-d19dotted-{FINAL_BUDGET}dots-{stamp}-{h8}-zeros"
    out = ROOT / "docs/downloads/cbs" / f"{stem}.tif"
    for ext in (".tif", ".zip", ".json"):
        out.with_suffix(ext).unlink(missing_ok=True)
    note = f"D19-dotted 19-band HGB cross-fitted {FINAL_BUDGET} collar-free dots zeros unique (wbggemsdoe2)"
    assert len(note) <= 140
    receipt = submission_writer.write_submission(out, cand, sample, fp, note=note, name=stem,
                    catalogue=cat, metadata={"campaign": "WBG2-CBS-20261027 pass-2 final",
                                             "arm": "ctrl_19b_dotted", "budget": FINAL_BUDGET,
                                             "ok_to_submit": bool(unique_disc)})
    insp = inspect_tif(out, sample, strict_all_finite=True)
    assert insp["format_valid_against_reference"]
    result = {"schema": "wbggems.cbs-final.v1", "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
              "arm": "ctrl_19b_dotted (control arm; CBS experiments negative vs control)",
              "budget": FINAL_BUDGET, "budget_factor_vs_campaign_x1": factor, "campaign_x1_budget": x1,
              "holdout_candidate_rule": {"evidence_class": "HOLDOUT-DTI",
                                         "evaluator_version": "gems57-pooled-hide-v2", **hold},
              "per_fold": per_fold, "unique_vs_9focus_and_siblings": unique_disc,
              "registry_comparison": rows,
              "artifact": {"stem": stem, "tif_path": str(out.relative_to(ROOT)),
                           "sha256": receipt["sha256"], "dots": int(cand_dots.sum()),
                           "note": note, "validator": insp},
              "supersedes": "wbg2-cbs-ctrl-19b-dotted-64284dots-20261027T191325Z-9cae06c2-zeros (holdout-optimal budget; live-pessimal; removed from downloads)"}
    (ROOT / "evidence/cbs_final.json").write_text(json.dumps(result, indent=2, allow_nan=False, default=float) + "\n")
    print(json.dumps({"stem": stem, "sha256": receipt["sha256"], "unique_disc": unique_disc}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
