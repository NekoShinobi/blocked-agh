import json
import logging
import os

import aiohttp

from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route


ADGUARDHOME_URL = os.getenv("ADGUARDHOME_URL", "")
ADGUARDHOME_USER = os.getenv("ADGUARDHOME_USER", "admin")
ADGUARDHOME_PASS = os.getenv("ADGUARDHOME_PASS", "")

NTFY_URL = os.getenv("NTFY_URL", "https://ntfy.urfmode.moe")
NTFY_TOKEN = os.getenv("NTFY_TOKEN", "")
NTFY_TOPIC = os.getenv("NTFY_TOPIC", "UnblockRequests")

BLOCKED_AGH_URL = os.getenv("BLOCKED_AGH_URL", "http://localhost:8000")
BACKGROUND_IMAGE_URL = os.getenv("BACKGROUND_IMAGE_URL", "")

# CORS configuration - comma-separated list of allowed origins
# Example: "http://localhost:3000,https://example.com,https://app.example.com"
# Use "*" to allow all origins (not recommended for production)
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if os.getenv("CORS_ALLOWED_ORIGINS") else []

if not all(
    (
        ADGUARDHOME_URL,
        ADGUARDHOME_USER,
        ADGUARDHOME_PASS,
        NTFY_TOKEN,
        NTFY_TOPIC,
        BLOCKED_AGH_URL,
    )
):
    raise ValueError("One or more required environment variables are missing.")


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
# Create formatter and set formatter.
formatter = logging.Formatter("%(asctime)s::%(levelname)s:%(module)s:%(lineno)d - %(message)s")

sh = logging.StreamHandler()
sh.setFormatter(formatter)
logger.addHandler(sh)


