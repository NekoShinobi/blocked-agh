import json
import logging
import os

import aiohttp

from starlette.applications import Starlette
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
            body {{
                margin: 0;
                padding: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                min-height: 100vh;
                position: relative;
                overflow: hidden;
            }}
            .background {{
                position: fixed;
                top: -10px;
                left: -10px;
                width: calc(100% + 20px);
                height: calc(100% + 20px);
                background-image: url('{BACKGROUND_IMAGE_URL}');
                background-size: cover;
                background-position: center;
                filter: blur(2px) saturate(120%) contrast(120%) brightness(50%);
                z-index: -1;
            }}
            .content {{
                position: relative;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .container {{
                text-align: center;
                padding: 40px;
                max-width: 600px;
                width: 90%;
            }}
            h1 {{
                color: white;
                font-size: 3em;
                margin-bottom: 40px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
            }}
            .input-container {{
                filter: none !important;
                background: white;
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            }}
            input[type="text"] {{
                width: 100%;
                padding: 15px;
                font-size: 16px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                box-sizing: border-box;
                transition: border-color 0.3s;
            }}
            input[type="text"]:focus {{
                outline: none;
                border-color: #667eea;
            }}
            button {{
                margin-top: 15px;
                padding: 15px 40px;
                font-size: 16px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                transition: transform 0.2s, box-shadow 0.2s;
                font-weight: 600;
            }}
            button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 5px 20px rgba(0,0,0,0.3);
            }}
            button:active {{
                transform: translateY(0);
            }}
            #result {{
                margin-top: 20px;
                padding: 15px;
                border-radius: 8px;
                display: none;
                font-size: 18px;
                font-weight: 600;
            }}
            .not-blocked {{
                background: #d4edda;
                color: #28a745;
                border: 1px solid #c3e6cb;
            }}
            .whitelisted {{
                background: #d1ecf1;
                color: #17a2b8;
                border: 1px solid #bee5eb;
            }}
            .blocked {{
                background: #f8d7da;
                color: #dc3545;
                border: 1px solid #f5c6cb;
            }}
            .error {{
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }}
            #unblockBtn {{
                display: none;
                margin-top: 10px;
                background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
            }}
            #unblockBtn:hover {{
                background: linear-gradient(135deg, #ff5252 0%, #e04b5f 100%);
            }}
            .button-container {{
                display: flex;
                justify-content: center;
            }}
        </style>
    """

    # HTML body content
    body = """
        <div class="background"></div>
        <div class="content">
            <div class="container">
                <h1>URL Checker</h1>
                <div class="input-container">
                    <input type="text" id="urlInput" placeholder="Enter URL to check if blocked by AGH" />
                    <button onclick="checkUrl()">Check URL</button>
                    <div id="result"></div>
                    <div class="button-container">
                        <button id="unblockBtn" onclick="requestUnblock()">Request Unblock</button>
                    </div>
                </div>
            </div>
        </div>
    """

    # JavaScript code
    script = """
        <script>
            let currentUrl = '';

            async function checkUrl() {
                const urlInput = document.getElementById('urlInput');
                const resultDiv = document.getElementById('result');
                const unblockBtn = document.getElementById('unblockBtn');
                const url = urlInput.value.trim();

                unblockBtn.style.display = 'none';

                if (!url) {
                    resultDiv.textContent = 'Please enter a URL';
                    resultDiv.className = 'error';
                    resultDiv.style.display = 'block';
                    return;
                }

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
                        resultDiv.textContent = 'Not Blocked';
                        resultDiv.className = 'not-blocked';
                    } else if (data.status === 'NotFilteredWhiteList') {
                        resultDiv.textContent = 'Whitelisted';
                        resultDiv.className = 'whitelisted';
                    } else if (data.status === 'FilteredBlackList') {
                        resultDiv.textContent = 'Blocked';
                        resultDiv.className = 'blocked';
                        unblockBtn.style.display = 'block';
                    } else {
                        resultDiv.textContent = 'Status: ' + data.status;
                        resultDiv.className = 'error';
                    }

                    resultDiv.style.display = 'block';
                } catch (error) {
                    resultDiv.textContent = 'Error: ' + error.message;
                    resultDiv.className = 'error';
                    resultDiv.style.display = 'block';
                }
            }

            async function requestUnblock() {
                const resultDiv = document.getElementById('result');
                const unblockBtn = document.getElementById('unblockBtn');

                if (!currentUrl) {
                    return;
                }

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
                        resultDiv.textContent = data.message || 'Unblock request submitted successfully';
                        resultDiv.className = 'whitelisted';
                        unblockBtn.style.display = 'none';
                    } else {
                        resultDiv.textContent = 'Failed to submit unblock request: ' + (data.error || 'Unknown error');
                        resultDiv.className = 'error';
                    }
                } catch (error) {
                    resultDiv.textContent = 'Error: ' + error.message;
                    resultDiv.className = 'error';
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
