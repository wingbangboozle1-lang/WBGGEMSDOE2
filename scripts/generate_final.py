#!/usr/bin/env python3
"""Final TIF: E2 recipe (winner of holdout) trained on the full catalogue.
Bands = all except dist_visible_fault_log (holdout showed catalogue-proximity
destroys recovery: E1 0.0227 vs E2 0.1321). Emission: greedy 2.8px-separated
packing, 44,090 budget (family-optimal range on the live ledger), dots
forbidden within 2px of catalogue faults (known faults are masked in scoring).
Output values are binary {0,1} float32 -> cannot trigger '[0,1]' error."""
import sys, os, json, hashlib, datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, rasterio
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingClassifier
from run_lane import build_features, sample_bands, predict_surface, emit_greedy, load, DATA
from submission_writer import write_submission
from validate_submission import validate

def main(budget=44090):
    labels_raw,_ = load("labels.tif"); labels_raw=labels_raw[0]
    footprint = labels_raw>=0; labels = labels_raw==1
    bands, names = build_features(labels)
    bands = bands[:-1]; names = names[:-1]           # drop dist_visible (E2)
    rng = np.random.default_rng(20261026)
    pos = np.where(footprint & labels)
    negm = np.where(footprint & ~ndi.binary_dilation(labels, iterations=3))
    nsel = rng.choice(len(negm[0]), 300000, replace=False)
    clf = HistGradientBoostingClassifier(max_iter=250, learning_rate=0.07, random_state=0)
    clf.fit(np.nan_to_num(np.concatenate([sample_bands(bands,pos),
            sample_bands(bands,(negm[0][nsel],negm[1][nsel]))])),
            np.concatenate([np.ones(len(pos[0])), np.zeros(len(nsel))]))
    surf = predict_surface(clf, bands)
    forb = ndi.binary_dilation(labels, iterations=2)
    dots = emit_greedy(surf, footprint & ~forb, budget, min_sep=2.8)
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    sha_surf = hashlib.sha256(surf.tobytes()).hexdigest()[:8]
    name = f"wbg2-h1-stepxasym-e2-{int(dots.sum())}dots-{ts}-{sha_surf}-zeros"
    out = f"docs/downloads/{name}.tif"
    write_submission(dots, os.path.join(DATA,"sample_submission.tif"), out)
    v = validate(out, os.path.join(DATA,"sample_submission.tif"))
    card = dict(name=name, file=out, dots=int(dots.sum()), budget=budget,
                surface_sha256=hashlib.sha256(surf.tobytes()).hexdigest(),
                validator=v, features=names,
                note=f"WBG2 H1 stepXasym E2 {int(dots.sum())}d holdout0.1321 no-catdist unique-check pending"[:140])
    open("evidence/final_candidate.json","w").write(json.dumps(card,indent=2))
    print(json.dumps(card,indent=2))

if __name__=="__main__": main()
