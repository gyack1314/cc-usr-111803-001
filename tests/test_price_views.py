"""核对已实现的日价与周表分别提供独立查询。"""
import tempfile
import unittest
from pathlib import Path

from capture_service.collection import collect
from capture_service.daily_prices import days
from capture_service.ledger import connect
from capture_service.weekly_prices import weeks

ROOT = Path(__file__).resolve().parents[1]


class PriceViews(unittest.TestCase):
    def test_initial_daily_and_weekly_queries(self):
        with tempfile.TemporaryDirectory() as directory:
            connection = connect(Path(directory) / 'prices.sqlite3')
            collect(connection, 'sample', ROOT / 'data' / 'normal.json')
            daily = days(connection, 'sample')
            weekly = weeks(connection, 'sample')
            self.assertEqual(daily[0]['observed_on'], '2026-11-11')
            self.assertEqual(weekly[0]['observed_days'], ['2026-11-11'])
            self.assertEqual(weekly[0]['status'], '有日价可核')
            connection.close()
