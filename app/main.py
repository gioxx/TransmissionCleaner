import asyncio
import datetime
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.cleaner import fetch_all_torrents, run_cleanup
from app.config import settings
from app.history import HistoryRepository
from app.models import CleanupResult, ServerResult
from app.notifier import notify_all
from app.presentation import format_size

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class AppState:
    last_run_time: datetime.datetime | None = None
    last_log: str = ""
    last_deleted: int = 0
    last_errors: int = 0
    flash: str = ""

    def update(self, result: CleanupResult) -> None:
        self.last_run_time = result.timestamp
        self.last_log = result.to_log()
        self.last_deleted = result.deleted_count
        self.last_errors = result.error_count


state = AppState()
scheduler = AsyncIOScheduler()
history = HistoryRepository()


def _persist(result: CleanupResult, trigger: str) -> None:
    if result.dry_run:
        return
    try:
        history.record(result, trigger)
    except Exception:
        logger.exception("Could not persist cleanup history")


async def scheduled_cleanup() -> None:
    logger.info("Scheduled cleanup starting")
    result = await asyncio.to_thread(run_cleanup)
    state.update(result)
    await asyncio.to_thread(_persist, result, "scheduled")
    await notify_all(result)
    logger.info("Scheduled cleanup done — removed %d", result.deleted_count)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await asyncio.to_thread(history.initialize)
        latest = await asyncio.to_thread(history.latest)
        if latest:
            state.last_run_time = latest.timestamp
            state.last_log = latest.log
            state.last_deleted = latest.deleted_count
            state.last_errors = latest.error_count
    except Exception:
        logger.exception("Could not initialize cleanup history")
    trigger = CronTrigger.from_crontab(settings.cleanup_schedule)
    scheduler.add_job(
        scheduled_cleanup,
        trigger,
        id="cleanup",
        replace_existing=True,
        misfire_grace_time=300,
    )
    scheduler.start()
    logger.info("Scheduler started with schedule: %s", settings.cleanup_schedule)
    yield
    scheduler.shutdown()


app = FastAPI(title="Transmission Cleaner", lifespan=lifespan)
templates = Jinja2Templates(directory="app/templates")


def _next_run() -> datetime.datetime | None:
    job = scheduler.get_job("cleanup")
    return job.next_run_time if job else None


def _format_dt(dt: datetime.datetime | None) -> str:
    if dt is None:
        return "—"
    local = dt.astimezone()
    return local.strftime("%Y-%m-%d %H:%M:%S")


def _next_run_iso(dt: datetime.datetime | None) -> str:
    if dt is None:
        return ""
    return dt.isoformat()


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    server_results: list[ServerResult] = await asyncio.to_thread(fetch_all_torrents)
    total_torrents = sum(len(sr.torrents) for sr in server_results)
    to_delete_count = sum(len(sr.to_delete) for sr in server_results)
    total_size = sum(t.size_bytes for sr in server_results for t in sr.torrents)
    to_delete_size = sum(t.size_bytes for sr in server_results for t in sr.to_delete)
    to_keep_size = total_size - to_delete_size
    connected_count = sum(1 for sr in server_results if sr.connected)
    next_run = _next_run()

    flash, state.flash = state.flash, ""
    ctx = {
        "request": request,
        "server_results": server_results,
        "total_torrents": total_torrents,
        "to_delete_count": to_delete_count,
        "to_keep_count": total_torrents - to_delete_count,
        "total_size_str": format_size(total_size),
        "to_delete_size_str": format_size(to_delete_size),
        "to_keep_size_str": format_size(to_keep_size),
        "server_count": len(settings.servers),
        "connected_count": connected_count,
        "next_run_str": _format_dt(next_run),
        "next_run_iso": _next_run_iso(next_run),
        "last_run_str": _format_dt(state.last_run_time),
        "last_log": state.last_log,
        "last_deleted": state.last_deleted,
        "last_errors": state.last_errors,
        "message": flash,
        "cfg": {
            "days_to_wait": settings.days_to_wait,
            "min_ratio": settings.min_ratio,
            "cleanup_schedule": settings.cleanup_schedule,
            "dry_run": settings.dry_run,
            "notifications": settings.active_notifications,
        },
    }
    return templates.TemplateResponse(request, "index.html", ctx)


@app.post("/run")
async def manual_run(request: Request):
    dry = request.query_params.get("dry") == "1"
    result = await asyncio.to_thread(run_cleanup, dry)
    state.update(result)
    await asyncio.to_thread(_persist, result, "manual")
    await notify_all(result)
    verb = "Dry run" if dry else "Cleanup"
    state.flash = f"{verb} complete — {result.deleted_count} removed, {result.error_count} errors"
    return RedirectResponse("/", status_code=303)


@app.get("/api/status")
async def api_status():
    next_run = _next_run()
    return {
        "next_run": _next_run_iso(next_run),
        "last_run": state.last_run_time.isoformat() if state.last_run_time else None,
        "last_deleted": state.last_deleted,
        "last_errors": state.last_errors,
        "schedule": settings.cleanup_schedule,
        "dry_run": settings.dry_run,
    }


@app.get("/api/torrents")
async def api_torrents():
    results = await asyncio.to_thread(fetch_all_torrents)
    return [
        {
            "server": sr.name,
            "connected": sr.connected,
            "error": sr.error,
            "torrents": [
                {
                    "name": t.name,
                    "status": t.status,
                    "size": t.size_str,
                    "age_days": t.age_days,
                    "ratio": round(t.ratio, 2),
                    "progress": t.progress_pct,
                    "will_delete": t.will_delete,
                }
                for t in sr.torrents
            ],
        }
        for sr in results
    ]


@app.get("/api/history")
async def api_history(q: str = "", page: int = 1, page_size: int = 20):
    items, total = await asyncio.to_thread(history.search, q, page, page_size)
    page = max(1, page)
    page_size = min(100, max(1, page_size))
    return {
        "items": [
            {"id": item.id, "timestamp": item.timestamp.isoformat(), "trigger": item.trigger,
             "deleted_count": item.deleted_count, "error_count": item.error_count, "log": item.log}
            for item in items
        ],
        "page": page, "page_size": page_size, "total": total,
        "pages": (total + page_size - 1) // page_size,
    }


@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request, q: str = "", page: int = 1):
    items, total = await asyncio.to_thread(history.search, q, page, 20)
    next_run = _next_run()
    return templates.TemplateResponse(request, "history.html", {
        "request": request, "items": items, "query": q, "page": max(1, page),
        "total": total, "pages": (total + 19) // 20,
        "next_run_str": _format_dt(next_run), "next_run_iso": _next_run_iso(next_run),
        "last_run_str": _format_dt(state.last_run_time),
        "cfg": {"dry_run": settings.dry_run},
        "page_title": "Cleanup history",
    })
