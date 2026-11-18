"""同一来源字节在迁移地址重现时，保留两处取得依据。"""
import tempfile
import unittest
from pathlib import Path

from capture_service.collection import collect, coverage
from capture_service.ledger import connect, entities

ROOT = Path(__file__).resolve().parents[1]


class SourceMirror(unittest.TestCase):
    def test_mirror_keeps_two_source_receipts_for_one_entity(self):
        with tempfile.TemporaryDirectory() as directory:
            connection = connect(Path(directory) / 'sources.sqlite3')
            collect(connection, 'sample', ROOT / 'data' / 'normal.json')
            collect(connection, 'sample', ROOT / 'data' / 'mirror.json')
            self.assertEqual(len(entities(connection, 'sample')), 2)
            self.assertEqual(coverage(connection, 'sample')['expected'], 3)
            urls = {row[0] for row in connection.execute(
                'SELECT source_url FROM collection_progress WHERE collection=?', ('sample',))}
            self.assertEqual(len(urls), 3)
            origins = {row[0] for row in connection.execute(
                'SELECT source_url FROM receipt_origins WHERE collection=? AND body_sha256=?',
                ('sample', entities(connection, 'sample')[0]['source']))}
            self.assertEqual(len(origins), 2)
            connection.close()
