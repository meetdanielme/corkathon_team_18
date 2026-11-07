import pytest

from footfall.remote import Connection
from footfall import db


def test_remote_driver_preserves_rows_drafts_and_reconnect(tmp_path):
    # The driver has no wheel for Python 3.13+ and building it needs Rust, so skip rather than
    # fail where it is absent. Vercel pins 3.12, so this still runs on the deployment target.
    libsql = pytest.importorskip("libsql", reason="libsql not installed; remote/Turso path not exercised")
    path = str(tmp_path / 'remote.sqlite3')
    with Connection(libsql.connect(path)) as c:
        db.init(c)
        db.seed(c)
        assert db.get_business(c)['radius_m'] == 1000
        did = db.create_draft(c, 'sample', 'Supplier', 'Original', 'template')
    with Connection(libsql.connect(path)) as c:
        assert db.get_draft(c, did)['text'] == 'Original'
        db.approve_draft(c, did)
        assert db.get_draft(c, did)['approved_at']
        db.update_draft(c, did, 'Edited')
        assert db.get_draft(c, did)['approved_at'] is None
        assert c.execute('select count(*) as n from drafts').fetchone()[0] == 1


def test_allowance_is_shared_and_stops_before_sdk_call(tmp_path, monkeypatch):
    from footfall.llm import LLM
    import pytest
    monkeypatch.setenv('FOOTFALL_AZURE_CALL_LIMIT', '1')
    monkeypatch.setenv('FOOTFALL_DB', str(tmp_path / 'allowance.sqlite3'))
    with db.connect(str(tmp_path / 'allowance.sqlite3')) as c:
        c.execute('CREATE TABLE ai_allowance (id INTEGER PRIMARY KEY, calls INTEGER NOT NULL)')
        c.execute('INSERT INTO ai_allowance VALUES (1,1)')
    with pytest.raises(ValueError, match='allowance reached'):
        LLM('azure').complete_json('JSON', 'ping')


def test_reconnect_after_network_preserves_committed_records(tmp_path):
    # Same reason as above: no libsql wheel for Python 3.13+, so skip instead of failing.
    libsql = pytest.importorskip("libsql", reason="libsql not installed; remote/Turso path not exercised")
    path = str(tmp_path / 'reconnect.sqlite3')
    factory = lambda: libsql.connect(path)
    with Connection(factory(), reconnect=factory) as c:
        c.execute('CREATE TABLE sample (value TEXT)')
        c.execute("INSERT INTO sample VALUES ('persisted')")
        c.commit()
        c.reconnect()
        assert c.execute('SELECT value FROM sample').fetchone()[0] == 'persisted'


def test_refresh_renews_connection_after_each_model_call(con):
    from footfall.scout.refresh import run_live
    from .conftest import FakeLLM, NOW
    calls = []
    class Hosted:
        def __getattr__(self, key):
            return getattr(con, key)
        def reconnect(self):
            assert not con.in_transaction
            calls.append('reconnected')
    count = len(db.get_sources(con))
    run = run_live(Hosted(), FakeLLM([{'events': [], 'uncertainties': []}] * count),
                   at=NOW, fetcher=lambda url: (url, 'empty page'))
    assert run['status'] == 'ok'
    assert len(calls) == count
