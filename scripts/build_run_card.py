#!/usr/bin/env python3
"""Validate the negative card and bind exact portable forensic outputs; no new run."""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
card_path = ROOT / 'evidence/run_card.json'
card = json.loads(card_path.read_text())
audit = json.loads((ROOT / 'evidence/registry_audit.json').read_text())
parallel = json.loads((ROOT / 'docs/data/portfolio.json').read_text())
review = json.loads((ROOT / 'evidence/parallel_review.json').read_text())
corroboration = json.loads((ROOT / 'evidence/parallel_candidate_audit.json').read_text())
conduit = json.loads((ROOT / 'evidence/conduit_review.json').read_text())
lat = audit['lattice_capacity']
dense = audit['dense_probability_prior']
# Stop before changing published files if the card is inconsistent with either
# independently reopened audit or any null/non-promotion invariant.
if not (card['verdict'] == 'negative' and card['ok_to_submit'] is False
        and card['ok_to_download_new_tif'] is False and card['raster_sha256'] is None
        and card['submission_name'] is None and card['submission_note'] is None
        and card['holdout']['dti'] is None and card['holdout']['ci95'] is None
        and card['holdout_dti']['value'] is None and card['holdout_dti']['ci95'] is None
        and card['experiment_count'] == 0 and card['weekly_submission_slots_used'] == 0
        and card['uniqueness']['candidate_surface_correlation'] is None
        and card['uniqueness']['candidate_final_overlap'] is None
        and card['uniqueness']['minimum_overlap_bound'] == lat['minimum_overlap']
        and card['registry']['binary_lattice_minimum_overlap_at_budget'] == lat['minimum_overlap']
        and lat['minimum_overlap'] == parallel['literal_registry_witness']['minimum_possible_overlap_at_example_budget']
        and dense['full_footprint_positive'] is True
        and parallel['dense_probability_witness']['universal_overlap_blocker'] is True
        and card['registry']['dense_probability_prior_full_footprint'] is True
        and review['ok_to_submit'] is False
        and corroboration['ok_to_submit'] is False
        and corroboration['candidate_sha256'] == review['sha256']
        and corroboration['witnesses']['lattice']['overlap_fraction'] == review['literal_overlap_3px']['lattice']
        and corroboration['format']['dataset_mask_invalid_inside_footprint'] == review['format']['masked_inside']
        and review['literal_overlap_3px']['lattice'] > .7
        and review['format']['format_valid_against_reference'] is False
        and card['parallel_session']['rejected_candidate_sha256'] == review['sha256']
        and card['parallel_session']['lattice_overlap_3px'] == review['literal_overlap_3px']['lattice']
        and card['parallel_session']['continuous_prior_overlap_3px'] == review['literal_overlap_3px']['continuous_prior']
        and card['parallel_session']['masked_inside_footprint'] == review['format']['masked_inside']
        and card['parallel_session']['source_reported_holdout'] == review['source_reported_holdout']
        and card['parallel_session']['ok_to_submit'] is False
        and conduit['ok_to_submit'] is False and conduit['holdout_dti'] is None
        and conduit['preplacement_surface_correlation'] is None
        and conduit['witnesses']['13GEMSDOE']['source_threshold_ge_0_5']['fraction'] > .7
        and card['conduit_parallel_session']['rejected_candidate_sha256'] == conduit['sha256']
        and card['conduit_parallel_session']['lattice_overlap_3px_source_threshold'] == conduit['witnesses']['13GEMSDOE']['source_threshold_ge_0_5']['fraction']
        and card['conduit_parallel_session']['continuous_prior_overlap_3px'] == conduit['witnesses']['17GEMSDOE_dense_prior']['source_threshold_ge_0_5']['fraction']
        and card['conduit_parallel_session']['holdout_dti'] is None
        and card['conduit_parallel_session']['preplacement_surface_correlation'] is None
        and card['conduit_parallel_session']['ok_to_submit'] is False
        and len(card['note']) <= 140):
    raise ValueError('Run-card evidence changed; manual review required before publication')
import sys
sys.path.insert(0, str(ROOT / 'src'))
from wbggems.release import CANONICAL_RUN_CARDS, digest, load_negative_release
release = load_negative_release(ROOT)
if any(row['lattice_overlap_3px'] <= 0.7 for row in release['artifacts']):
    raise ValueError('A saved TIFF no longer has a binary-lattice duplicate witness; review the release decision')


