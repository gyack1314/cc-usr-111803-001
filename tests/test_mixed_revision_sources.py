"""同日新版正文和旧日更正可以作为不同原文一同接收。"""
import tempfile
import unittest
from pathlib import Path

from capture_service.collection import collect, coverage
from capture_service.ledger import connect, entities

ROOT = Path(__file__).resolve().parents[1]


class MixedRevisionSources(unittest.TestCase):
    def test_revision_and_correction_have_separate_receipts(self):
        with tempfile.TemporaryDirectory() as directory:
            connection = connect(Path(directory) / 'prices.sqlite3')
            collect(connection, 'sample', ROOT / 'data' / 'normal.json')
            collect(connection, 'sample', ROOT / 'data' / 'revised-with-correction.json')
            self.assertEqual(len(entities(connection, 'sample')), 4)
            self.assertEqual(coverage(connection, 'sample')['expected'], 3)
            self.assertEqual(coverage(connection, 'sample')['received'], 3)
            connection.close()
