from pathlib import Path
import json
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from scripts import run_preflight as audit

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def shared():
    if not (audit.TEMPLATE / 'gems57/uniqueness.py').is_file():
        pytest.skip('shared template is not restored; run scripts/bootstrap_template.sh')
    return audit.shared_uniqueness()


def test_universal_positive_support_blocks_every_nonempty_candidate(shared):
    dots, near = shared
    fp = np.ones((9, 11), dtype=bool)
    prior = np.full(fp.shape, 0.001, dtype=np.float32)
    result = audit.universal_coverage(fp, prior, dots, near)
    assert result['universal_blocker'] is True
    assert result['positive_pixels_in_footprint'] == fp.size
    for position in [(0, 0), (4, 7), (8, 10)]:
        candidate = np.zeros_like(fp)
        candidate[position] = True
        assert np.all(near(dots(prior))[candidate])


def test_sparse_witness_does_not_prove_universal_blocker(shared):
    dots, near = shared
    fp = np.ones((20, 20), dtype=bool)
    prior = np.zeros(fp.shape, dtype=np.float32)
    prior[0, 0] = 1
    result = audit.universal_coverage(fp, prior, dots, near)
    assert result['universal_blocker'] is False
    assert result['uncovered_pixels_within_3px'] > 0
    # The boundary is Euclidean <= 3, not a square or 3.1 px.
    halo = near(dots(prior))
    assert halo[0, 3] and not halo[3, 1]


def test_witness_validation_is_fail_closed(shared):
    dots, near = shared
    fp = np.ones((5, 5), dtype=bool)
    for invalid in (np.nan, np.inf, -0.01, 1.01):
        prior = np.ones((5, 5), np.float32)
        prior[2, 2] = invalid
        with pytest.raises(ValueError):
            audit.universal_coverage(fp, prior, dots, near)
    with pytest.raises(ValueError):
        audit.universal_coverage(fp, np.ones((5, 6)), dots, near)
    with pytest.raises(ValueError):
        audit.universal_coverage(np.zeros((5, 5)), np.ones((5, 5)), dots, near)
    # Outside-footprint NaNs are valid and cannot become witness support.
    fp[0, 0] = False
    prior = np.ones((5, 5), np.float32)
    prior[0, 0] = np.nan
    assert audit.universal_coverage(fp, prior, dots, near)['universal_blocker']


def write_test_tif(path, array, transform=None, crs='EPSG:32611'):
    with rasterio.open(path, 'w', driver='GTiff', width=array.shape[1], height=array.shape[0],
                       count=1, dtype='float32', crs=crs,
                       transform=transform or from_origin(100, 1000, 100, 100)) as ds:
        ds.write(array.astype('float32'), 1)


def test_matching_grid_and_in_footprint_range_validation(tmp_path, monkeypatch):
    path = tmp_path / 'test.tif'
    a = np.zeros((3, 4), np.float32)
    write_test_tif(path, a)
    monkeypatch.setattr(audit, 'checked_path', lambda _: path)
    with rasterio.open(path) as ds:
        reference = (ds.shape, ds.crs, ds.transform)
    fp = np.ones(a.shape, bool)
    assert audit.load_matching({'id': 'test'}, reference, fp).shape == a.shape
    for value in [np.nan, np.inf, -1, 2]:
        a[0, 0] = value
        write_test_tif(path, a)
        with pytest.raises(ValueError):
            audit.load_matching({'id': 'test'}, reference, fp)
    a[0, 0] = np.nan
    fp[0, 0] = False
    write_test_tif(path, a)
    assert np.isnan(audit.load_matching({'id': 'test'}, reference, fp)[0, 0])
    write_test_tif(path, np.zeros_like(a), transform=from_origin(101, 1000, 100, 100))
    with pytest.raises(ValueError, match='Grid mismatch'):
        audit.load_matching({'id': 'test'}, reference, fp)


def test_published_run_card_cannot_be_mistaken_for_a_candidate():
    card = json.loads((ROOT / 'reports/run-card.json').read_text())
    assert card['verdict'] == 'negative' and not card['submission_allowed']
    assert card['raster_sha256'] is None and card['submission_name'] is None and card['submission_note'] is None
    assert card['holdout_dti']['value'] is None and card['holdout_dti']['ci95'] is None
    assert card['leakage_canary']['status'] == 'not run'
    assert card['validator_output']['status'].startswith('not run')
    assert card['experiments_run'] == card['submission_slots_used'] == 0
    witness = card['correlation_overlap_vs_registry']['universal_witness']
    assert witness['positive_pixels_in_footprint'] == witness['footprint_pixels']
    assert witness['fraction_covered_within_3px'] == 1 and witness['universal_blocker']


