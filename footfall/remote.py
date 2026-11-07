"""DB-API row compatibility for the remote libSQL driver (Turso)."""
class Row:
    def __init__(self, columns, values):
        self._columns, self._values = columns, values

    def keys(self):
        return self._columns

    def __getitem__(self, key):
        return self._values[self._columns.index(key)] if isinstance(key, str) else self._values[key]

    def __iter__(self):
        return iter(self._values)


class Cursor:
    def __init__(self, cursor):
        self._cursor = cursor
        self._columns = [d[0] for d in cursor.description] if cursor.description else []

    @property
    def lastrowid(self):
        return self._cursor.lastrowid

    def fetchone(self):
        row = self._cursor.fetchone()
        return Row(self._columns, row) if row is not None else None

    def fetchall(self):
        return [Row(self._columns, row) for row in self._cursor.fetchall()]

    def __iter__(self):
        return iter(self.fetchall())


class Connection:
    def __init__(self, raw, reconnect=None):
        self.raw = raw
        self._reconnect = reconnect

    def reconnect(self):
        """Renew an idle server stream only at an explicit committed boundary."""
        if self._reconnect is None:
            return
        if self.raw.in_transaction:
            raise RuntimeError("Cannot reconnect an uncommitted database transaction")
        try:
            self.raw.close()
        finally:
            self.raw = self._reconnect()

    def execute(self, sql, parameters=()):
        return Cursor(self.raw.execute(sql, parameters))

    def executescript(self, sql):
        return self.raw.executescript(sql)

    def commit(self):
        self.raw.commit()

    def rollback(self):
        self.raw.rollback()

    def close(self):
        self.raw.close()

    def __enter__(self):
        return self

    def __exit__(self, kind, value, traceback):
        try:
            self.rollback() if kind else self.commit()
        finally:
            self.close()
