"""目录与续采清单在首版资料接收时保持一致。"""
import tempfile
import unittest
from pathlib import Path

from capture_service.collection import collect, pending
from capture_service.ledger import connect

ROOT = Path(__file__).resolve().parents[1]


class PendingSources(unittest.TestCase):
    def test_initial_pending_source_is_cleared_after_arrival(self):
        with tempfile.TemporaryDirectory() as directory:
            connection = connect(Path(directory) / 'sources.sqlite3')
            collect(connection, 'sample', ROOT / 'data' / 'partial.json')
            waiting = pending(connection, 'sample')
            self.assertEqual(len(waiting), 1)
            self.assertEqual(waiting[0]['kind'], 'price_table')
            collect(connection, 'sample', ROOT / 'data' / 'normal.json')
            self.assertEqual(pending(connection, 'sample'), [])
            connection.close()
