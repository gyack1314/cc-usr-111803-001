"""更正撤回迟到时，当前日价回到页面新版次，已发布周报仍按当时资料复现。"""
import tempfile
import unittest
from pathlib import Path

from capture_service.archive import get, release, release_verified
from capture_service.collection import collect, coverage, pending
from capture_service.daily_prices import days
from capture_service.ledger import connect, entities
from capture_service.weekly_prices import weeks

ROOT = Path(__file__).resolve().parents[1]
COLLECTION = 'pork-001'
RETRACTION_URL = 'https://local-source-001.example.test/records/price_correction_retraction-A'


class CorrectionWithdrawalLifecycle(unittest.TestCase):
    def test_v1_correction_v2_late_retraction_and_archive_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            connection = connect(Path(directory) / 'withdrawal.sqlite3')

            # 阶段一：v1 日价 14.79 与周表核实后发布首版周报。
            collect(connection, COLLECTION, ROOT / 'data' / 'normal.json')
            first_revision = release_verified(connection, COLLECTION)
            first_view = get(connection, COLLECTION, first_revision)
            self.assertEqual(first_view['daily_prices'][0]['price_cny_kg'], 14.79)
            self.assertEqual(first_view['weekly_prices'][0]['difference_cny_kg'], 0.01)

            # 阶段二：更正 C-1（14.72）发布并覆盖当前日价，周报据此发布 14.72 版本。
            collect(connection, COLLECTION, ROOT / 'data' / 'correction-published.json')
            corrected_day = days(connection, COLLECTION)[0]
            self.assertEqual(corrected_day['price_cny_kg'], 14.72)
            self.assertTrue(corrected_day['correction_effective'])
            self.assertEqual(corrected_day['correction_id'], 'C-1')
            self.assertEqual(corrected_day['correction_issued_on'], '2026-11-15')
            self.assertEqual(corrected_day['observed_on'], '2026-11-11')
            corrected_week = weeks(connection, COLLECTION)[0]
            self.assertEqual(corrected_week['observed_mean_cny_kg'], 14.72)
            self.assertEqual(corrected_week['difference_cny_kg'], -0.06)
            self.assertEqual(len(corrected_week['missing_days']), 6)
            self.assertEqual(corrected_week['status'], '覆盖不完整')
            corrected_revision = release_verified(connection, COLLECTION)
            corrected_view = get(connection, COLLECTION, corrected_revision)
            self.assertEqual(corrected_view['daily_prices'][0]['price_cny_kg'], 14.72)

            # 阶段三：v2 日价 14.76 先到，撤回通知尚未取得。
            collect(connection, COLLECTION, ROOT / 'data' / 'withdrawal-pending.json')
            pending_coverage = coverage(connection, COLLECTION)
            self.assertEqual(pending_coverage['expected'], 4)
            self.assertEqual(pending_coverage['received'], 3)
            self.assertEqual(pending_coverage['missing_required'], [RETRACTION_URL])
            self.assertIn(RETRACTION_URL, pending_coverage['unverified_required'])
            self.assertEqual(pending(connection, COLLECTION),
                             [dict(url=RETRACTION_URL,
                                   kind='price_correction_retraction',
                                   expected_revision='v1')])
            pending_day = days(connection, COLLECTION)[0]
            # 缺少撤回依据不能当作更正已失效：当前解释仍受 C-1 影响。
            self.assertEqual(pending_day['price_cny_kg'], 14.72)
            self.assertEqual(pending_day['version'], 'v2')
            self.assertTrue(pending_day['correction_effective'])
            self.assertNotIn('retraction_sha256', pending_day)
            pending_week = weeks(connection, COLLECTION)[0]
            self.assertEqual(pending_week['observed_mean_cny_kg'], 14.72)
            self.assertEqual(pending_week['difference_cny_kg'], -0.06)
            # 撤回待取期间不能按已核实资料再次发布。
            with self.assertRaises(ValueError):
                release_verified(connection, COLLECTION)

            # 阶段四：撤回原文到达，接收进度、当前日价和周度差异一起变化。
            collect(connection, COLLECTION, ROOT / 'data' / 'withdrawal-complete.json')
            complete_coverage = coverage(connection, COLLECTION)
            self.assertEqual(complete_coverage['expected'], 4)
            self.assertEqual(complete_coverage['received'], 4)
            self.assertFalse(complete_coverage['missing_required'])
            self.assertFalse(complete_coverage['stale_required'])
            self.assertFalse(complete_coverage['unverified_required'])
            self.assertEqual(pending(connection, COLLECTION), [])

            restored_day = days(connection, COLLECTION)[0]
            self.assertEqual(restored_day['price_cny_kg'], 14.76)
            self.assertEqual(restored_day['version'], 'v2')
            self.assertEqual(restored_day['status'], '已核实')
            self.assertFalse(restored_day['correction_effective'])
            self.assertEqual(restored_day['correction_id'], 'C-1')
            # 日价、更正、撤回各自的原始发布时间与观测日均保留。
            self.assertEqual(restored_day['published_on'], '2026-11-18')
            self.assertEqual(restored_day['correction_issued_on'], '2026-11-15')
            self.assertEqual(restored_day['retraction_issued_on'], '2026-11-18')
            self.assertEqual(restored_day['observed_on'], '2026-11-11')
            self.assertIn('correction_sha256', restored_day)
            self.assertIn('retraction_sha256', restored_day)

            restored_week = weeks(connection, COLLECTION)[0]
            self.assertEqual(restored_week['observed_mean_cny_kg'], 14.76)
            self.assertEqual(restored_week['difference_cny_kg'], -0.02)
            self.assertEqual(restored_week['observed_days'], ['2026-11-11'])
            self.assertEqual(len(restored_week['missing_days']), 6)
            self.assertEqual(restored_week['status'], '覆盖不完整')
            new_revision = release_verified(connection, COLLECTION)
            self.assertEqual(get(connection, COLLECTION, new_revision)['daily_prices'][0]['price_cny_kg'], 14.76)

            # 五份原文（v1、周表、更正、v2、撤回）各自独立留痕，共五个实体与五张收据。
            self.assertEqual(len(entities(connection, COLLECTION)), 5)
            self.assertEqual(connection.execute(
                'SELECT COUNT(*) FROM receipts WHERE collection=?', (COLLECTION,)).fetchone()[0], 5)

            # 历史周报回查：先前发布的 14.72 与 14.79 版本仍按当时资料原样复现。
            self.assertEqual(get(connection, COLLECTION, first_revision), first_view)
            self.assertEqual(get(connection, COLLECTION, corrected_revision), corrected_view)
            self.assertEqual(get(connection, COLLECTION, corrected_revision)
                             ['weekly_prices'][0]['difference_cny_kg'], -0.06)
            self.assertEqual(get(connection, COLLECTION, first_revision)
                             ['daily_prices'][0]['price_cny_kg'], 14.79)
            connection.close()


class NoRetractionEvidenceGuard(unittest.TestCase):
    def test_correction_without_retraction_source_never_expires(self):
        with tempfile.TemporaryDirectory() as directory:
            connection = connect(Path(directory) / 'guard.sqlite3')
            collect(connection, COLLECTION, ROOT / 'data' / 'normal.json')
            collect(connection, COLLECTION, ROOT / 'data' / 'correction-published.json')
            day = days(connection, COLLECTION)[0]
            self.assertEqual(day['price_cny_kg'], 14.72)
            self.assertTrue(day['correction_effective'])
            self.assertNotIn('retraction_sha256', day)
            # 目录未登记撤回来源时，覆盖仍按既有三类来源闭合。
            state = coverage(connection, COLLECTION)
            self.assertEqual(state['expected'], 3)
            self.assertFalse(state['unverified_required'])
            release_verified(connection, COLLECTION)
            connection.close()
