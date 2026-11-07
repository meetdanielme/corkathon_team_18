from footfall import db
from footfall.app import create_app
from footfall.domain.cutoffs import cutoff_for
from datetime import date
from .conftest import NOW, FakeLLM, sign_in


def test_supplier_edit_persists_and_recalculates(tmp_path):
    app = create_app(db_path=str(tmp_path / 'a.db'), clock=lambda: NOW, llm=FakeLLM(enabled=False))
    c = sign_in(app.test_client())
    assert c.get('/suppliers/bakery-mon/edit').status_code == 200
    values = dict(supplier='New Bakery', contact_label='Maeve', delivery_day='mon', delivery_window='08:00-09:00',
                  rule_type='weekday', cutoff_day='fri', cutoff_time='12:30')
    assert c.post('/suppliers/bakery-mon/edit', data=values).status_code == 302
    with db.connect(app.config['DB_PATH']) as con:
        suppliers = {s['id']: s for s in db.get_suppliers(con, db.get_business(con)['id'])}
        s = suppliers['bakery-mon']
        assert s['supplier'] == 'New Bakery' and s['contact_label'] == 'Maeve'
        assert cutoff_for(s['cutoff_rule'], date(2026, 11, 16)).isoformat().startswith('2026-11-13T12:30')
        assert suppliers['bakery-tue']['supplier'] == 'Bakery'
        assert s['demo_label']  # editing does not turn assumptions into verified evidence
    assert c.post('/suppliers/bakery-mon/edit', data={**values, 'cutoff_time': '25:00'}).status_code == 400
    assert c.post('/suppliers/bakery-mon/edit', data={**values, 'rule_type': 'business_days_before', 'days_before': '1', 'closed': ['mon','tue','wed','thu','fri','sat','sun']}).status_code == 400
    assert c.get('/suppliers/missing/edit').status_code == 404


def test_orders_edit_recipient_resets_approval_and_rejects_blank(tmp_path):
    app = create_app(db_path=str(tmp_path / 'a.db'), clock=lambda: NOW, llm=FakeLLM(enabled=False))
    c = sign_in(app.test_client())
    with db.connect(app.config['DB_PATH']) as con:
        did = db.create_draft(con, 'old-insight', 'Bakery', 'Original order', 'template')
        db.approve_draft(con, did)
    assert 'Edit Order' in c.get('/orders').text
    assert c.post(f'/drafts/{did}', data={'text': 'Updated order', 'recipient_label': 'Maeve'}).status_code == 302
    with db.connect(app.config['DB_PATH']) as con:
        d = db.get_draft(con, did)
        assert (d['text'], d['recipient_label'], d['approved_at']) == ('Updated order', 'Maeve', None)
    assert c.post(f'/drafts/{did}', data={'text': ' ', 'recipient_label': 'Maeve'}).status_code == 400
    assert 'Updated order' in c.get('/orders').text
    assert c.get(f'/drafts/{did}').status_code == 200  # editable after related insight expires
    assert app.test_client().get('/orders').status_code == 302
