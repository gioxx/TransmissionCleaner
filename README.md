# 🧹 Transmission Cleaner

[![Docker Build/Publish](https://github.com/gioxx/TransmissionCleaner/actions/workflows/Docker-BuildPublish.yml/badge.svg)](https://github.com/gioxx/TransmissionCleaner/actions/workflows/Docker-BuildPublish.yml)
[![GitHub release](https://img.shields.io/github/v/release/gioxx/TransmissionCleaner)](https://github.com/gioxx/TransmissionCleaner/releases)
[![Docker Pulls](https://img.shields.io/docker/pulls/gioxx/transmissioncleaner)](https://hub.docker.com/r/gioxx/transmissioncleaner)
[![GitHub license](https://img.shields.io/github/license/gioxx/TransmissionCleaner)](LICENSE)

Automated cleanup for one or more [Transmission](https://transmissionbt.com/) instances. Removes torrents that have been seeding (or are stopped) for longer than a configurable number of days, optionally enforcing a minimum upload ratio before deletion. Ships as a Docker container with a built-in web dashboard, scheduled runs, and multi-channel notifications.

---

## Pre-built images

Images are built automatically for `linux/amd64` and `linux/arm64` on every push to `main` (tagged `dev`) and on every release tag (tagged `latest` + version number).

| Registry | Image |
|---|---|
| GitHub Container Registry | `ghcr.io/gioxx/transmissioncleaner:latest` |
| Docker Hub | `gioxx/transmissioncleaner:latest` |

```bash
# GHCR
docker pull ghcr.io/gioxx/transmissioncleaner:latest

# Docker Hub
docker pull gioxx/transmissioncleaner:latest
```

---

## Features

- **Multi-server** — monitor and clean multiple Transmission instances from a single container
- **Rule-based deletion** — age threshold + optional minimum ratio + completeness guard (incomplete downloads are never touched)
- **Scheduled runs** — any cron expression, default `0 6 * * *` (06:00 every day)
- **Web dashboard** — live torrent table with delete/keep badges, countdown to next run, last-run log
- **Dry-run mode** — preview what *would* be deleted without touching anything, both via env var and from the UI
- **Notifications** — Telegram, [Resend](https://resend.com) and SMTP, independently enabled, sent in parallel
- **REST API** — `/api/status` and `/api/torrents` for scripting or external integrations
- **Health check** — built-in Docker health check on `/api/status`

---

## Requirements

- Docker 24+ (or Podman with Docker Compose support)
- Network access from the container to each Transmission RPC endpoint (default port `9091`)

No Python installation required on the host.

---

## Quick start

### 1 — Clone or download

```bash
git clone https://github.com/gioxx/TransmissionCleaner.git
cd TransmissionCleaner
```

### 2 — Create your config files

```bash
cp stack.env.example stack.env
cp config/servers.json.example config/servers.json
cp .env.example .env
```

Edit `config/servers.json` with your Transmission server(s) — the file supports `//` and `/* */` comments:

```jsonc
[
  {
    "name": "Home",
    "host": "192.168.1.10",
    "port": 9091,
    "user": "admin",
    "password": "yourpassword"
  }
]
```

Then set your cleanup rules and notification settings in `stack.env`.

### 3 — Start

```bash
docker compose up -d
```

The pre-built image is pulled automatically from GHCR. Open **http://your-host:8080** — done.

> To build from source instead, uncomment `build: .` in `docker-compose.yml` and run `docker compose up -d --build`.

---

## Deployment options

### Option A — Docker Compose (recommended)

The repository ships a ready-to-use `docker-compose.yml` that pulls the pre-built image from GHCR. Copy the examples, fill in your values and run:

```bash
cp stack.env.example stack.env
cp config/servers.json.example config/servers.json
cp .env.example .env          # only if you need a port other than 8080
# edit the three files, then:
docker compose up -d
```

The `config/` directory is mounted as a volume, so `servers.json` persists across container restarts and updates.

Full `docker-compose.yml` for reference:

```yaml
services:
  transmission-cleaner:
    image: ghcr.io/gioxx/transmissioncleaner:latest
    # build: .   # uncomment to build from source instead
    container_name: transmission-cleaner
    ports:
      - "${HOST_PORT:-8080}:8080"  # set HOST_PORT in .env
    volumes:
      - ./config:/config   # servers.json lives here
    env_file:
      - stack.env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/status')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

---

### Option B — Docker Run

If you prefer a one-liner, build the image first and then run it:

```bash
# Run using the pre-built GHCR image
docker run -d \
  --name transmission-cleaner \
  --restart unless-stopped \
  -p 8080:8080 \
  -v "$(pwd)/config:/config" \
  --env-file stack.env \
  ghcr.io/gioxx/transmissioncleaner:latest
```

For a quick single-server test without a config file, use the inline fallback:

```bash
docker run -d \
  --name transmission-cleaner \
  --restart unless-stopped \
  -p 8080:8080 \
  -e TRANSMISSION_SERVERS='[{"name":"Home","host":"192.168.1.10","port":9091,"user":"admin","password":"s3cr3t"}]' \
  -e DAYS_TO_WAIT=10 \
  -e CLEANUP_SCHEDULE="50 7 * * 3" \
  transmission-cleaner:latest
```

---

### Option C — Portainer (Stacks)

1. In Portainer, go to **Stacks → Add stack**.
2. Give the stack a name, e.g. `transmission-cleaner`.
3. Choose **Web editor** and paste the `docker-compose.yml` content below.
4. Scroll to **Environment variables** and click **Add an environment variable** for each setting, or switch to **Advanced mode** and paste the contents of `stack.env.example` directly.
5. Click **Deploy the stack**.

```yaml
services:
  transmission-cleaner:
    image: transmission-cleaner:latest
    build:
      context: https://github.com/gioxx/TransmissionCleaner.git
    container_name: transmission-cleaner
    ports:
      - "8080:8080"
    volumes:
      - /your/host/path/config:/config   # put servers.json here
    environment:
      SERVERS_FILE: "/config/servers.json"
      DAYS_TO_WAIT: "10"
      MIN_RATIO: "0"
      CLEANUP_SCHEDULE: "50 7 * * 3"
      DRY_RUN: "false"
      NOTIFY_ALWAYS: "false"
      TELEGRAM_ENABLED: "false"
      TELEGRAM_BOT_TOKEN: ""
      TELEGRAM_CHAT_ID: ""
      RESEND_ENABLED: "false"
      RESEND_API_KEY: ""
      RESEND_FROM: "cleaner@yourdomain.com"
      RESEND_TO: "you@yourdomain.com"
      SMTP_ENABLED: "false"
      SMTP_HOST: "localhost"
      SMTP_PORT: "25"
      SMTP_FROM: "cleaner@yourdomain.com"
      SMTP_TO: "you@yourdomain.com"
      SMTP_TLS: "false"
    restart: unless-stopped
```

> **Portainer tip** — use the **Secrets** feature or Portainer's environment variable editor to avoid putting passwords in plain text inside the stack definition. For `servers.json`, bind-mount a directory from the host (e.g. `/opt/transmission-cleaner/config`) so credentials stay on the host filesystem and survive stack redeployments.

---

## Configuration reference

All configuration is done via environment variables (in your local `stack.env`, passed with `--env-file`, or set individually with `-e`). Use `stack.env.example` as the starting template.

### Transmission servers

Servers are configured via a **JSON file** mounted into the container. This is the recommended approach as it supports comments and multi-line formatting.

| Variable | Default | Description |
|---|---|---|
| `SERVERS_FILE` | `/config/servers.json` | Path to the servers config file inside the container |

**`config/servers.json` format** (supports `//` and `/* */` comments):

```jsonc
[
  {
    // Display name shown in the web UI and notifications
    "name": "S1",

    // Hostname or IP address of the Transmission instance
    "host": "192.168.1.10",

    // RPC port — optional, default 9091
    "port": 9091,

    // Leave empty if authentication is disabled
    "user": "admin",
    "password": "secret"
  },
  {
    "name": "S2",
    "host": "nas.local",
    "port": 9091,
    "user": "admin",
    "password": "secret"
  }
]
```

Copy the provided example to get started:

```bash
cp config/servers.json.example config/servers.json
```

**Fallback — inline env var**

If `SERVERS_FILE` does not exist, the app falls back to the `TRANSMISSION_SERVERS` environment variable. Useful for quick tests or single-server setups that don't need a mounted file:

```env
TRANSMISSION_SERVERS=[{"name":"Home","host":"192.168.1.10","port":9091,"user":"admin","password":"secret"}]
```

---

### Cleanup rules

| Variable | Default | Description |
|---|---|---|
| `DAYS_TO_WAIT` | `10` | Delete torrents that have been seeding/stopped for at least this many days |
| `MIN_RATIO` | `0` | Minimum upload ratio required before deletion. `0` disables this check |
| `CLEANUP_SCHEDULE` | `50 7 * * 3` | Cron expression for the automatic run |
| `DRY_RUN` | `false` | If `true`, log what would be deleted without actually deleting anything |

**Deletion criteria (all must be true):**

1. Torrent status is `seeding` or `stopped`
2. Download is 100% complete (incomplete downloads are never touched)
3. Torrent age ≥ `DAYS_TO_WAIT`
4. If `MIN_RATIO > 0`: upload ratio ≥ `MIN_RATIO`

**Cron schedule examples:**

| Expression | Meaning |
|---|---|
| `50 7 * * 3` | Every Wednesday at 07:50 (default) |
| `0 3 * * *` | Every day at 03:00 |
| `0 6 * * 1` | Every Monday at 06:00 |
| `0 */6 * * *` | Every 6 hours |
| `30 22 * * *` | Every day at 22:30 |

---

### Notifications

All three channels can be active simultaneously. By default, notifications are sent only when at least one torrent is deleted or an error occurs. Set `NOTIFY_ALWAYS=true` to receive a report on every run.

| Variable | Default | Description |
|---|---|---|
| `NOTIFY_ALWAYS` | `false` | Send notifications even when nothing was deleted |

#### Telegram

| Variable | Default | Description |
|---|---|---|
| `TELEGRAM_ENABLED` | `false` | Enable Telegram notifications |
| `TELEGRAM_BOT_TOKEN` | — | Bot token from [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_CHAT_ID` | — | Target chat/channel ID |

**How to get your credentials:**

1. Open Telegram and search for **@BotFather**.
2. Send `/newbot` and follow the prompts. Copy the token it gives you → `TELEGRAM_BOT_TOKEN`.
3. To get your personal chat ID, message **@userinfobot** → `TELEGRAM_CHAT_ID`.
4. For a group or channel, add the bot as admin, then check `https://api.telegram.org/bot<TOKEN>/getUpdates` after sending a message — look for `"chat":{"id": ...}`.

```env
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=123456789:AABBCCDDeeffGGHHiijjKKLLmmNNoopp
TELEGRAM_CHAT_ID=-100123456789
```

#### Resend

[Resend](https://resend.com) is a developer-friendly transactional email API with a generous free tier (3 000 emails/month).

| Variable | Default | Description |
|---|---|---|
| `RESEND_ENABLED` | `false` | Enable Resend notifications |
| `RESEND_API_KEY` | — | API key from the Resend dashboard |
| `RESEND_FROM` | — | Sender address (must be a verified domain in Resend) |
| `RESEND_TO` | — | Recipient address |

```env
RESEND_ENABLED=true
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
RESEND_FROM=cleaner@yourdomain.com
RESEND_TO=you@yourdomain.com
```

#### SMTP

Use your own mail server, a relay, or a provider like Gmail, Fastmail, Mailgun, etc.

| Variable | Default | Description |
|---|---|---|
| `SMTP_ENABLED` | `false` | Enable SMTP notifications |
| `SMTP_HOST` | `localhost` | SMTP server hostname |
| `SMTP_PORT` | `25` | SMTP port |
| `SMTP_USER` | — | Username (leave empty if not required) |
| `SMTP_PASSWORD` | — | Password |
| `SMTP_FROM` | — | Sender address |
| `SMTP_TO` | — | Recipient address |
| `SMTP_TLS` | `false` | `true` = implicit TLS / SMTPS (port 465). `false` = plain or STARTTLS |

**Gmail example** (App Password required — enable 2FA first):

```env
SMTP_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=you@gmail.com
SMTP_PASSWORD=xxxx-xxxx-xxxx-xxxx
SMTP_FROM=you@gmail.com
SMTP_TO=you@gmail.com
SMTP_TLS=true
```

**Local relay / Postfix (no auth):**

```env
SMTP_ENABLED=true
SMTP_HOST=192.168.1.1
SMTP_PORT=25
SMTP_FROM=cleaner@home.lan
SMTP_TO=me@example.com
SMTP_TLS=false
```

---

### Web UI port

The host port is configured via `.env` (not `stack.env`), because Docker Compose reads `.env` automatically for variable substitution in the compose file — `env_file:` only passes variables into the container and cannot affect port mapping.

```bash
cp .env.example .env
# then edit .env:
HOST_PORT=8081
```

| File | Variable | Default | Description |
|---|---|---|---|
| `.env` | `HOST_PORT` | `8080` | Port exposed on the host |

---

## Web dashboard

The dashboard is served at `http://your-host:8080` and auto-refreshes every 60 seconds.

```
┌─────────────────────────────────────────────────────────┐
│ 🧹 Transmission Cleaner        Next run: 05h 42m 18s   │
├─────────────────────────────────────────────────────────┤
│ [▶ Run cleanup now]  [👁 Dry run]  [↺ Refresh]         │
├──────────┬──────────┬──────────┬──────────┬────────────┤
│ Servers  │ Torrents │ To remove│  Keeping │            │
│    2     │    47    │    8     │    39    │            │
├─────────────────────────────────────────────────────────┤
│ ⚙️ Settings                                              │
│  Retain: 10 days  ·  Min ratio: disabled               │
│  Schedule: 0 6 * * *  ·  Notifications: Telegram, SMTP │
├─────────────────────────────────────────────────────────┤
│ 📡 S1 (192.168.1.10)             Connected  47 torrents │
│ ┌────────────────────┬────────┬──────┬────┬─────┬─────┐│
│ │ Name               │ Status │ Size │ Age│Ratio│     ││
│ │ Ubuntu 24.04 LTS   │ seeding│ 4 GB │ 15d│1.52 │🗑 Del││
│ │ Fedora 41 Workstat │ seeding│ 2 GB │  3d│0.21 │✓Keep││
│ └────────────────────┴────────┴──────┴────┴─────┴─────┘│
├─────────────────────────────────────────────────────────┤
│ 📋 Last run log                                         │
│  Transmission Cleaner — 2025-06-15 06:00:01            │
│  === S1 (192.168.1.10) ===                             │
│  Removed: Ubuntu 24.04 LTS | age: 15d | ratio: 1.52   │
└─────────────────────────────────────────────────────────┘
```

**Rows highlighted in red** will be deleted on the next automatic run (or immediately if you click *Run cleanup now*).

### Manual controls

| Button | Action |
|---|---|
| **Run cleanup now** | Executes the full cleanup immediately and sends notifications |
| **Dry run** | Fetches torrents and marks what *would* be deleted — no actual deletions, no notifications |
| **Refresh** | Reloads the page and queries all servers again |

---

## REST API

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Web dashboard (HTML) |
| `/run` | POST | Trigger cleanup (`?dry=1` for dry run) |
| `/api/status` | GET | Scheduler and last-run metadata (JSON) |
| `/api/torrents` | GET | Full torrent list per server (JSON) |

**`GET /api/status` example:**

```json
{
  "next_run": "2025-06-16T06:00:00+02:00",
  "last_run": "2025-06-15T06:00:01.234567",
  "last_deleted": 3,
  "last_errors": 0,
  "schedule": "0 6 * * *",
  "dry_run": false
}
```

**`GET /api/torrents` example:**

```json
[
  {
    "server": "S1",
    "connected": true,
    "error": "",
    "torrents": [
      {
        "name": "Ubuntu 24.04 LTS",
        "status": "seeding",
        "size": "4.00 GB",
        "age_days": 15,
        "ratio": 1.52,
        "progress": 100.0,
        "will_delete": true
      }
    ]
  }
]
```

**Trigger a cleanup from the command line:**

```bash
curl -X POST http://your-host:8080/run
# Dry run:
curl -X POST "http://your-host:8080/run?dry=1"
```

---

## Updating

```bash
git pull
docker compose up -d --build
```

Docker Compose will rebuild the image and recreate the container with zero downtime for the scheduler (the new container starts before the old one stops).

---

## Troubleshooting

### Cannot connect to Transmission

- Verify the `host` in `TRANSMISSION_SERVERS` is reachable from inside the container.
  ```bash
  docker exec transmission-cleaner python -c \
    "import socket; socket.create_connection(('192.168.1.10', 9091), 3)"
  ```
- If Transmission is on the same Docker host, use the host's LAN IP rather than `localhost` or `127.0.0.1` (which resolves to the container itself).
- If both containers are on the same Docker network, use the service name as hostname.

### Telegram notifications not arriving

- Confirm the bot has been started by sending `/start` to it.
- For a group/channel, make sure the bot is an admin.
- Test directly:
  ```bash
  curl "https://api.telegram.org/bot<TOKEN>/sendMessage" \
    -d chat_id=<CHAT_ID> \
    -d text="test"
  ```

### `TRANSMISSION_SERVERS` parsing error

The value must be valid JSON. Verify it with:

```bash
echo '$TRANSMISSION_SERVERS' | python3 -m json.tool
```

Common mistakes: single quotes inside the JSON string, trailing commas, missing brackets.

### View container logs

```bash
docker logs -f transmission-cleaner
```

---

## License

[MIT](LICENSE)
