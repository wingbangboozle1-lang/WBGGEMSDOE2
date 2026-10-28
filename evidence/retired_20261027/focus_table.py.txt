#!/usr/bin/env python3
"""Per-focus-site measured table: dots, geometry, model estimate, mutual uniqueness."""
import json, sys
from pathlib import Path
import numpy as np, rasterio
from scipy import ndimage as ndi
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts')); sys.path.insert(0,str(ROOT/'src'))
from fleet_stats import load_official
from score_model import make_model

def main():
    pins=json.load(open(ROOT/'data_public/focus_pins_verified.json'))['files']
    feat=json.load(open(ROOT/'data_public/fleet_features.json'))
    rows=[r for r in feat['rows'] if r['grid_matches_official']]
    X=np.asarray([[np.log10(max(r['support_px'],1)),r['median_px_to_catalogue'],r['frac_within_3px_catalogue'],
                   np.log10(r['components_8conn']+1),r['binary_fraction'],np.log10(r['mass']+1)] for r in rows],float)
    y=np.asarray([r['reported_score'] for r in rows],float)
    model=make_model().fit(X,y)
    cat,cat_meta,sub_meta,fp=load_official()
    dist_cat=ndi.distance_transform_edt(cat==0)
    cand=json.load(open(ROOT/'data_public/candidate.json'))
    with rasterio.open(ROOT/cand['file']) as s: mine=s.read(1)
    msup=mine>0; d_mine=ndi.distance_transform_edt(~msup)
    arrs={}
    for p in pins:
        with rasterio.open(ROOT/p['local']) as s: a=s.read(1)
        arrs[p['site']]=np.isfinite(a)&(a>0)
    out=[]
    for p in pins:
        sup=arrs[p['site']]; d=dist_cat[sup]
        x=np.asarray([[np.log10(int(sup.sum())),float(np.median(d)),float((d<=3).mean()),
                       np.log10(1+int(ndi.label(sup,structure=np.ones((3,3),bool))[1])),1.0,
                       np.log10(int(sup.sum())+1)]])
        others={s2:round(float((ndi.distance_transform_edt(~sup2)[sup]<=3).mean()),3) for s2,sup2 in arrs.items() if s2!=p['site']}
        out.append({**{k:p[k] for k in ('site','repository','ref','path','sha256','verified_sha256',
                                       'pin_match','user_reported_score','page_url','download_url')},
                    'dots':int(sup.sum()),'median_px_to_catalogue':round(float(np.median(d)),2),
                    'frac_within_3px_catalogue':round(float((d<=3).mean()),3),
                    'model_estimate':round(float(model.predict(x)[0]),4),
                    'max_overlap_vs_other_focus_sites':max(others.values()),
                    'min_overlap_vs_other_focus_sites':min(others.values()),
                    'overlap_with_wbg2_candidate':round(float((d_mine[sup]<=3).mean()),4),
                    'unique_vs_other_focus_sites':bool(max(others.values())<0.70)})
    for r in out: r['user_reported_score']=float(r['user_reported_score'])
    out.sort(key=lambda r:-r['user_reported_score'])
    json.dump({'evidence_class':'MEASURED + EMPIRICAL-ESTIMATE','rows':out},
              open(ROOT/'data_public/focus_table.json','w'),indent=1)
    for r in out:
        print(f"{r['site']:10s} rep={r['user_reported_score']:.4f} dots={r['dots']:6d} "
              f"est={r['model_estimate']:.3f} maxovl={r['max_overlap_vs_other_focus_sites']:.2f} unique={r['unique_vs_other_focus_sites']}")
if __name__=='__main__': main()
