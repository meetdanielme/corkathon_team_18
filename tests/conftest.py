from datetime import datetime

import pytest

from footfall import db
from footfall.domain.timeutil import TZ

NOW = datetime(2026, 11, 7, 22, 0, tzinfo=TZ)  # Saturday night after close


class FakeLLM:
    """Returns queued JSON responses; counts calls like the real adapter."""
    def __init__(self, responses=None, enabled=True):
        self.responses = list(responses or [])
        self.calls = 0
        self.enabled = enabled

    def complete_json(self, system, user):
        self.calls += 1
        if not self.responses:
            raise RuntimeError("no fake response queued")
        r = self.responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def sign_in(client):
    """Simulated demo sign-in, as the login form does."""
    with client.session_transaction() as s:
        s["user"] = "Bríd"
    return client


@pytest.fixture
def con(tmp_path):
    c = db.connect(str(tmp_path / "t.sqlite3"))
    db.init(c)
    db.seed(c)
    yield c
    c.close()
