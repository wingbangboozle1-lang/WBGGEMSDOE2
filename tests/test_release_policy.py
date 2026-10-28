"""Publication is a byte-bound negative decision, never a slot selector.

Portable fixtures use the saved H3 TIFF/ZIP and real pin table. These tests check
receipt integrity; geophysical measurements are independently rerun by audit_release.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

import pytest

from wbggems.release import CANONICAL_RUN_CARDS, NEGATIVE_RESEARCH_CARDS, digest, load_negative_release, read_json, require_experiment_lane, validate_negative_html

ROOT = Path(__file__).resolve().parents[1]


def write_report(root, report):
    (root / 'evidence/release_audit.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')


@pytest.fixture
def receipt_root(tmp_path):
    (tmp_path / 'config').mkdir()
    (tmp_path / 'evidence').mkdir()
    shutil.copyfile(ROOT / 'config/registry_inputs.json', tmp_path / 'config/registry_inputs.json')
    report = deepcopy(read_json(ROOT / 'evidence/release_audit.json'))
    row = next(r for r in report['artifacts'] if 'h3-pack' in r['path'])
    report['artifacts'] = [row]
    report['zip_archives'] = [r for r in report['zip_archives'] if r['member_sha256'] == row['sha256']]
    for rel in [*row['aliases'], *(r['path'] for r in report['zip_archives'])]:
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, p)
    report['scope'].update(owned_tif_paths=len(row['aliases']), distinct_tif_sha256=1)
    write_report(tmp_path, report)
    # Independent recheck prevents a modified receipt from erasing a decisive
    # comparison while retaining some other negative witness.
    (tmp_path / 'evidence/release_independent_review_20261027.json').write_text(json.dumps(report))
    return tmp_path, report


def test_current_real_bytes_have_only_negative_decisions():
    report = load_negative_release(ROOT)
    assert report['scope']['owned_tif_paths'] == 11
    assert len(report['artifacts']) == 9 and len(report['zip_archives']) == 8
    assert report['scope']['registry_rasters_opened'] == 13
    assert all('17GEMSDOE_dense_prior' in r['duplicate_witnesses'] and r['ok_to_submit'] is False for r in report['artifacts'])
    distal = next(r for r in report['artifacts'] if r['path'].startswith('candidate/'))
    assert distal['lattice_overlap_3px'] < .70 and distal['maximum_overlap_3px'] == 1.0
    assert report['approved_submission'] is None and report['leaderboard_score_estimate'] is None
    assert report['scope']['new_candidate_experiments'] == report['scope']['weekly_slots_used'] == 0


def test_portable_negative_receipt_loads_without_ignored_training_data(receipt_root):
    root, _ = receipt_root
    assert not (root / 'data').exists()
    assert load_negative_release(root)['ok_to_submit'] is False


@pytest.mark.parametrize('section,key,value', [
    ('root', 'ok_to_submit', True), ('root', 'verdict', 'promote'),
    ('root', 'approved_submission', 'fake.tif'), ('root', 'leaderboard_score_estimate', .3),
    ('policy', 'witness_exemptions', ['13GEMSDOE']), ('policy', 'radius_px', 2),
    ('policy', 'overlap_stop_strictly_greater_than', .71),
    ('policy', 'absolute_rank_stop_strictly_greater_than', .95),
    ('scope', 'all_current_registry_rasters_checked', True),
    ('scope', 'new_candidate_experiments', 1), ('scope', 'weekly_slots_used', 1),
    ('scope', 'new_candidate_experiments', False), ('scope', 'registry_rasters_opened', 14),
    ('scope', 'registry_manifest_sha256', '0'*64),
    ('artifact', 'ok_to_submit', True), ('artifact', 'verdict', 'promote'),
    ('artifact', 'surface_rank_correlation', .1), ('artifact', 'final_rank_correlation', .1),
    ('artifact', 'leaderboard_score_estimate', .2), ('artifact', 'organizer_receipt', {'score':.3}),
    ('artifact', 'lattice_overlap_3px', .4), ('artifact', 'maximum_overlap_3px', .4),
])
def test_no_boolean_score_policy_or_scope_override(receipt_root, section, key, value):
    root, report = receipt_root
    target = report if section == 'root' else report['artifacts'][0] if section == 'artifact' else report[section]
    target[key] = value
    write_report(root, report)
    with pytest.raises(ValueError):
        load_negative_release(root)


def test_inventory_rejects_nested_symlink_directory_that_could_hide_rasters(receipt_root):
    root, report = receipt_root
    external = root / 'outside'; external.mkdir()
    (external / 'hidden.tif').write_bytes(b'unreviewed raster')
    alias = root / 'candidate' / 'hidden'
    alias.parent.mkdir(parents=True, exist_ok=True)
    alias.symlink_to(external, target_is_directory=True)
    write_report(root, report)
    with pytest.raises(ValueError, match='symlink director'):
        load_negative_release(root)


@pytest.mark.parametrize('mutation', ['missing', 'repeated', 'sha', 'url', 'support', 'threshold', 'boolean_overlap', 'outside_unit_interval'])
def test_witness_measurements_must_match_pins_and_literal_threshold(receipt_root, mutation):
    root, report = receipt_root
    row = report['artifacts'][0]
    c = row['comparisons'][-1]
    if mutation == 'missing': row['comparisons'].pop()
    elif mutation == 'repeated': row['comparisons'][0] = deepcopy(row['comparisons'][1])
    elif mutation == 'sha': c['sha256'] = '0'*64
    elif mutation == 'url': c['source'] = 'https://example.invalid/not-the-pinned-bytes'
    elif mutation == 'support': c['support_type'] = 'silently_thresholded_prior'
    elif mutation == 'threshold': c['duplicate_stop'] = False
    elif mutation == 'boolean_overlap': c['overlap_3px'] = True
    elif mutation == 'outside_unit_interval': c['overlap_3px'] = 1.1
    write_report(root, report)
    with pytest.raises(ValueError): load_negative_release(root)


def test_decisive_witness_cannot_be_erased_even_if_summary_is_rewritten(receipt_root):
    root, report = receipt_root
    row = report['artifacts'][0]
    c = next(c for c in row['comparisons'] if c['registry_id'] == '13GEMSDOE')
    c.update(overlap_3px=.69, duplicate_stop=False)
    row['duplicate_witnesses'].remove('13GEMSDOE')
    row['lattice_overlap_3px'] = .69
    write_report(root, report)
    with pytest.raises(ValueError, match='decisive'): load_negative_release(root)


@pytest.mark.parametrize('mutation', ['changed_bytes','missing_file','added_tif','added_tiff','upper_tif','added_zip','upper_zip','candidate_path','symlink','duplicate_alias'])
def test_exact_inventory_has_no_extension_case_or_alias_bypass(receipt_root, mutation):
    root, report = receipt_root
    row = report['artifacts'][0]
    p = root / row['path']
    if mutation == 'changed_bytes': p.write_bytes(p.read_bytes()+b'changed')
    elif mutation == 'missing_file': p.unlink()
    elif mutation in ('added_tif','added_tiff','upper_tif','added_zip','upper_zip'):
        name = {'added_tif':'new.tif','added_tiff':'new.tiff','upper_tif':'new.TIF','added_zip':'new.zip','upper_zip':'new.ZIP'}[mutation]
        (p.parent / name).write_bytes(b'unreviewed')
    elif mutation == 'candidate_path':
        (root / 'candidate').mkdir()
        (root / 'candidate/unreviewed.tif').write_bytes(b'unreviewed')
    elif mutation == 'symlink':
        alias = root / row['aliases'][-1]
        alias.unlink(); alias.symlink_to(p)
    elif mutation == 'duplicate_alias': row['aliases'].append(row['path'])
    write_report(root, report)
    with pytest.raises(ValueError): load_negative_release(root)


@pytest.mark.parametrize('key', ['sha256', 'reference_sha256', 'submission_approval'])
def test_validator_cannot_attach_to_different_bytes_or_claim_approval(receipt_root, key):
    root, report = receipt_root
    report['artifacts'][0]['validator'][key] = True if key == 'submission_approval' else '0'*64
    write_report(root, report)
    with pytest.raises(ValueError): load_negative_release(root)


@pytest.mark.parametrize('mutation', ['extra_member','wrong_member_bytes','subdirectory','wrong_name','duplicate_zip'])
def test_zip_member_bytes_names_and_inventory_are_rechecked(receipt_root, mutation):
    root, report = receipt_root
    row = report['zip_archives'][0]
    p = root / row['path']
    if mutation == 'extra_member':
        with zipfile.ZipFile(p,'a') as z: z.writestr('unreviewed.txt','extra payload')
    elif mutation == 'wrong_member_bytes':
        with zipfile.ZipFile(p,'w') as z: z.writestr(row['member'], b'not the audited TIFF')
    elif mutation == 'subdirectory':
        data = (root / report['artifacts'][0]['path']).read_bytes()
        row['member'] = 'subdir/'+row['member']
        with zipfile.ZipFile(p,'w') as z: z.writestr(row['member'], data)
    elif mutation == 'wrong_name': row['member'] = 'not-the-member.tif'
    elif mutation == 'duplicate_zip': report['zip_archives'].append(deepcopy(row))
    row['sha256'] = digest(p)
    write_report(root, report)
    with pytest.raises(ValueError): load_negative_release(root)


@pytest.mark.parametrize('text', ['{"x":NaN}', '{"x":Infinity}', '{"x":-Infinity}', '{"x":false,"x":true}'])
def test_strict_json_rejects_nonstandard_numbers_and_duplicate_keys(tmp_path, text):
    p = tmp_path/'bad.json'; p.write_text(text)
    with pytest.raises(ValueError): read_json(p)


def test_all_published_json_is_standard_not_the_historical_archive():
    paths = [*ROOT.joinpath('docs/data').rglob('*.json'), *ROOT.joinpath('site/data').rglob('*.json'), *ROOT.joinpath('data_public').glob('*.json')]
    for path in paths:
        read_json(path)


def test_no_current_run_card_alias_can_retain_old_approval():
    expected = (ROOT / 'evidence/run_card.json').read_bytes()
    for rel in ('docs/data/run-card.json','docs/data/run_card.json','site/data/run_card.json','docs/RUN_CARD.json','docs/data/run-card-current.json','data_public/run_card.json'):
        assert (ROOT / rel).read_bytes() == expected, rel
    c = read_json(ROOT / 'evidence/run_card.json')
    assert c['raster_sha256'] is None and c['release_reconciliation']['approved_submission'] is None
    assert c['holdout']['dti'] is None and c['release_reconciliation']['corrected_msptcd_holdout'] is None
    assert len(c['note']) <= 140


@pytest.mark.parametrize('command', ['make_candidate.py','generate_h3_pack.py','write_h3_submission.py','final_audit.py','uniqueness_audit.py','run_wbg2_msptcd.py'])
def test_legacy_campaigns_stop_before_any_evidence_or_artifact_write(command):
    files = [ROOT / 'evidence/run_card.json', ROOT / 'evidence/RUN_CARD_MSPTCD.json', ROOT / 'evidence/release_audit.json', ROOT / 'data_public/candidate.json']
    before = {p: digest(p) for p in files}
    result = subprocess.run([sys.executable, str(ROOT/'scripts'/command)],capture_output=True,text=True,timeout=20)
    assert result.returncode != 0 and 'STOP' in result.stdout+result.stderr
    assert {p:digest(p) for p in files} == before


@pytest.mark.parametrize('status,lane', [('UNASSIGNED',None),('ASSIGNED','other-lane'),('ASSIGNED','wbg2-msptcd')])
def test_even_lane_assignment_is_not_a_registry_or_selector_override(tmp_path, status, lane):
    (tmp_path/'config').mkdir()
    (tmp_path/'config/research_hypotheses.json').write_text(json.dumps({'method_lane':{'status':status,'lane_id':lane}}))
    with pytest.raises(RuntimeError,match='STOP'):
        require_experiment_lane('wbg2-msptcd',tmp_path)


def test_all_legacy_entry_pages_show_same_block_and_research_only_links():
    for rel in ('docs/index.html','docs/release.html','docs/submit/index.html','docs/submission/index.html','docs/submission/executive-summary.html'):
        text = (ROOT / rel).read_text()
        assert 'data-release-status="blocked"' in text and 'DO NOT SUBMIT' in text
        assert 'No submission file' in text
        assert 'approved to download and submit' not in text.lower()
    for site in ('24','25','27','28','30','31','32','33','36'):
        text = (ROOT / f'docs/sites/GEMSDOE{site}.html').read_text()
        assert 'USER-REPORTED' in text and 'DO NOT SUBMIT' in text
        assert 'Estimated leaderboard score: unavailable.' in text
        assert 'Download historical TIFF for research only' in text


def test_reviewed_historical_metrics_are_not_relabelled_as_v2_validation():
    card = read_json(ROOT / 'evidence/RUN_CARD_MSPTCD.json')
    assert card['post_review']['promotion_evidence_valid'] is False
    assert card['post_review']['independently_reproduced_in_this_review'] is False
    assert card['post_review']['current_feature_version'] == 'msptcd-v2-axial-cos-squared'
    assert card['ok_to_submit'] is False
    results = read_json(ROOT / 'evidence/wbg2_msptcd_results.json')
    text = (ROOT / 'research/msptcd_findings.md').read_text()
    for arm in results['holdout_pooled']['scores'].values():
        assert f'{arm["dti"]:.6f}' in text
        assert f'[{arm["ci95"][0]:.6f}, {arm["ci95"][1]:.6f}]' in text


def test_no_stale_positive_heading_or_unqualified_owned_download_anywhere():
    from html.parser import HTMLParser
    from urllib.parse import urlsplit

    class Copy(HTMLParser):
        def __init__(self):
            super().__init__(); self.anchor=None; self.heading=None; self.anchors=[]; self.headings=[]; self.words=[]
        def handle_starttag(self, tag, attrs):
            attrs=dict(attrs)
            if tag=='a': self.anchor=[attrs.get('href',''), '']
            if tag in ('h1','h2','h3'): self.heading=['']
        def handle_data(self, text):
            self.words.append(text)
            if self.anchor is not None: self.anchor[1]+=text
            if self.heading is not None: self.heading[0]+=text
        def handle_endtag(self, tag):
            if tag=='a' and self.anchor is not None: self.anchors.append(self.anchor); self.anchor=None
            if tag in ('h1','h2','h3') and self.heading is not None: self.headings.append(self.heading[0]); self.heading=None

    for path in [*ROOT.joinpath('docs').rglob('*.html'), *ROOT.joinpath('site').rglob('*.html')]:
        parsed=Copy(); parsed.feed(path.read_text())
        assert not {'download and submit','submit this file','cleared for submission'} & {h.strip().lower() for h in parsed.headings}, path
        assert 'cleared exactly one' not in ' '.join(parsed.words).lower(), path
        for href, label in parsed.anchors:
            parts=urlsplit(href)
            if parts.scheme or Path(parts.path).suffix.lower() not in ('.tif','.tiff','.zip'): continue
            assert 'research' in label.lower() and 'DO NOT SUBMIT' in label, (path,href,label)


@pytest.mark.parametrize('relative', ['docs/rogue.tif','site/rogue.tiff','docs/data/unreviewed.zip','site/assets/raw.TIF'])
def test_published_assets_cannot_hide_an_unreviewed_raster_outside_downloads(receipt_root, relative):
    root, _ = receipt_root
    p=root/relative; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(b'unreviewed')
    with pytest.raises(ValueError): load_negative_release(root)


def test_one_canonical_run_card_contains_exact_existing_byte_validator_outputs():
    card = read_json(ROOT/'evidence/run_card.json')
    report = read_json(ROOT/'evidence/release_audit.json')
    bound = card['existing_artifact_audit']
    assert bound['source_sha256'] == digest(ROOT/'evidence/release_audit.json')
    assert bound['scope'] == report['scope']
    assert bound['zip_archives'] == report['zip_archives']
    assert [r['validator'] for r in bound['artifacts']] == [r['validator'] for r in report['artifacts']]
    assert [r['strict_all_finite_validator'] for r in bound['artifacts']] == [r['strict_all_finite_validator'] for r in report['artifacts']]
    assert card['raster_sha256'] is None and card['holdout']['dti'] is None


@pytest.mark.parametrize('relative', [*CANONICAL_RUN_CARDS, *NEGATIVE_RESEARCH_CARDS])
def test_a_parallel_current_card_cannot_grant_its_own_approval(receipt_root, relative):
    root, _ = receipt_root
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'verdict':'negative', 'ok_to_submit':True}))
    with pytest.raises(ValueError, match='negative-only dashboard refuses to publish'):
        load_negative_release(root)


def test_all_nine_current_run_card_aliases_are_the_canonical_negative_card():
    canonical = read_json(ROOT / 'evidence/run_card.json')
    for relative in CANONICAL_RUN_CARDS:
        assert read_json(ROOT / relative) == canonical, relative


@pytest.mark.parametrize('filename', ['run_wbg2_cbs.py','build_cbs_final.py',
    'run_campaign_20261027.py','novelty_refine.py','soft_novelty_refine.py',
    'audit_final_candidate.py','estimate_candidate.py'])
def test_concurrent_lane_entrypoints_cannot_overwrite_research_or_project_a_score(filename):
    before = digest(ROOT / 'evidence/run_card.json')
    result = subprocess.run([sys.executable, str(ROOT/'scripts'/filename)],
                            capture_output=True, text=True, timeout=10)
    assert result.returncode != 0 and 'STOP' in result.stdout+result.stderr
    assert digest(ROOT / 'evidence/run_card.json') == before


@pytest.mark.parametrize('body', [
    '<h3>Download and submit</h3>',
    '<b>1 FILE CLEARED</b>',
    '<a href="downloads/test.tif">Download</a>',
    '<a href="https://github.com/wingbangboozle1-lang/WBGGEMSDOE2/blob/main/downloads/test.tif?raw=1">Research only</a>',
])
def test_portable_pages_copy_guard_blocks_legacy_approval_or_unqualified_download(tmp_path, body):
    (tmp_path/'docs').mkdir()
    (tmp_path/'docs/legacy.html').write_text(body)
    with pytest.raises(ValueError):
        validate_negative_html(tmp_path)


def test_portable_pages_guard_accepts_unambiguous_research_copy(tmp_path):
    (tmp_path/'docs').mkdir()
    (tmp_path/'docs/legacy.html').write_text('<h3>Research only</h3><a href="downloads/test.tif">Research TIFF — DO NOT SUBMIT</a>')
    validate_negative_html(tmp_path)


def test_dashboard_audit_timestamp_is_bound_to_the_release_receipt_not_old_portfolio():
    from datetime import datetime, timezone
    receipt = read_json(ROOT / 'evidence/release_audit.json')
    expected = datetime.fromisoformat(receipt['generated_utc']).astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    home = (ROOT / 'docs/index.html').read_text()
    assert f'Release-byte audit<br><strong>{expected}</strong>' in home
