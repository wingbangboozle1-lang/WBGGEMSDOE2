"""Small fixtures exercise the exact pinned shared code, not a private metric fork."""
from pathlib import Path
import importlib
import sys

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

import prepare_data


@pytest.fixture(scope='module')
def shared():
    try:
        prepare_data.restore_template(False)
    except FileNotFoundError:
        pytest.skip('shared template absent; run scripts/prepare_data.py --fetch or restore_template(True)')
    sys.path.insert(0,str(prepare_data.TEMPLATE/'src'))
    return {name:importlib.import_module('gems57.'+name) for name in ['metric','spatial','evaluate_holdout','gates','submission_writer','uniqueness']}


def test_soft_dti_against_literal_bruteforce_random_and_masks(shared):
    metric=shared['metric'];rng=np.random.default_rng(440)
    for _ in range(12):
        truth=rng.random((7,8)) < .16
        pred=np.where(rng.random((7,8))<.20, rng.random((7,8)), 0)
        valid=rng.random((7,8))>.05; known=rng.random((7,8))<.04
        active=valid & ~known
        actual=metric.dti_exact(pred,truth,valid=valid,known=known)
        oracle=metric.dti_bruteforce(np.where(active,pred,0), truth & active)
        for k in ['tp','fp','fn','dti']:
            assert actual[k] == pytest.approx(oracle[k],abs=1e-10), (k,actual,oracle)


def test_delta_truth_credit_can_exceed_dot_self_credit(shared):
    metric=shared['metric'];truth=np.zeros((7,7),bool)
    truth[3,3]=truth[2,3]=truth[4,3]=truth[3,2]=truth[3,4]=True
    pred=np.zeros_like(truth,dtype=float);pred[3,3]=1
    result=metric.dti_exact(pred,truth)
    self_credit=1.0
    assert result['tp'] > self_credit  # docs' delta_T <= k is not generally true


def test_whole_segments_hidden_and_train_buffered(shared):
    spatial=shared['spatial']; eligible=np.ones((28,28),bool); cat=np.zeros_like(eligible)
    cat[2:22,13]=True  # crosses both quadrant boundaries
    cat[22:25,22]=True
    folds=list(spatial.folds(cat,eligible,buffer_px=2))
    assert len(folds)==4
    for fold in folds:
        assert not np.any(fold['visible'] & fold['held_all'])
        assert not np.any(fold['train'] & fold['held_all'])
        assert not np.any(fold['train'] & fold['region'])
        assert np.array_equal(fold['truth'],fold['held_all'] & fold['region'])
        # The same connected component cannot be partly visible if held.
        comp=fold['components']; held_ids=np.unique(comp[fold['held_all']]);held_ids=held_ids[held_ids>0]
        assert not np.isin(comp[fold['visible']],held_ids).any()


def test_evaluator_masks_visible_faults_pixel_exactly(shared):
    evaluator=shared['evaluate_holdout']; truth=np.zeros((7,7),bool);truth[3,3]=True
    visible=np.zeros_like(truth);visible[0,0]=True
    p=np.zeros((7,7),np.float32);p[3,3]=1;p[0,0]=1
    fold={'truth':truth,'visible':visible,'region':np.ones_like(truth)}
    scored,terms=evaluator.evaluate(p,fold,np.ones_like(truth),block_side=3)
    assert scored['n_truth']==1 and scored['n_emitted']==1
    assert scored['tpw']==pytest.approx(1) and scored['fpw']==pytest.approx(0)
    assert terms.sum(axis=0)[3]==1


def test_bootstrap_rejects_mismatched_truth_and_reports_ci(shared):
    evaluator=shared['evaluate_holdout']
    a=np.array([[.5,1,.5,1],[.3,2,.7,1]],float)
    b=np.array([[.4,1,.6,1],[.2,2,.8,1]],float)
    result=evaluator.pooled_summary({'candidate':a,'control':b},draws=100,seed=4,candidate='candidate')
    assert result['scores']['candidate']['withheld_positive_pixels']==2
    assert len(result['scores']['candidate']['ci95'])==2
    bad=b.copy();bad[0,3]=2
    with pytest.raises(ValueError,match='same integer truth count'):
        evaluator.pooled_summary({'candidate':a,'control':bad},draws=100,candidate='candidate')


