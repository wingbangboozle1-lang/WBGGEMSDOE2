#!/usr/bin/env python3
"""CBS (Covered Basement Step) campaign — see research/cbs_preregistration_20261027.md.

Reuses, unmodified: gems57.spatial.folds, gems57.evaluate_holdout
(gems57-pooled-hide-v2), gems57.submission_writer, and the label-free physics
operators in src/wbggems/msptcd.py. Inputs are the hash-pinned public mirrors
(restored by scripts/restore_public_mirrors.py); they are NOT authenticated
DrivenData downloads. This script spends no submission slot.
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, sys, time
from pathlib import Path
import numpy as np
import rasterio
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from wbggems.msptcd import RAW_BAND_NAMES, build_or_load_msptcd_cache  # noqa: E402
from wbggems.novelty import single_feature_auc, spearman_footprint  # noqa: E402
from wbggems.validate import inspect_tif  # noqa: E402

SUBSURFACE_RAW = ["mag_anom", "rtp", "tmi_hg", "iso_grav_anom_slope", "tmi_vg",
                  "iso_grav_anom_vg", "iso_grav_anom", "tmi", "depth_to_base_surf",
                  "cond_surf", "iso_grav_anom_hg"]
CBS_PHYSICS = ["mag_tilt_grad", "grav_tilt_grad", "dip_offset_concordance",
               "cond_flank_asymmetry", "depth_cover_log_step", "grav_mag_orient_coherence"]
STRAIN_RAW = ["geod_2ndinv", "geod_shearrate", "geod_dilaterate", "deq_n100a15", "ieq_n100a15"]
STRAIN_PHYSICS = ["strain_dilation_ratio", "strain_shear_edge_gate", "seismic_structural_index"]
CBS = SUBSURFACE_RAW + CBS_PHYSICS
CBS_ACTIVE = CBS + STRAIN_RAW + STRAIN_PHYSICS
SEP_RADIUS = 5

def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

def bayes_recal(prob, pi_sample, pi_true):
    p = np.clip(np.asarray(prob, np.float64), 1e-7, 1 - 1e-7)
    wp, wn = pi_true / max(pi_sample, 1e-9), (1 - pi_true) / max(1 - pi_sample, 1e-9)
    num = wp * p
    return (num / np.maximum(num + wn * (1 - p), 1e-12)).astype(np.float32)

def predict_chunked(clf, mmaps, names, target, pi_s, pi_t, chunk=512):
    h, w = target.shape
    out = np.zeros((h, w), np.float32)
    for y0 in range(0, h, chunk):
        y1 = min(h, y0 + chunk)
        ys, xs = np.nonzero(target[y0:y1])
        if ys.size == 0:
            continue
        X = np.empty((ys.size, len(names)), np.float32)
        for j, n in enumerate(names):
            X[:, j] = mmaps[n][y0:y1][ys, xs]
        blk = np.zeros((y1 - y0, w), np.float32)
        blk[ys, xs] = bayes_recal(clf.predict_proba(X)[:, 1], pi_s, pi_t)
        out[y0:y1] = blk
    return out

_DISK = None
def dotted(surface, eligible, budget):
    """Greedy descending-surface dots, Euclidean suppression radius SEP_RADIUS."""
    global _DISK
    if _DISK is None:
        yy, xx = np.mgrid[-SEP_RADIUS:SEP_RADIUS + 1, -SEP_RADIUS:SEP_RADIUS + 1]
        _DISK = (xx * xx + yy * yy) <= SEP_RADIUS * SEP_RADIUS
    h, w = surface.shape
    idx = np.flatnonzero(eligible.ravel())
    vals = surface.ravel()[idx]
    order = idx[np.argsort(-vals, kind="stable")]
    blocked = np.zeros((h, w), bool)
    dots = np.zeros((h, w), bool)
    taken = 0
    R = SEP_RADIUS
    for j in order:
        r, c = divmod(int(j), w)
        if blocked[r, c]:
            continue
        dots[r, c] = True
        taken += 1
        if taken >= budget:
            break
        r0, r1, c0, c1 = max(0, r - R), min(h, r + R + 1), max(0, c - R), min(w, c + R + 1)
        sub = _DISK[R - (r - r0):R - (r - r0) + (r1 - r0), R - (c - c0):R - (c - c0) + (c1 - c0)]
        blocked[r0:r1, c0:c1] |= sub
    return dots

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mirror", type=Path, default=Path("/tmp/wbg/mirror"))
    ap.add_argument("--template-src", type=Path, default=Path("/tmp/wbg/template/src"))
    ap.add_argument("--cache", type=Path, default=Path("/tmp/wbg/cache"))
    ap.add_argument("--focus-dir", type=Path, default=Path("/tmp/wbg/focus"))
    args = ap.parse_args()
    t0 = time.perf_counter()
    sys.path.insert(0, str(args.template_src))
    from gems57 import evaluate_holdout, spatial, submission_writer

    sample_path = args.mirror / "reference_grid_mirror.tif"
    feats_path = args.mirror / "training_features_mirror.tif"
    with rasterio.open(sample_path) as ds:
        ref = ds.read(1); fp = np.isfinite(ref) & (ds.read_masks(1) > 0)
    with rasterio.open(args.mirror / "existing_faults_mirror.tif") as ds:
        cat = (ds.read(1) == 1) & fp
    print(f"[cbs] footprint={fp.sum()} catalogue={cat.sum()}", flush=True)

    # ---- cache raw bands + physics (label-free) ----
    band_dir = args.cache / "bands"; band_dir.mkdir(parents=True, exist_ok=True)
    for i, name in enumerate(RAW_BAND_NAMES, 1):
        p = band_dir / f"band-{i:02d}.npy"
        if not p.is_file():
            with rasterio.open(feats_path) as ds:
                a = ds.read(i).astype(np.float32)
            tmp = p.with_suffix(".tmp.npy"); np.save(tmp, a); tmp.replace(p)
            del a
    phys = build_or_load_msptcd_cache(band_dir, args.cache / "physics", fp)
    paths = {RAW_BAND_NAMES[i - 1]: band_dir / f"band-{i:02d}.npy" for i in range(1, 20)}
    paths.update(phys)
    mmaps = {n: np.load(p, mmap_mode="r") for n, p in paths.items()}
    print("[cbs] features cached", flush=True)

    folds = list(spatial.folds(cat, fp, buffer_px=80))

    # ---- leakage canaries: every feature used by any arm ----
    used = sorted(set(RAW_BAND_NAMES) | set(CBS_PHYSICS) | set(STRAIN_PHYSICS))
    canary_rows, worst = [], (0.0, None)
    for name in used:
        mm = mmaps[name]; per_fold = []
        for f in folds:
            tv = f["train"] & np.isfinite(mm)
            fill = float(np.median(mm[tv][::8])) if tv.any() else 0.0
            sel = fp & f["region"] & ~f["visible"]
            res = single_feature_auc(np.where(np.isfinite(mm), mm, fill), f["truth"], sel)
            per_fold.append({"fold": int(f["fold"]), **res})
            if not res["canary_pass"]:
                raise RuntimeError(f"STOP canary {name} fold {f['fold']} AUC2={res['two_sided_auc']}")
        mx = max(r["two_sided_auc"] for r in per_fold)
        if mx > worst[0]:
            worst = (mx, name)
        canary_rows.append({"feature": name, "max_two_sided_auc": mx, "per_fold": per_fold})
    canary = {"evidence_class": "LEAKAGE-CANARY-MEASUREMENT", "threshold": 0.90,
              "features_tested": len(used), "folds_tested": len(folds), "all_passed": True,
              "max_two_sided_auc": worst[0], "max_two_sided_feature": worst[1], "features": canary_rows}
    print(f"[cbs] canaries CLEAN max AUC2={worst[0]:.4f} ({worst[1]})", flush=True)

    slope = np.array(mmaps["det_elev_slope"], dtype=np.float32)
    slope_gate_q70 = float(np.nanpercentile(slope[fp], 70))
    cover_gate = fp & (slope <= slope_gate_q70)
    low_relief_thr = float(np.nanmedian(slope[cat]))
    low_relief = slope <= low_relief_thr

    arms = ["ctrl_19b_dotted", "exp1_cbs_core", "exp2_cbs_cover", "exp3_cbs_active"]
    feat_sets = {"ctrl_19b_dotted": list(RAW_BAND_NAMES), "exp1_cbs_core": CBS,
                 "exp3_cbs_active": CBS_ACTIVE}
    oof_surface = {a: np.zeros(fp.shape, np.float32) for a in arms}
    terms = {a: None for a in arms}
    terms_lr = {a: None for a in arms}
    per_fold = []
    emitted_oof = {a: np.zeros(fp.shape, bool) for a in arms}

    for f in folds:
        fid = int(f["fold"])
        train, vis = f["train"], f["visible"]
        dvis = ndi.distance_transform_edt(~(vis & fp))
        pos = np.nonzero(train & vis)
        neg_pool = np.nonzero(train & (dvis > 3.0))
        rng = np.random.default_rng(20261027 + 101 * fid)
        n_pos = int(pos[0].size); n_neg = min(int(neg_pool[0].size), 4 * n_pos)
        sel = rng.choice(neg_pool[0].size, size=n_neg, replace=False)
        sy = np.concatenate([pos[0], neg_pool[0][sel]]); sx = np.concatenate([pos[1], neg_pool[1][sel]])
        y = np.concatenate([np.ones(n_pos, np.int8), np.zeros(n_neg, np.int8)])
        pi_s = n_pos / (n_pos + n_neg); pi_t = n_pos / float(train.sum())
        eval_region = fp & f["region"]
        base_elig = eval_region & (dvis > 3.0)
        budget = int(round(0.0082 * float(base_elig.sum())))
        fold_lr = dict(f); fold_lr["truth"] = f["truth"] & low_relief
        row = {"fold": fid, "receipt": f["receipt"], "budget_fold": budget, "arms": {}}
        for arm, names in feat_sets.items():
            X = np.empty((y.size, len(names)), np.float32)
            for j, n in enumerate(names):
                X[:, j] = mmaps[n][sy, sx]
            clf = HistGradientBoostingClassifier(max_iter=160, learning_rate=0.06,
                        max_leaf_nodes=31, min_samples_leaf=80, l2_regularization=2.0,
                        random_state=4200 + 17 * fid + arms.index(arm))
            clf.fit(X, y); del X
            p = predict_chunked(clf, mmaps, names, eval_region, pi_s, pi_t)
            oof_surface[arm][eval_region] = p[eval_region]
            del clf
        oof_surface["exp2_cbs_cover"][eval_region] = oof_surface["exp1_cbs_core"][eval_region]
        for arm in arms:
            elig = base_elig & cover_gate if arm == "exp2_cbs_cover" else base_elig
            dots = dotted(oof_surface[arm], elig, budget)
            emitted_oof[arm] |= dots
            pred = dots.astype(np.float32)
            sc, tm = evaluate_holdout.evaluate(pred, f, fp, block_side=200)
            terms[arm] = tm if terms[arm] is None else terms[arm] + tm
            sc2, tm2 = evaluate_holdout.evaluate(pred, fold_lr, fp, block_side=200)
            terms_lr[arm] = tm2 if terms_lr[arm] is None else terms_lr[arm] + tm2
            row["arms"][arm] = {"dti": sc["dti"], "n_emitted": sc["n_emitted"],
                                "n_truth": sc["n_truth"], "dti_low_relief": sc2["dti"]}
            print(f"  fold={fid} {arm:18s} DTI={sc['dti']:.6f} LR={sc2['dti']:.6f} dots={sc['n_emitted']}", flush=True)
        per_fold.append(row)

    exps = ["exp1_cbs_core", "exp2_cbs_cover", "exp3_cbs_active"]
    best = max(exps, key=lambda a: float(evaluate_holdout.from_terms(terms[a].sum(axis=0))))
    # Candidate construction uses the best arm overall (control included). If the
    # control wins, the CBS hypothesis is recorded as NEGATIVE and the control arm
    # ("19-band + dotted emission") becomes the candidate; both facts are reported.
    cand_arm = max(arms, key=lambda a: float(evaluate_holdout.from_terms(terms[a].sum(axis=0))))
    pooled = evaluate_holdout.pooled_summary(terms, draws=1000, seed=520810, candidate=cand_arm)
    pooled_lr = evaluate_holdout.pooled_summary(terms_lr, draws=1000, seed=520810, candidate=cand_arm)
    for a_ in arms:  # persist OOF surfaces for audit / candidate rebuilds
        np.save(args.cache / f"oof_{a_}.npy", oof_surface[a_])
    for a, s in pooled["scores"].items():
        print(f"  POOLED {a:18s} {s['dti']:.6f} CI[{s['ci95'][0]:.6f},{s['ci95'][1]:.6f}] N={s['withheld_positive_pixels']}", flush=True)
    print(f"[cbs] best_exp={best} cand_arm={cand_arm}; low-relief cand={pooled_lr['scores'][cand_arm]['dti']:.6f} N={pooled_lr['scores'][cand_arm]['withheld_positive_pixels']}", flush=True)

    # ---- budget sweep on winning OOF surface (same folds/evaluator) ----
    sweep = {}
    gate = (lambda e: e & cover_gate) if cand_arm == "exp2_cbs_cover" else (lambda e: e)
    for factor in (0.5, 0.75, 1.0, 1.33, 1.66):
        tm_sum, tot_dots = None, 0
        for f in folds:
            dvis = ndi.distance_transform_edt(~(f["visible"] & fp))
            elig = gate(fp & f["region"] & (dvis > 3.0))
            base = fp & f["region"] & (dvis > 3.0)
            b = int(round(0.0082 * factor * float(base.sum())))
            dots = dotted(oof_surface[cand_arm], elig, b)
            tot_dots += int(dots.sum())
            _, tm = evaluate_holdout.evaluate(dots.astype(np.float32), f, fp, block_side=200)
            tm_sum = tm if tm_sum is None else tm_sum + tm
        sweep[str(factor)] = {"holdout_dti": float(evaluate_holdout.from_terms(tm_sum.sum(axis=0))),
                              "total_dots_across_folds": tot_dots}
        print(f"  sweep x{factor}: DTI={sweep[str(factor)]['holdout_dti']:.6f} dots={tot_dots}", flush=True)
    best_factor = max(sweep, key=lambda k: sweep[k]["holdout_dti"])

    # ---- final candidate from cross-fitted OOF surface ----
    dcat = ndi.distance_transform_edt(~cat)
    elig_full = gate(fp & (dcat > 3.0))
    full_base = fp & (dcat > 3.0)
    final_budget = int(round(0.0082 * float(best_factor) * float(full_base.sum())))
    cand_dots = dotted(oof_surface[cand_arm], elig_full, final_budget)
    cand = cand_dots.astype(np.float32)
    print(f"[cbs] final dots={cand_dots.sum()} budget={final_budget} factor={best_factor}", flush=True)

    # ---- uniqueness vs nine focus champions + sibling lanes + literal witnesses ----
    cfg = json.loads((ROOT / "config/registry_inputs.json").read_text())
    reg_rows = []
    def compare(name, path, category):
        with rasterio.open(path) as ds:
            a = ds.read(1)
        ref_dots = np.isfinite(a) & (a > 0) & fp
        d = ndi.distance_transform_edt(~ref_dots)
        cov_frac = float(((d <= 3.0) & fp).sum()) / float(fp.sum())
        ov = float((d[cand_dots] <= 3.0).mean())
        ref_in = np.where(fp, np.nan_to_num(a, nan=0.0), 0.0).astype(np.float32)
        rho = spearman_footprint(np.where(fp, oof_surface[cand_arm], 0.0), ref_in, fp)
        reg_rows.append({"id": name, "category": category, "sha256": sha256(Path(path)),
                         "ref_dots": int(ref_dots.sum()), "coverage3px_of_footprint": cov_frac,
                         "candidate_overlap_3px": ov, "enrichment_over_coverage": ov / max(cov_frac, 1e-9),
                         "surface_spearman": rho, "exact_shared_dots": int((cand_dots & ref_dots).sum()),
                         "literal_duplicate_flag": bool(ov > 0.70 or abs(rho) > 0.90)})
        print(f"  vs {name:28s} overlap={ov:.4f} rho={rho:+.4f} coverage={cov_frac:.4f}", flush=True)
    for r in cfg["inputs"][:9]:
        compare(r["id"], args.focus_dir / f"{r['id']}.tif", "focus_champion")
    for nm, pth in [("DZ16", "docs/downloads/wbg2-dz16-n34500-20261027T000000Z-8e4646cf-zeros.tif"),
                    ("H3PACK", "docs/downloads/h3-pack/wbg3-h3pack-34k-20261027T174337Z-zeros.tif"),
                    ("MSPTCD_E3", "docs/downloads/msptcd/wbg2-msptcd-e3-25594dots-20261027T173000Z-2642eedd-zeros.tif"),
                    ("STEPXASYM", "docs/downloads/wbg2-h1-stepxasym-e2-34564dots-20261026T221541Z-efd46877-zeros.tif")]:
        compare(nm, ROOT / pth, "sibling_lane")
    for r in cfg["inputs"][9:]:
        p = args.focus_dir / f"{r['id']}.tif"
        if p.is_file():
            compare(r["id"], p, "literal_witness")

    disc = [r for r in reg_rows if r["category"] in ("focus_champion", "sibling_lane")]
    unique_disc = all(not r["literal_duplicate_flag"] for r in disc)
    ctrl_dti = pooled["scores"]["ctrl_19b_dotted"]["dti"]
    best_dti = pooled["scores"][cand_arm]["dti"]
    if cand_arm == "ctrl_19b_dotted":
        delta = pooled["paired_differences"][best]  # control vs best CBS arm
        beats_ctrl = bool(delta["ci95"][0] > 0)     # control beats best experiment
    else:
        delta = pooled["paired_differences"]["ctrl_19b_dotted"]
        beats_ctrl = bool(delta["ci95"][0] > 0)
    beats_repo_best = bool(best_dti > 0.04255426811430257)
    promote = bool(beats_ctrl and beats_repo_best and unique_disc)

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    h8 = hashlib.sha256(cand.tobytes()).hexdigest()[:8]
    stem = f"wbg2-cbs-{cand_arm}-{int(cand_dots.sum())}dots-{stamp}-{h8}-zeros".replace("_", "-")
    out_dir = ROOT / "docs/downloads/cbs"; out_dir.mkdir(parents=True, exist_ok=True)
    out_tif = out_dir / f"{stem}.tif"
    for ext in (".tif", ".zip", ".json"):
        out_tif.with_suffix(ext).unlink(missing_ok=True)
    note = f"CBS covered-basement-step {int(cand_dots.sum())} dots collar-free zeros; {'PROMOTE' if promote else 'DO NOT SUBMIT'} (wbggemsdoe2)"
    assert len(note) <= 140, note
    receipt = submission_writer.write_submission(out_tif, cand, sample_path, fp, note=note,
                    name=stem, catalogue=cat,
                    metadata={"campaign": "WBG2-CBS-20261027", "winning_arm": cand_arm, "winning_cbs_experiment": best,
               "cbs_hypothesis_verdict": ("supported" if cand_arm != "ctrl_19b_dotted" else "negative: control arm won"),
                              "promote_by_this_campaign": promote, "ok_to_submit": promote})
    insp = inspect_tif(out_tif, sample_path, strict_all_finite=True)
    assert insp["format_valid_against_reference"], insp

    results = {"schema": "wbggems.cbs-campaign.v1",
               "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
               "runtime_seconds": time.perf_counter() - t0,
               "budget_compliance": {"experiments_run": 3, "max_experiments": 3, "weekly_slots_used": 0},
               "inputs": {"training_features_mirror_sha256": sha256(feats_path),
                          "existing_faults_mirror_sha256": sha256(args.mirror / "existing_faults_mirror.tif"),
                          "reference_grid_mirror_sha256": sha256(sample_path),
                          "provenance_caveat": "Public owner mirrors, hash-pinned, NOT authenticated DrivenData downloads."},
               "canary_summary": {k: canary[k] for k in ("features_tested", "folds_tested", "all_passed", "max_two_sided_auc", "max_two_sided_feature")},
               "holdout_pooled": pooled, "holdout_low_relief_stratum": pooled_lr,
               "low_relief_definition": {"slope_threshold_median_at_catalogue": low_relief_thr,
                                         "slope_gate_q70_footprint": slope_gate_q70},
               "per_fold": per_fold, "winning_arm": cand_arm, "winning_cbs_experiment": best,
               "cbs_hypothesis_verdict": ("supported" if cand_arm != "ctrl_19b_dotted" else "negative: control arm won"),
               "budget_sweep_best_arm": sweep, "best_budget_factor": float(best_factor),
               "gates": {"beats_ctrl_paired_ci_gt0": beats_ctrl,
                         "beats_repo_best_same_evaluator_0.042554": beats_repo_best,
                         "unique_vs_9focus_and_siblings": unique_disc, "promote": promote},
               "registry_comparison": reg_rows,
               "artifact": {"stem": stem, "tif_path": str(out_tif.relative_to(ROOT)),
                            "sha256": receipt["sha256"], "dots": int(cand_dots.sum()),
                            "final_budget": final_budget, "note": note, "validator": insp}}
    (ROOT / "evidence/cbs_results.json").write_text(json.dumps(results, indent=2, allow_nan=False) + "\n")
    (ROOT / "evidence/cbs_canaries.json").write_text(json.dumps(canary, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"best": cand_arm, "best_cbs_exp": best, "best_dti": best_dti, "ctrl_dti": ctrl_dti, "promote": promote,
                      "artifact": results["artifact"]["tif_path"], "sha256": receipt["sha256"]}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
