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
