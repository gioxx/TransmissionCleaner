import hashlib
import re
from email import policy
from email.parser import BytesParser
from pathlib import Path

from app.history import HistoryRepository


def import_eml(path: Path, repository: HistoryRepository) -> str:
    raw = path.read_bytes()
    message = BytesParser(policy=policy.default).parsebytes(raw)
    if message.get("Subject", "").strip().lower() != "torrent deletion log":
        return "skipped"
    body = message.get_body(preferencelist=("plain",)).get_content()
    timestamp = message.get("Date")
    if not timestamp:
        return "skipped"
    from email.utils import parsedate_to_datetime
    deleted = _number(r"Files to delete:\s*(\d+)", body) or _number(r"Total removed:\s*(\d+)", body)
    errors = _number(r"Errors:\s*(\d+)", body)
    source_id = message.get("Message-Id") or hashlib.sha256(raw).hexdigest()
    return "imported" if repository.record_imported(parsedate_to_datetime(timestamp), deleted, errors, body.strip(), source_id) else "duplicate"


def _number(pattern: str, text: str) -> int:
    match = re.search(pattern, text, re.IGNORECASE)
    return int(match.group(1)) if match else 0
