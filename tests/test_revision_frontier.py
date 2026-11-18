"""目录要求的新版到达前，旧日价保留供查证但不能继续发布。"""
import tempfile
import unittest
from pathlib import Path
from capture_service.ledger import connect
from capture_service.collection import collect,register_sources,coverage
from capture_service.archive import release_verified,get
from capture_service.daily_prices import days
from capture_service.view import overview

ROOT=Path(__file__).resolve().parents[1]

class RevisionFrontier(unittest.TestCase):
    def test_revision_notice_does_not_yet_change_current_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            c=connect(Path(directory)/'state.sqlite3')
            collect(c,'sample',ROOT/'data'/'normal.json')
            old=release_verified(c,'sample')
            frozen=get(c,'sample',old)
            register_sources(c,'sample',ROOT/'data'/'revised.json')
            self.assertEqual(c.execute(
                'SELECT expected_revision FROM collection_sources WHERE collection=? AND source_kind=?',
                ('sample', 'daily_page')).fetchone()[0], 'v2')
            state = coverage(c,'sample')
            self.assertIn('https://local-source-001.example.test/records/daily_page-A',
                          state['stale_required'])
            self.assertTrue(state['unverified_required'])
            self.assertEqual(days(c,'sample')[0]['status'], '新版待取')
            self.assertTrue(overview(c,'sample')['publishable'])
            with self.assertRaises(ValueError):
                release_verified(c,'sample')
            self.assertEqual(get(c,'sample',old),frozen)
            c.close()