def _raster(path, array, transform, crs='EPSG:32611', dtype='float32'):
    a=np.asarray(array,dtype=dtype)
    if a.ndim==2:a=a[None,...]
    with rasterio.open(path,'w',driver='GTiff',height=a.shape[1],width=a.shape[2],count=a.shape[0],dtype=dtype,crs=crs,transform=transform) as out:out.write(a)


def test_saved_bytes_format_rejects_bad_range_nan_transform_and_outside(shared,tmp_path):
    gates=shared['gates']; tr=from_origin(243350,4508550,100,100); shape=(5,6)
    sample=tmp_path/'sample.tif';_raster(sample,np.zeros(shape),tr)
    fp=np.ones(shape,bool);fp[0,0]=False
    good=np.zeros(shape,np.float32);good[2,2]=1
    p=tmp_path/'good.tif';_raster(p,good,tr)
    assert gates.format_report(p,sample,footprint=fp)['ok']
    for name,arr in [('negative',np.full(shape,-.01)),('over',np.full(shape,1.01)),('nan',np.full(shape,np.nan)),('infinity',np.full(shape,np.inf))]:
        f=tmp_path/f'{name}.tif';_raster(f,arr,tr)
        assert not gates.format_report(f,sample,footprint=fp)['ok'],name
    outside=good.copy();outside[0,0]=1
    f=tmp_path/'outside.tif';_raster(f,outside,tr)
    assert not gates.format_report(f,sample,footprint=fp)['ok']
    f=tmp_path/'wrong_transform.tif';_raster(f,good,from_origin(243450,4508550,100,100))
    assert not gates.format_report(f,sample,footprint=fp)['ok']
    f=tmp_path/'two_bands.tif';_raster(f,np.stack([good,good]),tr)
    assert not gates.format_report(f,sample,footprint=fp)['ok']


def test_writer_refuses_silent_repair_and_bad_notes(shared,tmp_path):
    writer=shared['submission_writer'];fp=np.ones((3,3),bool)
    for x in [-.01,1.01,np.nan,np.inf]:
        p=np.zeros((3,3),np.float32);p[1,1]=x
        with pytest.raises(ValueError,match='finite and in'):
            writer.write_submission(tmp_path/'out.tif',p,tmp_path/'sample.tif',fp,note='research',name='test')
        assert not (tmp_path/'out.tif').exists()
    with pytest.raises(ValueError,match='note'):
        writer.write_submission(tmp_path/'out.tif',np.zeros((3,3),np.float32),tmp_path/'sample.tif',fp,note='x'*141,name='test')


def test_literal_novelty_has_no_saturation_exemption(shared):
    u=shared['uniqueness'];mine=np.zeros((8,8));mine[2,2]=1
    full=np.ones((8,8))
    assert u.dot_overlap(mine,full)==1


def test_masked_interior_known_shared_gap_is_a_supplemental_stop(shared, tmp_path, monkeypatch):
    # Shared gate sees finite zeros but ignores their in-footprint nodata mask.
    # Do not patch the pinned code here: upstream fix is still required.
    import validate_submission
    tr = from_origin(243350, 4508550, 100, 100)
    sample = tmp_path / 'sample.tif'
    candidate = tmp_path / 'candidate.tif'
    _raster(sample, np.ones((5, 6)), tr)
    with rasterio.open(candidate, 'w', driver='GTiff', height=5, width=6, count=1,
                       dtype='float32', crs='EPSG:32611', transform=tr, nodata=0) as ds:
        ds.write(np.zeros((5, 6), np.float32), 1)
    monkeypatch.setattr(validate_submission, 'SAMPLE_SHA', validate_submission.digest(sample))
    report = validate_submission.run(candidate, sample)
    assert report['shared_format_ok'] is True  # gap in the pinned upstream version
    assert report['masked_inside_footprint'] == 30
    assert report['supplemental_mask_and_format_ok'] is False
    assert report['ok'] is False and report['ok_to_submit'] is False
