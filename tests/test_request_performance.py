"""Guard remote database round trips and request-local freshness."""
from unittest.mock import patch

from footfall import db
from footfall.app import create_app
from footfall.scout.refresh import run_prepared
from tests.conftest import FakeLLM, NOW, sign_in


def test_event_evidence_is_loaded_in_constant_queries(con):
    run_prepared(con, at=NOW)
    queries = []
    con.set_trace_callback(queries.append)
    events = db.get_events(con, NOW)
    con.set_trace_callback(None)
    assert len(events) > 1
    assert all(e['evidence'] for e in events)
    assert len(queries) == 3  # sources, all evidence, all events
    for event in events:
        assert all(x['event_id'] == event['id'] for x in event['evidence'])
        assert [x['retrieved_at'] for x in event['evidence']] == sorted(x['retrieved_at'] for x in event['evidence'])


def test_public_pages_do_not_open_database(tmp_path):
    app = create_app(str(tmp_path / 'app.db'), clock=lambda: NOW, llm=FakeLLM(enabled=False))
    with patch('footfall.db.connect', side_effect=AssertionError('unexpected database call')):
        for path in ('/', '/login'):
            assert app.test_client().get(path).status_code == 200


def test_each_request_loads_events_once_and_sees_new_data(tmp_path):
    path = str(tmp_path / 'app.db')
    app = create_app(path, clock=lambda: NOW, llm=FakeLLM(enabled=False))
    with db.connect(path) as con:
        run_prepared(con, at=NOW)
    client = sign_in(app.test_client())
    iid = client.get('/api/insights').json['insights'][0]['id']
    with patch('footfall.db.get_events', wraps=db.get_events) as events:
        assert client.get('/app').status_code == 200
        assert events.call_count == 1
        assert client.get('/insights/' + iid).status_code == 200
        assert events.call_count == 2
    before = client.get('/api/insights').json
    with db.connect(path) as con:
        con.execute('DELETE FROM event_evidence')
        con.execute('DELETE FROM events')
    after = client.get('/api/insights').json
    assert before['insights']
    assert not any(i.get('event_id') for i in after['insights'])
