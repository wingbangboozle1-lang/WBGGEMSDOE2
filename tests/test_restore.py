import hashlib
from restore_public_mirrors import file_hash, verified


def test_git_blob_hash_and_bad_size(tmp_path):
    f = tmp_path / 'blob'
    f.write_bytes(b'hello\n')
    blob = hashlib.sha1(b'blob 6\0hello\n').hexdigest()
    sha = hashlib.sha256(b'hello\n').hexdigest()
    assert file_hash(f, 'sha1', git_blob=True) == blob
    assert verified(f, 6, blob=blob, sha256=sha)
    assert not verified(f, 7, blob=blob, sha256=sha)
    assert not verified(f, 6, blob='f' * 40, sha256=sha)