# The UI portion of this is mostly vibe-coded.
async def homepage(request):  # noqa: RUF029
    # CSS styles with dynamic background image
    # ruff: disable[E501]
    styles = f"""
        <style>
            :root {{
                --accent: #818cf8;
                --accent-strong: #6366f1;
                --glass: rgba(255, 255, 255, 0.08);
                --glass-border: rgba(255, 255, 255, 0.16);
                --field: rgba(255, 255, 255, 0.07);
                --field-border: rgba(255, 255, 255, 0.14);
                --text: #f8fafc;
                --text-muted: rgba(248, 250, 252, 0.62);
                --radius: 18px;
                --ease: cubic-bezier(0.16, 1, 0.3, 1);
            }}
            * {{
                box-sizing: border-box;
            }}
            body {{
                margin: 0;
                padding: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                min-height: 100vh;
                position: relative;
                color: var(--text);
                background:
                    radial-gradient(1200px 600px at 15% -10%, #312e81 0%, transparent 60%),
                    radial-gradient(1000px 700px at 100% 110%, #4c1d95 0%, transparent 55%),
                    linear-gradient(160deg, #0f172a 0%, #1e1b4b 100%);
            }}
            .background {{
                position: fixed;
                inset: -12px;
                background-image: url('{BACKGROUND_IMAGE_URL}');
                background-size: cover;
                background-position: center;
                filter: blur(3px) saturate(115%) contrast(112%) brightness(52%);
                z-index: -1;
            }}
            .content {{
                position: relative;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 24px;
            }}
            .container {{
                text-align: center;
                width: 100%;
                max-width: 440px;
                animation: rise 0.6s var(--ease) both;
            }}
            .brand {{
                display: inline-flex;
                align-items: center;
                gap: 10px;
                margin-bottom: 8px;
            }}
            .brand-dot {{
                width: 10px;
                height: 10px;
                border-radius: 50%;
                background: var(--accent);
                box-shadow: 0 0 0 4px rgba(129, 140, 248, 0.25);
            }}
            h1 {{
                color: var(--text);
                font-size: 2rem;
                font-weight: 700;
                letter-spacing: -0.02em;
                margin: 0;
            }}
            .subtitle {{
                color: var(--text-muted);
                font-size: 0.95rem;
                margin: 6px 0 28px;
            }}
            .card {{
                background: var(--glass);
                -webkit-backdrop-filter: blur(22px) saturate(140%);
                backdrop-filter: blur(22px) saturate(140%);
                border: 1px solid var(--glass-border);
                border-radius: var(--radius);
                padding: 26px;
                box-shadow: 0 24px 60px -20px rgba(0, 0, 0, 0.55);
            }}
            .field {{
                position: relative;
                display: flex;
                align-items: center;
            }}
            .field svg {{
                position: absolute;
                left: 16px;
                width: 18px;
                height: 18px;
                color: var(--text-muted);
                pointer-events: none;
            }}
            input[type="text"] {{
                width: 100%;
                padding: 15px 16px 15px 44px;
                font-size: 15px;
                color: var(--text);
                background: var(--field);
                border: 1px solid var(--field-border);
                border-radius: 12px;
                transition: border-color 0.25s, box-shadow 0.25s, background 0.25s;
            }}
            input[type="text"]::placeholder {{
                color: var(--text-muted);
            }}
            input[type="text"]:focus {{
                outline: none;
                background: rgba(255, 255, 255, 0.11);
                border-color: var(--accent);
                box-shadow: 0 0 0 4px rgba(129, 140, 248, 0.22);
            }}
            button {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                width: 100%;
                margin-top: 14px;
                padding: 14px 24px;
                font-size: 15px;
                font-weight: 600;
                font-family: inherit;
                color: white;
                background: linear-gradient(135deg, var(--accent-strong) 0%, #8b5cf6 100%);
                border: none;
                border-radius: 12px;
                cursor: pointer;
                transition: transform 0.2s var(--ease), box-shadow 0.2s, filter 0.2s;
            }}
            button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 12px 28px -10px rgba(99, 102, 241, 0.7);
            }}
            button:active {{
                transform: translateY(0);
            }}
            button:disabled {{
                cursor: default;
                opacity: 0.75;
                transform: none;
                box-shadow: none;
                filter: saturate(0.8);
            }}
            .spinner {{
                width: 16px;
                height: 16px;
                border: 2px solid rgba(255, 255, 255, 0.4);
                border-top-color: #fff;
                border-radius: 50%;
                animation: spin 0.7s linear infinite;
            }}
            #result {{
                margin-top: 16px;
                padding: 14px 16px;
                border-radius: 12px;
                display: none;
                align-items: center;
                gap: 10px;
                font-size: 15px;
                font-weight: 600;
                text-align: left;
                border: 1px solid transparent;
                animation: rise 0.35s var(--ease) both;
            }}
            #result.show {{
                display: flex;
            }}
            #result::before {{
                content: '';
                width: 9px;
                height: 9px;
                border-radius: 50%;
                flex: 0 0 auto;
                background: currentColor;
                box-shadow: 0 0 10px currentColor;
            }}
            .not-blocked {{
                background: rgba(34, 197, 94, 0.14);
                color: #4ade80;
                border-color: rgba(34, 197, 94, 0.32) !important;
            }}
            .whitelisted {{
                background: rgba(56, 189, 248, 0.14);
                color: #38bdf8;
                border-color: rgba(56, 189, 248, 0.32) !important;
            }}
            .blocked {{
                background: rgba(239, 68, 68, 0.14);
                color: #f87171;
                border-color: rgba(239, 68, 68, 0.32) !important;
            }}
            .error {{
                background: rgba(245, 158, 11, 0.14);
                color: #fbbf24;
                border-color: rgba(245, 158, 11, 0.32) !important;
            }}
            #unblockBtn {{
                display: none;
                margin-top: 12px;
                background: linear-gradient(135deg, #f43f5e 0%, #ec4899 100%);
            }}
            #unblockBtn:hover {{
                box-shadow: 0 12px 28px -10px rgba(244, 63, 94, 0.7);
            }}
            .footnote {{
                margin-top: 22px;
                font-size: 0.78rem;
                color: var(--text-muted);
            }}
            @keyframes rise {{
                from {{ opacity: 0; transform: translateY(12px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            @keyframes spin {{
                to {{ transform: rotate(360deg); }}
            }}
            @media (prefers-reduced-motion: reduce) {{
                *, *::before, *::after {{
                    animation-duration: 0.001ms !important;
                    transition-duration: 0.001ms !important;
                }}
            }}
        </style>
    """

    # HTML body content
    body = """
        <div class="background"></div>
        <div class="content">
            <div class="container">
                <div class="brand">
                    <span class="brand-dot"></span>
                    <h1>URL Checker</h1>
                </div>
                <p class="subtitle">Check if a domain is blocked by AdGuard Home</p>
                <div class="card">
                    <div class="field">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                            <circle cx="11" cy="11" r="8"></circle>
                            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                        </svg>
                        <input type="text" id="urlInput" placeholder="e.g. logs.netflix.com" autocomplete="off" spellcheck="false" />
                    </div>
                    <button id="checkBtn" onclick="checkUrl()">Check URL</button>
                    <div id="result" role="status" aria-live="polite"></div>
                    <button id="unblockBtn" onclick="requestUnblock()">Request Unblock</button>
                </div>
                <p class="footnote">Powered by AdGuard Home</p>
            </div>
        </div>
    """

    # JavaScript code
    script = """
        <script>
            let currentUrl = '';

            function showResult(text, kind) {
                const resultDiv = document.getElementById('result');
                resultDiv.textContent = text;
                resultDiv.className = 'show ' + kind;
            }

            function setLoading(button, isLoading, label) {
                if (isLoading) {
                    button.disabled = true;
                    button.dataset.label = button.textContent;
                    button.innerHTML = '<span class="spinner"></span>' + (label || 'Working...');
                } else {
                    button.disabled = false;
                    button.textContent = button.dataset.label || button.textContent;
                }
            }

            async function checkUrl() {
                const urlInput = document.getElementById('urlInput');
                const checkBtn = document.getElementById('checkBtn');
                const unblockBtn = document.getElementById('unblockBtn');
                const url = urlInput.value.trim();

                unblockBtn.style.display = 'none';

                if (!url) {
                    showResult('Please enter a URL', 'error');
                    return;
                }

                setLoading(checkBtn, true, 'Checking...');
                try {
                    const response = await fetch('/api/checkurl', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ url: url })
                    });

                    const data = await response.json();
                    currentUrl = url;

                    if (data.status === 'NotFilteredNotFound') {
                        showResult('Not Blocked', 'not-blocked');
                    } else if (data.status === 'NotFilteredWhiteList') {
                        showResult('Whitelisted', 'whitelisted');
                    } else if (data.status === 'FilteredBlackList') {
                        showResult('Blocked', 'blocked');
                        unblockBtn.style.display = 'flex';
                    } else {
                        showResult('Status: ' + data.status, 'error');
                    }
                } catch (error) {
                    showResult('Error: ' + error.message, 'error');
                } finally {
                    setLoading(checkBtn, false);
                }
            }

            async function requestUnblock() {
                const unblockBtn = document.getElementById('unblockBtn');

                if (!currentUrl) {
                    return;
                }

                setLoading(unblockBtn, true, 'Sending...');
                try {
                    const response = await fetch('/api/request_unblock', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ url: currentUrl })
                    });

                    const data = await response.json();

                    if (response.ok) {
                        showResult(data.message || 'Unblock request submitted successfully', 'whitelisted');
                        setLoading(unblockBtn, false);
                        unblockBtn.style.display = 'none';
                    } else {
                        showResult('Failed to submit unblock request: ' + (data.error || 'Unknown error'), 'error');
                        setLoading(unblockBtn, false);
                    }
                } catch (error) {
                    showResult('Error: ' + error.message, 'error');
                    setLoading(unblockBtn, false);
                }
            }

            document.getElementById('urlInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    checkUrl();
                }
            });
        </script>
    """

    # Combine all parts
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>URL Checker</title>
        {styles}
    </head>
    <body>
        {body}
        {script}
    </body>
    </html>
    """
    # ruff: enable[E501]
    return HTMLResponse(html_content)


async def get_agh_token(session):
    async with session.post(
        f"{ADGUARDHOME_URL}/control/login",
        json={"name": ADGUARDHOME_USER, "password": ADGUARDHOME_PASS},
    ) as resp:
        logger.info(await resp.text())
        if resp.status != 200:
            logger.error(f"Failed to login to AdGuard Home: {resp.status}")
            return None

        agh_session = resp.cookies.get("agh_session")
        logger.info("Successfully logged in to AdGuard Home")
        return agh_session.value if agh_session else None


async def check_url(request):
    data = await request.json()
    url = data.get("url", "")
    url = url.lstrip("https://").lstrip("http://")

    async with aiohttp.ClientSession() as session:
        agh_token = await get_agh_token(session)
        if not agh_token:
            return JSONResponse({"error": "Failed to authenticate with AdGuard Home"}, status_code=500)
        async with session.get(
            f"{ADGUARDHOME_URL}/control/filtering/check_host",
            params={"name": url, "qtype": "A"},
            cookies={"agh_session": agh_token},
        ) as resp:
            if resp.status != 200:
                return JSONResponse({"error": f"Failed to check URL: {resp.text}"}, status_code=500)
            result = await resp.json()
            logger.info(f"URL {url} check result: {result}")

    return JSONResponse({"url": url, "status": result["reason"], "result": result})


async def request_unblock(request):
    data = await request.json()
    url = data.get("url", "")

    # First make a notification to ntfy with NTFY_TOKEN on NTFY_TOPIC with a button that calls unblock_url endpoint.
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://ntfy.urfmode.moe/",
            headers={"Authorization": f"Bearer {NTFY_TOKEN}"},
            data=json.dumps(
                {
                    "topic": NTFY_TOPIC,
                    "title": "Unblock Request",
                    "message": f"Request to unblock URL: {url}",
                    "actions": [
                        {
                            "action": "http",
                            "label": "Unblock URL",
                            "url": f"{BLOCKED_AGH_URL}/api/unblock_url",
                            "method": "POST",
                            "headers": {
                                "Content-Type": "application/json",
                            },
                            "body": json.dumps({"url": url}),
                            "clear": True,
                        }
                    ],
                }
            ),
        ) as resp:
            if resp.status != 200:
                return JSONResponse(
                    {"error": f"Failed to send notification: {await resp.text()}"},
                    status_code=500,
                )
            logger.info(f"Unblock request notification sent for URL: {url}")

    return JSONResponse(
        {
            "url": url,
            "message": "Unblock request notification sent successfully",
        }
    )


async def unblock_url(request):
    data = await request.json()
    url = data.get("url", "")

    async with aiohttp.ClientSession() as session:
        agh_token = await get_agh_token(session)
        if not agh_token:
            return JSONResponse({"error": "Failed to authenticate with AdGuard Home"}, status_code=500)
        async with session.get(f"{ADGUARDHOME_URL}/control/filtering/status") as resp:
            if resp.status != 200:
                return JSONResponse(
                    {"error": f"Failed to get filtering status: {resp.text}"},
                    status_code=500,
                )
            status = await resp.json()
            logger.info(f"Filtering status retrieved: {status}")

        user_rules = list(status.get("user_rules", []))
        unblock_rule = f"@@||{url}^$important"
        user_rules.append(unblock_rule)

        async with session.post(
            f"{ADGUARDHOME_URL}/control/filtering/set_rules",
            json={"rules": user_rules},
            cookies={"agh_session": agh_token},
        ) as resp:
            if resp.status != 200:
                return JSONResponse({"error": f"Failed to set user rules: {resp.text}"}, status_code=500)
            logger.info(f"Unblock rule added for URL: {url}")

    return JSONResponse({"url": url, "message": "Unblock request completed successfully"})


app = Starlette(
    debug=True,
    routes=[
        Route("/", homepage),
        Route("/api/checkurl", check_url, methods=["POST"]),
        Route("/api/request_unblock", request_unblock, methods=["POST"]),
        Route("/api/unblock_url", unblock_url, methods=["POST"]),
    ],
)

# Add CORS middleware if origins are configured
if CORS_ALLOWED_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
