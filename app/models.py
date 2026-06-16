import datetime
from dataclasses import dataclass, field


@dataclass
class TorrentInfo:
    id: int
    name: str
    status: str
    size_bytes: int
    date_added: datetime.datetime
    ratio: float
    percent_done: float
    server_name: str
    hash_string: str
    will_delete: bool = False
    delete_error: str = ""

    @property
    def age_days(self) -> int:
        now = datetime.datetime.now(tz=self.date_added.tzinfo)
        return (now - self.date_added).days

    @property
    def size_str(self) -> str:
        b = self.size_bytes
        if b >= 1_000_000_000:
            return f"{b / 1_000_000_000:.2f} GB"
        if b >= 1_000_000:
            return f"{b / 1_000_000:.2f} MB"
        return f"{b / 1_000:.1f} KB"

    @property
    def progress_pct(self) -> float:
        return round(self.percent_done * 100, 1)

    @property
    def status_class(self) -> str:
        return {
            "seeding": "badge-green",
            "downloading": "badge-blue",
            "stopped": "badge-gray",
            "checking": "badge-yellow",
            "check pending": "badge-yellow",
            "download pending": "badge-blue",
            "seed pending": "badge-green",
        }.get(self.status, "badge-gray")


@dataclass
class ServerResult:
    name: str
    host: str
    torrents: list[TorrentInfo] = field(default_factory=list)
    error: str = ""
    connected: bool = True

    @property
    def to_delete(self) -> list[TorrentInfo]:
        return [t for t in self.torrents if t.will_delete]

    @property
    def to_keep(self) -> list[TorrentInfo]:
        return [t for t in self.torrents if not t.will_delete]


@dataclass
class CleanupResult:
    timestamp: datetime.datetime
    server_results: list[ServerResult]
    deleted_count: int
    error_count: int
    dry_run: bool

    def to_log(self) -> str:
        lines = [
            f"Transmission Cleaner — {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
        ]
        if self.dry_run:
            lines.append("DRY RUN — no actual deletions performed")
        lines.append("")
        for sr in self.server_results:
            lines.append(f"=== {sr.name} ({sr.host}) ===")
            if not sr.connected:
                lines.append(f"  ERROR: {sr.error}")
                lines.append("")
                continue
            deleted = sr.to_delete
            if deleted:
                for t in deleted:
                    verb = "Would remove" if self.dry_run else "Removed"
                    lines.append(
                        f"  {verb}: {t.name}"
                        f" | age: {t.age_days}d | ratio: {t.ratio:.2f} | size: {t.size_str}"
                    )
            else:
                lines.append("  Nothing to remove.")
            lines.append(f"  Kept: {len(sr.to_keep)} | Removed: {len(deleted)}")
            lines.append("")
        lines.append(f"Total removed: {self.deleted_count} | Errors: {self.error_count}")
        return "\n".join(lines)

    def to_telegram(self) -> str:
        header = f"<b>Transmission Cleaner</b> — {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
        if self.dry_run:
            header += "\n<i>Dry run — nothing actually deleted</i>"
        parts = [header]
        for sr in self.server_results:
            parts.append(f"\n<b>{sr.name}</b>")
            if not sr.connected:
                parts.append(f"❌ {sr.error}")
                continue
            deleted = sr.to_delete
            if deleted:
                for t in deleted:
                    parts.append(f"🗑 {t.name} ({t.age_days}d · ratio {t.ratio:.2f} · {t.size_str})")
            else:
                parts.append("✅ Nothing to remove")
        parts.append(f"\n<b>Total removed:</b> {self.deleted_count}")
        return "\n".join(parts)

    def to_email_body(self) -> str:
        return self.to_log()
