import json
import os
import re
from dataclasses import dataclass

_DEFAULT_SERVERS_FILE = "/config/servers.json"


def _strip_comments(text: str) -> str:
    """Remove // line comments and /* block comments */ from a JSON string."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"//[^\n]*", "", text)
    return text


def _load_servers() -> list["ServerConfig"]:
    path = os.getenv("SERVERS_FILE", _DEFAULT_SERVERS_FILE)
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            data = json.loads(_strip_comments(f.read()))
        return [ServerConfig(**s) for s in data]
    # fallback: inline JSON env var (legacy / single-server convenience)
    raw = os.getenv("TRANSMISSION_SERVERS", "[]")
    return [ServerConfig(**s) for s in json.loads(raw)]


@dataclass
class ServerConfig:
    name: str
    host: str
    port: int = 9091
    user: str = ""
    password: str = ""


@dataclass
class Settings:
    servers: list[ServerConfig]
    days_to_wait: int
    min_ratio: float
    cleanup_schedule: str
    dry_run: bool
    notify_always: bool
    telegram_enabled: bool
    telegram_bot_token: str
    telegram_chat_id: str
    resend_enabled: bool
    resend_api_key: str
    resend_from: str
    resend_to: str
    smtp_enabled: bool
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    smtp_from: str
    smtp_to: str
    smtp_tls: bool

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            servers=_load_servers(),
            days_to_wait=int(os.getenv("DAYS_TO_WAIT", "10")),
            min_ratio=float(os.getenv("MIN_RATIO", "0")),
            cleanup_schedule=os.getenv("CLEANUP_SCHEDULE", "0 6 * * *"),
            dry_run=os.getenv("DRY_RUN", "false").lower() == "true",
            notify_always=os.getenv("NOTIFY_ALWAYS", "false").lower() == "true",
            telegram_enabled=os.getenv("TELEGRAM_ENABLED", "false").lower() == "true",
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
            resend_enabled=os.getenv("RESEND_ENABLED", "false").lower() == "true",
            resend_api_key=os.getenv("RESEND_API_KEY", ""),
            resend_from=os.getenv("RESEND_FROM", ""),
            resend_to=os.getenv("RESEND_TO", ""),
            smtp_enabled=os.getenv("SMTP_ENABLED", "false").lower() == "true",
            smtp_host=os.getenv("SMTP_HOST", "localhost"),
            smtp_port=int(os.getenv("SMTP_PORT", "25")),
            smtp_user=os.getenv("SMTP_USER", ""),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            smtp_from=os.getenv("SMTP_FROM", ""),
            smtp_to=os.getenv("SMTP_TO", ""),
            smtp_tls=os.getenv("SMTP_TLS", "false").lower() == "true",
        )

    @property
    def active_notifications(self) -> list[str]:
        active = []
        if self.telegram_enabled:
            active.append("Telegram")
        if self.resend_enabled:
            active.append("Resend")
        if self.smtp_enabled:
            active.append("SMTP")
        return active


settings = Settings.from_env()
