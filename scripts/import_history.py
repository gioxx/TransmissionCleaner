#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.history import HistoryRepository
from app.importer import import_eml


def main() -> int:
    parser = argparse.ArgumentParser(description="Import Transmission Cleaner .eml history")
    parser.add_argument("paths", nargs="+", type=Path, help=".eml files or directories")
    parser.add_argument("--db", default="/config/cleanups.db", help="SQLite history database")
    parser.add_argument("--dry-run", action="store_true", help="Only report what would be imported")
    args = parser.parse_args()
    files = sorted({file for path in args.paths for file in (path.glob("*.eml") if path.is_dir() else [path]) if file.suffix.lower() == ".eml"})
    repository = None
    if not args.dry_run:
        repository = HistoryRepository(args.db)
        repository.initialize()
    counts = {"imported": 0, "duplicate": 0, "skipped": 0}
    for file in files:
        if args.dry_run:
            status = "would import" if file.exists() else "skipped"
        else:
            status = import_eml(file, repository) if file.exists() else "skipped"
        if status == "would import":
            counts["imported"] += 1
        elif status in counts:
            counts[status] += 1
        print(f"{status}: {file}")
    print(f"Read: {len(files)} | Imported: {counts['imported']} | Duplicates: {counts['duplicate']} | Skipped: {counts['skipped']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
