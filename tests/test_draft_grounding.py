import pytest

from footfall.domain import drafts
from tests.conftest import FakeLLM
from tests.test_drafts_app import INSIGHT


@pytest.mark.parametrize('output', [
    {'text': 'Please send 40 extra loaves.'},
    {'text': 'Please send forty extra loaves.'},
    {'text': 'Please send 12 extra loaves.'},
    {'text': 'The supplier has confirmed free delivery.'},
    {'style': 'warm', 'text': 'Delivery is free.'},
    {'style': 'Send 12 loaves'}, {'style': []}, {'style': None},
    None, [], 'warm', {},
])
def test_untrusted_model_content_falls_back(output):
    result = drafts.draft(INSIGHT, FakeLLM([output]))
    assert result['source'] == 'template'
    assert result['text'] == drafts.template_draft(INSIGHT)[1]


@pytest.mark.parametrize('style', ['standard', 'concise', 'warm'])
@pytest.mark.parametrize('case', ['upcoming', 'missed', 'decrease'])
def test_every_style_preserves_supported_facts_and_owner_control(style, case):
    insight = {**INSIGHT, 'action_deadline': {**INSIGHT['action_deadline']}}
    if case == 'missed':
        insight['action_deadline']['status'] = 'missed'
    if case == 'decrease':
        insight['direction'] = 'decrease'
    result = drafts.draft(insight, FakeLLM([{'style': style}]))
    assert result['source'] == 'llm'
    assert insight['title'] in result['text']
    assert insight['window_label'] in result['text']
    assert drafts.unsupported_numbers(result['text'], insight) == []
    if case == 'missed':
        assert 'passed' in result['text'] and 'late change' in result['text']
    elif case == 'upcoming':
        assert insight['action_deadline']['cutoff_label'] in result['text']
        assert 'confirm quantities' in result['text']
    else:
        assert 'access' in result['text'] and 'timing' in result['text']


def test_provider_failure_keeps_template():
    result = drafts.draft(INSIGHT, FakeLLM([RuntimeError('unavailable')]))
    assert result['source'] == 'template'


@pytest.mark.parametrize('response,expected_source', [
    ({'style': 'warm'}, 'llm'),
    ({'style': 'warm', 'text': 'Send forty extra loaves for free.'}, 'template'),
])
def test_app_persists_only_grounded_generated_message(tmp_path, response, expected_source):
    from footfall import db
    from footfall.app import create_app
    from footfall.scout.refresh import run_prepared
    from tests.conftest import NOW, sign_in

    app = create_app(db_path=str(tmp_path / 'draft.sqlite3'), clock=lambda: NOW,
                     llm=FakeLLM([response]))
    with db.connect(app.config['DB_PATH']) as con:
        run_prepared(con, at=NOW)
    client = sign_in(app.test_client())
    insight = next(i for i in client.get('/api/insights').get_json()['insights']
                   if i['title'] == 'Graduation ceremony')
    result = client.post(f"/insights/{insight['id']}/draft")
    draft_id = int(result.headers['Location'].split('/')[-1])
    with db.connect(app.config['DB_PATH']) as con:
        saved = db.get_draft(con, draft_id)
    assert saved['source'] == expected_source
    assert saved['approved_at'] is None
    assert 'forty' not in saved['text'] and 'free' not in saved['text']
    assert 'Wed 11 Nov 16:00' in saved['text']
