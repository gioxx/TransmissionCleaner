import datetime
import tempfile
import unittest
from pathlib import Path

from app.history import HistoryRepository
from app.importer import import_eml


EMAIL = """Subject: Torrent deletion log
Date: Wed, 10 Jun 2026 07:50:01 +0200
Message-Id: <old-1@example.test>
From: cleaner@example.test
To: user@example.test
Content-Type: text/plain; charset=utf-8

--- Processing server: MiData ---
Name: Old.Movie.mkv, Status: seeding, Size: 2 GB, Added: 2026-06-01 08:00:00, Expired: True, Ratio: 0.00
Removing Old.Movie.mkv after 10 days (expired) (Ratio: 0.00, Size: 2 GB)
-----------------------------------------------
Files not to delete: 7
Files to delete: 1
"""


class ImporterTests(unittest.TestCase):
    def test_imports_old_email_into_history(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "history.db"
            eml = Path(directory) / "old.eml"
            eml.write_text(EMAIL, encoding="utf-8")
            repo = HistoryRepository(str(path))
            repo.initialize()

            result = import_eml(eml, repo)

            self.assertEqual(result, "imported")
            record = repo.latest()
            self.assertEqual(record.trigger, "imported")
            self.assertEqual(record.deleted_count, 1)
            self.assertIn("Old.Movie.mkv", record.log)
            self.assertEqual(record.timestamp, datetime.datetime(2026, 6, 10, 7, 50, 1, tzinfo=datetime.timezone(datetime.timedelta(hours=2))))

    def test_does_not_import_same_message_twice(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            eml = root / "old.eml"
            eml.write_text(EMAIL, encoding="utf-8")
            repo = HistoryRepository(str(root / "history.db"))
            repo.initialize()

            self.assertEqual(import_eml(eml, repo), "imported")
            self.assertEqual(import_eml(eml, repo), "duplicate")
            self.assertEqual(repo.search()[1], 1)


if __name__ == "__main__":
    unittest.main()
