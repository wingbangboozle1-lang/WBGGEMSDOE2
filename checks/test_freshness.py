from types import SimpleNamespace
import pytest
import refresh_registry_refs as freshness

ROW={'site':'GEMSDOE24','repository':'buffedlizard55-lab/GEMSDOE24','ref':'a'*40}


def test_changed_head_only_reports_freshness_not_new_raster_audit(monkeypatch):
    monkeypatch.setattr(freshness.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=0,stdout='b'*40+'\n'))
    r=freshness.head(ROW)
    assert r['changed'] and r['current_head']=='b'*40
    assert r['audited_ref']=='a'*40 and r['status']=='checked'


def test_network_failure_is_unknown_not_current(monkeypatch):
    monkeypatch.setattr(freshness.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=1,stdout=''))
    r=freshness.head(ROW)
    assert r['changed'] is None and r['status']=='unknown'


def test_rejects_unexpected_repositories():
    with pytest.raises(ValueError):
        freshness.head({'site':'x','repository':'someone/else','ref':'a'*40})
