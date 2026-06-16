import datetime
import logging

from transmission_rpc import Client
from transmission_rpc.error import TransmissionError

from app.config import settings, ServerConfig
from app.models import TorrentInfo, ServerResult, CleanupResult

logger = logging.getLogger(__name__)


def _coerce_utc(dt: datetime.datetime) -> datetime.datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=datetime.timezone.utc)
    return dt


def _should_delete(t: TorrentInfo) -> bool:
    if t.status not in ("seeding", "stopped"):
        return False
    if t.percent_done < 1.0:
        return False
    if t.age_days < settings.days_to_wait:
        return False
    if settings.min_ratio > 0 and t.ratio < settings.min_ratio:
        return False
    return True


def _make_client(server: ServerConfig) -> Client:
    return Client(
        host=server.host,
        port=server.port,
        username=server.user,
        password=server.password,
    )


def fetch_server_torrents(server: ServerConfig) -> ServerResult:
    result = ServerResult(name=server.name, host=server.host)
    try:
        client = _make_client(server)
        for t in client.get_torrents():
            date_added = _coerce_utc(t.added_date)
            ratio = t.upload_ratio if t.upload_ratio is not None else 0.0
            if ratio < 0:
                ratio = 0.0
            info = TorrentInfo(
                id=t.id,
                name=t.name,
                status=t.status,
                size_bytes=t.total_size or 0,
                date_added=date_added,
                ratio=ratio,
                percent_done=t.percent_done if t.percent_done is not None else 0.0,
                server_name=server.name,
                hash_string=t.hash_string,
            )
            info.will_delete = _should_delete(info)
            result.torrents.append(info)
    except TransmissionError as e:
        logger.error("Transmission error on %s: %s", server.name, e)
        result.connected = False
        result.error = str(e)
    except Exception as e:
        logger.error("Unexpected error on %s: %s", server.name, e)
        result.connected = False
        result.error = str(e)
    return result


def fetch_all_torrents() -> list[ServerResult]:
    return [fetch_server_torrents(s) for s in settings.servers]


def run_cleanup(dry_run: bool = False) -> CleanupResult:
    effective_dry_run = dry_run or settings.dry_run
    server_results: list[ServerResult] = []
    total_deleted = 0
    total_errors = 0

    for server in settings.servers:
        sr = fetch_server_torrents(server)
        if not sr.connected:
            total_errors += 1
            server_results.append(sr)
            continue

        if not effective_dry_run:
            try:
                client = _make_client(server)
                for torrent in sr.to_delete:
                    try:
                        client.remove_torrent(torrent.id, delete_data=True)
                        total_deleted += 1
                        logger.info("Removed %s from %s", torrent.name, server.name)
                    except TransmissionError as e:
                        torrent.delete_error = str(e)
                        total_errors += 1
                        logger.error("Failed to remove %s: %s", torrent.name, e)
            except Exception as e:
                sr.error = str(e)
                total_errors += 1
        else:
            total_deleted += len(sr.to_delete)

        server_results.append(sr)

    return CleanupResult(
        timestamp=datetime.datetime.now(),
        server_results=server_results,
        deleted_count=total_deleted,
        error_count=total_errors,
        dry_run=effective_dry_run,
    )
