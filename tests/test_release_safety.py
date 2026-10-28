"""Regressions for literal novelty, retired entry points and a complete site rebuild."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from audit_release_triage import audit_one


RETIRED = (
    'make_candidate.py', 'final_audit.py', 'uniqueness_audit.py',
    'generate_h3_pack.py', 'write_h3_submission.py', 'run_wbg2_msptcd.py',
    'run_wbg2_cbs.py', 'run_campaign_20261027.py', 'run_wbg2_dphs.py',
    'audit_dphs_and_fleet.py', 'candidate_estimate.py', 'score_model.py',
    'focus_table.py', 'verify_prompt_ledger.py', 'h3_analysis.py',
    'mass_balance.py', 'fleet_stats.py', 'fetch_external_layers.py',
)


@pytest.mark.parametrize('script', RETIRED)
def test_retired_entry_points_stop_before_writing(script):
    result = subprocess.run([sys.executable, str(ROOT / 'scripts' / script), '--selftest'],
                            capture_output=True, text=True, timeout=10)
    assert result.returncode != 0
    assert 'STOP' in result.stdout + result.stderr
    assert any((folder / (script + '.txt')).is_file() for folder in (ROOT / 'evidence/retired_20261027', ROOT / 'evidence/reconciliation_archive/incoming-29abbf69'))


def write_raster(path: Path, values: np.ndarray) -> None:
    with rasterio.open(path, 'w', driver='GTiff', width=values.shape[1], height=values.shape[0],
                       count=1, dtype='float32', crs='EPSG:32611',
                       transform=from_origin(0, values.shape[0] * 100, 100, 100)) as dst:
        dst.write(values.astype('float32'), 1)


def test_literal_stop_is_strictly_over_seventy_percent_and_never_approves(tmp_path):
    reference = tmp_path / 'reference.tif'
    candidate = tmp_path / 'candidate.tif'
    footprint = np.ones((10, 10), dtype=bool)
    values = np.zeros((10, 10), dtype='float32')
    values[0, :10] = 1
    write_raster(reference, np.zeros((10, 10)))
    write_raster(candidate, values)
    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    coverage = np.zeros((10, 10), dtype=bool)
    coverage[0, :7] = True
    at_limit = audit_one(candidate, digest, reference, footprint, coverage)
    assert at_limit['final_dot_overlap_3px_vs_13GEMSDOE'] == 0.7
    assert at_limit['literal_witness_result'] == 'no-witness-in-scope'
    assert at_limit['registry_complete'] is False and at_limit['ok_to_submit'] is False
    coverage[0, 7] = True
    above_limit = audit_one(candidate, digest, reference, footprint, coverage)
    assert above_limit['final_dot_overlap_3px_vs_13GEMSDOE'] == 0.8
    assert above_limit['literal_witness_result'] == 'duplicate-stop'
    assert above_limit['preplacement_surface_rank_correlation'] is None
    assert above_limit['ok_to_submit'] is False
    with pytest.raises(ValueError, match='hash mismatch'):
        audit_one(candidate, '0' * 64, reference, footprint, coverage)


def copy_site_sources(destination: Path) -> None:
    for name in ('scripts', 'src', 'config', 'docs', 'site', 'evidence', 'downloads', 'candidate',
                 'research', 'data_public', 'artifacts'):
        shutil.copytree(ROOT / name, destination / name,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    shutil.copy(ROOT / 'index.html', destination / 'index.html')


def test_site_regeneration_cannot_restore_a_historical_approval(tmp_path):
    copy_site_sources(tmp_path)
    for name in ('build_hypotheses.py', 'build_run_card.py', 'build_site.py',
                 'build_site_data.py', 'build_msptcd_site.py', 'build_release.py'):
        result = subprocess.run([sys.executable, str(tmp_path / 'scripts' / name)],
                                cwd=tmp_path, capture_output=True, text=True, timeout=25)
        assert result.returncode == 0, (name, result.stdout, result.stderr)
    rejected_phrases = (
        'one file is approved to download and submit',
        'one file is ready to download and submit',
        'submit exactly one file:',
        'cleared exactly one submission',
        'zero-leakage holdout',
        'zero-leakage verification',
        'forensic proof',
        'exact path past',
        'why 0.2778 won',
        'portal-safe',
        'proven empirically',
    )
    pages = [tmp_path / 'index.html', *list((tmp_path / 'docs').rglob('*.html')),
             *list((tmp_path / 'site').rglob('*.html'))]
    for page in pages:
        text = page.read_text(encoding='utf-8').lower()
        assert all(phrase not in text for phrase in rejected_phrases), page
    # Every entrypoint must retain the independently measured negative decision.
    for rel in ('docs/index.html', 'docs/executive-summary.html'):
        text = (tmp_path / rel).read_text(encoding='utf-8')
        assert 'DO NOT SUBMIT' in text and 'OK TO DOWNLOAD AND SUBMIT' not in text, rel
    for rel in ('docs/submit/index.html', 'docs/submission/index.html',
                'docs/msptcd/index.html'):
        text = (tmp_path / rel).read_text(encoding='utf-8')
        assert 'No file is approved for submission.' in text and 'DO NOT SUBMIT' in text, rel
    for rel in ('docs/dphs/index.html', 'docs/dphs/executive-summary.html',
                'docs/dphs/how-to-submit.html'):
        text = (tmp_path / rel).read_text(encoding='utf-8').lower()
        assert 'do not submit' in text and 'not independently' in text, rel
        assert 'gems57-pooled-hide-v2' in text and '60,988' in text, rel
        assert '99.836%' in text and 'portal acceptance' in text, rel
    executive = (tmp_path / 'docs/dphs/executive-summary.html').read_text().lower()
    assert 'exact known-fault pixels' in executive and 'not a two-pixel collar' in executive
    assert 'causal effect is unmeasured' in executive
    howto = (tmp_path / 'docs/dphs/how-to-submit.html').read_text().lower()
    assert 'rejected bytes' in howto and 'null/nan outside' in howto
    card = json.loads((tmp_path / 'docs/data/RUN_CARD_FINAL.json').read_text())
    assert card['verdict'] == 'negative' and card['ok_to_submit'] is False
    assert card['raster_sha256'] is None and card['submission_name'] is None
    assert card['submission_note'] is None and len(card['note']) <= 140


def test_concurrent_distal_is_rejected_not_passed_or_projected():
    audit = json.loads((ROOT / 'evidence/release_audit.json').read_text())
    row = next(r for r in audit['artifacts'] if r['path'].startswith('candidate/'))
    assert row['positive_support_cells'] == 6000
    assert row['lattice_overlap_3px'] == pytest.approx(0.6716666666666666)
    assert row['maximum_overlap_3px'] == 1.0
    assert row['duplicate_witnesses'] == ['17GEMSDOE_dense_prior']
    assert row['strict_all_finite_validator']['format_valid_against_reference'] is True
    assert row['ok_to_submit'] is False and row['surface_rank_correlation'] is None
    paths = ('docs/data/RUN_CARD_DISTAL.json', 'evidence/RUN_CARD_DISTAL.json',
             'evidence/wbg2_distal_candidate.json', str(Path(row['path']).with_suffix('.json')))
    cards = [json.loads((ROOT / p).read_text()) for p in paths]
    assert all(card == cards[0] for card in cards)
    card = cards[0]
    assert card['verdict'] == 'negative' and card['ok_to_submit'] is False
    assert card['raster_sha256'] == row['sha256']
    assert card['surface_rank_correlation'] is card['holdout_dti'] is None
    assert card['leaderboard_score_estimate'] is card['submission_name'] is card['submission_note'] is None
    assert 'unresolved' in card['continuous_prior_caveat'].lower()
    page = (ROOT / 'docs/candidate.html').read_text().lower()
    assert 'do not submit' in page and '67.167%' in page and '100.0%' in page
    assert 'format+uniqueness pass' not in page and 'empirical 0.23' not in page


@pytest.mark.parametrize('change', ('score', 'ci', 'count', 'hash'))
@pytest.mark.parametrize('builder', ('build_site.py', 'build_release.py'))
def test_dphs_builders_refuse_changed_unmatched_historical_receipt(tmp_path, change, builder):
    copy_site_sources(tmp_path)
    path = tmp_path / 'evidence/wbg2_dphs_results.json'
    result = json.loads(path.read_text())
    score = result['pooled_holdout_summary']['scores']['exp3_dphs_submodular']
    if change == 'score':
        score['dti'] = 0.99
    elif change == 'ci':
        score['ci95'][0] = 0.99
    elif change == 'count':
        score['withheld_positive_pixels'] += 1
    else:
        result['emitted_candidate']['tif_sha256'] = '0' * 64
    path.write_text(json.dumps(result))
    run = subprocess.run([sys.executable, str(tmp_path / 'scripts' / builder)],
                         cwd=tmp_path, capture_output=True, text=True, timeout=25)
    assert run.returncode != 0 and 'Historical DPHS' in run.stderr


@pytest.mark.parametrize('phrase', ('exact path past 0.4544', 'why 0.2778 won',
                                    'portal-safe', 'proven empirically',
                                    'zero-leakage verification'))
def test_negative_publisher_rejects_unsupported_legacy_copy(tmp_path, phrase):
    copy_site_sources(tmp_path)
    (tmp_path / 'docs/legacy-unsafe.html').write_text(f'<html><body><h1>{phrase}</h1></body></html>')
    run = subprocess.run([sys.executable, str(tmp_path / 'scripts/build_release.py')],
                         cwd=tmp_path, capture_output=True, text=True, timeout=25)
    assert run.returncode != 0 and 'Unsupported legacy campaign claim' in run.stderr


@pytest.mark.parametrize('receipt', ('registry_independent_review_20261027.json',
                                     'release_independent_review_20261027.json'))
def test_run_card_rejects_changed_independent_measurements(tmp_path, receipt):
    copy_site_sources(tmp_path)
    path = tmp_path / 'evidence' / receipt
    record = json.loads(path.read_text())
    if receipt.startswith('registry'):
        record['lattice_capacity']['covered_cells'] -= 1
    else:
        record['artifacts'][0]['lattice_overlap_3px'] = 0.5
    path.write_text(json.dumps(record))
    run = subprocess.run([sys.executable, str(tmp_path / 'scripts/build_run_card.py')],
                         cwd=tmp_path, capture_output=True, text=True, timeout=25)
    assert run.returncode != 0 and 'Independent recheck changed a measurement' in run.stderr


def test_builder_replaces_legacy_dphs_html_before_publication(tmp_path):
    copy_site_sources(tmp_path)
    for name in ('index.html', 'executive-summary.html', 'how-to-submit.html'):
        (tmp_path / 'docs/dphs' / name).write_text('<h1>Exact path past 0.4544</h1>')
    run = subprocess.run([sys.executable, str(tmp_path / 'scripts/build_release.py')],
                         cwd=tmp_path, capture_output=True, text=True, timeout=25)
    assert run.returncode == 0, run.stderr
    for name in ('index.html', 'executive-summary.html', 'how-to-submit.html'):
        text = (tmp_path / 'docs/dphs' / name).read_text().lower()
        assert 'exact path past' not in text and 'do not submit' in text


def test_builder_refuses_if_historical_artifact_no_longer_matches_triage(tmp_path):
    copy_site_sources(tmp_path)
    artifact = tmp_path / 'docs/downloads/wbg2-dz16-n34500-20261027T000000Z-8e4646cf-zeros.tif'
    artifact.write_bytes(artifact.read_bytes() + b'tamper')
    result = subprocess.run([sys.executable, str(tmp_path / 'scripts/build_site.py')],
                            cwd=tmp_path, capture_output=True, text=True, timeout=15)
    assert result.returncode != 0 and 'Changed or multiply-listed research artifact' in result.stderr


def test_builder_refuses_tampered_final_card_even_if_legacy_card_is_negative(tmp_path):
    copy_site_sources(tmp_path)
    card_path = tmp_path / 'evidence/RUN_CARD_FINAL.json'
    card = json.loads(card_path.read_text())
    card['ok_to_submit'] = True
    card_path.write_text(json.dumps(card))
    result = subprocess.run([sys.executable, str(tmp_path / 'scripts/build_site.py')],
                            cwd=tmp_path, capture_output=True, text=True, timeout=15)
    assert result.returncode != 0 and 'negative-only dashboard refuses to publish' in result.stderr

def test_registered_candidate_is_the_only_publishable_owned_download(tmp_path):
    """Both lanes publish through one register; forged registrations fail closed."""
    sys.path.insert(0, str(ROOT / 'src'))
    from wbggems.release import approved_candidates, validate_negative_html

    register = json.loads((ROOT / 'config/release_register.json').read_text())
    edti = next(c for c in register['candidates'] if c['lane'] == 'WBG4-EDTI')
    art = (ROOT / edti['path']).read_bytes()

    def build(destination, record=None):
        for candidate in register['candidates']:
            for key in ('path', 'zip', 'run_card', 'holdout_evidence', 'uniqueness_evidence'):
                if not candidate.get(key):
                    continue
                target = destination / candidate[key]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / candidate[key]).read_bytes())
        (destination / 'config').mkdir(parents=True, exist_ok=True)
        payload = record or register
        (destination / 'config/release_register.json').write_text(json.dumps(payload))

    # Both lanes are registered, and each resolves to real bytes.
    built = tmp_path / 'ok'
    build(built)
    approved = approved_candidates(built)
    expected = {c['path'] for c in register['candidates']}
    expected |= {c['zip'] for c in register['candidates'] if c.get('zip')}
    assert set(approved) == expected
    for rel in approved:
        if rel.endswith('.tif'):
            assert digest_of(built / rel) == approved[rel]['sha256']

    # A linked page is allowed for a registered artifact, refused for anything else.
    def page(destination, name, label):
        body = (f'<html><body><h1>Status</h1><a href="https://github.com/'
                f'wingbangboozle1-lang/WBGGEMSDOE2/blob/main/artifacts/wbg4/{name}.tif?raw=1">'
                f'{label}</a></body></html>')
        (destination / 'docs').mkdir(parents=True, exist_ok=True)
        (destination / 'docs/index.html').write_text(body)

    page(built, Path(edti['path']).stem, 'Download the submission TIF')
    validate_negative_html(built)

    unregistered = tmp_path / 'unregistered'
    build(unregistered)
    page(unregistered, 'some-other-zeros', 'Download the submission TIF')
    with pytest.raises(ValueError, match='Unqualified owned research download'):
        validate_negative_html(unregistered)

    tampered = tmp_path / 'tampered'
    build(tampered)
    (tampered / edti['path']).write_bytes(art[:-1] + b'\x00')
    with pytest.raises(ValueError, match='Registered candidate bytes changed'):
        approved_candidates(tampered)

    missing = tmp_path / 'missing'
    build(missing)
    (missing / edti['run_card']).unlink()
    with pytest.raises(ValueError, match='Registered candidate evidence missing'):
        approved_candidates(missing)


def digest_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
