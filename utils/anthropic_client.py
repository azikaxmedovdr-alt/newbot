import os
import json
import urllib.request
import urllib.error
import asyncio
import logging

logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


async def ask_agent(system_prompt: str, history: list, user_message: str) -> str:
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is not set!")

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    body = json.dumps({
        "model": "openrouter/auto",
        "messages": messages,
        "max_tokens": 1024
    }).encode("utf-8")

    req = urllib.request.Request(
        OPENROUTER_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://virtual-office-bot.railway.app",
            "X-Title": "Virtual Office Bot"
        },
        method="POST"
    )

    def do_request():
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8")
            logger.error(f"OpenRouter error {e.code}: {body}")
            raise

    loop = asyncio.get_event_loop()

    for attempt in range(3):
        try:
            data = await loop.run_in_executor(None, do_request)
            return data["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 2:
                wait = 15 * (attempt + 1)
                logger.info(f"Rate limited, waiting {wait}s (attempt {attempt+1}/3)...")
                await asyncio.sleep(wait)
            else:
                raise

    raise Exception("РЎРµСЂРІРёСЃ РІСЂРµРјРµРЅРЅРѕ РЅРµРґРѕСЃС‚СѓРїРµРЅ. РџРѕРїСЂРѕР±СѓР№С‚Рµ С‡РµСЂРµР· РјРёРЅСѓС‚Сѓ.")

