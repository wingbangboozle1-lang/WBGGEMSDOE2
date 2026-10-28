"""Checkout diagnostics must never turn a byte-hash pass into an approval."""
import copy
import json
from pathlib import Path
import sys

import pytest

from wbggems.readiness import inspect_checkout, inspect_file, render_readiness
from wbggems.release import digest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import check_readiness


def test_file_missing_changed_verified(tmp_path):
    path = tmp_path / 'input'
    expected = 'a' * 64
    assert inspect_file(tmp_path, 'input', expected)['status'] == 'missing'
    path.write_bytes(b'input')
    assert inspect_file(tmp_path, 'input', expected)['status'] == 'changed'
    row = inspect_file(tmp_path, 'input', digest(path))
    assert row['status'] == 'verified'
    assert row['actual_sha256'] == row['expected_sha256']


def test_escape_is_rejected_including_symlink(tmp_path):
    root = tmp_path / 'checkout'
    root.mkdir()
    (tmp_path / 'external').write_text('outside')
    for relative in ('../external', str(tmp_path / 'external')):
        with pytest.raises(ValueError, match='escapes'):
            inspect_file(root, relative, 'a' * 64)
    (root / 'link').symlink_to(tmp_path / 'external')
    with pytest.raises(ValueError, match='escapes'):
        inspect_file(root, 'link', 'a' * 64)


def test_diagnostic_is_non_authorizing_and_inventory_is_byte_bound():
    report = inspect_checkout(ROOT)
    assert report['ok_to_submit'] is False
    assert report['research_launch_authorized'] is False
    assert report['new_raster'] is None and report['leaderboard_estimate'] is None
    assert report['experiments_run'] == report['weekly_slots_used'] == 0
    assert report['existing_research_inventory'] == {
        'tif_paths': 14, 'distinct_tif_hashes': 12, 'zip_paths': 11,
        'all_rejected_by_literal_overlap': True,
    }
    assert {r['status'] for r in report['gates']} <= {'verified', 'blocked', 'not-run'}
    assert report['sources']['evidence/release_audit.json'] == digest(ROOT / 'evidence/release_audit.json')


def test_even_all_available_files_cannot_clear_science_registry_or_selector(monkeypatch):
    monkeypatch.setattr('wbggems.readiness.inspect_file', lambda *args: {'status': 'verified'})
    report = inspect_checkout(ROOT)
    gates = {r['id']: r['status'] for r in report['gates']}
    assert gates['shared-code'] == gates['mirror-inputs'] == gates['raw-band-cache'] == 'verified'
    assert gates['registry'] == gates['selector'] == gates['shared-format'] == 'blocked'
    assert gates['scientific-validation'] == 'not-run'
    assert report['ok_to_submit'] is report['research_launch_authorized'] is False


def test_html_escapes_and_labels_snapshot_not_live():
    report = inspect_checkout(ROOT)
    report['gates'][0]['detail'] = '<script>alert(1)</script>'
    html = render_readiness(report)
    assert '<script>' not in html and '&lt;script&gt;' in html
    assert 'DO NOT SUBMIT' in html
    assert 'Dated local checkout snapshot' in html
    assert 'HOLDOUT-DTI' in html and 'paired spatial confidence interval' in html


def test_cli_default_and_check_exit_codes(tmp_path, monkeypatch):
    report = inspect_checkout(ROOT)
    monkeypatch.setattr(check_readiness, 'ROOT', tmp_path)
    monkeypatch.setattr(check_readiness, 'inspect_checkout', lambda _: copy.deepcopy(report))
    assert check_readiness.main([]) == 0
    assert check_readiness.main(['--check']) == 2
    assert json.loads((tmp_path / 'evidence/checkout_readiness.json').read_text()) == report
    assert (tmp_path / 'docs/readiness.html').is_file()


def test_corrupt_release_never_writes_diagnostic(tmp_path, monkeypatch):
    monkeypatch.setattr(check_readiness, 'ROOT', tmp_path)
    def fail(_):
        raise ValueError('changed artifact inventory')
    monkeypatch.setattr(check_readiness, 'inspect_checkout', fail)
    assert check_readiness.main([]) == 1
    assert not (tmp_path / 'docs/readiness.html').exists()


def test_home_banner_distinguishes_reported_science_and_saved_byte_measurement():
    html = (ROOT / 'docs/index.html').read_text()
    assert 'SOURCE-REPORTED HOLDOUT-DTI 0.173477' in html
    assert 'the campaign and its canaries were not independently replayed' in html
    assert '99.836% of this file' in html and 'registered binary lattice' in html
    assert '99.94% vs' not in html
    assert 'Why 0.2778 won' not in html
    assert 'href="readiness.html"' in html
