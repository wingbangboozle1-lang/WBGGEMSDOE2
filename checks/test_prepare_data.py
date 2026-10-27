import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest
import prepare_data


def test_good_cached_file_is_never_downloaded(tmp_path, monkeypatch):
    path=tmp_path/'x';path.write_bytes(b'known')
    expected=hashlib.sha256(b'known').hexdigest()
    monkeypatch.setattr(prepare_data.subprocess, 'run', lambda *a,**k: pytest.fail('unexpected network call'))
    prepare_data.fetch_checked('a/b','ref','x',path,expected)
    assert path.read_bytes()==b'known'


def test_hash_failure_does_not_replace_original_or_leave_partial(tmp_path,monkeypatch):
    path=tmp_path/'x';path.write_bytes(b'original')
    def fake_run(*args,stdout,**kwargs):
        stdout.write(b'bad download')
        return SimpleNamespace(returncode=0,stderr=b'')
    monkeypatch.setattr(prepare_data.subprocess,'run',fake_run)
    with pytest.raises(ValueError,match='Hash mismatch'):
        prepare_data.fetch_checked('a/b','ref','x',path,hashlib.sha256(b'right').hexdigest())
    assert path.read_bytes()==b'original'
    assert not (tmp_path/'x.partial').exists()


def test_missing_template_is_fail_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(prepare_data,'TEMPLATE',tmp_path/'empty')
    with pytest.raises(FileNotFoundError):
        prepare_data.restore_template(False)


def _pins(data: bytes):
    h = hashlib.sha256(data).hexdigest()
    return {f'data/official/{name}': h for name in (
        'labels.tif', 'existing_faults.tif', 'sample_submission.tif', 'training_features.tif')}


def test_existing_official_bytes_are_never_replaced_or_partially_touched(tmp_path):
    root = tmp_path / 'data' / 'official'
    root.mkdir(parents=True)
    (root / 'sample_submission.tif').write_bytes(b'actual user sample')
    with pytest.raises(ValueError, match='Refusing to overwrite'):
        prepare_data.guard_existing_mirrors(tmp_path, _pins(b'owner mirror'))
    assert (root / 'sample_submission.tif').read_bytes() == b'actual user sample'
    assert not (root / 'labels.tif').exists()


def test_guard_allows_matching_bytes_and_rejects_dangling_links(tmp_path):
    root = tmp_path / 'data' / 'official'
    root.mkdir(parents=True)
    (root / 'sample_submission.tif').write_bytes(b'mirror')
    prepare_data.guard_existing_mirrors(tmp_path, _pins(b'mirror'))
    (root / 'training_features.tif').symlink_to('missing.tif')
    with pytest.raises(ValueError, match='Refusing to overwrite'):
        prepare_data.guard_existing_mirrors(tmp_path, _pins(b'mirror'))
    assert (root / 'training_features.tif').is_symlink()


def test_atomic_install_does_not_replace_a_concurrent_arrival(tmp_path):
    staged = tmp_path / 'staged'
    target = tmp_path / 'target'
    staged.write_bytes(b'mirror')
    expected = hashlib.sha256(b'mirror').hexdigest()
    target.write_bytes(b'new user data')
    with pytest.raises(ValueError, match='concurrently created'):
        prepare_data.install_without_overwrite(staged, target, expected)
    assert target.read_bytes() == b'new user data'
    target.unlink()
    prepare_data.install_without_overwrite(staged, target, expected)
    assert target.read_bytes() == b'mirror'
    prepare_data.install_without_overwrite(staged, target, expected)  # idempotent


def test_shared_feature_assembly_is_isolated_and_no_clobber(tmp_path, monkeypatch):
    monkeypatch.setattr(prepare_data, 'ROOT', tmp_path)
    content = b'fake but hash-checked feature data'
    expected = hashlib.sha256(content).hexdigest()
    target = tmp_path / 'data/official/training_features.tif'
    calls = []
    def assemble(root):
        calls.append(root)
        assert root != tmp_path
        assert (root / '.cache/source_parts').is_symlink()
        (root / '.cache/training_features.tif').write_bytes(content)
    prepare_data.stage_feature_mirror(SimpleNamespace(assemble_features=assemble), target, expected)
    assert target.read_bytes() == content
    assert len(calls) == 1
    assert not calls[0].exists()  # temporary staging directory removed
    target.write_bytes(b'user data')
    with pytest.raises(ValueError, match='concurrently created'):
        prepare_data.stage_feature_mirror(SimpleNamespace(assemble_features=assemble), target, expected)
    assert target.read_bytes() == b'user data'
