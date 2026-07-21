import datetime
import tempfile
import unittest
from pathlib import Path

from app.history import HistoryRepository
from app.models import CleanupResult


class HistoryTests(unittest.TestCase):
    def test_persists_latest_and_searches_log(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = HistoryRepository(str(Path(directory) / "history.db"))
            repo.initialize()
            result = CleanupResult(datetime.datetime.now(datetime.UTC), [], 2, 1, False)
            result.server_results = []
            repo.record(result, "manual")
            latest = repo.latest()
            self.assertEqual(latest.deleted_count, 2)
            found, total = repo.search("Total removed")
            self.assertEqual((len(found), total), (1, 1))

    def test_rejects_dry_run(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = HistoryRepository(str(Path(directory) / "history.db"))
            repo.initialize()
            result = CleanupResult(datetime.datetime.now(datetime.UTC), [], 0, 0, True)
            with self.assertRaises(ValueError):
                repo.record(result, "manual")


if __name__ == "__main__":
    unittest.main()
