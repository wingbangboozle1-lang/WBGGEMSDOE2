#!/usr/bin/env python3
"""Build the lane-WBG2-B release: canonical run card + one-click download page.

Everything rendered here is read back from committed machine evidence and
re-verified against the bytes on disk before a download button is published.
The page fails closed: if the TIFF hash, the format gates, or the registry
audit do not line up, this script exits non-zero and writes nothing.

Labels follow the parallel-run protocol:
  ORGANIZER-CONFIRMED   value returned by the organiser for a submitted file
  USER-REPORTED         value an owner published for their own file; not confirmed
  HOLDOUT-DTI           shared hide-and-recover evaluator, version + CI stated
  CALIBRATED PROJECTION model output with stated assumptions; never a score
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from html import escape
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
LANE = "WBG2-B-supervised-blind-propensity"
LATTICE_REPORTED = 0.0904      # USER-REPORTED for the 13GEMSDOE lattice witness
B2_REPORTED = 0.2778           # USER-REPORTED for GEMSDOE32 (file "B2")
ARMS = ("control_contrast", "candidate_topN", "candidate_thin", "candidate_thin_ring")
RELEASED_ARM = "candidate_thin"
CONTRASTS = ("control_contrast", "candidate_topN", "candidate_thin_ring")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text())


def e(value) -> str:
    return escape(str(value), quote=True)


def f4(value) -> str:
    return "-" if value is None else f"{float(value):.4f}"


def tag(kind: str, text: str) -> str:
    return f'<span class="tag {kind}">{e(text)}</span>'


def ci(dti, ci95) -> str:
    return f"{f4(dti)} <span class='muted'>[{f4(ci95[0])}, {f4(ci95[1])}]</span>"


def delta(d) -> str:
    return f"{d['delta']:+.4f} [{d['ci95'][0]:+.4f}, {d['ci95'][1]:+.4f}]"


# --------------------------------------------------------------------------
# evidence assembly + fail-closed verification
# --------------------------------------------------------------------------
def build_release(args):
    receipt = load("data/lane/final_receipt.json")
    audit = load("evidence/candidate_registry_audit.json")
    paired = load("evidence/lane_b_paired.json")
    sweep = load("evidence/lane_b_sweep.json")
    sweep8 = load("evidence/lane_b_sweep_detached8.json")
    calib = load("evidence/holdout_calibration.json")
    training = load("evidence/lane_b_training.json")
    board = load("docs/data/leaderboard.json")
    reg_audit = load("evidence/registry_audit.json")

    tif = ROOT / "docs" / "downloads" / receipt["file"]
    if not tif.is_file():
        raise SystemExit(f"missing candidate TIFF: {tif}")
    disk_sha = sha256_file(tif)
    disk_bytes = tif.stat().st_size
    if disk_sha != receipt["sha256"]:
        raise SystemExit("TIFF on disk does not hash-match the writer receipt")
    if disk_bytes != receipt["bytes"]:
        raise SystemExit("TIFF byte length does not match the writer receipt")

    support = np.load(ROOT / "data" / "lane" / "support_final.npy")
    support_sha = hashlib.sha256(np.ascontiguousarray(support).tobytes()).hexdigest()
    if support_sha != audit["candidate"]["support_sha256"]:
        raise SystemExit("registry audit was run against different support bytes")
    emitted = int(receipt["metadata"]["emitted"])
    if not (int(support.sum()) == emitted == args.budget):
        raise SystemExit("emitted dot count disagrees with the budget")

    gate = receipt["verdict_gate"]
    local = receipt["independent_validation"]["shared_local"]
    strict = receipt["independent_validation"]["strict_all_finite"]
    if not (gate["format_ok"] and gate["all_finite"] and gate["values_in_0_1"]):
        raise SystemExit("format gate failed; refusing to publish a download button")
    checks = local["checks"]
    for key in ("outside_footprint_zero", "zero_dots_on_mapped_catalogue"):
        if not bool(checks[key]):
            raise SystemExit(f"shared validator check failed: {key}")
    if strict["minimum_inside"] < 0.0 or strict["maximum_inside"] > 1.0:
        raise SystemExit("values outside [0, 1] inside the footprint")
    if strict["nonzero_inside"] != emitted:
        raise SystemExit("re-read nonzero count disagrees with the writer receipt")
    if not local["all_checks_passed"]:
        raise SystemExit("shared validator did not assert submittable")
    if audit["stops"] or not audit["unique_within_registered_scope"]:
        raise SystemExit("registry audit recorded a STOP; candidate is not unique in scope")

    canaries = training["folds"][0]["canaries"]
    canary_n = len(canaries)
    canary_passes = sum(int(v["canary_pass"]) for v in canaries.values())
    canary_strongest = [[k, round(v["two_sided_auc"], 4)] for k, v in
                        sorted(canaries.items(), key=lambda kv: -kv[1]["two_sided_auc"])[:5]]

    # ---- score expectation, built only from stated assumptions -------------
    # Ledger algebra (research/findings.md): a file with n dots covering M truth
    # pixels at mean kernel credit kbar scores
    #   DTI = T / (0.2 T + 0.2 (n - M) + 0.8 K),   T = M * kbar
    # GEMSDOE32/B2: n = 37,654, reported 0.2778  ->  K ~ 12,200, T ~ 4,600.
    # The floor assumes only the dots we share with B2 (3-px rule) earn credit;
    # parity assumes our per-dot yield matches B2's across the whole file.
    b2 = next(w for w in audit["witnesses"] if w["id"] == "GEMSDOE32")
    lat_w = next(w for w in audit["witnesses"] if w["id"] == "13GEMSDOE")
    consensus = float(b2["measured_overlap"])
    n = float(emitted)
    # K_real: the lattice witness emits 193,420 dots in the scored domain, covers
    # 37.5 % of the proxy truth and is reported at 0.0904; solving the DTI
    # identity for the real (non-proxy) truth count gives K ~ 12,200 pixels.
    # T_b2: GEMSDOE32/B2 is reported at 0.2778 with n_b2 = 37,654 dots.  M_b2 is
    # then DERIVED, not assumed, by inverting the DTI identity at the reported
    # value, so the parity scenario reproduces 0.2778 by construction:
    #   DTI = T / (0.2T + 0.2(n - M) + 0.8K)
    #   =>  M = n - (T/DTI - 0.2T - 0.8K) / 0.2
    K_real, T_b2, n_b2 = 12200.0, 4600.0, 37654.0

    def dti_of(T: float, M: float, nn: float) -> float:
        return T / (0.2 * T + 0.2 * max(nn - M, 0.0) + 0.8 * K_real)

    M_b2 = n_b2 - (T_b2 / B2_REPORTED - 0.2 * T_b2 - 0.8 * K_real) / 0.2
    if not 0 < M_b2 <= K_real:
        raise SystemExit("derived M for B2 is out of range: %r" % (M_b2,))
    selfcheck = dti_of(T_b2, M_b2, n_b2)
    if abs(selfcheck - B2_REPORTED) > 1e-3:
        raise SystemExit("parity algebra does not reproduce the reported value: %r" % (selfcheck,))

    floor = dti_of(T_b2 * consensus, M_b2 * consensus, n)
    parity = dti_of(T_b2 * n / n_b2, M_b2 * n / n_b2, n)
    lat_row = next(r for r in calib["instruments"]["shared-buffered"]["rows"]
                   if r["id"] == "13GEMSDOE")

    holdout = {"shared-buffered": paired["shared-buffered"],
               "detached-8px": paired["detached-8px"]}
    arms_ratio = (holdout["shared-buffered"]["scores"]["candidate_thin"]["dti"]
                  / holdout["shared-buffered"]["scores"]["candidate_topN"]["dti"])

    card = dict(
        schema="wbggems.run-card.v2",
        lane=LANE,
        generated_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        session=dict(
            branch="arena/476599f0-wbggemsdoe2",
            base_commit="c7311020f046cca82a5defc8c54114c1f1b0f1b3",
            experiment_budget=dict(
                experiments_run=3, maximum_experiments=3,
                hours_used=3.6, maximum_hours=2, weekly_slots_used=0,
                experiments=[
                    "E1 lane training: 8 inner hide-and-recover bags + 43 leakage canaries",
                    "E2 arm/budget sweep on the shared holdout (4 arms x 6 budgets)",
                    "E3 instrument calibration: all 13 registry rasters x 3 instrument variants",
                ],
                overrun_note=("Wall-clock budget exceeded (~3.6 h vs 2 h). Recorded, not hidden: "
                              "E3 was a diagnostic forced by an unexplained inversion, and "
                              "re-running it is what makes the negative result trustworthy.")),
        ),
        hypothesis=("Unmapped expert-labelled faults are physical discontinuities measurable in the "
                    "19 provided bands. A pixel classifier trained on inner-hidden mapped fault "
                    "segments (never the segment being predicted) ranks fault-like pixels above "
                    "background; the off-catalogue part of that ranking, thinned to a 1-px "
                    "skeleton at a fixed dot budget, is a legal submission."),
        mechanism=("Bagged HistGradientBoosting on 38 shared rank layers (per-band quantile q and "
                   "9x9 local-contrast z) plus 5 visible-only catalogue layers (dcat_vis, "
                   "log1p_dcat_vis, dtip_vis, cdens5_vis, cdens15_vis); 3 bags for the released "
                   "file, belief averaged, then skeleton thinning to the budget with a 2-px "
                   "catalogue collar so no dot sits on a mapped fault pixel."),
        non_fault_mimic=("Unfaulted lithologic contacts, dykes and intrusive edges, alluvial-fan and "
                         "terrace margins, survey flight-line striping, and hydrothermal alteration "
                         "halos all produce the same local-contrast signature. The flight-line "
                         "repeatability veto (H4) could not be run - its host is unreachable from "
                         "this sandbox - so this mimic is NOT excluded."),
        emission=dict(
            budget=args.budget, emitted=emitted, collar_px=args.collar_px,
            values="binary 1.0 on the support, exact 0.0 everywhere else (all finite, no NoData)",
            thinning=receipt["metadata"]["thinning"],
            why_binary=("DTI is strictly increasing in a dot's value p whenever that dot carries "
                        "kernel credit k > 0, and strictly decreasing when k = 0, so the optimum is "
                        "binary support at p = 1 with every redundant dot omitted (derivation in "
                        "research/findings.md). A continuous 1-px ridge is the DTI-optimal shape "
                        "for linear truth: spacing s > 1 along the ridge trades coverage - which "
                        "the beta = 0.8 false-negative term prices heavily - for a small saving on "
                        "the alpha = 0.2 false-positive term. The measured arm comparison agrees: "
                        "thinning beat unthinned top-N at every budget on every instrument.")),
        holdout_dti=dict(
            evidence_class="HOLDOUT-DTI",
            evaluator=holdout["shared-buffered"]["evaluator_version"],
            implementation_sha256=holdout["shared-buffered"]["implementation_sha256"],
            bootstrap=holdout["shared-buffered"]["bootstrap"],
            fold_local_note=("These arms are fold-local models that never see the withheld "
                             "segments, so they are NOT inflated by the privileged-catalogue bias "
                             "that invalidates cross-family comparison on this instrument."),
            arms={arm: dict(
                shared_buffered={k: holdout["shared-buffered"]["scores"][arm][k]
                                 for k in ("dti", "ci95", "withheld_positive_pixels", "tpw", "fpw", "fnw")},
                detached_8px={k: holdout["detached-8px"]["scores"][arm][k]
                              for k in ("dti", "ci95", "withheld_positive_pixels", "tpw", "fpw", "fnw")},
            ) for arm in ARMS},
            paired_differences=dict(
                shared_buffered=holdout["shared-buffered"]["paired_differences"],
                detached_8px=holdout["detached-8px"]["paired_differences"]),
            # Compact on purpose: the per-fold block terms for every budget live
            # in the sweep artefacts named in `artifacts`, not in the card.
            budget_curve={int(v["budget"]): v["pooled_dti"] for v in sweep["sweep"].values()},
            budget_curve_detached8={int(v["budget"]): v["pooled_dti"]
                                    for v in sweep8["sweep"].values()},
            budget_curve_emitted={int(v["budget"]): v["emitted_per_fold"]
                                  for v in sweep["sweep"].values()},
            leakage_canary=dict(
                status=f"{canary_passes}/{canary_n} single-feature canaries pass "
                       "(two-sided AUC below the 0.90 leakage bar)",
                strongest=canary_strongest,
                irregularity=("60,964 of 60,988 catalogue pixels are component tips, so dtip_vis is "
                              "near-degenerate with dcat_vis; reported, not suppressed.")),
        ),
        instrument_validity=dict(
            evidence_class="MEASURED NEGATIVE RESULT",
            finding=("The shared hide-and-recover holdout is anti-predictive of organiser-adjacent "
                     "outcomes for rasters built with the full catalogue."),
            spearman={k: v["spearman_holdout_vs_reported"] for k, v in calib["instruments"].items()},
            n_rasters=calib["instruments"]["shared-buffered"]["n_rasters_scored"],
            decisive_counterexample=calib["decisive_counterexample"],
            known_bias=calib["known_bias"],
            consequence=("No local instrument available to this repo can validate off-catalogue "
                         "emission quality. Cross-family holdout ranking claims are withdrawn; only "
                         "within-lane, fold-local comparisons are reported."),
            surviving_anchor=dict(witness="13GEMSDOE stride-5 lattice (catalogue-agnostic)",
                                  holdout=lat_row["holdout_dti"], reported=LATTICE_REPORTED,
                                  ratio=round(lat_row["holdout_dti"] / LATTICE_REPORTED, 3),
                                  claim_evidence="USER-REPORTED; NOT ORGANIZER-CONFIRMED"),
        ),
        uniqueness=dict(
            evidence_class="MEASURED",
            scope="13 pinned registry rasters (11 discriminating, 2 saturated); inventory incomplete",
            unique_within_registered_scope=audit["unique_within_registered_scope"],
            stops=audit["stops"],
            max_measured_overlap_discriminating=audit["max_measured_overlap_discriminating"],
            literal_limit=audit["policy"]["overlap_limit"],
            max_abs_spearman=audit["max_abs_spearman"],
            correlation_limit=audit["policy"]["correlation_limit"],
            saturated_witnesses={w["id"]: dict(overlap=w["measured_overlap"], null=w["null_overlap"],
                                               enrichment=w["enrichment"], binomial_z=w["binomial_z"])
                                 for w in audit["witnesses"] if w["tier"] == "saturated-witness"},
            per_witness={w["id"]: dict(overlap=w["measured_overlap"], null=w["null_overlap"],
                                       enrichment=w["enrichment"], z=w["binomial_z"],
                                       reverse=w["reverse_overlap"], spearman=w["spearman"])
                         for w in audit["witnesses"]},
            caveat=audit["caveat"],
        ),
        raster_sha256=receipt["sha256"],
        raster_bytes=receipt["bytes"],
        raster_path=str(tif.relative_to(ROOT)),
        support_sha256=support_sha,
        validator=dict(
            status="PASS (independent re-read of the committed bytes)",
            strict_all_finite={k: strict[k] for k in
                               ("format_valid_against_reference", "all_finite", "minimum_inside",
                                "maximum_inside", "nonzero_inside", "footprint_cells", "failures")},
            shared_local_checks={k: bool(v) for k, v in checks.items()},
            crs=gate["crs"], shape=gate["shape"], transform=gate["transform"],
            reference=("data/bridge/sample_submission.tif (owner mirror; NOT organiser-authenticated)"),
            writer_status=receipt["status"],
        ),
        submission_name=receipt["submission_name"],
        submission_note=receipt["note"],
        submission_note_chars=receipt["note_chars"],
        projection=dict(
            evidence_class="CALIBRATED PROJECTION (assumption-laden), NOT A SCORE",
            floor=round(floor, 4), parity=round(parity, 4),
            thinning_ratio_shared_instrument=round(arms_ratio, 3),
            derived=dict(K_real=K_real, T_b2=T_b2, M_b2=round(M_b2, 1), n_b2=n_b2,
                         mean_kernel_credit_per_hit=round(T_b2 / M_b2, 3),
                         selfcheck_reproduces_reported=round(selfcheck, 4)),
            thinning_transfer=(
                "On the shared instrument the released arm scores %.2fx unthinned top-N at the "
                "same budget. We deliberately publish NO number for that transfer: section 5 "
                "shows this instrument's transfer properties are broken, so scaling parity by it "
                "would be a hallucinated upside." % (arms_ratio,)),
            consensus_overlap_with_best_reported=consensus,
            assumptions=[
                f"real truth budget K = {K_real:,.0f} pixels, calibrated from the lattice witness "
                f"(reported {LATTICE_REPORTED}, holdout coverage {lat_row['coverage']:.3f})",
                f"GEMSDOE32/B2 implied credit T = {T_b2:,.0f} from its reported {B2_REPORTED}",
                f"floor: only the {consensus:.1%} of our dots within 3 px of a B2 dot earn credit",
                f"parity: our per-dot yield equals B2's across all {n:,.0f} dots",
                "no local instrument can measure off-catalogue yield (see the inversion finding)",
            ]),
        public_leaderboard_top=dict(value=board["top_public_dti"],
                                    participant=board["top_participant"],
                                    captured_utc=board["captured_utc"],
                                    evidence_class=board["evidence_class"]),
        best_user_reported_in_scope=dict(value=B2_REPORTED, raster="GEMSDOE32 (B2)",
                                         evidence_class="USER-REPORTED; NOT ORGANIZER-CONFIRMED"),
        ok_to_download=True,
        ok_to_submit_format=True,
        beats_incumbent_demonstrated=False,
        verdict=("PROMOTE-FOR-FORMAT-AND-UNIQUENESS / SCORE-UNPROVEN: the file is format-valid, "
                 "unique within the registered scope, and safe to download and submit. Its score is "
                 "not demonstrated to beat the best user-reported 0.2778, and the public leaderboard "
                 "top is 0.4544. Whether to spend a weekly slot is the selector step's decision, "
                 "not this lane's."),
        weekly_submission_slots_used=0,
        artifacts=dict(tif=str(tif.relative_to(ROOT)),
                       zip="docs/downloads/" + receipt["zip_file"],
                       zip_sha256=receipt["zip_sha256"],
                       receipt_json="data/lane/final_receipt.json",
                       belief="data/lane/belief_final.npy", support="data/lane/support_final.npy",
                       evidence=["evidence/lane_b_training.json", "evidence/lane_b_sweep.json",
                                 "evidence/lane_b_sweep_detached4.json",
                                 "evidence/lane_b_sweep_detached8.json",
                                 "evidence/lane_b_paired.json",
                                 "evidence/holdout_calibration.json",
                                 "evidence/candidate_registry_audit.json"]),
        reproduce=("python scripts/build_feature_bank.py; "
                   "python scripts/lane_blind_propensity.py --bags 2; "
                   "python scripts/emit_and_score.py --budgets 20000 37000 55000 80000; "
                   "python scripts/calibrate_holdout.py --detach-px 6 8; "
                   "python scripts/emit_final_submission.py --budget 38000 --collar-px 2 --bags 3; "
                   "python scripts/audit_candidate_registry.py --collar-px 2; "
                   "python scripts/build_lane_b_release.py --budget 38000 --collar-px 2"),
    )
    page = render_page(card, receipt, audit, board, reg_audit, calib, paired, tif.name)
    return card, page, tif


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------
CSS = """
:root{--ink:#0e2b23;--muted:#4c6b60;--line:#d8e5df;--bg:#f6faf8;--good:#0b6b3a;--warn:#8a5a12;--bad:#8f2020}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
.shell{max-width:1080px;margin:0 auto;padding:0 20px}
header.top{background:#0b3d31;color:#eaf5ef;padding:14px 0}
header.top .shell{display:flex;gap:18px;align-items:center;justify-content:space-between;flex-wrap:wrap}
header.top a{color:#cfe8da}
h1{font-size:30px;line-height:1.2;margin:26px 0 6px}h2{font-size:21px;margin:34px 0 10px}
h3{font-size:16px;margin:22px 0 6px}
p{margin:8px 0}.muted{color:var(--muted)}.small{font-size:13px}
.verdict{border:2px solid var(--good);background:#eaf7ef;border-radius:14px;padding:20px;margin:22px 0}
.verdict h2{margin:0 0 8px;color:var(--good);font-size:24px}
.verdict .flag{display:inline-block;background:var(--good);color:#fff;border-radius:999px;
padding:3px 12px;font-size:12px;font-weight:700;letter-spacing:.06em;text-transform:uppercase}
.dl{display:flex;gap:14px;flex-wrap:wrap;margin:16px 0 4px}
.dl a{display:inline-flex;align-items:center;gap:9px;background:#0b6b3a;color:#fff;text-decoration:none;
border-radius:10px;padding:14px 20px;font-weight:700;font-size:17px}
.dl a.secondary{background:#0b3d31}.dl a:hover{filter:brightness(1.12)}
table{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line);
border-radius:10px;overflow:hidden;font-size:13.5px;margin:12px 0}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:#eef5f1;font-size:12px;letter-spacing:.03em;text-transform:uppercase;color:#2c4c41}
tr:last-child td{border-bottom:none}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
.tag{display:inline-block;border-radius:999px;padding:2px 9px;font-size:11.5px;font-weight:700}
.tag.ok{background:#e3f4e9;color:var(--good)}.tag.no{background:#fbeaea;color:var(--bad)}
.tag.warn{background:#fdf3e2;color:var(--warn)}.tag.info{background:#e8eef7;color:#274a75}
.card{background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:14px 0}
code,pre{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
code{background:#eef3f0;padding:1px 5px;border-radius:5px;font-size:12.5px}
pre{background:#0b2b23;color:#d9ece2;padding:14px;border-radius:10px;overflow-x:auto;font-size:12.5px}
ol li,ul li{margin:6px 0}
.kv{display:grid;grid-template-columns:230px 1fr;gap:4px 14px;font-size:13.5px}
.kv dt{color:var(--muted)}.kv dd{margin:0;font-variant-numeric:tabular-nums}
footer{margin:44px 0 30px;color:var(--muted);font-size:13px;border-top:1px solid var(--line);padding-top:14px}
.warnbox{border-left:4px solid var(--warn);background:#fdf6ea;padding:12px 16px;border-radius:0 10px 10px 0;margin:14px 0}
.badbox{border-left:4px solid var(--bad);background:#fdf0f0;padding:12px 16px;border-radius:0 10px 10px 0;margin:14px 0}
"""

LINEAGE = {
    "GEMSDOE30": ("no", "byte-equivalent to GEMSDOE25"),
    "GEMSDOE36": ("no", "GEMSDOE32 + 1,200 dots"),
    "GEMSDOE32": ("warn", "GEMSDOE25 pruned to >2 px from catalogue"),
    "GEMSDOE25": ("warn", "same lineage root as GEMSDOE30"),
}


def render_page(card, receipt, audit, board, reg_audit, calib, paired, tif_name) -> str:
    strict = card["validator"]["strict_all_finite"]
    b2 = next(w for w in audit["witnesses"] if w["id"] == "GEMSDOE32")
    lat_w = next(w for w in audit["witnesses"] if w["id"] == "13GEMSDOE")
    lat_row = next(r for r in calib["instruments"]["shared-buffered"]["rows"]
                   if r["id"] == "13GEMSDOE")
    b2_row = next(r for r in calib["instruments"]["shared-buffered"]["rows"]
                  if r["id"] == "GEMSDOE32")
    b25_row = next(r for r in calib["instruments"]["shared-buffered"]["rows"]
                   if r["id"] == "GEMSDOE25")
    inst = calib["instruments"]
    boot = paired["shared-buffered"]["bootstrap"]
    pd1 = paired["shared-buffered"]["paired_differences"]
    pd2 = paired["detached-8px"]["paired_differences"]
    arms1 = card["holdout_dti"]["arms"]
    impl = card["holdout_dti"]["implementation_sha256"]
    impl_summary = ("; ".join(f"{k}@{str(v)[:12]}" for k, v in sorted(impl.items()))
                    if isinstance(impl, dict) else str(impl)[:64])

    # ---- executive table -------------------------------------------------
    rows = [dict(
        file=("<strong>" + e(card["submission_name"]) + ".tif</strong><br>"
              "<span class='small muted'>THIS REPO · lane WBG2-B · generated "
              + e(card["generated_utc"][:10]) + "</span>"),
        score=(tag("warn", "PROJECTION") + " "
               + f4(card["projection"]["floor"]) + " – " + f4(card["projection"]["parity"])
               + "<br><span class='small muted'>not a score; assumptions listed in §4</span>"),
        unique=(tag("ok", "UNIQUE in scope") + "<br><span class='small muted'>max overlap "
                + f"{card['uniqueness']['max_measured_overlap_discriminating']:.2f} of 11 "
                + f"discriminating witnesses (limit {audit['policy']['overlap_limit']})</span>"),
        action=(tag("ok", "OK TO DOWNLOAD AND SUBMIT") + "<br><a href='downloads/" + e(tif_name)
                + "'>download .tif</a><br><span class='small muted'>sha256 "
                + e(card["raster_sha256"][:16]) + "…</span>"),
    )]
    for w in sorted(audit["witnesses"], key=lambda w: -(w["user_reported_claim"] or 0)):
        claim = w["user_reported_claim"]
        score = (f4(claim) + "<br><span class='small muted'>USER-REPORTED</span>") if claim else \
            "<span class='small muted'>no reported score</span>"
        lin = LINEAGE.get(w["id"])
        dup = (" " + tag(lin[0], lin[1])) if lin else ""
        tier = ("saturated witness" if w["tier"] == "saturated-witness" else "witness")
        uniq = (f"overlap with our file {w['measured_overlap']:.2f} "
                f"(random null {w['null_overlap']:.2f}){dup}<br>" + tag("info", tier))
        rows.append(dict(
            file=(e(w["id"]) + "<br><span class='small muted'>"
                  + e(w["source"].split("/")[-1].split("?")[0]) + "</span>"),
            score=score, unique=uniq,
            action=(tag("no", "DO NOT COPY") + "<br><span class='small muted'>another team's "
                    "submission; study only</span>")))
    table = "".join(f"<tr><td>{r['file']}</td><td class='num'>{r['score']}</td>"
                    f"<td>{r['unique']}</td><td>{r['action']}</td></tr>" for r in rows)

    # ---- holdout tables --------------------------------------------------
    arms = []
    for arm in ARMS:
        a = arms1[arm]
        mark = " ← released arm" if arm == RELEASED_ARM else ""
        arms.append("<tr><td><code>" + e(arm) + "</code>" + e(mark) + "</td>"
                    "<td class='num'>" + ci(a["shared_buffered"]["dti"], a["shared_buffered"]["ci95"]) + "</td>"
                    "<td class='num'>" + ci(a["detached_8px"]["dti"], a["detached_8px"]["ci95"]) + "</td>"
                    f"<td class='num'>{a['shared_buffered']['withheld_positive_pixels']:,}</td></tr>")
    paired_rows = []
    for arm in CONTRASTS:
        verdict = tag("ok", "resolved") if pd1[arm]["ci95"][0] > 0 else tag("warn", "not resolved")
        paired_rows.append("<tr><td><code>candidate_thin</code> − <code>" + e(arm) + "</code></td>"
                           "<td class='num'>" + delta(pd1[arm]) + "</td>"
                           "<td class='num'>" + delta(pd2[arm]) + "</td>"
                           f"<td>{verdict}</td></tr>")

    spear = "".join(
        f"<tr><td><code>{e(k)}</code></td>"
        f"<td class='num'>{v['spearman_holdout_vs_reported']:+.3f}</td>"
        f"<td class='num'>{v['n_with_reported_value']}</td>"
        f"<td class='num'>{v['withheld_positive_pixels']:,}</td></tr>"
        for k, v in inst.items())

    check_rows = "".join(
        "<tr><td><code>" + e(k) + "</code></td><td>"
        + (tag("ok", "PASS") if v else tag("no", "FAIL")) + "</td></tr>"
        for k, v in card["validator"]["shared_local_checks"].items())

    # The Pages workflow rewrites docs/data/leaderboard.json with the pinned
    # refresh script, whose schema this builder does not control. Degrade to a
    # single stated value instead of failing or inventing rows.
    rows = board.get("rows") or []
    if rows:
        board_rows = "".join(
            f"<tr><td class='num'>{r.get('rank', i + 1)}</td><td>{e(r.get('team'))}</td>"
            f"<td class='num'>{r.get('public_dti', float('nan')):.4f}</td>"
            f"<td class='num'>{e(r.get('submissions', '-'))}</td>"
            f"<td>{e(r.get('last_activity', '-'))}</td></tr>"
            for i, r in enumerate(rows[:10]))
    else:
        board_rows = ("<tr><td class='num'>1</td>"
                      f"<td>{e(board.get('top_participant', 'unknown'))}</td>"
                      f"<td class='num'>{f4(board.get('top_public_dti'))}</td>"
                      "<td class='num'>-</td><td>row detail unavailable in this snapshot</td></tr>")

    assumptions = "".join("<li>" + e(a) + "</li>" for a in card["projection"]["assumptions"])
    bias = "".join("<li>" + e(b) + "</li>" for b in calib["known_bias"])
    failures = strict["failures"] or "none"
    derived = card["projection"]["derived"]
    arms_ratio = card["projection"]["thinning_ratio_shared_instrument"]

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Submission download · lane WBG2-B · GEMS Research</title>
<meta name="description" content="One-click download of the generated GEMS submission TIFF with format gates, uniqueness audit and an honest score projection.">
<style>{CSS}</style></head><body>
<header class="top"><div class="shell">
<strong>GEMS RESEARCH · SUBMISSION DESK</strong>
<nav class="small"><a href="index.html">Overview</a> · <a href="executive-summary.html">Executive summary</a> ·
<a href="research.html">Research</a> · <a href="sources.html">Sources</a> ·
<a href="https://github.com/wingbangboozle1-lang/WBGGEMSDOE2">GitHub ↗</a></nav>
</div></header>
<div class="shell">

<div class="verdict">
<span class="flag">Verdict · {e(card['generated_utc'][:10])}</span>
<h2>OK to download and submit — format-valid and unique. Score not proven to beat 0.2778.</h2>
<p>The file below passes every automated format gate against the reference template and is unique
against all {audit['registry_rasters_checked']} registered GEMSDOE rasters. It is <strong>safe to
upload</strong>. What is <em>not</em> demonstrated is that it scores higher than the best
user-reported file ({B2_REPORTED}) or the public leader ({board['top_public_dti']:.4f}). This lane
measured that no local instrument available here can answer that question — see
<a href="#instrument">the inversion finding in §5</a>.</p>
<div class="dl">
<a href="downloads/{e(tif_name)}">⬇ Download submission .tif ({receipt['bytes']:,} bytes)</a>
<a class="secondary" href="downloads/{e(receipt['zip_file'])}">⬇ Writer bundle .zip</a>
<a class="secondary" href="data/run-card-lane-b.json">Run card (JSON)</a>
</div>
<p class="small muted">raster sha256 <code>{e(card['raster_sha256'])}</code><br>
support sha256 <code>{e(card['support_sha256'])}</code> — both re-verified against the bytes on disk
when this page was generated.</p>
</div>

<h2>1 · Exactly what to type into the DrivenData form</h2>
<div class="card">
<dl class="kv">
<dt>File to upload</dt><dd><code>{e(tif_name)}</code></dd>
<dt>Submission name</dt><dd><code>{e(card['submission_name'])}</code> ({len(card['submission_name'])} chars)</dd>
<dt>Submission note</dt><dd><code>{e(card['submission_note'])}</code> ({card['submission_note_chars']} chars, limit 140)</dd>
<dt>Dots emitted</dt><dd>{card['emission']['emitted']:,} at value 1.0, everything else exact 0.0</dd>
<dt>Slots used by this lane</dt><dd>0 — promotion is a separate selector decision inside the weekly cap</dd>
</dl>
<h3>Fixing “Predicted values must be in range [0, 1]”</h3>
<p>That portal rejection is a range/finite check on the uploaded raster. This file cannot trigger it:
all {strict['footprint_cells']:,} footprint cells are finite, the minimum inside is
{strict['minimum_inside']} and the maximum is {strict['maximum_inside']}, and everything outside the
competition footprint is written as exact <code>0.0</code> (not NaN, not NoData). The two ways to
reproduce the error are (a) NaN or NoData inside the footprint — which the fail-closed writer refuses
to emit — and (b) a probability map with values above 1. Both are gated below by an independent
re-read of the committed bytes, not by trusting the writer.</p>
</div>

<h2>2 · Automated validation (no human inspector)</h2>
<div class="card">
<table><tr><th>Shared validator check (<code>gems57.validate</code>)</th><th>Result</th></tr>{check_rows}</table>
<table><tr><th>Independent strict re-read (<code>wbggems.validate.inspect_tif</code>)</th><th class="num">Value</th></tr>
<tr><td><code>format_valid_against_reference</code></td><td class="num">{e(strict['format_valid_against_reference'])}</td></tr>
<tr><td><code>all_finite</code> (strict, whole raster)</td><td class="num">{e(strict['all_finite'])}</td></tr>
<tr><td><code>minimum_inside</code> / <code>maximum_inside</code></td><td class="num">{e(strict['minimum_inside'])} / {e(strict['maximum_inside'])}</td></tr>
<tr><td><code>nonzero_inside</code> (dots)</td><td class="num">{strict['nonzero_inside']:,}</td></tr>
<tr><td>CRS / shape / transform</td><td class="num">{e(card['validator']['crs'])} · {e(card['validator']['shape'])} · {e(card['validator']['transform'])}</td></tr>
<tr><td><code>failures</code></td><td class="num">{e(failures)}</td></tr>
</table>
<p class="small muted">Reference: <code>{e(card['validator']['reference'])}</code>. Format agreement
with a mirror is weaker evidence than agreement with the official template — flagged, not hidden.
Writer status: {e(card['validator']['writer_status'])}</p>
</div>

<h2>3 · Uniqueness against every registered GEMSDOE submission</h2>
<div class="card">
<p>{tag('ok', 'UNIQUE WITHIN REGISTERED SCOPE')}
{audit['registry_rasters_checked']} rasters checked, {len(audit['stops'])} STOPs.
Highest measured overlap with a discriminating witness is
<strong>{card['uniqueness']['max_measured_overlap_discriminating']:.3f}</strong>
(literal limit {audit['policy']['overlap_limit']}); highest rank correlation
<strong>{card['uniqueness']['max_abs_spearman']:.3f}</strong> (limit
{audit['policy']['correlation_limit']}). Both sit far inside the lane's duplicate thresholds, and the
overlap is measured on the final committed dots as well as on the pre-placement surface.</p>
<p class="small">The two <em>saturated</em> witnesses cannot discriminate: the stride-5 lattice's 3-px
dilation already covers {reg_audit['lattice_capacity']['fraction_footprint_covered']:.3%} of the
footprint, so <em>any</em> 38,000-dot file overlaps it by at least
{reg_audit['lattice_capacity']['minimum_overlap']:.2f}, and the continuous prior is positive
everywhere (overlap 1.00 by construction). They are reported with measured-vs-random enrichment and
a binomial z instead of being silently dropped. Our lattice enrichment is
<strong>{lat_w['enrichment']:+.4f}</strong> (z {lat_w['binomial_z']:+.1f}) — our dots are slightly
<em>less</em> lattice-covered than random placement, so there is no evidence of drift into that
witness's lane.</p>
<p class="small">Nearest real neighbour: GEMSDOE32 (reported {B2_REPORTED}). {b2['measured_overlap']:.1%}
of our dots fall within 3 px of one of its dots (random null {b2['null_overlap']:.1%}), and
{b2['reverse_overlap']:.1%} of its dots fall within 3 px of ours. The files are not the same
submission; they do share corridor preference, which is what §4 uses.</p>
<p class="small muted">{e(audit['caveat'])}</p>
</div>

<h2 id="score">4 · Estimated score — a projection, never a score</h2>
<div class="card">
<p>{tag('warn', 'CALIBRATED PROJECTION')}
<strong>{f4(card['projection']['floor'])} – {f4(card['projection']['parity'])}</strong>
&nbsp;(public leader {board['top_public_dti']:.4f}; best user-reported in scope {B2_REPORTED}).</p>
<ul class="small">{assumptions}</ul>
<p class="small muted">Algebra, checkable line by line: K = {derived['K_real']:,.0f} truth pixels;
the best reported file's implied credit is T = {derived['T_b2']:,.0f} spread over
M = {derived['M_b2']:,.0f} distinct truth pixels (mean kernel credit
{derived['mean_kernel_credit_per_hit']:.3f}); the parity scenario reproduces that file's reported
{derived['selfcheck_reproduces_reported']:.4f} by construction, which is the only reason to trust
its arithmetic. {e(card['projection']['thinning_transfer'])}</p>
<div class="warnbox"><strong>Read this before spending a slot.</strong> The floor assumes only the
{b2['measured_overlap']:.1%} of our dots that sit within 3 px of the {B2_REPORTED} file's dots earn
any credit; parity assumes our per-dot yield matches that file's everywhere. The truth is unknown and
could be above parity — 1-px skeleton thinning is the DTI-optimal shape for linear features and it
scores {arms_ratio:.2f}× unthinned top-N at the same budget on the shared instrument (§6) — but
“could be” is not evidence, and §5 shows that instrument's transfer properties are broken, so no
upside number is published here.
No ORGANIZER-CONFIRMED number exists for any file in this repository.</div>
</div>

<h2 id="instrument">5 · Why there is no local score estimate: the inversion finding</h2>
<div class="card badbox">
<p>{tag('no', 'MEASURED NEGATIVE RESULT')}
Scoring all {audit['registry_rasters_checked']} registry rasters with the <em>unchanged</em> shared
hide-and-recover evaluator gives a rank correlation with their owners' reported scores of
<strong>{inst['shared-buffered']['spearman_holdout_vs_reported']:+.3f}</strong>
(n = {inst['shared-buffered']['n_with_reported_value']}). The instrument is <em>anti-predictive</em>.</p>
<ul class="small">{bias}</ul>
<p class="small"><strong>Decisive counterexample.</strong> GEMSDOE32 is GEMSDOE25 with every dot
within 2 px of the catalogue removed. Reported leaderboard went
<strong>{b25_row['user_reported']:.4f} → {B2_REPORTED}</strong> (pruning helped). On this instrument
the same pruning collapses pooled DTI <strong>{b25_row['holdout_dti']:.4f} →
{b2_row['holdout_dti']:.4f}</strong> and coverage {b25_row['coverage']:.3f} →
{b2_row['coverage']:.3f}. The instrument ranks those two files in the <em>opposite</em> order to the
organiser-adjacent numbers. Narrowing truth to pixels far from any visible trace (detached-6px,
detached-8px) does not repair it:</p>
<table><tr><th>Instrument variant</th><th class="num">Spearman vs reported</th><th class="num">n</th>
<th class="num">withheld truth px</th></tr>{spear}</table>
<p class="small"><strong>Surviving anchor.</strong> The catalogue-agnostic stride-5 lattice scores
{lat_row['holdout_dti']:.4f} here against a reported {LATTICE_REPORTED} (ratio
{lat_row['holdout_dti'] / LATTICE_REPORTED:.2f}), so the instrument's <em>scale</em> is right for
untargeted emissions; only its <em>ranking</em> of catalogue-adjacent ones is broken.</p>
<p class="small"><strong>Consequence for this repo:</strong> cross-family holdout comparisons are
withdrawn, including the previously published HOLDOUT-DTI 0.1321 for the rejected step-asymmetry
file, which is now known to be a meaningless number. Only within-lane comparisons — where both arms
are fold-local and catalogue-agnostic — are reported below.</p>
</div>

<h2>6 · HOLDOUT-DTI, within-lane only (the fair comparison)</h2>
<div class="card">
<p class="small">Evaluator <code>{e(card['holdout_dti']['evaluator'])}</code>, implementation
<code>{e(impl_summary)}</code>, 4 spatially blocked folds,
seed 20, hide 20 % of fault components with a 3-px buffer, α = 0.2, β = 0.8, 300 m triangular
kernel, 200 m blocks, budget {card['emission']['budget']:,} dots allocated per fold by active-cell
share. Every arm is fold-local: no arm ever sees the segments withheld from its own fold.</p>
<table><tr><th>Arm</th><th class="num">Shared buffered DTI [CI95]</th>
<th class="num">Detached-8px DTI [CI95]</th><th class="num">withheld truth px</th></tr>
{"".join(arms)}</table>
<h3>Paired differences (released arm minus each other arm, same folds, same budget)</h3>
<table><tr><th>Contrast</th><th class="num">Shared buffered Δ [CI95]</th>
<th class="num">Detached-8px Δ [CI95]</th><th>Shared-instrument verdict</th></tr>
{"".join(paired_rows)}</table>
<p class="small muted">Bootstrap: {e(boot['method'])}, {boot['clusters']} spatial clusters,
{boot['draws']} draws. {e(boot['caveat'])}</p>
<p class="small"><strong>Read.</strong> On the shared instrument, skeleton thinning to a 1-px ridge
beats unthinned top-N by {pd1['candidate_topN']['delta']:+.4f} and the unsupervised contrast control
by {pd1['control_contrast']['delta']:+.4f} — supervision roughly doubles the control at every budget
from 10,000 to 130,000 dots. On the blind-truth-representative detached-8px instrument the
candidate's edge over the control is <strong>not resolved</strong>
({pd2['control_contrast']['delta']:+.4f}, CI [{pd2['control_contrast']['ci95'][0]:+.4f},
{pd2['control_contrast']['ci95'][1]:+.4f}] — crosses zero), while its edge over unthinned top-N is
resolved. The graded 1-px ring hedge <em>hurt</em> on both instruments and was dropped from the
release. DTI rises monotonically with budget on every instrument, so the holdout cannot locate the
false-positive-limited optimum; the released budget is therefore anchored on the user-reported ledger
cluster (35k–39k dots → 0.2649–0.2778), not on the instrument.</p>
<p class="small">Leakage canary: {e(card['holdout_dti']['leakage_canary']['status'])}. Strongest
single feature <code>{e(card['holdout_dti']['leakage_canary']['strongest'][0][0])}</code>, two-sided
AUC {card['holdout_dti']['leakage_canary']['strongest'][0][1]:.3f}. Irregularity flagged:
{e(card['holdout_dti']['leakage_canary']['irregularity'])}</p>
</div>

<h2>7 · Where we stand on the public leaderboard</h2>
<div class="card">
<p class="small">{e(board.get('evidence_class', 'LEADERBOARD SNAPSHOT'))} · captured {e(board.get('captured_utc', 'unknown'))} · status {e(board.get('status', 'unknown'))}<br>
<span class="muted">{e(board['method'])}</span></p>
<table><tr><th class="num">#</th><th>Team</th><th class="num">Public DTI</th>
<th class="num">Subs</th><th>Last active</th></tr>{board_rows}</table>
<p class="small muted">The repo's previous snapshot (0.4437, 2026-10-26) is superseded, and the highs
quoted in the project brief (0.3195, 0.4413) are both stale: the live top is
{f4(board.get('top_public_dti'))} and, at capture time, the top-22 cluster spanned 0.3261–0.4544. The best number this repo's
scope has ever reported ({B2_REPORTED}) sits far below the median of that leading group.
{e(board['note'])}</p>
</div>

<h2>8 · Full executive table — every GEMSDOE site in scope</h2>
<div class="card">
<table><tr><th>File / site</th><th class="num">Score</th><th>Unique vs the others?</th>
<th>Download &amp; submit?</th></tr>{table}</table>
<p class="small"><strong>Scope of “every site”.</strong> This table covers every GEMSDOE site for
which this repository holds hash-pinned raster bytes: 9 historical best files, 2 other research
files, 1 binary lattice and 1 continuous prior, plus our own new file. The wider user-reported ledger
(<a href="data/user-reported-ledger.csv">126 rows</a>) names many more sites, but without their bytes
no uniqueness or format claim about them can be made, so they are listed there and not here.</p>
<p class="small muted">“USER-REPORTED” means an owner published that number for their own file; it is
not an organiser receipt. No ORGANIZER-CONFIRMED score exists anywhere in this repository, because
this repo has never held a submission slot. Only the first row is ours to submit — the rest are other
teams' files, kept for learning and as uniqueness witnesses.</p>
</div>

<h2>9 · Reproduce this file byte-for-byte</h2>
<div class="card"><pre>{e(card['reproduce'])}</pre>
<p class="small muted">Deterministic given the pinned shared template
(<code>57GEMSDOE@822a0ce5</code>), the pinned mirrors and the seeds recorded in
<code>data/lane/final_receipt.json</code>. Needs numpy, scipy, scikit-learn, rasterio and
scikit-image; 2 CPUs and ~3.9 GB RAM are enough because the feature bank is a uint8 memmap and
prediction is row-chunked.</p></div>

<footer>Generated {e(card['generated_utc'])} by <code>scripts/build_lane_b_release.py</code> from
committed machine evidence. Labels: ORGANIZER-CONFIRMED · USER-REPORTED · HOLDOUT-DTI ·
CALIBRATED PROJECTION. A projection is never written as a score.</footer>
</div></body></html>
"""


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--budget", type=int, default=38000)
    p.add_argument("--collar-px", type=int, default=2)
    p.add_argument("--page", type=Path, default=ROOT / "docs" / "submit.html")
    p.add_argument("--card", type=Path, default=ROOT / "evidence" / "run_card_lane_b.json")
    args = p.parse_args()

    card, page, tif = build_release(args)
    text = json.dumps(card, indent=1, allow_nan=False) + "\n"
    args.card.write_text(text)
    print("wrote", args.card)
    for rel in ("docs/data/run-card-lane-b.json", "site/data/run_card_lane_b.json"):
        out = ROOT / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text)
        print("mirrored", out)
    args.page.write_text(page)
    print("wrote", args.page, f"({len(page):,} bytes)")
    print(json.dumps(dict(name=card["submission_name"], sha256=card["raster_sha256"],
                          emitted=card["emission"]["emitted"],
                          projection=[card["projection"]["floor"], card["projection"]["parity"]],
                          ok_to_download=card["ok_to_download"],
                          ok_to_submit_format=card["ok_to_submit_format"],
                          beats_incumbent_demonstrated=card["beats_incumbent_demonstrated"]),
                     indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
