<div align="center">

# 🛡️ Blocked AGH

**A dead-simple web UI to check if a domain is blocked by [AdGuard Home](https://adguard.com/en/adguard-home/overview.html) — and request an unblock with one tap.**

[![Python](https://img.shields.io/badge/python-3.13%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/ghcr.io-blocked--agh-2496ED?logo=docker&logoColor=white)](https://github.com/NekoShinobi/blocked-agh/pkgs/container/blocked-agh)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

![URL Checker web interface](https://github.com/NekoShinobi/blocked-agh/blob/latest/screenshot.png?raw=true)

</div>

---

## Why?

I wanted a really simple site where my family could check whether a domain is blocked by my AdGuard Home instance, plus a workflow to submit an unblock request without giving anyone access to the AdGuard dashboard.

> [!WARNING]
> The endpoints are **not authenticated in any way**. Do **not** expose this over public networks — run it behind a VPN, a reverse proxy with auth, or on a trusted LAN only.

> _Disclaimer: the rest of this README (and most of the UI) was written mostly by Claude._

## Features

- 🔍 **URL Checker** — check any domain against AdGuard Home from a clean web UI
- 🚦 **Clear status** — Not Blocked (green) · Whitelisted (blue) · Blocked (red)
- 🔔 **One-tap unblock** — sends an [ntfy](https://ntfy.sh) notification with an approve button
- ✅ **One-click approval** — approving the notification adds an allowlist rule to AdGuard Home
- 🎨 **Custom background** — point it at any image via an env var (falls back to a gradient)
- 🐳 **Docker-ready** — a prebuilt image is published to GHCR on every release

## Quick Start

The recommended way to run Blocked AGH is the **published Docker image**:

```
ghcr.io/nekoshinobi/blocked-agh:latest
```

### Docker (one-liner)

```bash
docker run -d \
  --name blocked-agh \
  -p 8000:8000 \
  -e ADGUARDHOME_URL=http://your-adguard-home:3000 \
  -e ADGUARDHOME_USER=admin \
  -e ADGUARDHOME_PASS=your_password \
  -e BLOCKED_AGH_URL=http://your-server:8000 \
  -e NTFY_URL=https://ntfy.sh \
  -e NTFY_TOPIC=UnblockRequests \
  -e NTFY_TOKEN=your_ntfy_token \
  ghcr.io/nekoshinobi/blocked-agh:latest
```

Then open <http://localhost:8000>.

### Docker Compose (recommended)

```yaml
services:
  blocked-agh:
    image: ghcr.io/nekoshinobi/blocked-agh:latest
    container_name: blocked-agh
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - ADGUARDHOME_URL=http://adguardhome:3000
      - ADGUARDHOME_USER=admin
      - ADGUARDHOME_PASS=your_password
      - BLOCKED_AGH_URL=http://blocked-agh:8000
      - NTFY_URL=https://ntfy.sh
      - NTFY_TOPIC=UnblockRequests
      - NTFY_TOKEN=your_ntfy_token
      - BACKGROUND_IMAGE_URL=
      - CORS_ALLOWED_ORIGINS=http://blocked-agh:8000
```

```bash
docker compose up -d
```

> A ready-to-edit [`compose.example.yml`](compose.example.yml) is included in the repo — copy it to `compose.yml` and fill in your values.

<details>
<summary><strong>Alternative: run from source (uv)</strong></summary>

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/NekoShinobi/blocked-agh.git
cd blocked-agh
uv sync

# set env vars (see Configuration below), then:
uv run uvicorn blocked_agh.web:app --host 0.0.0.0 --port 8000
```

</details>

## Requirements

- An **AdGuard Home** instance (with API access)
- An **ntfy** server + topic (for unblock notifications)
- **Docker**, _or_ Python 3.13+ with [uv](https://docs.astral.sh/uv/) to run from source

## Configuration

All configuration is done through environment variables.

| Variable | Description | Required | Default |
|----------|-------------|:--------:|---------|
| `ADGUARDHOME_URL` | AdGuard Home API URL | ✅ | — |
| `ADGUARDHOME_USER` | AdGuard Home username | ✅ | `admin` |
| `ADGUARDHOME_PASS` | AdGuard Home password | ✅ | — |
| `BLOCKED_AGH_URL` | Public URL of this service (used in the ntfy action button) | ✅ | `http://localhost:8000` |
| `NTFY_TOPIC` | ntfy topic for notifications | ✅ | `UnblockRequests` |
| `NTFY_TOKEN` | ntfy authentication token | ✅ | — |
| `NTFY_URL` | ntfy server URL | ⬜ | `https://ntfy.sh` |
| `BACKGROUND_IMAGE_URL` | Background image URL (blank → gradient fallback) | ⬜ | — |
| `CORS_ALLOWED_ORIGINS` | Comma-separated list of allowed CORS origins | ⬜ | — |

### CORS

The ntfy "Unblock" button calls this service from a different origin, so you may need to allow it:

```bash
# Single origin
CORS_ALLOWED_ORIGINS="https://blocked.example.com"

# Multiple origins (comma-separated, no spaces)
CORS_ALLOWED_ORIGINS="https://ntfy.sh,http://your-server:8000"

# Allow all origins (not recommended)
CORS_ALLOWED_ORIGINS="*"
```

If unset or empty, CORS is disabled and only same-origin requests are allowed.

## Usage

1. Open `http://localhost:8000` (or your `BLOCKED_AGH_URL`).
2. Enter a domain and click **Check URL** (or press <kbd>Enter</kbd>).
3. Read the status:
   - **Not Blocked** — the domain is allowed
   - **Whitelisted** — the domain is explicitly on the allowlist
   - **Blocked** — the domain is blocked by AdGuard Home
4. If it's blocked, click **Request Unblock** to fire off an ntfy notification.
5. Approve the request from the ntfy notification — the domain is unblocked instantly.

## How It Works

1. **Check** — the service authenticates to AdGuard Home and queries its filtering API for the domain.
2. **Request** — an unblock request posts an ntfy notification carrying an HTTP action button.
3. **Approve** — tapping the button calls `POST /api/unblock_url` on this service.
4. **Unblock** — the service appends an allowlist rule to AdGuard Home in the form `@@||domain.com^$important`.

## API Reference

<details>
<summary><code>POST /api/checkurl</code> — check if a domain is blocked</summary>

**Request**
```json
{ "url": "example.com" }
```

**Response**
```json
{
  "url": "example.com",
  "status": "NotFilteredNotFound | NotFilteredWhiteList | FilteredBlackList",
  "result": { }
}
```
</details>

<details>
<summary><code>POST /api/request_unblock</code> — send an unblock notification</summary>

**Request**
```json
{ "url": "example.com" }
```

**Response**
```json
{
  "url": "example.com",
  "message": "Unblock request notification sent successfully"
}
```
</details>

<details>
<summary><code>POST /api/unblock_url</code> — apply the unblock (called by the ntfy action)</summary>

**Request**
```json
{ "url": "example.com" }
```

**Response**
```json
{
  "url": "example.com",
  "message": "Unblock request completed successfully"
}
```
</details>

## Development

```bash
uv sync                                       # install deps (incl. dev extras)
uv run uvicorn blocked_agh.web:app --reload   # run with auto-reload
uv run pytest tests                           # run the test suite
```

Run the dev stack with Docker Compose:

```bash
docker compose -f compose-dev.yml up
```

## Contributing

Contributions are welcome — please open an issue or submit a pull request.

## License

Released under the [MIT License](LICENSE).