def local_input_snapshot(root: Path, existing: dict) -> dict:
    """Describe what is actually available now; historic receipts do not imply persistence."""
    def inspect(relative: str, expected_sha256: str | None = None,
                expected_bytes: int | None = None) -> dict:
        rel = Path(relative)
        if rel.is_absolute() or '..' in rel.parts:
            raise ValueError(f'Unsafe local input path: {relative}')
        path = root / rel
        present = path.is_file() and not path.is_symlink()
        actual_sha256 = digest(path) if present else None
        actual_bytes = path.stat().st_size if present else None
        hash_match = (actual_sha256 == expected_sha256) if expected_sha256 else present
        size_match = (actual_bytes == expected_bytes) if expected_bytes is not None else present
        return {
            'path': rel.as_posix(), 'present': present,
            'expected_sha256': expected_sha256, 'sha256': actual_sha256,
            'expected_bytes': expected_bytes, 'bytes': actual_bytes,
            'hash_match': hash_match, 'size_match': size_match,
            'verified': bool(present and hash_match and size_match),
        }

    prep = json.loads((root / 'evidence/data_preparation.json').read_text())
    official_inputs = [inspect(row['path'], row['sha256'], row['bytes'])
                       for row in prep.get('files', [])]
    if len(official_inputs) != 4:
        raise ValueError('Expected four pinned owner-mirror competition input records')

    mirror = inspect('data/training_features_mirror.tif',
                     existing['source_sha256'], existing['source_bytes'])
    cache_receipt_path = root / existing['feature_cache_receipt']
    cache_receipt = json.loads(cache_receipt_path.read_text())
    expected_bands = cache_receipt.get('bands', [])
    if len(expected_bands) != 19:
        raise ValueError('Expected 19 raw-band cache hash receipts')
    band_checks = [inspect(row['cache_file'], row['sha256']) for row in expected_bands]
    band_present_count = sum(row['present'] for row in band_checks)
    band_verified_count = sum(row['verified'] for row in band_checks)

    pins = json.loads((root / 'registry/template_pins.json').read_text())
    required_upstream = ('src/gems57/evaluate_holdout.py',
                         'src/gems57/submission_writer.py')
    pin_by_path = {row['upstream_path']: row for row in pins['files']}
    template_roots = ('.cache/shared-template', 'data/shared_template')
    template_checks = []
    for template_root in template_roots:
        for upstream in required_upstream:
            pin = pin_by_path.get(upstream)
            if pin is None:
                raise ValueError(f'Missing shared-template hash pin: {upstream}')
            template_checks.append(inspect(
                f'{template_root}/{upstream}', pin['sha256'], pin['bytes']))
    template_verified = any(
        all(row['verified'] for row in template_checks[i:i + len(required_upstream)])
        for i in (0, len(required_upstream)))

    derived_bank_paths = []
    for parent in (root / '.cache', root / 'data'):
        if parent.is_dir():
            derived_bank_paths.extend(str(path.relative_to(root)) for path in parent.rglob('bank_u8.npy')
                                      if path.is_file() and not path.is_symlink())
    # Check the official-label-free raw mirror aliases without assuming that a
    # prior owner mirror has organizer provenance.
    small_mirrors = [
        inspect('data/reference_grid_mirror.tif',
                '2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc',
                1_599_597),
        inspect('data/existing_faults_mirror.tif',
                '7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093',
                425_830),
    ]

    missing_official = sum(not row['verified'] for row in official_inputs)
    verified_official = len(official_inputs) - missing_official
    verified_small = sum(row['verified'] for row in small_mirrors)
    shared_tools = 'verified at a pinned path' if template_verified else 'not verified in the local cache'
    bank_text = 'found' if derived_bank_paths else 'not present'
    summary = (
        f"At check time, {verified_official}/{len(official_inputs)} pinned data/official owner-mirror "
        f"inputs are present and hash/size verified ({missing_official} missing or mismatched); "
        f"the full feature mirror is {'verified' if mirror['verified'] else 'not present or not verified'}; "
        f"{band_verified_count}/19 raw-band caches are present and hash verified "
        f"({band_present_count} files present); shared evaluator/writer code is {shared_tools}; "
        f"the derived feature bank is {bank_text}. {verified_small}/2 small audit mirrors are verified. "
        "These are owner-mirror bytes, not authenticated organizer downloads."
    )
    return {
        'checked_utc': datetime.now(timezone.utc).isoformat(),
        'summary': summary,
        'competition_inputs_from_prior_receipt': official_inputs,
        'full_feature_mirror': mirror,
        'raw_band_cache': {
            'directory': '.cache/features', 'expected_count': len(expected_bands),
            'present_count': band_present_count, 'verified_count': band_verified_count,
            'filenames': [Path(row['path']).name for row in band_checks if row['present']],
            'files': band_checks,
        },
        'shared_template': {
            'repository': pins['repository'], 'commit': pins['ref'],
            'required_tools_verified': template_verified,
            'required_files': template_checks,
        },
        'derived_shared_feature_bank': {
            'available': bool(derived_bank_paths), 'paths': sorted(derived_bank_paths),
        },
        'small_audit_mirrors': small_mirrors,
        'organizer_authenticated': False,
    }