def test_focus_report_pins_and_pixel_relationships():
    pins = json.loads((ROOT / 'site-data/registry-pins.json').read_text())
    report = json.loads((ROOT / 'reports/focus-review.json').read_text())
    assert len(pins['focus_sites']) == len(report['rows']) == 9
    by_name = {x['site']: x for x in report['rows']}
    for row in pins['focus_sites']:
        result = by_name[row['site']]
        assert result['sha256'] == row['sha256']
        assert result['max_forward_overlap_3px'] > 0.70
        assert result['unique_vs_nine_under_literal_rule'] is False
        assert result['evidence_class'].startswith('USER-REPORTED')
    ancestry = report['ancestry']
    assert ancestry['d28_pixels_outside_h19_5'] == 0
    assert ancestry['gems25_vs_gems30_support_xor_pixels'] == 0
    assert ancestry['gems31_vs_d28_pruned_le_1px_xor_pixels'] == 0
    assert ancestry['gems32_vs_d28_pruned_le_2px_xor_pixels'] == 0
    assert (ancestry['d28_positive_pixels'], ancestry['gems31_positive_pixels'], ancestry['gems32_positive_pixels']) == (44090, 40199, 37654)


def test_modified_shared_dependency_is_rejected(tmp_path, monkeypatch):
    import shutil
    original = audit.TEMPLATE.parent
    if not (original / 'src/gems57/metric.py').is_file():
        pytest.skip('shared template not restored')
    target = tmp_path / 'template'
    shutil.copytree(original / 'src/gems57', target / 'src/gems57')
    (target / 'scripts').mkdir(parents=True)
    shutil.copy2(original / 'scripts/prepare_data.py', target / 'scripts/prepare_data.py')
    metric = target / 'src/gems57/metric.py'
    metric.write_text(metric.read_text() + '\n# local modification\n')
    monkeypatch.setattr(audit, 'TEMPLATE', target / 'src')
    with pytest.raises(RuntimeError, match='metric.py'):
        audit.shared_uniqueness()


def test_inspector_does_not_promote_even_locally_valid_historical_file():
    from scripts import validate_raster
    raster = ROOT / '.cache/references/GEMSDOE32.tif'
    if not raster.exists() or not (ROOT / '.cache/audit/prior-continuous.tif').exists():
        pytest.skip('pinned research inputs not restored')
    result = validate_raster.inspect(raster)
    assert result['format_report']['ok'] is True
    assert result['witness_overlap_3px'] == 1.0
    assert result['submission_allowed'] is False
    assert result['verdict'] == 'negative' and result['registry_complete'] is False


def test_witness_is_pinned_in_shared_inventory(shared):
    manifest = json.loads((ROOT / 'site-data/registry-pins.json').read_text())
    witness = next(x for x in manifest['inputs'] if x['id'] == 'universal_witness')
    proof = audit.verify_witness_in_inventory(witness)
    assert proof['git_blob'] == '2ef0c06c25cdab62ba3381a1b43db230776fc631'
    with pytest.raises(RuntimeError, match='not uniquely indexed'):
        audit.verify_witness_in_inventory({**witness, 'ref': 'not-the-snapshot'})


def test_shared_format_report_rejects_out_of_range_and_nonfinite_pixels(tmp_path, shared):
    # Synthetic local format fixtures are not candidate predictions.
    from gems57.gates import format_report
    sample = tmp_path / 'reference.tif'
    fixture = tmp_path / 'malformed.tif'
    a = np.zeros((3, 4), np.float32)
    write_test_tif(sample, a)
    for invalid in [-0.01, 1.01, np.inf, np.nan]:
        a[1, 1] = invalid
        write_test_tif(fixture, a)
        report = format_report(fixture, sample, footprint=np.ones(a.shape, bool))
        assert report['ok'] is False
        assert report['problems']
        a[1, 1] = 0


def test_inspection_cli_exits_blocked_even_after_successful_format_check():
    import subprocess
    import sys
    raster = ROOT / '.cache/references/GEMSDOE32.tif'
    if not raster.exists() or not (ROOT / '.cache/audit/prior-continuous.tif').exists():
        pytest.skip('pinned research inputs not restored')
    proc = subprocess.run([sys.executable, 'scripts/validate_raster.py', str(raster)],
                          cwd=ROOT, capture_output=True, text=True, check=False)
    assert proc.returncode == 2, proc.stderr
    data = json.loads(proc.stdout)
    assert data['format_report']['ok'] is True and data['submission_allowed'] is False
