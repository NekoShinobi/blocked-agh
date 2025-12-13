# Blocked AGH

## Why?

I wanted to create a simple site where my family could get a really simple UI to just check to see if a site has been blocked by my AdGuardHome instance and a workflow that will submit an unblock request.

**Please note that the endpoints are not protected at all in anyway, so do not use this over public networks.**

(Disclaimer, Rest of README written mostly by Claude)

A web interface for checking if URLs are blocked by AdGuard Home and requesting unblocks through notifications.

## Features

- 🔍 **URL Checker** - Simple web UI to check if a URL is blocked by AdGuard Home
- 🚫 **Block Status Detection** - Displays clear status indicators:
  - ✅ Not Blocked (green)
  - ⚪ Whitelisted (light blue)
  - 🔴 Blocked (red)
- 🔔 **Unblock Requests** - Send unblock requests via Ntfy notifications with one-click approval
- 🎨 **Customizable Background** - Configure your own background image via environment variable
- 🐳 **Docker Ready** - Easy deployment with Docker Compose

## Screenshots

The web interface features a clean, modern design with a blurred background image and a centered input box for checking URLs.

![alt text](https://github.com/xNinjaKittyx/blocked-agh/blob/main/screenshot.jpg?raw=true)


## Requirements

- Python 3.13+
- AdGuard Home instance
- Ntfy server (for unblock notifications)

## Installation

### Using Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/yourusername/blocked-agh.git
cd blocked-agh
```

2. Copy the example compose file:
```bash
cp compose.example.yml compose.yml
```

3. Edit `compose.yml` with your configuration:
```yaml
environment:
  - ADGUARDHOME_URL=http://your-adguard-home:3000
  - ADGUARDHOME_USER=admin
  - ADGUARDHOME_PASS=your_actual_password
  - BLOCKED_AGH_URL=http://your-server:8000
  - NTFY_URL=https://ntfy.sh
  - NTFY_TOPIC=YourUnblockTopic
  - NTFY_TOKEN=your_actual_ntfy_token
  - BACKGROUND_IMAGE_URL=https://example.com/your-image.jpg
```

4. Start the service:
```bash
docker compose up -d
```

### Manual Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/blocked-agh.git
cd blocked-agh
```

2. Install dependencies using uv:
```bash
uv sync
```

3. Set environment variables:
```bash
export ADGUARDHOME_URL=http://your-adguard-home:3000
export ADGUARDHOME_USER=admin
export ADGUARDHOME_PASS=your_password
export BLOCKED_AGH_URL=http://localhost:8000
export NTFY_URL=https://ntfy.sh
export NTFY_TOPIC=UnblockRequests
export NTFY_TOKEN=your_ntfy_token
export BACKGROUND_IMAGE_URL=https://example.com/image.jpg
```

4. Run the application:
```bash
uv run uvicorn blocked_agh.web:app --host 0.0.0.0 --port 8000
```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `ADGUARDHOME_URL` | AdGuard Home API URL | Yes | - |
| `ADGUARDHOME_USER` | AdGuard Home username | Yes | `admin` |
| `ADGUARDHOME_PASS` | AdGuard Home password | Yes | - |
| `BLOCKED_AGH_URL` | Public URL of this service | Yes | `http://localhost:8000` |
| `NTFY_URL` | Ntfy server URL | No | `https://ntfy.sh` |
| `NTFY_TOPIC` | Ntfy topic for notifications | Yes | `UnblockRequests` |
| `NTFY_TOKEN` | Ntfy authentication token | Yes | - |
| `BACKGROUND_IMAGE_URL` | URL for background image | No | - |

## Usage

1. Navigate to `http://localhost:8000` (or your configured URL)
2. Enter a URL in the input box
3. Click "Check URL" or press Enter
4. View the block status:
   - **Not Blocked** - URL is allowed
   - **Whitelisted** - URL is explicitly whitelisted
   - **Blocked** - URL is blocked by AdGuard Home
5. If blocked, click "Request Unblock" to send a notification
6. Approve the unblock from your Ntfy notification

## API Endpoints

### `POST /api/checkurl`
Check if a URL is blocked by AdGuard Home.

**Request:**
```json
{
  "url": "example.com"
}
```

**Response:**
```json
{
  "url": "example.com",
  "status": "NotFilteredNotFound|NotFilteredWhiteList|FilteredBlackList",
  "result": { ... }
}
```

### `POST /api/request_unblock`
Request to unblock a URL (sends notification).

**Request:**
```json
{
  "url": "example.com"
}
```

**Response:**
```json
{
  "url": "example.com",
  "message": "Unblock request notification sent successfully"
}
```

### `POST /api/unblock_url`
Unblock a URL in AdGuard Home (called from notification action).

**Request:**
```json
{
  "url": "example.com"
}
```

**Response:**
```json
{
  "url": "example.com",
  "message": "Unblock request completed successfully"
}
```

## Development

1. Install development dependencies:
```bash
uv sync
```

2. Run with auto-reload:
```bash
uv run uvicorn blocked_agh.web:app --reload
```

3. Run with Docker Compose in development mode:
```bash
docker compose -f compose-dev.yml up
```

## How It Works

1. **URL Check**: The service queries AdGuard Home's filtering API to check if a URL is blocked
2. **Unblock Request**: When a user requests an unblock, a notification is sent to Ntfy with an action button
3. **One-Click Approval**: Clicking the notification button calls the `/api/unblock_url` endpoint
4. **AdGuard Update**: The service adds an allowlist rule to AdGuard Home using the format `@@||domain.com^$important`

## License

See [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter any issues or have questions, please open an issue on GitHub.
