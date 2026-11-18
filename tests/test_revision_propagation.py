"""目录修订会改变当前价格与发布门禁，但不改写旧周报。"""
import tempfile
import unittest
from pathlib import Path

from capture_service.archive import get, release, release_verified
from capture_service.collection import collect, coverage
from capture_service.daily_prices import days
from capture_service.ledger import connect
from capture_service.weekly_prices import weeks

ROOT = Path(__file__).resolve().parents[1]


class RevisionPropagation(unittest.TestCase):
    def test_revision_and_correction_propagate_without_rewriting_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            connection = connect(Path(directory) / 'prices.sqlite3')
            collect(connection, 'sample', ROOT / 'data' / 'normal.json')
            original = release(connection, 'sample')
            original_view = get(connection, 'sample', original)

            collect(connection, 'sample', ROOT / 'data' / 'revision-pending.json')
            pending_day = days(connection, 'sample')[0]
            self.assertEqual(pending_day['price_cny_kg'], 14.79)
            self.assertEqual(pending_day['status'], '新版待取')
            self.assertIn(
                'https://local-source-001.example.test/records/daily_page-A',
                coverage(connection, 'sample')['stale_required'],
            )
            with self.assertRaises(ValueError):
                release_verified(connection, 'sample')

            collect(connection, 'sample', ROOT / 'data' / 'revised-with-correction.json')
            current_day = days(connection, 'sample')[0]
            self.assertEqual(current_day['price_cny_kg'], 14.72)
            self.assertEqual(current_day['status'], '已核实')
            current_week = weeks(connection, 'sample')[0]
            self.assertEqual(current_week['observed_mean_cny_kg'], 14.72)
            self.assertEqual(current_week['status'], '覆盖不完整')
            self.assertEqual(len(current_week['missing_days']), 6)
            self.assertEqual(get(connection, 'sample', original), original_view)
            connection.close()