if (card['release_reconciliation']['owned_tif_paths'] != release['scope']['owned_tif_paths']
        or card['release_reconciliation']['distinct_raster_sha256'] != release['scope']['distinct_tif_sha256']):
    raise ValueError('Research inventory changed; review the canonical disposition')

availability = local_input_snapshot(ROOT, card['raw_feature_inputs'])
release_scope = release['scope']
zip_count = len(release['zip_archives'])
card['generated_utc'] = availability['checked_utc']
card['updated_utc'] = availability['checked_utc']
card['validator']['status'] = (
    f"No new raster generated. Independent readback covers {release_scope['owned_tif_paths']} TIFF paths / "
    f"{release_scope['distinct_tif_sha256']} distinct SHA-256 identities, {zip_count} ZIP archives, "
    f"and {release_scope['registry_rasters_opened']} pinned registry witnesses; each saved TIFF identity "
    "exceeds the 70% three-pixel overlap stop against the registered binary lattice. Format PASS is not organizer acceptance."
)
card['release_reconciliation']['owned_tif_paths'] = release_scope['owned_tif_paths']
card['release_reconciliation']['distinct_raster_sha256'] = release_scope['distinct_tif_sha256']
card['release_reconciliation']['pinned_witnesses'] = release_scope['registry_rasters_opened']
card['release_reconciliation']['zip_archives'] = zip_count
card['raw_feature_inputs']['status'] = availability['summary']
card['raw_feature_inputs']['current_availability'] = availability
card['raw_feature_inputs']['derived_shared_bank_available'] = availability['derived_shared_feature_bank']['available']
card['holdout']['status'] = (
    "NOT RUN: method lane remains unassigned and the literal preflight blocks candidate placement. "
    f"Current local-input check: {availability['summary']} No corrected-v2 holdout result exists."
)
card['holdout_dti']['reason'] = (
    "No assigned lane or complete current registry; no HOLDOUT-DTI was measured. "
    f"Current local-input check: {availability['summary']}"
)
# Derive exact existing-artifact diagnostics from the independently generated
# audit; never populate the null NEW-candidate or score fields.
card['existing_artifact_audit'] = {
    'evidence_class': release['evidence_class'],
    'source_path': 'evidence/release_audit.json',
    'source_sha256': digest(ROOT / 'evidence/release_audit.json'),
    'recorded_utc': release['generated_utc'],
    'scope': release['scope'],
    'reference': release['reference'],
    'artifacts': [{k:r[k] for k in ('path','aliases','sha256','positive_support_cells','validator',
                                   'strict_all_finite_validator','surface_rank_correlation',
                                   'final_rank_correlation','lattice_overlap_3px','maximum_overlap_3px',
                                   'duplicate_witnesses','leaderboard_score_estimate','ok_to_submit','verdict')}
                  for r in release['artifacts']],
    'zip_archives': release['zip_archives'],
}

text = json.dumps(card, indent=2, allow_nan=False) + '\n'
for rel in CANONICAL_RUN_CARDS:
    out = ROOT / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    print('Mirrored canonical card:', out)
